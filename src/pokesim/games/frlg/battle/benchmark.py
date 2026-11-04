"""FireRed/LeafGreen (Gen 3) seeded trials, Wilson intervals, and replay traces."""

from collections import Counter
import copy
import hashlib
import json
import math
import random

from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI, move_id
from pokesim.games.frlg.battle.engine import BRIDGE, Engine
from pokesim.games.frlg.battle.schema import validate_cases
from pokesim.games.frlg.battle.policy import POLICY, locked, player_action, replacement, trainer_item


def wilson(wins, total):
    """95% binomial Wilson interval, including all-win and all-loss samples."""
    z = 1.959963984540054
    p = wins / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, center - radius), min(1.0, center + radius)]


def scenario_for(case, pret):
    """Resolve a fixture to the exact team and supplies sent to the engine."""
    trainer = copy.deepcopy(pret["trainers"][case["trainer"]])
    trainer["bag"] = dict(Counter(move_id(item) for item in trainer["items"]))
    result = copy.deepcopy(case)
    result["trainer"] = trainer
    result["bag"] = {move_id(k): v for k, v in result.get("bag", {}).items()}
    return result


def reveal(state, known):
    """Track moves visible in the actual battle protocol, for AI history queries."""
    for line in state["log"]:
        parts = line.split("|")
        if len(parts) > 3 and parts[1] == "move" and parts[2].startswith("p1a:"):
            known.add(move_id(parts[3]))
    state["own"]["revealed_moves"] = [m for m in state["own"]["moves"] if m["id"] in known]


def trial(engine, scenario, ai, master_seed, index, turn_limit):
    """One complete battle, retaining decisions, state, and engine protocol."""
    trial_seed = "{}:{}".format(master_seed, index)
    seeds = random.Random("engine:" + trial_seed)
    engine_seed = [seeds.randrange(65536) for _ in range(4)]
    rng = random.Random("ai:" + trial_seed)
    state = engine.request(command="start", scenario=scenario, seed=engine_seed)
    known, decisions, log = set(), [], list(state["log"])
    flags = scenario["trainer"]["ai"]
    items = [move_id(item) for item in scenario["trainer"]["items"]]
    while not state["ended"] and state["turn"] <= turn_limit:
        reveal(state, known)
        if state["needs_switch"]:
            own, foe = {"kind": "pass"}, replacement(state)
        else:
            own = player_action(state, ai, flags, items,
                enable_complex_planning=scenario.get('enable_complex_planning', False),
                planning_goals=scenario.get('planning_goals'))
            foe = locked(state["foe"]) or trainer_item(state, items) or ai.choose_move(state, flags, rng)
        decisions.append({"turn": state["turn"], "hp": state["own"]["hp"],
            "foe": state["foe"]["species"], "foe_hp": state["foe"]["hp"], "own": own, "opponent": foe})
        state = engine.request(command="step", own=own, foe=foe)
        log.extend(state["log"])
    won = state["winner"] == "Player"
    outcome = "win" if won else ("loss" if state["ended"] else "turn_limit")
    evidence = state["own"].get("faint") or state["own"]
    return {"outcome": outcome, "turns": state["turn"] - 1,
        "items_used": state["items_used"], "trainer_items_used": state["trainer_items_used"],
        "foe_at_end": state["foe"]["species"], "status_at_end": evidence["status"],
        "volatiles_at_end": evidence["volatiles"], "boosts_at_end": evidence["boosts"],
        "final_damage_effect": evidence.get("effect"), "hp_remaining": state["own"]["hp"],
        "seed": {"master": master_seed, "trial": index, "engine": engine_seed},
        "progression": state.get("progression"),
        "decisions": decisions, "log": log}


def evaluate(cases, pret, battles=1000, seed=1, turn_limit=200, progress=None, sampling=None, family_size=None):
    """Report probabilities conditional on this model, inputs, and policies."""
    if not isinstance(battles, int) or isinstance(battles, bool) or battles < 1:
        raise ValueError("battles must be a positive integer")
    if not isinstance(turn_limit, int) or turn_limit < 1:
        raise ValueError("turn_limit must be a positive integer")
    validate_cases(cases, pret)
    family_size = len(cases) if family_size is None else family_size
    if type(family_size) is not int or family_size < len(cases):
        raise ValueError('Sampling family must include all requested cases')
    if sampling is not None and sampling.minimum > battles:
        raise ValueError("Minimum trials exceeds maximum trial budget")
    ai = NPCTrainerAI(pret)
    results = []
    with Engine() as engine:
        for case in cases:
            scenario = scenario_for(case, pret)
            wins, turns, hp = 0, 0, 0
            losses, states, outcomes = Counter(), Counter(), Counter()
            final_effects, used, trainer_used, examples = Counter(), Counter(), Counter(), {}
            sampling_result = None
            for index in range(battles):
                played = trial(engine, scenario, ai, seed, index, turn_limit)
                outcomes[played["outcome"]] += 1
                wins += played["outcome"] == "win"
                turns += played["turns"]
                hp += played["hp_remaining"]
                used.update(played["items_used"])
                trainer_used.update(played["trainer_items_used"])
                if played["outcome"] != "win":
                    losses[played["foe_at_end"]] += 1
                    if played["final_damage_effect"]:
                        final_effects[played["final_damage_effect"]] += 1
                    if played["boosts_at_end"].get("accuracy", 0) < 0:
                        states["accuracy_down"] += 1
                    for status in [played["status_at_end"]] + played["volatiles_at_end"]:
                        if status:
                            states[status] += 1
                examples.setdefault(played["outcome"], played)
                if progress and (index + 1) % min(100, battles) == 0:
                    progress(case["id"], index + 1, battles)
                if sampling is not None:
                    checked = sampling.check(wins, index + 1, battles, family_size)
                    if checked is not None:
                        sampling_result = checked
                        if checked["stop_reason"]:
                            break
            completed = index + 1
            result = {"id": case["id"], "inputs": scenario, "battles": completed,
                "wins": wins, "win_probability": wins / completed,
                "outcomes": dict(outcomes), "mean_turns": turns / completed, "mean_hp_remaining": hp / completed,
                "mean_items_used": {k: v / completed for k, v in used.items()},
                "mean_trainer_items_used": {k: v / completed for k, v in trainer_used.items()},
                "losses_by_foe": dict(losses), "conditions_present_at_loss": dict(states),
                "final_damage_effects": dict(final_effects),
                "examples": examples}
            if sampling is not None:
                result.update(confidence_sequence=sampling_result, maximum_battles=battles)
            else:
                result["wilson_95"] = wilson(wins, completed)
            results.append(result)
    fingerprint = hashlib.sha256(json.dumps(pret, sort_keys=True).encode()).hexdigest()
    report = {"format": "pokesim-frlg-report/1", "seed": seed, "turn_limit": turn_limit,
        "policy": POLICY, "engine": json.loads((BRIDGE / "package.json").read_text())["dependencies"],
        "engine_lock_sha256": hashlib.sha256((BRIDGE / "package-lock.json").read_bytes()).hexdigest(),
        "pret_source": pret["source"], "pret_snapshot_sha256": fingerprint,
        "assumptions": ["Solo lead: no player switching; a fainted lead loses.",
            "pret scoring scripts; Smogon damage helpers approximate pret AI_CalcDmg.",
            "No voluntary opponent switching; mandatory replacements use pret-derived rules.",
            "Python AI RNG and Showdown battle RNG are separate seeded streams, not cartridge RNG emulation.",
            "Only listed fixture stats are measured; remaining stats use the recorded assumptions.",
            "Cases with progression data award solo EXP/EVs and learn moves after actual knockouts; legacy fixtures keep level/stats/moves fixed.",
            "Conditions at loss are descriptive, not proven causes of loss.",
            "Turn-limit outcomes count as non-wins and are also reported separately."],
        "results": results}
    if sampling is not None:
        report["sampling"] = sampling.describe(family_size)
        report["assumptions"].append("Confidence sequences cover modeled win-within-turn-limit probabilities across all requested cases and all sampling looks; they do not cover input or engine error.")
    return report

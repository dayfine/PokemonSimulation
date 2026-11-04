"""Reconcile observed FRLG starting states; this does not simulate the fights.

Inventory/PP follow recorded acquisitions and actual executed moves. HP at
battle end is a sourced observation, not damage calculated by this module.
EVs accumulate immediately; summary stats refresh only on level/evolution.
"""

from collections import defaultdict

from pokesim.games.frlg.progression.ledger import audit, fingerprint, video_time
from pokesim.games.frlg.progression.moves import reconstruct_moves, move_names
from pokesim.games.frlg.progression.stats import ORDER, gain_evs, summary_stats

MEDICINE = {"POTION": 20, "SUPER_POTION": 50, "HYPER_POTION": 200,
            "MAX_POTION": 999, "FULL_RESTORE": 999, "ORAN_BERRY": 10}
CURES = {"PARLYZ_HEAL": ("par",), "ANTIDOTE": ("psn", "tox"), "AWAKENING": ("slp",),
         "BURN_HEAL": ("brn",), "ICE_HEAL": ("frz",), "FULL_HEAL": ("par", "psn", "tox", "slp", "brn", "frz")}
PP_ITEMS = {"ETHER", "MAX_ETHER", "ELIXIR", "MAX_ELIXIR"}
BATTLE_ITEMS = set(MEDICINE) | set(CURES) | {"FULL_HEAL", "BURN_HEAL", "ICE_HEAL",
    "X_ATTACK", "X_DEFEND", "X_SPECIAL", "X_SPEED", "X_ACCURACY", "DIRE_HIT", "GUARD_SPEC",
    "ETHER", "MAX_ETHER", "ELIXIR", "MAX_ELIXIR", "POKE_BALL"}


def reconstruct_states(route, reference, moves, history):
    """Export every recorded encounter's player state under a declared profile."""
    if history.get("format") != "pokesim-frlg-state-history/1":
        raise ValueError("Unsupported state history format")
    exp_run = audit(route, reference, "observed_wild_wins")
    move_run = reconstruct_moves(route, reference, moves)
    profile = history["profile"]
    nature = reference["natures"][profile["nature"]]
    ivs, evs = profile["ivs"], dict(profile["initial_evs"])
    if set(ivs) != set(ORDER) or any(type(n) is not int or not 0 <= n <= 31 for n in ivs.values()):
        raise ValueError("Six valid IVs are required")
    if any(evs[s] != 0 for s in ORDER):
        raise ValueError("This gift-starter reconstruction requires zero initial EVs")
    events = {e["id"]: e for e in route["events"]}
    battle_ids = {e["id"] for e in route["events"] if e["kind"] in ("trainer_battle", "wild_battle", "scripted_battle")}
    if set(history["battles"]) != battle_ids:
        raise ValueError("State history must cover every lead encounter exactly once")
    preparation, decisions, checks = defaultdict(list), defaultdict(list), defaultdict(list)
    for action in history["before_events"]:
        if action["before_event"] not in events or not action.get("evidence"):
            raise ValueError("Unsourced or unknown preparation event")
        preparation[action["before_event"]].append(action)
    for decision in move_run["changes"]:
        when = decision["when"]
        decisions[(when["event"], when["at"], when.get("foe_index"))].append(decision)
    for check in history.get("checks", []):
        if check["event"] not in events or not check.get("evidence"):
            raise ValueError("Unsourced or unknown state checkpoint")
        if check["at"] == "after_foe" and set(check) - {"event", "at", "foe_index", "stats", "evidence"}:
            raise ValueError("After-foe checkpoints support raw stats only; HP/PP use battle boundaries")
        checks[(check["event"], check["at"], check.get("foe_index"))].append(check)

    species, level = route["lead"]["species"], route["lead"]["level"]
    stat_evs = dict(evs)
    stats = summary_stats(reference["species"][species]["base_stats"], level, ivs, stat_evs, nature)
    hp, status, held, badges = stats["hp"], "", "", []
    pp = {m: reference["move_pp"][m] for m in move_run["initial_moves"]}
    bag = defaultdict(int)
    transactions, snapshots, passed = [], [], []

    def refresh():
        nonlocal stats, stat_evs, hp
        stat_evs = dict(evs)
        new = summary_stats(reference["species"][species]["base_stats"], level, ivs, stat_evs, nature)
        hp += new["hp"] - stats["hp"]
        stats = new

    def spend(item, quantity, origin):
        if type(quantity) is not int or quantity < 1 or bag[item] < quantity:
            raise ValueError("Negative or invalid inventory at {}: {}".format(origin, item))
        before = bag[item]
        bag[item] -= quantity
        transactions.append({"event": origin, "item": item, "delta": -quantity,
                             "before": before, "after": bag[item]})

    def apply_move(name, phase, index=None):
        for decision in decisions[(name, phase, index)]:
            if decision["action"] == "learn":
                if decision.get("replaces"):
                    del pp[decision["replaces"]]
                pp[decision["move"]] = reference["move_pp"][decision["move"]]

    def check_state(name, phase, index=None):
        for check in checks[(name, phase, index)]:
            for label, actual in (("hp", hp), ("max_hp", stats["hp"]), ("status", status)):
                if label in check and check[label] != actual:
                    raise ValueError("{} mismatch at {}: {} != {}".format(label, name, actual, check[label]))
            for label, actual in (("stats", stats), ("pp", pp), ("bag", bag)):
                for key, expected in check.get(label, {}).items():
                    if label != "bag" and key not in actual:
                        raise ValueError("Unknown {} checkpoint key: {}".format(label, key))
                    if actual.get(key, 0) != expected:
                        raise ValueError("{} {} mismatch at {}: {} != {}".format(label, key, name, actual.get(key, 0), expected))
            for reading in check.get("pp_readings", []):
                if pp[reading["move"]] - reading.get("spent_since_entry", 0) != reading["remaining"]:
                    raise ValueError("PP reading mismatch at " + name)
            passed.append({"event": name, "at": phase, "foe_index": index, "evidence": check["evidence"]})

    def current():
        alternative = dict(ivs, atk=profile["alternate_attack_iv"])
        return {"species": species, "level": level, "hp": hp, "max_hp": stats["hp"],
            "status": status, "stats": dict(stats), "nature": profile["nature"], "ivs": dict(ivs),
            "gender": profile["gender"], "ability": reference["species"][species]["abilities"][0],
            "evs_earned": dict(evs), "evs_applied_to_stats": dict(stat_evs),
            "alternate_attack_iv_stats": summary_stats(reference["species"][species]["base_stats"], level, alternative, stat_evs, nature),
            "pp": dict(pp), "held_item": held, "badges": list(badges),
            "inventory": dict(sorted((item, count) for item, count in bag.items() if count)),
            "battle_bag": dict(sorted((item, count) for item, count in bag.items() if count and item in BATTLE_ITEMS))}

    badge_after = {"brock": "boulder", "misty": "cascade", "surge": "thunder", "koga": "soul",
        "blaine": "volcano", "erika": "rainbow", "sabrina": "marsh", "giovanni-gym": "earth"}
    for event, row in zip(route["events"], exp_run["timeline"]):
        name = event["id"]
        if row["level_before"] != level:
            raise ValueError("Level progression drift at " + name)
        for action in preparation[name]:
            kind = action["kind"]
            if kind == "acquire":
                for item, quantity in action["items"].items():
                    if type(quantity) is not int or quantity < 1:
                        raise ValueError("Invalid acquisition quantity")
                    before = bag[item]
                    bag[item] += quantity
                    transactions.append({"event": name, "item": item, "delta": quantity, "before": before, "after": bag[item]})
            elif kind == "full_heal":
                hp, status = stats["hp"], ""
                pp = {m: reference["move_pp"][m] for m in pp}
            elif kind == "equip":
                if held:
                    bag[held] += 1
                spend(action["item"], 1, name)
                held = action["item"]
            elif kind == "remove":
                for item, quantity in action["items"].items():
                    spend(item, quantity, name)
            elif kind == "use_item":
                item, quantity = action["item"], action["quantity"]
                if item not in set(MEDICINE) | set(CURES) | PP_ITEMS | {"REPEL", "SUPER_REPEL", "ESCAPE_ROPE"}:
                    raise ValueError("Unsupported out-of-battle item use: " + item)
                spend(item, quantity, name)
                if item in MEDICINE:
                    hp = min(stats["hp"], hp + MEDICINE[item] * quantity)
                if item == "FULL_RESTORE" or status in CURES.get(item, ()):
                    status = ""
                if item in ("ETHER", "MAX_ETHER", "ELIXIR", "MAX_ELIXIR"):
                    targets = [action["move"]] if item in ("ETHER", "MAX_ETHER") else list(pp)
                    for move in targets:
                        pp[move] = min(reference["move_pp"][move], pp[move] + (999 if item.startswith("MAX_") else 10) * quantity)
            else:
                raise ValueError("Unknown preparation kind: " + kind)
        apply_move(name, "before")
        check_state(name, "before")
        entry = current()
        facts = history["battles"].get(name)
        if facts:
            for move, count in facts["move_uses"].items():
                if move not in pp or type(count) is not int or count < 0 or pp[move] < count:
                    raise ValueError("Negative or invalid PP at {}: {}".format(name, move))
                pp[move] -= count
            for item, count in facts["item_uses"].items():
                if item in PP_ITEMS:
                    raise ValueError("In-battle PP recovery requires ordered events")
                if item not in BATTLE_ITEMS:
                    raise ValueError("Unsupported battle item: " + item)
                spend(item, count, name)
        for index, foe in enumerate(row["defeats"]):
            evs = gain_evs(evs, reference["species"][foe["species"]]["ev_yield"], reference["ev_limits"])
            if foe["level_after"] != level:
                level = foe["level_after"]
                refresh()
            apply_move(name, "after_foe", index)
            check_state(name, "after_foe", index)
        if event["kind"] == "rare_candy":
            spend("RARE_CANDY", 1, name)
            level = row["level_after"]
            refresh()
        if event["kind"] == "evolution":
            species = event["species"]
            refresh()
        apply_move(name, "after")
        if facts:
            if (facts.get("evidence_ref", {}).get("event") != name or type(facts["end_hp"]) is not int
                    or not 1 <= facts["end_hp"] <= stats["hp"] or facts["end_status"] not in ("", "par", "psn", "tox", "brn", "frz", "slp")):
                raise ValueError("Invalid or unsourced ending HP at " + name)
            hp, status = facts["end_hp"], facts["end_status"]
            snapshots.append({"event": name, "kind": event["kind"], "video_start": event["video_start"],
                "trainer": event.get("trainer"), "starting_state": entry, "ending_state": current(),
                "observed_move_uses": facts["move_uses"], "observed_item_uses": facts["item_uses"],
                "evidence_ref": facts["evidence_ref"]})
        check_state(name, "after")
        if name in badge_after:
            badges.append(badge_after[name])
    if len(passed) != len(history.get("checks", [])):
        raise ValueError("Unapplied state checkpoint")
    return {"format": "pokesim-frlg-starting-states/1", "source": history["source"], "scope": history["scope"],
        "profile": profile, "history_sha256": fingerprint(history), "reference_sha256": fingerprint(reference),
        "route_sha256": fingerprint(route), "moves_sha256": fingerprint(moves),
        "battles": snapshots, "transactions": transactions, "checks_passed": passed, "move_pp": reference["move_pp"],
        "video_reviews": history["video_reviews"], "corrections": history.get("corrections", []), "final_state": current(),
        "simulation_ready": False,
        "combat_inputs": "Player states only; battle.run.trainer_cases adds NPC and live-progression inputs."}


def states_markdown(report):
    """Readable starting states with complete PP and positive bag counts."""
    lines = ["# Pokeguy battle starting states", "",
        "Reconciled recorded-route inputs, conditional on the sourced events and declared starter profile. These are player-state snapshots, not simulated outcomes or complete engine-ready trainer scenarios.", "",
        "Attack IV25 uses the overlay; the JSON retains the IV24 stat alternative. Raw stats exclude badges and temporary stages. EVs earned after the last level-up/evolution are tracked separately from EVs applied to current stats.", "",
        "HP on exit is a note checkpoint or explicit no-damage carry-forward, carried to the next preparation/battle. PP counts executed moves (misses included, prevented attacks excluded); inventories never silently reset to a later reading. Unknown quest/TM pockets are outside the tracked consumable scope.", "",
        "The JSON also contains all six raw stats, earned/applied EVs, held item, badges, ability, gender, alternative Attack-IV stats, and a conservation log for every inventory transaction.", "",
        "PP is keyed by move identity; display order is not a claim about controller slots. In-battle item quantities are reconciled, but their exact turn placement is not a replay policy.", "",
        "{} source checkpoints pass. {} trainer fights and {} total lead encounters are represented.".format(
            len(report["checks_passed"]), sum(b["kind"] == "trainer_battle" for b in report["battles"]), len(report["battles"])), "",
        "| Video | Battle | Species / level / HP | Moves and PP | Battle consumables on entry |",
        "|---|---|---|---|---|"]
    for battle in report["battles"]:
        s = battle["starting_state"]
        pp = ", ".join("{} {}/{}".format(move_names([m]), value,
            # Maxima are immutable source data, provided in the report below.
            report["move_pp"][m]) for m, value in s["pp"].items())
        bag = ", ".join("{} ×{}".format(item.replace("_", " ").title(), count) for item, count in s["battle_bag"].items()) or "None"
        lines.append("| [{}]({}&t={}) | {} | {} Lv{} {}/{} | {} | {} |".format(
            video_time(battle["video_start"]), report["source"]["video"], battle["video_start"], battle["event"],
            s["species"].title(), s["level"], s["hp"], s["max_hp"], pp, bag))
    lines += ["", "## Focused video reviews", ""]
    for review in report["video_reviews"]:
        lines.append("- [{}]({}&t={}): {}".format(review["topic"], report["source"]["video"],
            int(review["video_start"]), review["result"]))
    lines += ["", "## Reconciled note discrepancies", ""]
    for correction in report["corrections"]:
        lines.append("- {}: {}".format(correction["topic"], correction.get("basis") or correction["reconciled"]))
    lines += ["", "The [trainer benchmark](../battles/pokeguy-benchmark.md) combines these player states with full NPC parties and live progression to estimate conditional per-battle win rates. These state snapshots alone are not complete engine scenarios.", ""]
    return "\n".join(lines)

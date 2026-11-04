"""Basic move, healing, and replacement policies for solo FRLG benchmarks.

Policies inspect current state, never the next RNG draw. Healing is chosen
against a sampled opponent move distribution and current residual damage.
"""

from collections import Counter
import math
import random

POLICY = "solo-greedy-heal/1"
HEALS = {"potion": 20, "superpotion": 50, "hyperpotion": 200,
         "maxpotion": float("inf"), "fullrestore": float("inf")}
CURES = {"slp": "awakening", "psn": "antidote", "tox": "antidote",
         "par": "parlyzheal", "brn": "burnheal", "frz": "iceheal"}


def mean(values):
    return sum(values) / len(values)


def usable(mon):
    return [(i, m) for i, m in enumerate(mon["moves"]) if m["pp"] > 0 and not m["disabled"]]


def locked(mon):
    if mon["locked_move"]:
        return {"kind": "move", "slot": next(i for i, m in enumerate(mon["moves"]) if m["id"] == mon["locked_move"])}
    return None


def attack(state):
    """Fewest expected turns to KO, then accuracy and weaker move to conserve PP."""
    own, foe = state["own"], state["foe"]
    candidates = []
    for slot, move in usable(own):
        expected = mean(move["damage"]) * move["accuracy"] / (2 if move["two_turn"] else 1)
        if expected > 0:
            turns = math.ceil(foe["hp"] / expected)
            if min(move["damage"]) >= foe["hp"] and move["accuracy"] == 1:
                turns = 2 if move["two_turn"] else 1
            candidates.append(((turns, -move["accuracy"], move["power"], -move["pp"]), slot))
    slot = min(candidates)[1] if candidates else (usable(own)[0][0] if usable(own) else 0)
    return {"kind": "move", "slot": slot}


def trainer_item(state, item_order):
    """pret ShouldUseItem: thresholds, status cures, and item-slot restrictions."""
    foe = state["foe"]
    left = sum(p["hp"] > 0 for p in state["party"])
    for index, item in enumerate(item_order):
        if index and left > len(item_order) - index + 1:
            continue
        if not state["trainer_bag"].get(item, 0) or not foe["hp"]:
            continue
        low = foe["hp"] < foe["max_hp"] // 4
        healing = item in HEALS and (low or (item != "fullrestore" and foe["max_hp"] - foe["hp"] > HEALS[item]))
        cure = item == "fullheal" and (foe["status"] or "confusion" in foe["volatiles"])
        if healing or cure:
            return {"kind": "item", "item": item}
    return None


def threat(state, ai, flags, samples=32):
    """An 80th percentile next-turn loss estimate, including existing residuals.

    This is a decision heuristic; Showdown determines the actual turn outcome.
    Sampling uses a separate fixed stream and does not reveal the battle seed.
    """
    rng, counts = random.Random(0), Counter()
    for _ in range(samples):
        counts[ai.choose_move(state, flags, rng)["slot"]] += 1
    own, foe = state["own"], state["foe"]
    residual = own["max_hp"] // 8 * (int(own["status"] in ("psn", "tox")) + int("leechseed" in own["volatiles"]))
    losses = [(residual, 0.0)]
    for slot, count in counts.items():
        move = foe["moves"][slot]
        weight = count / samples
        hit = move["accuracy"] * (0.75 if foe["status"] == "par" else 1)
        if foe["status"] == "slp" and foe["sleep_turns"] > 1:
            hit = 0
        losses.append((residual, weight * (1 - hit)))
        for roll in move["damage"]:
            losses.append((roll + residual, weight * hit * 15 / 16 / len(move["damage"])))
        for roll in move["critical"]:
            losses.append((roll + residual, weight * hit / 16 / len(move["critical"])))
    cumulative, likely = 0.0, residual
    for loss, weight in sorted(losses):
        cumulative += weight
        likely = loss
        if cumulative >= 0.8:
            break
    return {"likely": likely, "mean": sum(loss * weight for loss, weight in losses),
            "max": max(loss for loss, weight in losses if weight)}


def player_action(state, ai, flags, items):
    """Choose a finishing hit, a useful cure/heal, or the best damaging move."""
    own, foe = state["own"], state["foe"]
    forced = locked(own)
    if forced:
        return forced
    choice = attack(state)
    move = own["moves"][choice["slot"]]
    fast = move.get("priority", 0) > 0 or own["speed"] > foe["speed"]
    if (fast and own["status"] not in ("slp", "par", "frz") and "confusion" not in own["volatiles"]
            and not move.get("two_turn") and move.get("accuracy") == 1
            and min(move.get("damage", [0])) >= foe["hp"] and not trainer_item(state, items)):
        return choice
    danger = threat(state, ai, flags)
    # A cure costs a turn. Avoid spending it when that turn is likely fatal.
    cure = CURES.get(own["status"])
    if cure and state["bag"].get(cure, 0) and own["hp"] > danger["likely"]:
        return {"kind": "item", "item": cure}
    if "confusion" in own["volatiles"] and state["bag"].get("fullheal", 0) and own["hp"] > danger["likely"]:
        return {"kind": "item", "item": "fullheal"}
    missing = own["max_hp"] - own["hp"]
    if own["hp"] <= max(own["max_hp"] / 2, danger["max"]):
        for item, heal in sorted(HEALS.items(), key=lambda pair: pair[1]):
            gained = min(heal, missing)
            if state["bag"].get(item, 0) and gained > danger["likely"] and gained > 0:
                return {"kind": "item", "item": item}
    return choice


def replacement(state):
    """pret's type-first replacement pass, then its strongest-damage fallback.

    Only compulsory replacements are modeled. The preview fallback uses
    Smogon damage, rather than pret AI_CalcDmg's internal arithmetic.
    """
    candidates = sorted((p for p in state["party"] if p["hp"] > 0), key=lambda p: p["party_index"])
    for mon in sorted(candidates, key=lambda p: -p["replacement_type_score"]):
        if mon["replacement_type_score"] > 0 and any(m.get("effectiveness", 0) > 1 for m in mon["moves"]):
            return {"kind": "switch", "slot": mon["position"]}
    best = max(candidates, key=lambda p: max(max(m.get("damage", [0])) for m in p["moves"]))
    return {"kind": "switch", "slot": best["position"]}

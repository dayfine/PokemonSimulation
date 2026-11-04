"""Tier A: choose attacks, respecting PP and locked moves; no bag actions."""

import math


def mean(values):
    return sum(values) / len(values)


def usable(mon):
    return [(i, m) for i, m in enumerate(mon["moves"]) if m["pp"] > 0 and not m["disabled"]]


def locked(mon):
    if mon["locked_move"]:
        return {"kind": "move", "slot": next((i for i, m in enumerate(mon["moves"]) if m["id"] == mon["locked_move"]), 0)}
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



def choose_action(state):
    return locked(state["own"]) or attack(state)

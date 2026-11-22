"""Opposing FRLG trainer medicines and replacement choices; not our policy."""

from pokesim.games.frlg.battle.items import HEALS


MAX_TRAINER_ITEMS = 4


def trainer_item_slots(state, item_order):
    """pret ShouldUseItem's slot gate: slot i > 0 is skipped while more than 4 - i + 1 of the
    trainer's Pokemon are alive, and a used slot is cleared. Equal items are used lowest slot
    first, so the first `used` slots of an item are the spent ones. Returns the open slots' items."""
    left = sum(p["hp"] > 0 for p in state["party"])
    used = dict(state.get("trainer_items_used") or {})
    open_slots = []
    for index, item in enumerate(item_order):
        if used.get(item, 0) > 0:
            used[item] -= 1
            continue
        if index and left > MAX_TRAINER_ITEMS - index + 1:
            continue
        if state["trainer_bag"].get(item, 0):
            open_slots.append(item)
    return open_slots


def trainer_item(state, item_order):
    """pret ShouldUseItem: thresholds, status cures, and item-slot restrictions."""
    foe = state["foe"]
    for item in trainer_item_slots(state, item_order):
        if not foe["hp"]:
            continue
        low = foe["hp"] < foe["max_hp"] // 4
        healing = item in HEALS and (low or (item != "fullrestore" and foe["max_hp"] - foe["hp"] > HEALS[item]))
        cure = item == "fullheal" and (foe["status"] or "confusion" in foe["volatiles"])
        if healing or cure:
            return {"kind": "item", "item": item}
    return None


def trainer_heals_below_quarter(state, item_order):
    """True when the trainer will use a Full Restore / HP item if its active foe drops below 1/4."""
    return any(item in HEALS for item in trainer_item_slots(state, item_order))


def replacement(state):
    """pret's type-first replacement pass, then its strongest-damage fallback.

    Only compulsory replacements are modeled. The preview fallback uses
    Smogon damage, rather than pret AI_CalcDmg's internal arithmetic.
    """
    candidates = sorted((p for p in state["party"] if p["hp"] > 0 and
        p['party_index'] != state['foe']['party_index']), key=lambda p: p["party_index"])
    for mon in sorted(candidates, key=lambda p: -p["replacement_type_score"]):
        if mon["replacement_type_score"] > 0 and any(m.get("effectiveness", 0) > 1 for m in mon["moves"]):
            return {"kind": "switch", "slot": mon["position"]}
    best = max(candidates, key=lambda p: max(max(m.get("damage", [0])) for m in p["moves"]))
    return {"kind": "switch", "slot": best["position"]}

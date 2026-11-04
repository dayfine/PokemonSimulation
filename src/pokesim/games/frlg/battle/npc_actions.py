"""Opposing FRLG trainer medicines and replacement choices; not our policy."""

from pokesim.games.frlg.battle.items import HEALS


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

"""Import the pret data the Mail Glitch grind model needs (wild spots, rematches, species, moves).

    PYTHONPATH=src python3 -m pokesim.games.frlg.progression.grind_pret --repo external/pokefirered \
        --out data/games/frlg/progression/mail-glitch-grind-pret.json

Reads FireRed land tables, VS Seeker rematch parties, species, learnsets,
moves, natures, and the type chart from a pret/pokefirered checkout. No ROM.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from pokesim.formats.contract_format import json_text
from pokesim.games.frlg.battle.pret import blocks, field

SPOTS = {
    "pokemon-tower-5f": ["MAP_POKEMON_TOWER_5F"],
    "victory-road": ["MAP_VICTORY_ROAD_1F", "MAP_VICTORY_ROAD_2F", "MAP_VICTORY_ROAD_3F"],
}  # Cerulean Cave and Sevault Canyon need Sevii story progress the mg-03 save lacks.
REMATCH_MAP = "MAP_ROUTE8"  # Rematch route next to Lavender's Pokémon Center.
PLAYER_SPECIES = ("BLASTOISE", "FARFETCHD", "MR_MIME")
STAT_FIELDS = (("hp", "HP"), ("atk", "Attack"), ("def", "Defense"), ("spe", "Speed"),
               ("spa", "SpAttack"), ("spd", "SpDefense"))
GROWTH = {"GROWTH_MEDIUM_FAST": lambda n: n ** 3,
          "GROWTH_MEDIUM_SLOW": lambda n: 6 * n ** 3 // 5 - 15 * n ** 2 + 100 * n - 140,
          "GROWTH_FAST": lambda n: 4 * n ** 3 // 5, "GROWTH_SLOW": lambda n: 5 * n ** 3 // 4}


def rematch_trainers(vs_seeker, map_name):
    """Final (post-game steady-state) single-battle rematch party id per trainer on one map."""
    entries = re.findall(r"\{\s*\{([^}]*)\},\s*MAP\((MAP_\w+)\)\s*\}", vs_seeker)
    final = []
    for ids, entry_map in entries:
        if entry_map == map_name:
            tiers = [t for t in re.findall(r"TRAINER_\w+|SKIP", ids) if t != "SKIP"]
            final.append(tiers[-1][len("TRAINER_"):])
    return final


def import_grind_data(repo):
    hashes = {}

    def read(name):
        raw = (repo / name).read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        return raw.decode()

    wild = json.loads(read("src/data/wild_encounters.json"))
    group = next(g for g in wild["wild_encounter_groups"] if g["label"] == "gWildMonHeaders")
    land_rates = next(f for f in group["fields"] if f["type"] == "land_mons")["encounter_rates"]
    map_flags = {}
    for path in sorted((repo / "data/maps").glob("*/map.json")):
        header = json.loads(path.read_text())
        map_flags[header["id"]] = {"allow_running": header["allow_running"], "allow_cycling": header["allow_cycling"]}
    spots, used = {}, set(PLAYER_SPECIES)
    for spot, maps in SPOTS.items():
        tables = []
        for entry in group["encounters"]:
            if entry["map"] in maps and entry["base_label"].endswith("_FireRed"):
                land = entry["land_mons"]
                mons = [{"species": m["species"][len("SPECIES_"):], "min_level": m["min_level"],
                         "max_level": m["max_level"]} for m in land["mons"]]
                used.update(m["species"] for m in mons)
                tables.append({"map": entry["map"], "encounter_rate": land["encounter_rate"],
                               **map_flags[entry["map"]], "slots": mons})
        if len(tables) != len(maps):
            raise ValueError("Missing FireRed land table for " + spot)
        spots[spot] = tables
    trainers = blocks(read("src/data/trainers.h"), "TRAINER")
    parties = read("src/data/trainer_parties.h")
    rematches = {}
    for name in rematch_trainers(read("src/vs_seeker.c"), REMATCH_MAP):
        body = trainers[name]
        pointer = re.search(r"\.party\s*=\s*(\w+)\((s\w+)\)", body)
        party = re.search(r"\b" + pointer[2] + r"\[\]\s*=\s*\{(.*?)\n\};", parties, re.S)
        members = []
        for mon in re.findall(r"\{(.*?)\n    \}", party[1], re.S):
            member = {"species": field(mon, "species")[len("SPECIES_"):], "level": int(field(mon, "lvl")),
                      "iv": int(field(mon, "iv"))}
            moves = re.search(r"\.moves\s*=\s*\{([^}]*)\}", mon)
            if moves:
                member["moves"] = re.findall(r"MOVE_(\w+)", moves[1])
            members.append(member)
            used.add(member["species"])
        rematches[name] = {"double": field(body, "doubleBattle") == "TRUE", "party": members}
    species_text = read("src/data/pokemon/species_info.h")
    species = dict(re.findall(r"\[SPECIES_(\w+)\]\s*=\s*\{\n(.*?)\n    \},", species_text, re.S))
    learned_text = read("src/data/pokemon/level_up_learnsets.h")
    learned = {name: [[int(level), move] for level, move in re.findall(
        r"LEVEL_UP_MOVE\(\s*(\d+),\s*MOVE_(\w+)\)", body)]
        for name, body in re.findall(r"static const u16 (s\w+)\[\]\s*=\s*\{(.*?)\};", learned_text, re.S)}
    pointers = dict(re.findall(r"\[SPECIES_(\w+)\]\s*=\s*(s\w+)",
                               read("src/data/pokemon/level_up_learnset_pointers.h")))
    pokemon, move_names = {}, set()
    for name in sorted(used):
        body = species[name]
        growth = field(body, "growthRate")
        pokemon[name] = {"base_stats": {k: int(field(body, "base" + s)) for k, s in STAT_FIELDS},
            "types": list(dict.fromkeys(re.findall(r"TYPE_(\w+)", re.search(r"\.types\s*=\s*\{([^}]*)\}", body)[1]))),
            "abilities": [a for a in re.findall(r"ABILITY_(\w+)", re.search(r"\.abilities\s*=\s*\{([^}]*)\}", body)[1])
                          if a != "NONE"],
            "exp_yield": int(field(body, "expYield")), "growth_rate": growth,
            "learnset": learned[pointers[name]]}
        move_names.update(move for _, move in pokemon[name]["learnset"])
    for party in rematches.values():
        for member in party["party"]:
            move_names.update(member.get("moves", []))
    move_names.update(("SURF", "BITE", "BLIZZARD", "STRENGTH", "SAND_ATTACK", "LEER", "FURY_ATTACK",
                       "KNOCK_OFF", "BARRIER", "CONFUSION", "SUBSTITUTE", "STRUGGLE"))
    move_data = blocks(read("src/data/battle_moves.h"), "MOVE")
    moves = {}
    for name in sorted(move_names):
        body = move_data[name]
        moves[name] = {"effect": field(body, "effect")[len("EFFECT_"):], "power": int(field(body, "power")),
            "type": field(body, "type")[len("TYPE_"):], "accuracy": int(field(body, "accuracy")),
            "pp": int(field(body, "pp")), "chance": int(field(body, "secondaryEffectChance")),
            "priority": int(field(body, "priority"))}
    chart_text = re.search(r"gTypeEffectiveness\[\d+\]\s*=\s*\{(.*?)\};", read("src/battle_main.c"), re.S)[1]
    type_chart = [[a, d, {"TYPE_MUL_NO_EFFECT": 0, "TYPE_MUL_NOT_EFFECTIVE": 5, "TYPE_MUL_SUPER_EFFECTIVE": 20}[m]]
                  for a, d, m in re.findall(r"TYPE_(\w+),\s*TYPE_(\w+),\s*(TYPE_MUL_\w+)", chart_text)
                  if a != "FORESIGHT"]
    nature_order = ("atk", "def", "spe", "spa", "spd")
    natures = [dict(zip(nature_order, [100 + 10 * int(n) for n in re.findall(r"[+-]?\d+", values)]))
               for _, values in re.findall(r"\[NATURE_(\w+)\]\s*=\s*\{([+\-\d,\s]+)\}", read("src/pokemon.c"))]
    if len(natures) != 25:
        raise ValueError("Review changed nature table")
    curves = read("src/data/pokemon/experience_tables.h")
    for growth in {p["growth_rate"] for p in pokemon.values()}:
        if growth not in GROWTH:
            raise ValueError("Unsupported growth rate " + growth)
    if "#define EXP_MEDIUM_FAST(n)(CUBE(n))" not in curves:
        raise ValueError("Review changed Medium Fast growth formula")
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return {"format": "pokesim-frlg-grind-data/1",
        "source": {"repository": "https://github.com/pret/pokefirered", "revision": revision, "sha256": hashes},
        "land_slot_rates": land_rates, "spots": spots, "rematch_map": REMATCH_MAP, "rematches": rematches,
        "growth_curves": {g: [0, 1] + [GROWTH[g](n) for n in range(2, 101)]
                          for g in sorted({p["growth_rate"] for p in pokemon.values()})},
        "species": pokemon, "moves": moves, "natures": natures, "type_chart": type_chart}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json_text(import_grind_data(args.repo)))


if __name__ == "__main__":
    main()

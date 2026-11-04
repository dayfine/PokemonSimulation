"""Generate EXP data and starter-family learnsets for a curated FRLG route.

    PYTHONPATH=src python3 -m pokesim.games.frlg.progression.pret --repo external/pokefirered \
        --route data/runs/pokeguy-leafgreen-15934/events.json --out /tmp/reference.json

No ROM, C/C++ build, Node engine, or network connection is required.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from pokesim.games.frlg.battle.pret import blocks, field
from pokesim.games.frlg.progression.experience import medium_slow_thresholds


RULE_SOURCES = ("src/battle_script_commands.c", "src/pokemon.c", "src/script_pokemon_util.c",
    "data/maps/PokemonTower_7F/scripts.inc", "data/maps/PokemonTower_6F/scripts.inc")


def import_reference(repo, route, move_history=None):
    """Resolve trainer IDs and species independently of observed level claims."""
    hashes = {}

    def read(name):
        raw = (repo / name).read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        return raw.decode()

    trainers = blocks(read("src/data/trainers.h"), "TRAINER")
    parties = read("src/data/trainer_parties.h")
    # Skip the inline SPECIES_NONE initializer; it has no species fields.
    species = dict(re.findall(r"\[SPECIES_(\w+)\]\s*=\s*\{\n(.*?)\n    \},",
                             read("src/data/pokemon/species_info.h"), re.S))
    curves = read("src/data/pokemon/experience_tables.h")
    learned_text = read("src/data/pokemon/level_up_learnsets.h")
    learned = {name: [{"level": int(level), "move": move} for level, move in re.findall(
        r"LEVEL_UP_MOVE\(\s*(\d+),\s*MOVE_(\w+)\)", body)]
        for name, body in re.findall(r"static const u16 (s\w+)\[\]\s*=\s*\{(.*?)\};", learned_text, re.S)}
    pointers = dict(re.findall(r"\[SPECIES_(\w+)\]\s*=\s*(s\w+)",
        read("src/data/pokemon/level_up_learnset_pointers.h")))
    if "#define EXP_MEDIUM_SLOW(n)((6 * CUBE(n)) / 5 - (15 * SQUARE(n)) + (100 * n) - 140)" not in curves:
        raise ValueError("Review changed pret Medium Slow growth formula before importing")
    for source in RULE_SOURCES:
        read(source)
    used_species = {"SQUIRTLE", "WARTORTLE", "BLASTOISE"}
    selected = {}
    for event in route["events"]:
        if event["kind"] != "trainer_battle":
            if "opponent" in event:
                used_species.add(event["opponent"]["species"])
            continue
        name = event["trainer"]
        if name in selected:
            continue
        body = trainers[name[len("TRAINER_"):]]
        pointer = re.search(r"\.party\s*=\s*\w+\((s\w+)\)", body)
        if pointer is None or field(body, "doubleBattle") != "FALSE":
            raise ValueError("Unsupported trainer party " + name)
        party = re.search(r"\b" + pointer[1] + r"\[\]\s*=\s*\{(.*?)\n\};", parties, re.S)
        if party is None:
            raise ValueError("Missing trainer party " + name)
        members = [{"species": field(mon, "species")[len("SPECIES_"):], "level": int(field(mon, "lvl"))}
            for mon in re.findall(r"\{(.*?)\n    \}", party[1], re.S)]
        if not members:
            raise ValueError("Empty trainer party " + name)
        used_species.update(mon["species"] for mon in members)
        selected[name] = {"name": re.search(r'\.trainerName\s*=\s*_\("(.*?)"\)', body)[1],
                          "party": members}
    pokemon = {name: {"exp_yield": int(field(species[name], "expYield")),
                     "growth_rate": field(species[name], "growthRate"),
                     "ev_yield": {stat: int(field(species[name], "evYield_" + suffix)) for stat, suffix in
                         (("hp", "HP"), ("atk", "Attack"), ("def", "Defense"), ("spe", "Speed"), ("spa", "SpAttack"), ("spd", "SpDefense"))}}
               for name in sorted(used_species)}
    for name in ("SQUIRTLE", "WARTORTLE", "BLASTOISE"):
        if pokemon[name]["growth_rate"] != "GROWTH_MEDIUM_SLOW":
            raise ValueError("Review changed Squirtle family growth rate")
        pokemon[name]["learnset"] = learned[pointers[name]]
        pokemon[name]["base_stats"] = {stat: int(field(species[name], "base" + suffix)) for stat, suffix in
            (("hp", "HP"), ("atk", "Attack"), ("def", "Defense"), ("spe", "Speed"), ("spa", "SpAttack"), ("spd", "SpDefense"))}
        pokemon[name]["abilities"] = re.findall(r"ABILITY_(\w+)", re.search(r"\.abilities\s*=\s*\{([^}]+)\}", species[name])[1])
    pokemon_source = (repo / "src/pokemon.c").read_text()
    nature_order = ("atk", "def", "spe", "spa", "spd")
    natures = {name.title(): dict(zip(nature_order, [100 + 10 * int(n) for n in re.findall(r"[+-]?\d+", values)]))
        for name, values in re.findall(r"\[NATURE_(\w+)\]\s*=\s*\{([+\-\d,\s]+)\}", pokemon_source)}
    if len(natures) != 25:
        raise ValueError("Review changed nature table")
    move_names = {m["move"] for name in ("SQUIRTLE", "WARTORTLE", "BLASTOISE") for m in pokemon[name]["learnset"]}
    if move_history:
        move_names.update(c["move"] for c in move_history["decisions"])
    move_data = blocks(read("src/data/battle_moves.h"), "MOVE")
    pp = {name: int(field(move_data[name], "pp")) for name in sorted(move_names)}
    limits = read("include/constants/pokemon.h")
    ev_limits = {key: int(re.search(r"#define " + symbol + r"\s+(\d+)", limits)[1])
        for key, symbol in (("per_stat", "MAX_PER_STAT_EVS"), ("total", "MAX_TOTAL_EVS"))}
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return {"format": "pokesim-frlg-exp-data/1",
        "source": {"repository": "https://github.com/pret/pokefirered", "revision": revision, "sha256": hashes},
        "growth_curves": {"GROWTH_MEDIUM_SLOW": medium_slow_thresholds()},
        "trainers": selected, "species": pokemon, "natures": natures, "move_pp": pp, "ev_limits": ev_limits}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--moves", type=Path, help="Move history; uses route sibling moves.json when present")
    args = parser.parse_args()
    move_path = args.moves or args.route.with_name("moves.json")
    history = json.loads(move_path.read_text()) if move_path.exists() else None
    reference = import_reference(args.repo, json.loads(args.route.read_text()), history)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reference, indent=2) + "\n")


if __name__ == "__main__":
    main()

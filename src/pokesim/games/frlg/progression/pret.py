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


RULE_SOURCES = ("src/battle_script_commands.c", "src/pokemon.c",
    "data/maps/PokemonTower_7F/scripts.inc", "data/maps/PokemonTower_6F/scripts.inc")


def import_reference(repo, route):
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
                     "growth_rate": field(species[name], "growthRate")}
               for name in sorted(used_species)}
    for name in ("SQUIRTLE", "WARTORTLE", "BLASTOISE"):
        if pokemon[name]["growth_rate"] != "GROWTH_MEDIUM_SLOW":
            raise ValueError("Review changed Squirtle family growth rate")
        pokemon[name]["learnset"] = learned[pointers[name]]
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return {"format": "pokesim-frlg-exp-data/1",
        "source": {"repository": "https://github.com/pret/pokefirered", "revision": revision, "sha256": hashes},
        "growth_curves": {"GROWTH_MEDIUM_SLOW": medium_slow_thresholds()},
        "trainers": selected, "species": pokemon}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    reference = import_reference(args.repo, json.loads(args.route.read_text()))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(reference, indent=2) + "\n")


if __name__ == "__main__":
    main()

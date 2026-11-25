"""Import what predicts a level-up from pret/pokefirered: learnsets, evolutions and HM moves.

    PYTHONPATH=src python3 -m pokesim.games.frlg.progression.level_up_pret --repo external/pokefirered \
        --out data/games/frlg/progression/level-up-pret.json

Covers every species in gLevelUpLearnsets (level_up_learnsets.h and its pointer
table), gEvolutionTable (evolution.h) and sHMMoves in pokemon.c, the list
IsHMMove2 checks before a move may be forgotten. `#if defined(FIRERED)` /
`#elif defined(LEAFGREEN)` arms are resolved for one game version (FireRed by
default): today they differ in Dugtrio's level-1 move order and Deoxys's learnset.
Names drop the SPECIES_/MOVE_/ITEM_/EVO_ prefixes, as the other pret extracts do.
No ROM or decomp build is needed.
"""

import argparse
import hashlib
from pathlib import Path
import re
import subprocess

from pokesim.formats.contract_format import json_text

VERSIONS = ("FIRERED", "LEAFGREEN")
# evolution.h's parameter column means a level, an item, a beauty threshold or nothing.
LEVEL_METHODS = ("LEVEL", "LEVEL_ATK_GT_DEF", "LEVEL_ATK_EQ_DEF", "LEVEL_ATK_LT_DEF", "LEVEL_SILCOON",
                 "LEVEL_CASCOON", "LEVEL_NINJASK", "LEVEL_SHEDINJA")
ITEM_METHODS = ("ITEM", "TRADE_ITEM")
NO_PARAMETER_METHODS = ("FRIENDSHIP", "FRIENDSHIP_DAY", "FRIENDSHIP_NIGHT", "TRADE")


def select_version(text, version):
    """Keep the lines a build for `version` compiles from `#if defined(...)` blocks."""
    kept, stack = [], []  # stack entries: [this arm active, an earlier arm was taken]
    for line in text.splitlines():
        directive = line.strip()
        condition = re.fullmatch(r"#(if|elif) defined\((\w+)\)", directive)
        if condition and condition[1] == "if":
            stack.append([condition[2] == version, condition[2] == version])
        elif condition:
            taken = stack[-1][1]
            stack[-1] = [not taken and condition[2] == version, taken or condition[2] == version]
        elif directive == "#else":
            stack[-1] = [not stack[-1][1], True]
        elif directive == "#endif":
            stack.pop()
        elif directive.startswith("#if"):
            raise ValueError("Unsupported conditional " + directive)
        elif all(active for active, _ in stack):
            kept.append(line)
    if stack:
        raise ValueError("Unterminated conditional")
    return "\n".join(kept)


def evolution(method, parameter, species):
    method = method[len("EVO_"):]
    entry = {"method": method}
    if method in LEVEL_METHODS:
        entry["level"] = int(parameter)
    elif method in ITEM_METHODS:
        entry["item"] = parameter[len("ITEM_"):]
    elif method == "BEAUTY":
        entry["beauty"] = int(parameter)
    elif method not in NO_PARAMETER_METHODS or parameter != "0":
        raise ValueError("Unsupported evolution " + method + " " + parameter)
    entry["species"] = species
    return entry


def import_level_up_data(repo, version="FIRERED"):
    """Learnsets and evolutions per species, plus HM moves, with input hashes and revision."""
    if version not in VERSIONS:
        raise ValueError("Unknown game version " + version)
    hashes = {}

    def read(name):
        raw = (repo / name).read_bytes()
        hashes[name] = hashlib.sha256(raw).hexdigest()
        return raw.decode()

    learnset_text = select_version(read("src/data/pokemon/level_up_learnsets.h"), version)
    learnsets = {name: [[int(level), move] for level, move in re.findall(
        r"LEVEL_UP_MOVE\(\s*(\d+),\s*MOVE_(\w+)\)", body)]
        for name, body in re.findall(r"static const u16 (s\w+)\[\]\s*=\s*\{(.*?)\};", learnset_text, re.S)}
    pointer_text = select_version(read("src/data/pokemon/level_up_learnset_pointers.h"), version)
    pointers = re.findall(r"\[SPECIES_(\w+)\]\s*=\s*(s\w+)", pointer_text)
    evolution_text = select_version(read("src/data/pokemon/evolution.h"), version)
    evolutions = {}
    for name, body in re.findall(r"\[SPECIES_(\w+)\]\s*=\s*\{(\{.*?\})\},", evolution_text, re.S):
        evolutions[name] = [evolution(*entry) for entry in re.findall(
            r"\{\s*(EVO_\w+),\s*(\w+),\s*SPECIES_(\w+)\s*\}", body)]
    if sum(map(len, evolutions.values())) != evolution_text.count("EVO_"):
        raise ValueError("Review changed evolution table layout")
    species = {}
    for name, pointer in pointers:
        if name != "NONE":
            species[name] = {"learnset": learnsets[pointer], "evolutions": evolutions.pop(name, [])}
    if evolutions:
        raise ValueError("Evolutions for species without a learnset: " + ", ".join(evolutions))
    hm_table = re.search(r"static const u16 sHMMoves\[\]\s*=\s*\{(.*?)\};", read("src/pokemon.c"), re.S)[1]
    if "#" in hm_table:
        raise ValueError("Review conditional HM move table")
    hm_moves = re.findall(r"MOVE_(\w+)", hm_table)
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return {"format": "pokesim-frlg-level-up/1",
            "source": {"repository": "https://github.com/pret/pokefirered", "revision": revision, "sha256": hashes},
            "version": version, "hm_moves": hm_moves, "species": species}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--version", choices=VERSIONS, default="FIRERED")
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json_text(import_level_up_data(args.repo, args.version)))


if __name__ == "__main__":
    main()

"""Import FRLG NPC parties and reachable AI scripts from pret/pokefirered.

The default snapshot covers the original four AutoStory experiments. Pass
--run-data to import every trainer and player move from a run reference.

Run from the repo root:
    PYTHONPATH=src python3 -m pokesim.games.frlg.battle.pret --repo external/pokefirered \
        --out data/games/frlg/battles/pret.json

Produces a revision-stamped JSON snapshot. No ROM or decomp build is needed.
Only single battles are supported. Trainer held items are preserved.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

TRAINERS = (
    "RIVAL_CERULEAN_BULBASAUR", "LEADER_MISTY", "RIVAL_SS_ANNE_BULBASAUR",
    "LEADER_LT_SURGE",
)
ROOTS = {"CHECK_BAD_MOVE": "AI_CheckBadMove", "CHECK_VIABILITY": "AI_CheckViability",
         "TRY_TO_FAINT": "AI_TryToFaint"}
NATURES = ("Hardy Lonely Brave Adamant Naughty Bold Docile Relaxed Impish Lax "
           "Timid Hasty Serious Jolly Naive Modest Mild Quiet Bashful Rash "
           "Calm Gentle Sassy Careful Quirky").split()


def blocks(text, prefix):
    """Designated C initializer bodies keyed by their constant name."""
    return dict(re.findall(r"\[" + prefix + r"_(\w+)\]\s*=\s*\{(.*?)\n    \},", text, re.S))


def field(body, name):
    match = re.search(r"\." + name + r"\s*=\s*([^,\n]+)", body)
    if not match:
        raise ValueError("Missing field " + name)
    return match.group(1).strip()


def constants(body, prefix):
    return re.findall(prefix + r"_([A-Z0-9_]+)", body)


def compile_scripts(text, effects):
    """Keep control-flow paths reachable for these trainers' move effects.

    Instructions remain symbolic. The runtime rejects unimplemented commands;
    it never silently replaces an unknown command with a generic policy.
    """
    labels, instructions = {}, []
    for raw in text.splitlines():
        line = raw.split("@")[0].strip()
        if not line or line.startswith("#"):
            continue
        label = re.fullmatch(r"(\w+)::?", line)
        if label:
            labels[label[1]] = len(instructions)
            continue
        op, _, rest = line.partition(" ")
        if op.startswith(".") and op not in (".byte", ".2byte"):
            continue
        args = [a.strip() for a in rest.split(",")] if rest else []
        if op == "if_effect" and args[0] not in effects:
            continue
        if op == "if_not_effect" and args[0] not in effects:
            op, args = "goto", [args[-1]]
        instructions.append([op] + args)
    pending = [labels[label] for label in ROOTS.values()]
    visited = set()
    while pending:
        index = pending.pop()
        if index in visited:
            continue
        visited.add(index)
        op, *args = instructions[index]
        for arg in args:
            if arg in labels:
                pending.append(labels[arg])
        # Data tables terminate at -1; they are not executable instructions.
        terminal = op in ("end", "goto") or (op in (".byte", ".2byte") and "-1" in args)
        if not terminal and index + 1 < len(instructions):
            pending.append(index + 1)
    kept = sorted(visited)
    remap = {old: new for new, old in enumerate(kept)}
    return {"roots": ROOTS, "labels": {k: remap[v] for k, v in labels.items() if v in remap},
            "instructions": [instructions[i] for i in kept]}


def import_checkout(repo, trainer_ids=TRAINERS, player_moves=()):
    """Import requested trainers and moves, recording input hashes and revision."""
    inputs = {}

    def read(name):
        raw = (repo / name).read_bytes()
        inputs[name] = hashlib.sha256(raw).hexdigest()
        return raw.decode()

    trainer_data = blocks(read("src/data/trainers.h"), "TRAINER")
    parties = read("src/data/trainer_parties.h")
    names = dict(re.findall(r'\[SPECIES_(\w+)\]\s*=\s*_\("(.*?)"\)', read("src/data/text/species_names.h")))
    chars = {char[-1]: int(code, 16) for char, code in re.findall(
        r"^'(\\?.)'\s*=\s*([0-9A-F]{2})\s*$", read("charmap.txt"), re.M)}
    learned_text = read("src/data/pokemon/level_up_learnsets.h")
    learned = {name: [(int(lvl), move) for lvl, move in re.findall(
        r"LEVEL_UP_MOVE\(\s*(\d+),\s*MOVE_(\w+)\)", body)]
        for name, body in re.findall(r"static const u16 (s\w+)\[\]\s*=\s*\{(.*?)\};", learned_text, re.S)}
    pointers = dict(re.findall(r"\[SPECIES_(\w+)\]\s*=\s*(s\w+)", read("src/data/pokemon/level_up_learnset_pointers.h")))
    moves = blocks(read("src/data/battle_moves.h"), "MOVE")
    trainers, used_moves = {}, set()
    for key in trainer_ids:
        key = key[len("TRAINER_"):] if key.startswith("TRAINER_") else key
        body = trainer_data[key]
        if field(body, "doubleBattle") != "FALSE":
            raise ValueError("Only single trainer battles are supported")
        party_name = re.search(r"\.party\s*=\s*(\w+)\((s\w+)\)", body)
        if not party_name:
            raise ValueError("Unknown trainer party layout")
        party = re.search(r"\b" + party_name[2] + r"\[\]\s*=\s*\{(.*?)\n\};", parties, re.S)[1]
        trainer_name = re.search(r'\.trainerName\s*=\s*_\("(.*?)"\)', body)[1]
        name_hash, members = 0, []
        for mon in re.findall(r"\{(.*?)\n    \}", party, re.S):
            species = field(mon, "species")[len("SPECIES_"):]
            level = int(field(mon, "lvl"))
            given = re.search(r"\.moves\s*=\s*\{(.*?)\}", mon, re.S)
            known = constants(given[1], "MOVE") if given else []
            if not given:
                for lvl, move in learned[pointers[species]]:
                    if lvl > level:
                        break
                    if move not in known:
                        known = (known + [move])[-4:]
            known = [move for move in known if move != "NONE"]
            used_moves.update(known)
            name_hash += sum(chars[c] for c in trainer_name + names[species])
            personality = ((0x78 if "F_TRAINER_FEMALE" in body else 0x88) + (name_hash << 8)) & 0xFFFFFFFF
            raw_iv = int(field(mon, "iv"))
            held = re.search(r"\.heldItem\s*=\s*ITEM_(\w+)", mon)
            held_item = held[1] if held and held[1] != "NONE" else ""
            member = {"species": species, "level": level, "iv": raw_iv * 31 // 255,
                            "pret_iv": raw_iv, "nature": NATURES[personality % 25],
                            "personality": personality, "ability_slot": 0, "moves": known}
            if held_item:
                member['held_item'] = held_item
            members.append(member)
        flags = constants(field(body, "aiFlags"), "AI_SCRIPT")
        if set(flags) - ROOTS.keys():
            raise ValueError("Unsupported trainer AI flags: " + str(flags))
        trainers["TRAINER_" + key] = {"name": trainer_name, "ai": flags, "party": members,
            "items": [i for i in constants(re.search(r"\.items\s*=\s*\{(.*?)\}", body)[1], "ITEM") if i != "NONE"]}
    # Include effects of our fixture moves for the AI's move-history queries.
    used_moves.update(player_moves)
    used_moves.update(("BITE", "TAIL_WHIP", "BUBBLE", "WITHDRAW", "WATER_PULSE", "DIG", "MEGA_KICK", "TACKLE"))
    metadata = {move: {"effect": field(moves[move], "effect"), "power": int(field(moves[move], "power")),
                       "type": field(moves[move], "type"), "pp": int(field(moves[move], "pp"))} for move in sorted(used_moves)}
    ai = compile_scripts(read("data/battle_ai_scripts.s"), {m["effect"] for m in metadata.values()})
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    return {"format": "pokesim-frlg-pret/1", "source": {"repository": "https://github.com/pret/pokefirered",
            "revision": revision, "sha256": inputs}, "trainers": trainers, "moves": metadata, "ai": ai}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-data", type=Path, help="Run directory containing reference.json")
    args = parser.parse_args()
    if args.run_data:
        reference = json.loads((args.run_data / 'reference.json').read_text())
        data = import_checkout(args.repo, reference['trainers'], reference['move_pp'])
    else:
        data = import_checkout(args.repo)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()

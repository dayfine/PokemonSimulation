"""Read the party from a FireRed/LeafGreen (Gen 3) battery save, read-only.

    PYTHONPATH=src python3 -m pokesim.games.frlg.progression.save_party \
        --repo external/pokefirered path/to/fr.sav

Layout from pret/pokefirered include/save.h and include/pokemon.h: two slots
of 14 sections (0x1000 bytes each), the newest valid slot wins; the party is
in section 1, trainer ID in section 0. Each 48-byte box substructure block is
XOR-encrypted with personality ^ OT ID and ordered by personality % 24.
Species and move numbers are resolved to names from the given pret checkout.
"""

import argparse
from itertools import permutations
import json
from pathlib import Path
import re
import struct

SECTION_SIZE = 0x1000
SECTIONS_PER_SLOT = 14
SECTION_DATA_SIZE = 0xF80
SIGNATURE = 0x08012025
TRAINER_ID_OFFSET = 0x0A        # SaveBlock2.playerTrainerId
PARTY_COUNT_OFFSET = 0x34       # SaveBlock1.playerPartyCount (FRLG)
PARTY_OFFSET = 0x38             # SaveBlock1.playerParty (FRLG)
POCKETS = {"items": (0x310, 42), "key_items": (0x3B8, 30)}  # SaveBlock1.bagPocket_* (FRLG)
MON_SIZE = 100
SUBSTRUCT_ORDERS = ["".join(order) for order in permutations("GAEM")]  # pokemon.c GetSubstruct
STAT_NAMES = ("hp", "atk", "def", "spe", "spa", "spd")  # IV/EV bit and byte order


def section_checksum(data):
    """CalculateChecksum: 32-bit word sum folded to 16 bits."""
    total = sum(struct.unpack_from("<%dI" % (len(data) // 4), data)) & 0xFFFFFFFF
    return (total + (total >> 16)) & 0xFFFF


def newest_sections(save):
    """Section id -> data of the valid slot with the highest save counter."""
    best = None
    for slot in range(2):
        sections, counter = {}, None
        for index in range(SECTIONS_PER_SLOT):
            base = (slot * SECTIONS_PER_SLOT + index) * SECTION_SIZE
            block = save[base:base + SECTION_SIZE]
            section_id, checksum, signature, counter = struct.unpack_from("<HHII", block, 0xFF4)
            if signature != SIGNATURE or section_id >= SECTIONS_PER_SLOT:
                break
            sections[section_id] = block
        if len(sections) != SECTIONS_PER_SLOT:
            continue
        if any(section_checksum(sections[i][:size]) != struct.unpack_from("<H", sections[i], 0xFF6)[0]
               for i, size in ((0, SECTION_DATA_SIZE), (1, SECTION_DATA_SIZE))):
            continue
        if best is None or counter > best[0]:
            best = (counter, sections)
    if best is None:
        raise ValueError("No valid Gen 3 save slot")
    return best[1]


def decode_text(raw):
    """Gen 3 English charmap subset: letters, digits, space and apostrophe."""
    table = {0x00: " ", 0xB4: "'", 0xAD: ".", 0xAE: "-"}
    table.update({0xA1 + i: str(i) for i in range(10)})
    table.update({0xBB + i: chr(ord("A") + i) for i in range(26)})
    table.update({0xD5 + i: chr(ord("a") + i) for i in range(26)})
    text = ""
    for byte in raw:
        if byte == 0xFF:
            break
        text += table.get(byte, "?")
    return text


def decode_mon(raw, player_trainer_id, species_names, move_names):
    """One 100-byte party Pokémon; raises if the substructure checksum fails."""
    personality, ot_id = struct.unpack_from("<II", raw, 0)
    key = personality ^ ot_id
    words = [w ^ key for w in struct.unpack_from("<12I", raw, 32)]
    plain = struct.pack("<12I", *words)
    if sum(struct.unpack("<24H", plain)) & 0xFFFF != struct.unpack_from("<H", raw, 28)[0]:
        raise ValueError("Pokémon substructure checksum mismatch")
    order = SUBSTRUCT_ORDERS[personality % 24]
    part = {letter: plain[12 * order.index(letter):12 * order.index(letter) + 12] for letter in "GAEM"}
    species, item, exp = struct.unpack_from("<HHI", part["G"])
    moves = struct.unpack_from("<4H", part["A"])
    pp = part["A"][8:12]
    ev_bytes = part["E"][:6]
    iv_word = struct.unpack_from("<I", part["M"], 4)[0]
    level, = struct.unpack_from("<B", raw, 84)
    hp, *stats = struct.unpack_from("<7H", raw, 86)
    return {"nickname": decode_text(raw[8:18]), "species": species_names[species],
            "level": level, "exp": exp, "held_item": item,
            "traded": ot_id != player_trainer_id,
            "hp": hp, "stats": dict(zip(("hp", "atk", "def", "spe", "spa", "spd"), stats)),
            "ivs": {name: (iv_word >> (5 * i)) & 31 for i, name in enumerate(STAT_NAMES)},
            "evs": dict(zip(STAT_NAMES, ev_bytes)),
            "moves": [{"name": move_names[m], "pp": pp[i], "pp_ups": (part["G"][8] >> (2 * i)) & 3}
                      for i, m in enumerate(moves) if m],
            "nature_index": personality % 25,
            "ability_slot": iv_word >> 31, "personality": personality}


def constant_names(header, prefix):
    """Number -> pret constant suffix from a `#define PREFIX_NAME n` header."""
    names = {}
    for name, value in re.findall(r"#define " + prefix + r"(\w+)\s+(\d+)\b", header):
        names.setdefault(int(value), name)
    return names


def read_party(save, repo):
    """Party list from raw save bytes, names resolved against a pret checkout."""
    species_names = constant_names((repo / "include/constants/species.h").read_text(), "SPECIES_")
    move_names = constant_names((repo / "include/constants/moves.h").read_text(), "MOVE_")
    sections = newest_sections(save)
    trainer_id, = struct.unpack_from("<I", sections[0], TRAINER_ID_OFFSET)
    team = sections[1]
    count, = struct.unpack_from("<I", team, PARTY_COUNT_OFFSET)
    if not 0 < count <= 6:
        raise ValueError("Invalid party count %d" % count)
    return [decode_mon(team[PARTY_OFFSET + MON_SIZE * i:PARTY_OFFSET + MON_SIZE * (i + 1)],
                       trainer_id, species_names, move_names) for i in range(count)]


def read_pocket(save, repo, pocket):
    """Item names in one bag pocket (quantities are encrypted and not needed here)."""
    item_names = constant_names((repo / "include/constants/items.h").read_text(), "ITEM_")
    offset, count = POCKETS[pocket]
    team = newest_sections(save)[1]
    ids = struct.unpack_from("<%dH" % (2 * count), team, offset)[::2]
    return [item_names[i] for i in ids if i]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("save", type=Path)
    args = parser.parse_args()
    save = args.save.read_bytes()
    print(json.dumps({"party": read_party(save, args.repo),
                      "bag": {pocket: read_pocket(save, args.repo, pocket) for pocket in POCKETS}}, indent=1))


if __name__ == "__main__":
    main()

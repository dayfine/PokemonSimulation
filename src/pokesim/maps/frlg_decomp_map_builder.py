# Imported from dayfine/Arduino-Source@51c0ce6128e5981da56b370a770874b96a1e129f
# Original path: devtools/maps/frlg_maps.py
"""Writes FRLG overworld maps as JSON, from the pret/pokefirered decompilation.

Owned by PokemonSimulation; export the JSON pack to console consumers.

Usage (the FRLG map set in data/games/frlg/maps/runtime; see its README.md):
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --all \
        --scope data/games/frlg/maps/pokeguy-map-scope.json --item-identities \
        --out data/games/frlg/maps/runtime --manifest data/maps/runtime-manifest.json --check
Other folders:
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --out <folder> Route3 Route4
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --out <folder>
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --out <folder> --check
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --all --out /tmp/frlg-world-candidate
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --all \
        --scope data/games/frlg/maps/pokeguy-map-scope.json --out /tmp/frlg-pokeguy-candidate

Downloads each map's data/maps/<map>/map.json, its layout's map.bin and its
tilesets' metatile_attributes.bin at --commit into --cache, then writes
<out>/<map>.json in the schema of Pokemon::MapData (Pokemon_MapData.h).
A map whose header doesn't allow running (indoors) says so; a trainer has
their sight and the ways they look.
Warps and connections lead only to maps in the same run (with --all, the whole
catalog, scope-excluded maps included, so every source link is emitted by
name): a warp to a map outside the run has no destination, and a connection to
one is left out. A warp arrives at
point "warp_<n>" of its map, the tile of that map's warp n. Other named points
and flag sets come from POINTS and FLAG_SETS below.

With --all, enumerate the complete pinned map catalog into an empty candidate
directory; this does not approve the data or support all movement mechanics.
With --scope, omit explicitly excluded maps but preserve their boundary links.
Without map names, the maps are the ones already in --out; with them, those
maps are added to the ones in --out, so warps and connections still join
them all. --check writes nothing: it regenerates them and fails if any file
differs. With --manifest, maps whose status is verified are reviewed content:
they are allowed outside the scope and not compared; every candidate must be
in scope and match the generator byte for byte. Export the generated pack with pokesim.maps.runtime_map_pack for
Arduino consumers.

Base maps (docs/maps/OVERLAYS.md): with --all, --scope and --manifest, every
manifest map gets a base, including verified maps outside the scope, and --check
compares every one byte for byte. Bases are never edited by hand; story state,
console measurements and remake deltas are overlay operations in
data/games/frlg/maps/overlays/<Map>.json (pokesim.maps.map_overlays).
"""
import argparse
from collections import deque
import hashlib
import json
import os
import re
import struct
import subprocess
import sys

from pokesim.formats.contract_format import json_text as contract_json_text
from . import npc_path
from .runtime_symbols import CLOSED_SIDES, LEDGE_GLYPHS
from .item_identity import INPUTS as ITEM_SOURCE_INPUTS, digest, enrich_objects
from .item_pickup_sources import frlg_pickups, unresolved as unresolved_pickup
from .runtime_map_coordinates import compact_map
from .runtime_map_format import map_text as readable_map_text
from .frlg_map_scope import read_scope
from .frlg_map_set import statuses

COMMIT = 'ce6406d8c2eaf46d543c8a2606de0c3cb1951982'
#   When COMMIT was pinned, for each map's "source".
COMMIT_DATE = '2026-10-31'

#   Behaviors with a glyph of their own (Pokemon_MapData.h has the legend).
TERRAIN = {
    'MB_TALL_GRASS': '~', 'MB_WARP_DOOR': 'D',
    'MB_SPIN_UP': 'u', 'MB_SPIN_DOWN': 'd', 'MB_SPIN_LEFT': 'l', 'MB_SPIN_RIGHT': 'r',
    'MB_STOP_SPINNING': 'o', 'MB_FALL_WARP': 'H', 'MB_STRENGTH_BUTTON': 'B',
    **{'MB_IMPASSABLE_' + side.name: glyph for glyph, side in CLOSED_SIDES.items()},
}
#   Open tiles whose warp is taken other than by walking into it: how.
WARP_ENTRIES = {
    'MB_CAVE_DOOR': 'cave_entrance',
    'MB_REGULAR_WARP': 'step_on',
    'MB_LADDER': 'step_on', 'MB_UP_ESCALATOR': 'step_on', 'MB_DOWN_ESCALATOR': 'step_on',
    'MB_SOUTH_ARROW_WARP': 'walk_south', 'MB_NORTH_ARROW_WARP': 'walk_north',
    'MB_EAST_ARROW_WARP': 'walk_east', 'MB_WEST_ARROW_WARP': 'walk_west',
    #   Stairs at the side of a room warp like an exit mat, the way the stairs
    #   go up or down (IsDirectionalStairWarpMetatileBehavior()).
    'MB_UP_RIGHT_STAIR_WARP': 'walk_east', 'MB_DOWN_RIGHT_STAIR_WARP': 'walk_east',
    'MB_UP_LEFT_STAIR_WARP': 'walk_west', 'MB_DOWN_LEFT_STAIR_WARP': 'walk_west',
}
#   Ledges, by the way the player hops over them.
LEDGES = {'MB_JUMP_' + direction.name: glyph for direction, glyph in LEDGE_GLYPHS.items()}
#   MB_COUNTER only lets the player talk to someone across it
#   (MetatileBehavior_IsCounter()); walking is decided by the collision bit, so a
#   counter tile without collision (PewterCity_Museum_1F (11, 5)) is floor.
FLOOR = (
    'MB_NORMAL', 'MB_CAVE', 'MB_ROCK_STAIRS', 'MB_TALL_GRASS',
    'MB_SAND', 'MB_SAND_CAVE', 'MB_MOUNTAIN_TOP', 'MB_ICE', 'MB_COUNTER',
    #   Not surfable (sBehaviorSurfable): the player walks on it, as on the
    #   sand bars of Route 21.
    'MB_SHALLOW_WATER',
)
# pret/pokefirered src/metatile_behavior.c, sBehaviorSurfable at COMMIT.
# Water is `w`, blocked for walking; Surf, waterfall and current execution
# require separate game movement bindings. Water with the collision bit (the
# sea rocks of Route 21) blocks Surf too, so it is `#` like any other tile.
SURFABLE_WATER = frozenset({
    'MB_POND_WATER', 'MB_FAST_WATER', 'MB_DEEP_WATER', 'MB_WATERFALL',
    'MB_OCEAN_WATER', 'MB_UNUSED_WATER', 'MB_CYCLING_ROAD_WATER',
    'MB_EASTWARD_CURRENT', 'MB_WESTWARD_CURRENT', 'MB_NORTHWARD_CURRENT', 'MB_SOUTHWARD_CURRENT'})
#   A metatile's encounter type (METATILE_ATTRIBUTE_ENCOUNTER_TYPE in
#   include/fieldmap.h): on a map with land encounters, a step onto a LAND
#   tile may start a wild battle, as on every floor tile of a cave.
ENCOUNTER_TYPE_SHIFT, ENCOUNTER_TYPE_MASK = 24, 0x7
TILE_ENCOUNTER_LAND = 1
#   Open tiles closed on one side, and the region that lists those of them
#   with wild encounters, which their glyph can't say.
CLOSED_GLYPHS = frozenset(CLOSED_SIDES)
WILD_REGION = 'wild'
DIRECTIONS = {'up': 'north', 'down': 'south', 'left': 'west', 'right': 'east'}

#   Places and flag sets the decompilation doesn't name, written into the map
#   they belong to.
#   A `*_front` point is where the player stands to talk to someone across a
#   counter, or to walk north through a door.
POINTS = {
    #   Where a new game starts (WarpToPlayersRoom() in src/new_game.c).
    'PalletTown_PlayersHouse_2F': {'start': (6, 6)},
    'PalletTown': {'oaks_lab_front': (16, 14)},
    #   The clerk is across the counter to the west.
    'ViridianCity_Mart': {'clerk_front': (4, 3)},
    'ViridianCity_PokemonCenter_1F': {'nurse_front': (7, 4)},
    'PewterCity': {'gym_front': (15, 17)},
    'PewterCity_PokemonCenter_1F': {'nurse_front': (7, 4)},
    'PewterCity_Gym': {'brock_front': (6, 6)},
    #   The Magikarp salesman is at (1, 3), west of `salesman_front`.
    'Route4_PokemonCenter_1F': {'nurse_front': (7, 4), 'salesman_front': (2, 3)},
    #   The tile in front of the PC.
    'CeruleanCity_PokemonCenter_1F': {'pc': (11, 2), 'nurse_front': (7, 4)},
    #   The clerk (2, 3) is across the counter to the west.
    'CeruleanCity_Mart': {'clerk_front': (4, 3)},
    #   Below Misty (8, 6).
    'CeruleanCity_Gym': {'misty_front': (8, 7)},
    #   Where the player stands after entering from Cerulean City.
    'CeruleanCave_1F': {'entrance': (33, 21)},
    #   Mewtwo's tile. Its battle starts by talking to it from the south.
    'CeruleanCave_B1F': {'mewtwo': (7, 12)},
    'VermilionCity_PokemonCenter_1F': {'nurse_front': (7, 4)},
}
FLAG_SETS = {
    #   Set once the player has entered the Hall of Fame. They clear the way
    #   to Cerulean Cave: its guard, the rival and the Rocket.
    'CeruleanCity': {'after_hall_of_fame': [
        'FLAG_HIDE_CERULEAN_CAVE_GUARD',
        'FLAG_HIDE_CERULEAN_RIVAL',
        'FLAG_HIDE_CERULEAN_ROCKET',
    ]},
    #   Set at every new game (EventScript_ResetAllMapFlags in
    #   data/event_scripts.s): people who are on the map only in a scene.
    #   The S.S. Anne's rival stands on the Captain's door until his scene
    #   brings him out.
    'SSAnne_2F_Corridor': {'new_game': ['FLAG_HIDE_SS_ANNE_RIVAL']},
    'VermilionCity': {'new_game': ['FLAG_HIDE_VERMILION_CITY_OAKS_AIDE']},
}

#   Silph Co.'s Card Key doors. The map's blockdata has every door open; the
#   map's OnLoad script closes each one whose flag is unset
#   (`call_if_unset FLAG, EventScript_Close<n>FDoor<m>` in
#   data/scripts/silphco_doors.inc, closing by `setmetatile x, y, _, 1`, where
#   1 is the impassable bit). A new game has every flag unset, so every door is
#   closed in the base. A door is a gate (glyph `G`, an entry of the map's
#   `gates` table): its tiles are the ones the script closes that are walkable
#   in the blockdata; the barrier's top wall edge stays `#` open or closed. The
#   overlay for each map opens the gate once its flag is set.
DOOR_SCRIPTS = 'data/scripts/silphco_doors.inc'
DOOR_MAPS = frozenset(f'SilphCo_{floor}F' for floor in range(2, 12))
SETMETATILE = re.compile(r'\s*setmetatile\s+(\d+),\s*(\d+),\s*\w+,\s*([01])\s*$')
CALL_IF_UNSET = re.compile(r'\s*call_if_unset\s+(FLAG_\w+),\s*(\w+)\s*$')
GATE_GLYPH = 'G'


def script_blocks(text):
    """The lines of each `Label::` block of an .inc script file, by label."""
    blocks, label = {}, None
    for line in text.splitlines():
        match = re.match(r'(\w+)::', line)
        if match:
            label = match.group(1)
            blocks[label] = []
        elif label:
            blocks[label].append(line.split('@')[0])
    return blocks


def impassable_tiles(block):
    """The tiles a script's `setmetatile` calls make impassable."""
    tiles = []
    for line in block:
        match = SETMETATILE.match(line)
        if match and match.group(3) == '1':
            tiles.append((int(match.group(1)), int(match.group(2))))
    return tiles


def closed_doors(decomp, name):
    """The Card Key doors a map's OnLoad script closes at a new game, as a list
    of (flag, close script, tiles made impassable). Empty for other maps."""
    if name not in DOOR_MAPS:
        return []
    on_load = script_blocks(decomp.read(f'data/maps/{name}/scripts.inc').decode())[f'{name}_OnLoad']
    scripts = script_blocks(decomp.read(DOOR_SCRIPTS).decode())
    doors = []
    for line in on_load:
        match = CALL_IF_UNSET.match(line)
        if match:
            doors.append((match.group(1), match.group(2), impassable_tiles(scripts[match.group(2)])))
    return doors


def door_gates(doors, open_tiles):
    """The `gates` table of a Silph Co. map from its closed doors and the rows
    of the blockdata (every door open). Keys are the flag without its
    `FLAG_SILPH_<n>F_` prefix, lower case (`door`, `door_1`)."""
    gates = {}
    for flag, _script, closed in doors:
        tiles = [(x, y) for x, y in closed if open_tiles[y][x] != '#']
        glyphs = {open_tiles[y][x] for x, y in tiles}
        if len(glyphs) != 1:
            raise ValueError(f'{flag}: expected one open glyph, found {sorted(glyphs)}')
        gates[re.sub(r'FLAG_SILPH_\d+F_', '', flag).lower()] = {
            'tiles': sorted([x, y] for x, y in tiles), 'open_glyph': glyphs.pop(), 'new_game': 'closed',
            'opens_by': 'card_key_face_a', 'flag': flag}
    return gates


def set_tiles(tiles, coords, glyph):
    """`tiles` (row strings) with the given (x, y) tiles set to `glyph`."""
    rows = list(tiles)
    for x, y in coords:
        rows[y] = rows[y][:x] + glyph + rows[y][x + 1:]
    return rows


#   Pokemon Mansion's statue switches. One flag, FLAG_POKEMON_MANSION_SWITCH_STATE,
#   is shared by all four floors: facing a statue and pressing A asks "press
#   the secret switch?"; on yes, data/scripts/pokemon_mansion.inc sets the flag
#   (PokemonMansion_EventScript_PressSwitch_<floor>) or clears it
#   (..._ResetSwitch_<floor>), and each `setmetatile x, y, LABEL, collision`
#   there redraws barriers and floor. Each floor's OnLoad calls the press script
#   while the flag is set. The blockdata is the reset state (checked below), so
#   a new game's base is the blockdata. Each tile the press changes is part of a
#   gate (glyph `G`): a connected group that opens when the switch is on (a
#   barrier there at reset) or when it is off (open floor at reset).
MANSION_SWITCH = 'mansion'
MANSION_SWITCH_FLAG = 'FLAG_POKEMON_MANSION_SWITCH_STATE'
MANSION_SCRIPTS = 'data/scripts/pokemon_mansion.inc'
MANSION_FLOORS = ('PokemonMansion_1F', 'PokemonMansion_2F', 'PokemonMansion_3F', 'PokemonMansion_B1F')
SETMETATILE_LABEL = re.compile(r'\s*setmetatile\s+(\d+),\s*(\d+),\s*(\w+),\s*([01])\s*$')
FACING_STEP = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}


def metatile_calls(block):
    """The (x, y, label, collision) of each `setmetatile` call of a script,
    except the statue's eyes (a picture; the tile keeps its collision)."""
    calls = []
    for line in block:
        match = SETMETATILE_LABEL.match(line)
        if match and 'Statue' not in match.group(3):
            calls.append((int(match.group(1)), int(match.group(2)), match.group(3), int(match.group(4))))
    return calls


def connected(tiles):
    """The 4-connected groups of a set of (x, y) tiles, each sorted."""
    left, groups = set(tiles), []
    while left:
        stack, group = [min(left)], []
        left.discard(stack[0])
        while stack:
            x, y = stack.pop()
            group.append((x, y))
            for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                near = (x + step[0], y + step[1])
                if near in left:
                    left.discard(near)
                    stack.append(near)
        groups.append(sorted(group))
    return groups


def mansion_gates(scripts, name, tiles):
    """The `gates` table of a Mansion floor whose blockdata rows are `tiles`.
    A barrier (collision 1) is `#`; any other metatile has the glyph the reset
    script's blockdata tiles give its label. Raises if the blockdata is not the
    reset state, so the generator and the scripts cannot drift apart."""
    floor = name[len('PokemonMansion_'):]
    blocks = script_blocks(scripts)
    press = metatile_calls(blocks[f'PokemonMansion_EventScript_PressSwitch_{floor}'])
    reset = metatile_calls(blocks[f'PokemonMansion_EventScript_ResetSwitch_{floor}'])
    by_label = {}
    for x, y, label, collision in reset:
        glyph = tiles[y][x]
        if (glyph == '#') != (collision == 1):
            raise ValueError(f'{name} ({x}, {y}): blockdata {glyph!r} is not the reset state ({label}, collision {collision})')
        if by_label.setdefault(label, glyph) != glyph:
            raise ValueError(f'{name}: {label} is drawn as both {by_label[label]!r} and {glyph!r} in the blockdata')
    opens_on, opens_off = {}, {}
    for x, y, label, collision in press:
        glyph = '#' if collision == 1 else by_label[label]
        if tiles[y][x] == glyph:
            continue
        if glyph == '#':
            opens_off[(x, y)] = tiles[y][x]
        else:
            opens_on[(x, y)] = glyph
    groups = [(group, 'on', opens_on) for group in connected(opens_on)] + [
        (group, 'off', opens_off) for group in connected(opens_off)]
    groups.sort(key=lambda item: min((y, x) for x, y in item[0]))
    gates = {}
    for number, (group, open_when, glyphs) in enumerate(groups, 1):
        open_glyphs = {glyphs[tile] for tile in group}
        if len(open_glyphs) != 1:
            raise ValueError(f'{name}: a gate at {group[0]} is open as {sorted(open_glyphs)}')
        gates[f'barrier_{number}'] = {
            'tiles': [list(tile) for tile in group], 'open_glyph': open_glyphs.pop(),
            'new_game': 'open' if open_when == 'off' else 'closed',
            'switch': MANSION_SWITCH, 'open_when': open_when}
    return gates


def mansion_switches(source):
    """The `switches` table of a Mansion floor from its map.json: the statues
    (bg_events running the floor's `_EventScript_Statue`), each pressed from the
    tile it is faced from."""
    statues = []
    for event in source['bg_events']:
        if event.get('script', '').endswith('_EventScript_Statue'):
            facing = event['player_facing_dir'].removeprefix('BG_EVENT_PLAYER_FACING_').lower()
            dx, dy = FACING_STEP[facing]
            statues.append({'coord': [event['x'], event['y']], 'face_from': [event['x'] - dx, event['y'] - dy], 'facing': facing})
    return {MANSION_SWITCH: {'flag': MANSION_SWITCH_FLAG, 'toggle': True, 'floors': list(MANSION_FLOORS),
                             'statues': sorted(statues, key=lambda s: s['coord'])}}


#   Victory Road's boulder switches. A Strength boulder pushed onto a button
#   tile (MB_STRENGTH_BUTTON, glyph B) runs the coord event of that tile
#   directly (src/field_player_avatar.c DoBoulderFinish ->
#   src/field_control_avatar.c HandleBoulderActivateVictoryRoadSwitch; the
#   event's own `var_value 99` is never met by walking, the var is 0). The
#   script `<Floor>_EventScript_FloorSwitch<n>` redraws the barrier open with
#   `setmetatile` and sets a scene VAR to 100, which is permanent until
#   Route23_OnTransition resets every one of them to 0 (data/maps/Route23/
#   scripts.inc). Each floor's OnLoad draws the barrier closed while its VAR is
#   not 100 (`call_if_ne VAR, 100, <Floor>_EventScript_SetRockBarrier<n>`).
#   The blockdata is the open state, so the base shows the barrier as gate
#   tiles (G), closed at a new game. The barrier is two metatiles, `Top` and
#   `Bottom`, which open to different glyphs, so each is a gate of its own.
VICTORY_ROAD_FLOORS = ('VictoryRoad_1F', 'VictoryRoad_2F', 'VictoryRoad_3F')
VICTORY_ROAD_SET_VALUE = 100
CALL_IF_NE = re.compile(r'\s*call_if_ne\s+(VAR_\w+),\s*(\d+),\s*(\w+)\s*$')
SETVAR = re.compile(r'\s*setvar\s+(VAR_\w+),\s*(\d+)\s*$')
SETMETATILE_PART = re.compile(r'\s*setmetatile\s+(\d+),\s*(\d+),\s*METATILE_Cave_(?:RockBarrier|Floor_Ledge)_(Top|Bottom),\s*([01])\s*$')
FLOOR_SWITCH = re.compile(r'\w+_EventScript_FloorSwitch\d*\Z')


def victory_road_gates(scripts, source, name, tiles):
    """(`gates`, `switches`) of a Victory Road floor from its scripts.inc text,
    its map.json (`source`) and the blockdata rows `tiles` (barrier open).
    Gates are `barrier_<n>_top` and `barrier_<n>_bottom` for the n-th
    `call_if_ne` of OnLoad, moved by switch `floor_switch_<n>`; raises if a
    floor switch does not redraw exactly the tiles OnLoad closes."""
    blocks = script_blocks(scripts)
    gates, switches = {}, {}
    barriers = []
    for line in blocks[f'{name}_OnLoad']:
        match = CALL_IF_NE.match(line)
        if match and int(match.group(2)) == VICTORY_ROAD_SET_VALUE:
            barriers.append((match.group(1), match.group(3)))
    pressers = [(event, blocks[event['script']]) for event in source.get('coord_events', [])
                if FLOOR_SWITCH.match(event.get('script', ''))]
    if len(barriers) != len(pressers):
        raise ValueError(f'{name}: {len(barriers)} barriers but {len(pressers)} floor switches')
    for number, (var, label) in enumerate(barriers, 1):
        closes = {}
        for line in blocks[label]:
            match = SETMETATILE_PART.match(line)
            if match and match.group(4) == '1':
                closes[(int(match.group(1)), int(match.group(2)))] = match.group(3).lower()
        found = [(event, block) for event, block in pressers
                 if (var, str(VICTORY_ROAD_SET_VALUE)) in [m.groups() for m in map(SETVAR.match, block) if m]]
        if len(found) != 1:
            raise ValueError(f'{name}: {var} is set by {len(found)} floor switches')
        event, block = found[0]
        opens = {(int(m.group(1)), int(m.group(2))) for m in map(SETMETATILE_PART.match, block) if m and m.group(4) == '0'}
        if opens != set(closes):
            raise ValueError(f'{name}: {var} closes {sorted(closes)} in OnLoad but its floor switch opens {sorted(opens)}')
        x, y = event['x'], event['y']
        if tiles[y][x] != 'B':
            raise ValueError(f'{name}: floor switch ({x}, {y}) is {tiles[y][x]!r}, not a Strength button')
        for part in ('top', 'bottom'):
            group = sorted([x_, y_] for (x_, y_), kind in closes.items() if kind == part)
            glyphs = {tiles[y_][x_] for x_, y_ in group}
            if len(glyphs) != 1:
                raise ValueError(f'{name}: barrier {number} {part} is open as {sorted(glyphs)}')
            gates[f'barrier_{number}_{part}'] = {
                'tiles': group, 'open_glyph': glyphs.pop(), 'new_game': 'closed',
                'switch': f'floor_switch_{number}', 'open_when': 'on'}
        switches[f'floor_switch_{number}'] = {
            'flag': var, 'set_value': VICTORY_ROAD_SET_VALUE, 'toggle': False, 'floors': [name],
            'pressed_by': 'strength_boulder', 'buttons': [{'coord': [x, y]}]}
    return gates, switches


class Decomp:
    def __init__(self, commit, cache):
        self.commit = commit
        self.raw = 'https://raw.githubusercontent.com/pret/pokefirered/' + commit
        self.cache = os.path.join(cache, commit)

    def path(self, rel):
        local = os.path.join(self.cache, rel)
        if not os.path.exists(local):
            os.makedirs(os.path.dirname(local), exist_ok=True)
            subprocess.run(['curl', '-sfL', f'{self.raw}/{rel}', '-o', local], check=True)
        return local

    def read(self, rel):
        with open(self.path(rel), 'rb') as file:
            return file.read()


def behaviors(decomp):
    names = {}
    for line in decomp.read('include/constants/metatile_behaviors.h').decode().splitlines():
        match = re.match(r'#define (MB_\w+)\s+(0x[0-9A-Fa-f]+|\d+)', line)
        if match:
            names[int(match.group(2), 0)] = match.group(1)
    return names


def tileset_attributes(decomp, symbol):
    """The metatile attributes of tileset `symbol` (gTileset_<name>), from the
    file src/data/tilesets/metatiles.h names for gMetatileAttributes_<name>:
    folder names don't always follow the symbol (gTileset_SSAnne is ss_anne)."""
    attributes = symbol.replace('gTileset_', 'gMetatileAttributes_')
    match = re.search(
        r'\b' + attributes + r'\[\]\s*=\s*INCBIN_U32\("([^"]+)"\)',
        decomp.read('src/data/tilesets/metatiles.h').decode(),
    )
    if not match:
        sys.exit(f'No {attributes} in src/data/tilesets/metatiles.h.')
    data = decomp.read(match.group(1))
    return [struct.unpack_from('<I', data, i)[0] for i in range(0, len(data), 4)]


#   Signs the player reads by walking into them moving north or south
#   (TrySetUpWalkIntoSignpostScript() in src/field_control_avatar.c). A
#   signpost needs a sign event on its tile; the others don't.
SIGN_BEHAVIORS = ('MB_POKEMON_CENTER_SIGN', 'MB_POKEMART_SIGN', 'MB_INDIGO_PLATEAU_SIGN_1', 'MB_INDIGO_PLATEAU_SIGN_2')


def tile_glyph(behavior, collision, unhandled, sign_event=False):
    """The tile's glyph, and how its warp (if it has one) is entered: None for
    walking into it, the default."""
    if behavior in SIGN_BEHAVIORS or (behavior == 'MB_SIGNPOST' and sign_event):
        return 'S', None
    if behavior == 'MB_WARP_DOOR':
        return 'D', None    # doors have collision
    if behavior in LEDGES:
        return LEDGES[behavior], None
    if collision:
        return '#', None
    if behavior in WARP_ENTRIES:
        return '.', WARP_ENTRIES[behavior]
    if behavior in TERRAIN:
        return TERRAIN[behavior], 'step_on' if behavior == 'MB_FALL_WARP' else None
    if 'WATER' in behavior and behavior not in FLOOR:
        return 'w', None
    if behavior not in FLOOR:
        unhandled[behavior] = unhandled.get(behavior, 0) + 1
    return '.', None


def land_encounter(attributes):
    """Whether, on a map with land encounters, a step onto a tile with these
    metatile attributes may start a wild battle."""
    return (attributes >> ENCOUNTER_TYPE_SHIFT) & ENCOUNTER_TYPE_MASK == TILE_ENCOUNTER_LAND


def encounter_glyph(glyph, attributes):
    """On a map with land encounters: `glyph` for a tile with these metatile
    attributes, open floor where wild Pokemon appear written as tall grass."""
    return '~' if glyph == '.' and land_encounter(attributes) else glyph


def wild_edge(glyph, attributes):
    """On a map with land encounters: whether a tile closed on one side, with
    these metatile attributes, has wild encounters. Its glyph can't say so;
    the map lists it in region WILD_REGION."""
    return glyph in CLOSED_GLYPHS and land_encounter(attributes)


def grid(decomp, layout, names, unhandled, signs=frozenset(), land_encounters=False, unresolved=None):
    """The map's tile rows, elevation rows, how the warp on each tile is
    entered, by (x, y), where it isn't by walking into it, and the tiles closed
    on one side that have wild encounters. With `land_encounters`, open floor
    where wild Pokemon appear (a cave's) is written as tall grass, the glyph
    for "open, with wild encounters"."""
    width, height = layout['width'], layout['height']
    blocks = decomp.read(layout['blockdata_filepath'])
    primary = tileset_attributes(decomp, layout['primary_tileset'])
    secondary = tileset_attributes(decomp, layout['secondary_tileset'])
    tiles, elevation, entries, wild_edges = [], [], {}, []
    for y in range(height):
        row, levels = '', ''
        for x in range(width):
            value = struct.unpack_from('<H', blocks, 2 * (y * width + x))[0]
            metatile, collision, level = value & 0x3ff, (value >> 10) & 3, value >> 12
            attributes = primary[metatile] if metatile < 640 else secondary[metatile - 640]
            behavior = names.get(attributes & 0x1ff, hex(attributes & 0x1ff))
            before = unhandled.get(behavior, 0)
            glyph, entry = tile_glyph(behavior, collision, unhandled, (x, y) in signs)
            if unresolved is not None and unhandled.get(behavior, 0) > before:
                glyph = ' '  # Unknown cells are blocked by the shared movement model.
                unresolved.setdefault(behavior, []).append([x, y])
            if unresolved is not None and behavior in SURFABLE_WATER and not collision:
                glyph = 'w'
            if land_encounters and entry is None:
                glyph = encounter_glyph(glyph, attributes)
                if wild_edge(glyph, attributes):
                    wild_edges.append([x, y])
            row += glyph
            if entry:
                entries[(x, y)] = entry
            levels += '%x' % level
        tiles.append(row)
        elevation.append(levels)
    return tiles, elevation, entries, wild_edges


#   Movement types that wander or walk back and forth: they stay within
#   initial +- range (IsCoordOutsideObjectEventMovementRange() in
#   src/event_object_movement.c). The pairs move along one axis only. Walk
#   sequences (WALK_SEQUENCE) walk a fixed path instead; see walk_sequence().
MOVING = ('MOVEMENT_TYPE_WANDER_', 'MOVEMENT_TYPE_WALK_UP_AND_DOWN',
          'MOVEMENT_TYPE_WALK_DOWN_AND_UP', 'MOVEMENT_TYPE_WALK_LEFT_AND_RIGHT', 'MOVEMENT_TYPE_WALK_RIGHT_AND_LEFT')
WALK_SEQUENCE = 'MOVEMENT_TYPE_WALK_SEQUENCE_'
VERTICAL = ('UP_AND_DOWN', 'DOWN_AND_UP')
HORIZONTAL = ('LEFT_AND_RIGHT', 'RIGHT_AND_LEFT')


def wander_box(obj, tiles):
    """The tiles a person who walks on their own may stand on, kept inside the
    map, or None if they stand still."""
    movement = obj.get('movement_type', '')
    if not movement.startswith(MOVING):
        return None
    x = 0 if movement.endswith(VERTICAL) else int(obj.get('movement_range_x') or 0)
    y = 0 if movement.endswith(HORIZONTAL) else int(obj.get('movement_range_y') or 0)
    if x == 0 and y == 0:
        return None
    return {
        'x0': max(obj['x'] - x, 0), 'y0': max(obj['y'] - y, 0),
        'x1': min(obj['x'] + x, len(tiles[0]) - 1), 'y1': min(obj['y'] + y, len(tiles) - 1),
    }



class Ground:
    """What a person's step checks on each tile of a map: the blockdata
    collision bits, metatile behavior and elevation (GetCollisionAtCoords() in
    src/event_object_movement.c), as rows."""
    def __init__(self, collision, behavior, elevation):
        self.collision, self.behavior, self.elevation = collision, behavior, elevation

    def inside(self, x, y):
        return 0 <= y < len(self.collision) and 0 <= x < len(self.collision[0])


def read_ground(decomp, layout, names):
    """The Ground of `layout`, from its blockdata and tilesets."""
    width, height = layout['width'], layout['height']
    blocks = decomp.read(layout['blockdata_filepath'])
    primary = tileset_attributes(decomp, layout['primary_tileset'])
    secondary = tileset_attributes(decomp, layout['secondary_tileset'])
    collision, behavior, elevation = [], [], []
    for y in range(height):
        values = [struct.unpack_from('<H', blocks, 2 * (y * width + x))[0] for x in range(width)]
        collision.append([(value >> 10) & 3 for value in values])
        elevation.append([value >> 12 for value in values])
        behavior.append([names.get((primary[value & 0x3ff] if value & 0x3ff < 640 else secondary[(value & 0x3ff) - 640]) & 0x1ff, '')
                         for value in values])
    return Ground(collision, behavior, elevation)


STEPS = {'UP': (0, -1), 'DOWN': (0, 1), 'LEFT': (-1, 0), 'RIGHT': (1, 0)}
#   The behaviors that close a tile's side (MetatileBehavior_Is*Blocked() in
#   src/metatile_behavior.c), by side.
CLOSED_BY = {
    'UP': ('MB_IMPASSABLE_NORTH', 'MB_IMPASSABLE_NORTHEAST', 'MB_IMPASSABLE_NORTHWEST'),
    'DOWN': ('MB_IMPASSABLE_SOUTH', 'MB_IMPASSABLE_SOUTHEAST', 'MB_IMPASSABLE_SOUTHWEST'),
    'LEFT': ('MB_IMPASSABLE_WEST', 'MB_IMPASSABLE_NORTHWEST', 'MB_IMPASSABLE_SOUTHWEST'),
    'RIGHT': ('MB_IMPASSABLE_EAST', 'MB_IMPASSABLE_NORTHEAST', 'MB_IMPASSABLE_SOUTHEAST'),
}
OPPOSITE = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}


def walk_sequence_rules(source):
    """Each walk sequence's shortcut, from its MovementType_WalkSequence*_Step1()
    in src/event_object_movement.c, by movement type: (index, axis), where at
    sequence index `index`, back on its start column (axis x) or row (axis y),
    the person skips to the next direction."""
    rules = {}
    for name, index, axis, to in re.findall(
            r'MovementType_WalkSequence(\w+)_Step1\(.*?\)\s*\{.*?directionSequenceIndex == (\d) && '
            r'objectEvent->initialCoords\.([xy]) == objectEvent->currentCoords\.\3\)\s*\{\s*'
            r'objectEvent->directionSequenceIndex = (\d);', source, re.S):
        if int(to) != int(index) + 1:
            raise ValueError('unexpected walk sequence shortcut in ' + name)
        movement = WALK_SEQUENCE + re.sub(r'(?<!^)(?=[A-Z])', '_', name).upper()
        rules[movement] = (int(index), axis)
    if len(rules) != 24:
        raise ValueError(f'expected 24 walk sequences, read {len(rules)}')
    return rules


def walk_sequence(start, elevation, ranges, directions, shortcut, ground, objects=frozenset()):
    """The tiles a person walking a sequence of `directions` steps through,
    from `start` on the map `ground`, and the index of the tile they go on
    from after the last: {'tiles': [[x, y], ...], 'loop': i}. A person stopped
    for good (by a wall, other ground or a person in `objects`) has the tile
    they stand on as the last and loop to it.

    The rule of src/event_object_movement.c: each step,
    MovementType_WalkSequence*_Step1() skips direction `shortcut` = (index,
    axis) when back on the start column/row, then MoveNextDirectionInSequence()
    goes back to direction 0 when on the start tile at direction 3, and tries
    the current direction. GetCollisionAtCoords() answers
    COLLISION_OUTSIDE_RANGE past start +- range (a range of 0 is no limit on
    that axis; IsCoordOutsideObjectEventMovementRange()): the person turns to
    the next direction and tries once more. Any other collision (blocked tile
    or closed side, ground at another elevation, a person) and they walk in
    place, keeping their direction, so a wall stops them for good. The player
    and other walking people are not simulated; outside the map counts as
    blocked."""
    (x0, y0), (range_x, range_y), (skip_index, skip_axis) = start, ranges, shortcut

    def outside_range(x, y):
        return (range_x and not x0 - range_x <= x <= x0 + range_x) or (range_y and not y0 - range_y <= y <= y0 + range_y)

    def collision(x, y, level, direction):
        dx, dy = STEPS[direction]
        tx, ty = x + dx, y + dy
        if outside_range(tx, ty):
            return 'outside_range'
        if (not ground.inside(tx, ty) or ground.collision[ty][tx]
                or ground.behavior[y][x] in CLOSED_BY[direction] or ground.behavior[ty][tx] in CLOSED_BY[OPPOSITE[direction]]):
            return 'impassable'
        if level != 0 and ground.elevation[ty][tx] not in (0, 15) and ground.elevation[ty][tx] != level:
            return 'elevation'
        if (tx, ty) in objects:
            return 'object'
        return None

    def next_index(x, y, index):
        if index == skip_index and (x if skip_axis == 'x' else y) == (x0 if skip_axis == 'x' else y0):
            index += 1
        if index == 3 and (x, y) == (x0, y0):
            index = 0
        return index

    x, y, level = x0, y0, elevation
    index = next_index(x, y, 0)
    seen, tiles, tile_of_state = {}, [[x, y]], []
    while (x, y, index, level) not in seen:
        seen[(x, y, index, level)] = len(tile_of_state)
        tile_of_state.append(len(tiles) - 1)
        hit = collision(x, y, level, directions[index])
        if hit == 'outside_range':
            index += 1
            if index > 3:
                raise ValueError(f'walk sequence from {start} runs past its last direction')
            hit = collision(x, y, level, directions[index])
        if not hit:
            dx, dy = STEPS[directions[index]]
            x, y = x + dx, y + dy
            if ground.elevation[y][x] != 15:
                level = ground.elevation[y][x]
            tiles.append([x, y])
        index = next_index(x, y, index)
    loop = tile_of_state[seen[(x, y, index, level)]]
    if tiles[-1] == tiles[loop] and loop != len(tiles) - 1:
        tiles.pop()    # back where the loop starts
    return {'tiles': tiles, 'loop': loop}


LEG_DIRECTIONS = {step: direction for direction, step in npc_path.STEPS.items()}


def path_legs(walk):
    """A walk_sequence() walk as path legs (npc_path), or None if the person
    never leaves their start tile. Raises unless the walk loops back to its
    start or stops for good."""
    tiles, loop = walk['tiles'], walk['loop']
    if len(tiles) == 1:
        return None
    if loop == 0:
        steps, stops = tiles + [tiles[0]], False
    elif loop == len(tiles) - 1:
        steps, stops = tiles, True
    else:
        raise ValueError(f'walk from {tiles[0]} neither returns to its start nor stops')
    legs = []
    for (ax, ay), (bx, by) in zip(steps, steps[1:]):
        direction = LEG_DIRECTIONS[(bx - ax, by - ay)]
        if legs and legs[-1][0] == direction:
            legs[-1][1] += 1
        else:
            legs.append([direction, 1])
    if stops:
        legs[-1].append(npc_path.STUCK)
    return legs


def sequence_path(obj, ground, rules, objects=frozenset()):
    """A walk sequence's path legs (path_legs()), or None for any other movement."""
    movement = obj.get('movement_type', '')
    if not movement.startswith(WALK_SEQUENCE):
        return None
    directions = movement[len(WALK_SEQUENCE):].split('_')
    ranges = (int(obj.get('movement_range_x') or 0), int(obj.get('movement_range_y') or 0))
    return path_legs(walk_sequence((obj['x'], obj['y']), int(obj.get('elevation') or 0), ranges, directions,
                                   rules[movement], ground, objects))


#   Which way a person stands, by how they move.
FACINGS = {
    'MOVEMENT_TYPE_FACE_UP': 'north', 'MOVEMENT_TYPE_FACE_DOWN': 'south',
    'MOVEMENT_TYPE_FACE_LEFT': 'west', 'MOVEMENT_TYPE_FACE_RIGHT': 'east',
}
#   The ways a trainer who turns looks. A trainer who moves some other way
#   (wanders, looks around) may look any way.
TURNING_LOOKS = {
    'MOVEMENT_TYPE_FACE_DOWN_AND_UP': ['south', 'north'],
    'MOVEMENT_TYPE_FACE_LEFT_AND_RIGHT': ['west', 'east'],
    'MOVEMENT_TYPE_FACE_UP_AND_LEFT': ['north', 'west'],
    'MOVEMENT_TYPE_FACE_UP_AND_RIGHT': ['north', 'east'],
    'MOVEMENT_TYPE_FACE_DOWN_AND_LEFT': ['south', 'west'],
    'MOVEMENT_TYPE_FACE_DOWN_AND_RIGHT': ['south', 'east'],
    'MOVEMENT_TYPE_WANDER_UP_AND_DOWN': ['north', 'south'],
    'MOVEMENT_TYPE_WANDER_LEFT_AND_RIGHT': ['west', 'east'],
}
ALL_LOOKS = ['north', 'east', 'south', 'west']


def trainer(obj):
    """A trainer's sight and, unless they only face one way, the ways they
    look; None for anyone who doesn't battle on sight."""
    sight = int(obj.get('trainer_sight_or_berry_tree_id') or 0)
    if obj.get('trainer_type') != 'TRAINER_TYPE_NORMAL' or sight < 1:
        return None
    movement = obj.get('movement_type', '')
    if movement in FACINGS:
        return {'sight': sight}
    return {'sight': sight, 'looks': TURNING_LOOKS.get(movement, ALL_LOOKS)}


def map_object(obj, tiles, event_index=None, path=None):
    kind = obj['graphics_id'].replace('OBJ_EVENT_GFX_', '').lower()
    data = {'name': kind, 'kind': 'item' if kind == 'item_ball' else 'npc', 'x': obj['x'], 'y': obj['y']}
    if kind == 'item_ball' and event_index is not None:
        reference = {key: value for key, value in
                     dict(index=event_index, id=obj.get('local_id'), script=obj.get('script')).items()
                     if value is not None}
        if reference:
            data['source_event'] = reference
    box = wander_box(obj, tiles)
    if box:
        data['wander'] = box
    if path:
        data['path'] = path
    sight = trainer(obj)
    if sight:
        #   A trainer who faces one way looks that way.
        if 'looks' not in sight:
            data['facing'] = FACINGS[obj['movement_type']]
        data['trainer'] = sight
    flag = obj.get('flag') or '0'
    if flag != '0':
        data['hide_flag'] = flag
    return data


def item_scripts(decomp):
    """The pinned item-ball script resolver inputs (item-source-inputs.json), read
    from the decomp at its own commit and checked against their reviewed hashes."""
    inputs = json.loads(ITEM_SOURCE_INPUTS.read_text())
    source = inputs['sources']['frlg']
    if source['revision'] != getattr(decomp, 'commit', COMMIT):
        raise ValueError('item scripts are pinned at another decomp revision')
    files = {}
    for key, path in inputs['resolvers']['frlg'].items():
        raw = decomp.read(path)
        if digest(raw) != source['files'][path]['sha256']:
            raise ValueError('item script hash mismatch: ' + path)
        files[key] = (path, raw)
    return source, files


def decomp_item_identities(decomp, objects):
    """Item balls on a map the pinned catalog doesn't list: their item and count
    from the ball's own finditem script. A script that is not a plain finditem
    stays unresolved."""
    items = [o for o in objects if o.get('kind') == 'item']
    if not items:
        return None
    source, files = item_scripts(decomp)
    pickups = frlg_pickups(files['scripts'][1].decode(), files['macros'][1].decode())
    for obj in items:
        script = obj.get('source_event', {}).get('script') if isinstance(obj.get('source_event'), dict) else None
        obj.pop('pickup', None)
        obj.update(pickups.get(script) or unresolved_pickup('script is not a supported fixed item pickup'))
    return dict(repository=source['repository'], revision=source['revision'],
                scripts=files['scripts'][0], scripts_sha256=digest(files['scripts'][1]),
                macros=files['macros'][0], macros_sha256=digest(files['macros'][1]),
                source_game=source['source_game'], target_game=source['target_game'],
                target_game_relation=source['target_game_relation'], verification=source['verification'])


def hidden_items(source, tiles):
    """Hidden items (bg_events of type hidden_item): data only, they never block."""
    result = []
    for index, event in enumerate(source.get('bg_events', [])):
        if event.get('type') != 'hidden_item' or not (0 <= event['x'] < len(tiles[0]) and 0 <= event['y'] < len(tiles)):
            continue
        record = {'coord': [event['x'], event['y']], 'item': event['item'].replace('ITEM_', '', 1).lower(),
                  'quantity': int(event.get('quantity', 1)), 'flag': event['flag'], 'source_bg_event': index}
        if event.get('underfoot'):
            record['underfoot'] = True
        result.append(record)
    return result


#   Tiles the player never walks onto: their elevation only matters for doors,
#   which the player is put on by a warp and leaves at once.
UNWALKABLE = '#^v<>DS'
GROUND = '3'


def ground_only(tiles, elevation):
    """Whether every walkable tile is at ground level, so that the map can
    leave out its elevation grid (the loader reads ground everywhere)."""
    return all(level == GROUND for row, levels in zip(tiles, elevation)
               for tile, level in zip(row, levels) if tile not in UNWALKABLE)


def elevation_omission_reason(tiles, elevation, warps=None, points=None):
    """Return the documented reason to omit the elevation grid, or None to retain it."""
    # 1. Pure ground: every non-obstacle tile is level 3
    if all(level == GROUND for row, levels in zip(tiles, elevation)
           for tile, level in zip(row, levels) if tile not in UNWALKABLE):
        return 'all walkable tiles are ground level (3); non-ground levels appear only on unwalkable walls/obstacles'

    # Water is never omitted: Arduino's FRLG walker reads a missing grid as ground
    # everywhere, and water's own level (1) is what stops a walking player from
    # stepping onto it (the elevation mismatch that starts Surf instead).

    # 2. Reachable tiles: all reachable land (and water) is level 3, and any non-3 tiles are isolated/unreachable obstacles
    if warps is not None and points is not None:
        h, w = len(tiles), len(tiles[0])
        starts = set()
        for warp in warps:
            if 'coord' in warp:
                starts.add(tuple(warp['coord']))
            elif 'x' in warp and 'y' in warp:
                starts.add((warp['x'], warp['y']))
        for pt in points.values():
            starts.add(tuple(pt))
        queue = deque([s for s in starts if 0 <= s[0] < w and 0 <= s[1] < h])
        visited = set(queue)
        while queue:
            cx, cy = queue.popleft()
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in visited:
                    if tiles[ny][nx] not in '#DS':
                        visited.add((nx, ny))
                        queue.append((nx, ny))

        reachable_ground = all(elevation[y][x] == GROUND for (x, y) in visited if tiles[y][x] not in UNWALKABLE)
        #   A map entered only by its connections has no start to search from.
        flat_water = all(level == GROUND for row, levels in zip(tiles, elevation)
                         for tile, level in zip(row, levels) if tile == 'w')
        if visited and reachable_ground and flat_water:
            return 'all reachable land is ground level (3); non-ground tiles are unreachable boundary or counter tiles'

    return None


def warp_point(index):
    return f'warp_{index}'


def static_warp_id(event):
    """Return a fixed source warp index, or None for the explicit dynamic token."""
    value = event['dest_warp_id']
    if value == 'WARP_ID_DYNAMIC':
        return None
    if type(value) is int and value >= 0:
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)
    raise ValueError('unsupported source warp id: ' + repr(value))


def warp(event, entries, loaded, sources):
    """A warp event as MapData's warp: how it is entered, and the point it
    leads to, if its map is loaded and has that warp."""
    data = {'x': event['x'], 'y': event['y'], 'enter': entries.get((event['x'], event['y']), 'walk_into')}
    to_map, index = loaded.get(event['dest_map']), static_warp_id(event)
    if index is None:
        data['unresolved'] = 'dynamic_destination'
        data['source_destination'] = {'map': event['dest_map'], 'warp': event['dest_warp_id']}
        return data
    if to_map is not None and index < len(sources[to_map].get('warp_events', [])):
        data['to_map'] = to_map
        data['to_point'] = warp_point(index)
    return data


def arrivals(sources, loaded):
    """For each map, the indices of its warps that a warp leads to."""
    arriving = {name: set() for name in sources}
    for source in sources.values():
        for event in source.get('warp_events', []):
            to_map = loaded.get(event['dest_map'])
            index = static_warp_id(event)
            if to_map is not None and index is not None and index < len(sources[to_map].get('warp_events', [])):
                arriving[to_map].add(index)
    return arriving


def land_encounter_maps(decomp):
    """The ids of the maps that have land encounters (src/data/wild_encounters.json)."""
    groups = json.loads(decomp.read('src/data/wild_encounters.json'))['wild_encounter_groups']
    return {e['map'] for group in groups for e in group.get('encounters', []) if 'land_mons' in e}


def walk_sequence_paths(decomp, source, layouts, names):
    """The path of each person on the map who walks a sequence, by object
    event index. People who don't move on their own block them."""
    objects = source.get('object_events', [])
    walkers = [index for index, obj in enumerate(objects) if obj.get('movement_type', '').startswith(WALK_SEQUENCE)]
    if not walkers:
        return {}
    rules = walk_sequence_rules(decomp.read('src/event_object_movement.c').decode())
    land = read_ground(decomp, layouts[source['layout']], names)
    standing = frozenset((obj['x'], obj['y']) for obj in objects
                         if not obj.get('movement_type', '').startswith((WALK_SEQUENCE,) + MOVING))
    paths = {index: sequence_path(objects[index], land, rules, standing) for index in walkers}
    return {index: path for index, path in paths.items() if path}


def map_json(decomp, name, sources, layouts, names, loaded, unhandled, land_maps=frozenset(), include_item_identities=False, candidate=False):
    source = sources[name]
    signs = frozenset((e['x'], e['y']) for e in source.get('bg_events', []) if e.get('type') == 'sign')
    unresolved = {} if candidate else None
    tiles, elevation, entries, wild_edges = grid(
        decomp, layouts[source['layout']], names, unhandled, signs, source['id'] in land_maps, unresolved
    )
    #   Judge the elevation grid and hidden items on the map with its doors
    #   open: opening them is what a route needs, and it is the blockdata.
    open_tiles = tiles
    gates = door_gates(closed_doors(decomp, name), open_tiles)
    switches = {}
    if name in MANSION_FLOORS:
        gates = mansion_gates(decomp.read(MANSION_SCRIPTS).decode(), name, open_tiles)
        switches = mansion_switches(source)
    if name in VICTORY_ROAD_FLOORS:
        gates, switches = victory_road_gates(decomp.read(f'data/maps/{name}/scripts.inc').decode(), source, name, open_tiles)
    tiles = set_tiles(open_tiles, [tuple(c) for gate in gates.values() for c in gate['tiles']], GATE_GLYPH)
    warp_events = source.get('warp_events', [])
    points = {n: [x, y] for n, (x, y) in POINTS.get(name, {}).items()}
    for index in sorted(arrivals(sources, loaded)[name]):
        points[warp_point(index)] = [warp_events[index]['x'], warp_events[index]['y']]
    paths = walk_sequence_paths(decomp, source, layouts, names)
    data = {
        'name': name,
        'source': {'decomp_file': f'data/maps/{name}/map.json', 'revision': getattr(decomp, 'commit', COMMIT), 'date': COMMIT_DATE},
        'allow_running': source.get('allow_running', True),
        'tiles': tiles, 'elevation': elevation,
        'points': points,
        'regions': {WILD_REGION: wild_edges} if wild_edges else {},
        'warps': [warp(event, entries, loaded, sources) for event in warp_events],
        #   A few objects stand off the map, where no route meets them.
        'objects': [
            map_object(obj, tiles, index if include_item_identities else None, paths.get(index))
            for index, obj in enumerate(source.get('object_events', []))
            if 0 <= obj['x'] < len(tiles[0]) and 0 <= obj['y'] < len(tiles)
        ],
        'flag_sets': FLAG_SETS.get(name, {}),
        'connections': [
            {'side': DIRECTIONS[c['direction']], 'to_map': loaded[c['map']], 'offset': c['offset']}
            for c in (source.get('connections') or []) if c['map'] in loaded
        ],
    }
    if candidate:
        source_objects = [(index, obj) for index, obj in enumerate(source.get('object_events', []))
                          if 0 <= obj['x'] < len(tiles[0]) and 0 <= obj['y'] < len(tiles)]
        for obj, (index, original) in zip(data['objects'], source_objects):
            obj.setdefault('source_event', index)
            if 'script' in original:
                obj['source_script'] = original['script']
            if 'local_id' in original:
                obj['source_local_id'] = original['local_id']
        if unresolved:
            data['unresolved_tiles'] = unresolved
    if include_item_identities:
        events_hash = hashlib.sha256(decomp.read(f'data/maps/{name}/map.json')).hexdigest()
        data['objects'], identity_source = enrich_objects(data['objects'], 'frlg', name, events_hash, source_revision=getattr(decomp, 'commit', COMMIT))
        if identity_source is None:
            identity_source = decomp_item_identities(decomp, data['objects'])
        if identity_source is not None:
            data['source']['item_identities'] = identity_source
    #   A hole (MB_FALL_WARP, glyph H) drops the player to the warp event it
    #   names; the landing tile is no way back up, so the warp is one way.
    for entry in data['warps']:
        if open_tiles[entry['y']][entry['x']] == 'H':
            entry['one_way'] = True
    if gates:
        data['gates'] = gates
    if switches:
        data['switches'] = switches
    hidden = hidden_items(source, open_tiles)
    if hidden:
        data['hidden_items'] = hidden
    if candidate:
        for obj in data['objects']:
            event = obj.get('source_event')
            if isinstance(event, dict):
                if set(event) - {'index', 'id', 'script'} or not {'index', 'script'} <= set(event):
                    raise ValueError('unsupported source event provenance: ' + repr(event))
                obj['source_event'] = event['index']
                obj['source_script'] = event['script']
                if 'id' in event:
                    obj['source_local_id'] = event['id']
    if not data['regions']:
        del data['regions']
    omission = elevation_omission_reason(open_tiles, elevation, data.get('warps', []), data.get('points', {}))
    if omission is not None:
        del data['elevation']
        if candidate:
            data['source']['elevation_omitted'] = omission
    if data['allow_running']:
        del data['allow_running']
    return data


def json_text(data):
    return readable_map_text(compact_map(data))


def all_map_names(decomp):
    """Read actual map groups; metadata arrays are not additional maps."""
    groups = json.loads(decomp.read('data/maps/map_groups.json'))
    order = groups.get('group_order')
    if not isinstance(order, list) or not order:
        raise ValueError('map catalog requires group_order')
    names = set()
    for group in order:
        values = groups.get(group)
        if not isinstance(values, list) or any(not isinstance(n, str) or not re.fullmatch(r'[A-Za-z0-9_]+', n) for n in values):
            raise ValueError('invalid map catalog group: ' + str(group))
        names.update(values)
    return sorted(names)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--commit', default=COMMIT)
    parser.add_argument('--cache', default=os.path.expanduser('~/.cache/pokefirered'))
    parser.add_argument('--out', required=True, help='folder of the <map>.json files')
    parser.add_argument('--item-identities', action='store_true', help='enrich from the pinned pickup catalog')
    parser.add_argument('--check', action='store_true', help='check the files in --out instead of writing them')
    parser.add_argument('--all', dest='all_maps', action='store_true', help='generate the pinned full catalog into an empty candidate directory')
    parser.add_argument('--scope', help='with --all: explicit reviewed exclusion inventory; preserve boundary links')
    parser.add_argument('--manifest', help='with --all and --scope: every manifest map gets a base, in scope or not')
    parser.add_argument('maps', nargs='*', help='default: the maps already in --out')
    args = parser.parse_args()
    decomp = Decomp(args.commit, args.cache)
    if args.scope and not args.all_maps:
        parser.error('--scope requires --all')
    if args.manifest and not args.scope:
        parser.error('--manifest requires --all and --scope')
    listed = set()
    if args.manifest:
        status = statuses(json.loads(open(args.manifest).read()))
        listed = set(status)
    if args.all_maps:
        if args.maps:
            parser.error('--all cannot be combined with explicit map names')
        if not args.check and os.path.isdir(args.out) and any(n.endswith('.json') for n in os.listdir(args.out)):
            parser.error('--all requires an empty candidate directory; use --check to verify an existing candidate')
        try:
            args.maps = all_map_names(decomp)
        except ValueError as error:
            parser.error(str(error))
    if os.path.isdir(args.out):
        args.maps = sorted(set(args.maps) | {f[:-5] for f in os.listdir(args.out) if f.endswith('.json')})
    if not args.maps:
        parser.error('no maps given, and none in --out')

    excluded = read_scope(args.scope, args.maps, args.commit) if args.scope else {}
    #   A listed map outside the scope (a verified Center, Cerulean Cave) still gets its base.
    excluded = {name: reason for name, reason in excluded.items() if name not in listed}
    names = behaviors(decomp)
    layouts = {l['id']: l for l in json.loads(decomp.read('data/layouts/layouts.json'))['layouts'] if 'id' in l}
    sources = {m: json.loads(decomp.read(f'data/maps/{m}/map.json')) for m in args.maps}
    loaded = {source['id']: m for m, source in sources.items()}
    unhandled = {}
    land_maps = land_encounter_maps(decomp)
    maps = []
    for name in args.maps:
        if name in excluded:
            continue
        data = map_json(decomp, name, sources, layouts, names, loaded, unhandled, land_maps, args.item_identities, candidate=args.all_maps)
        text = contract_json_text(compact_map(data)) if args.all_maps else json_text(data)
        maps.append((name, text))
    if unhandled:
        if args.all_maps:
            sys.exit(f'Unhandled non-collision behaviors in candidate catalog: {unhandled}')
        print(f'Unhandled non-collision behaviors written as floor (legacy selected-map mode): {unhandled}')
    if args.check:
        differ = []
        if args.scope:
            unexpected = {f[:-5] for f in os.listdir(args.out) if f.endswith('.json')} - {n for n, _ in maps}
            if unexpected:
                sys.exit('Out-of-scope map files: ' + ' '.join(sorted(unexpected)))
        for name, text in maps:
            path = os.path.join(args.out, name + '.json')
            if not os.path.exists(path) or open(path, newline='').read() != text:
                differ.append(name)
        if args.manifest:
            if listed != {n for n, _ in maps}:
                sys.exit('Manifest maps differ from the generated bases: '
                         + ' '.join(sorted(listed ^ {n for n, _ in maps})))
        if differ:
            sys.exit(f'Differ from the generator: {" ".join(differ)}. Regenerate them without --check.')
        print(f'{len(maps)} maps in {args.out} match the generator.')
        return
    os.makedirs(args.out, exist_ok=True)
    for name, text in maps:
        with open(os.path.join(args.out, name + '.json'), 'w', newline='') as out:
            out.write(text)


if __name__ == '__main__':
    main()

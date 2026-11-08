# Imported from dayfine/Arduino-Source@51c0ce6128e5981da56b370a770874b96a1e129f
# Original path: devtools/maps/frlg_maps.py
"""Writes FRLG overworld maps as JSON, from the pret/pokefirered decompilation.

Owned by PokemonSimulation; export the JSON pack to console consumers.

Usage:
    PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --out data/games/frlg/maps/runtime \
        Route3 Route4 Route4_PokemonCenter_1F
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
Warps and connections lead only to maps in the same run: a warp to another map
has no destination, and a connection to one is left out. A warp arrives at
point "warp_<n>" of its map, the tile of that map's warp n. Other named points
and flag sets come from POINTS and FLAG_SETS below.

With --all, enumerate the complete pinned map catalog into an empty candidate
directory; this does not approve the data or support all movement mechanics.
With --scope, omit explicitly excluded maps but preserve their boundary links.
Without map names, the maps are the ones already in --out; with them, those
maps are added to the ones in --out, so warps and connections still join
them all. --check writes nothing: it regenerates them and fails if any file
differs. Export the generated pack with pokesim.maps.runtime_map_pack for
Arduino consumers.
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
from .runtime_symbols import CLOSED_SIDES, LEDGE_GLYPHS
from .item_identity import enrich_objects
from .runtime_map_coordinates import compact_map
from .runtime_map_format import map_text as readable_map_text
from .frlg_map_scope import read_scope

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
FLOOR = (
    'MB_NORMAL', 'MB_CAVE', 'MB_ROCK_STAIRS', 'MB_TALL_GRASS',
    'MB_SAND', 'MB_SAND_CAVE', 'MB_MOUNTAIN_TOP', 'MB_ICE',
)
# pret/pokefirered src/metatile_behavior.c, sBehaviorSurfable at COMMIT.
# Preserve water in the full baseline; it remains blocked for walking. Surf,
# waterfall and current execution require separate game movement bindings.
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

#   Tiles a script changes for good once the story is past it, written as
#   the story finds them after: Vermilion Gym's beams across rows 6 and 7
#   go off once both switches are found
#   (VermilionCity_Gym_EventScript_SetBeamsOff: (4..6, 6..7) floor,
#   FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES). No route of the story's goes
#   north of them before that, and one after can't end a leg on them as on
#   a wall.
OPENED_TILES = {
    'VermilionCity_Gym': [(x, y) for y in (6, 7) for x in (4, 5, 6)],
}


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
    if 'WATER' in behavior:
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
            if unresolved is not None and behavior in SURFABLE_WATER:
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


def wander_box(obj, tiles):
    """The tiles a wandering person may stand on, kept inside the map, or None
    if they stand still."""
    movement = obj.get('movement_type', '')
    if 'WANDER' not in movement:
        return None
    x = 0 if 'UP_AND_DOWN' in movement else int(obj.get('movement_range_x') or 0)
    y = 0 if 'LEFT_AND_RIGHT' in movement else int(obj.get('movement_range_y') or 0)
    if x == 0 and y == 0:
        return None
    return {
        'x0': max(obj['x'] - x, 0), 'y0': max(obj['y'] - y, 0),
        'x1': min(obj['x'] + x, len(tiles[0]) - 1), 'y1': min(obj['y'] + y, len(tiles) - 1),
    }


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


def map_object(obj, tiles, event_index=None):
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

    # 2. Ground land with flat water: water has no bridges or level changes
    no_bridge_levels = not any(c in '456789abcdef' for r in elevation for c in r if c != '3')
    land_and_water = all((level == GROUND if tile != 'w' else level in ('0', '1', '3'))
                         for row, levels in zip(tiles, elevation)
                         for tile, level in zip(row, levels) if tile not in UNWALKABLE)
    if land_and_water and no_bridge_levels:
        return 'all walkable land is ground level (3); water is flat without bridges'

    # 3. Reachable tiles: all reachable land is level 3, and any non-3 tiles are isolated/unreachable obstacles
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

        reachable_land_3 = all(elevation[y][x] == GROUND for (x, y) in visited if tiles[y][x] not in UNWALKABLE and tiles[y][x] != 'w')
        reachable_water_flat = all(elevation[y][x] in ('0', '1', '3') for (x, y) in visited if tiles[y][x] == 'w')
        no_reachable_bridges = not any(elevation[y][x] in '456789abcdef' for (x, y) in visited if elevation[y][x] != '3')
        if reachable_land_3 and reachable_water_flat and no_reachable_bridges:
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


def map_json(decomp, name, sources, layouts, names, loaded, unhandled, land_maps=frozenset(), include_item_identities=False, candidate=False):
    source = sources[name]
    signs = frozenset((e['x'], e['y']) for e in source.get('bg_events', []) if e.get('type') == 'sign')
    unresolved = {} if candidate else None
    tiles, elevation, entries, wild_edges = grid(
        decomp, layouts[source['layout']], names, unhandled, signs, source['id'] in land_maps, unresolved
    )
    for x, y in ([] if candidate else OPENED_TILES.get(name, [])):
        tiles[y] = tiles[y][:x] + '.' + tiles[y][x + 1:]
    warp_events = source.get('warp_events', [])
    points = {n: [x, y] for n, (x, y) in POINTS.get(name, {}).items()}
    for index in sorted(arrivals(sources, loaded)[name]):
        points[warp_point(index)] = [warp_events[index]['x'], warp_events[index]['y']]
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
            map_object(obj, tiles, index if include_item_identities else None) for index, obj in enumerate(source.get('object_events', []))
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
        data['source']['generation_status'] = 'unreviewed-full-catalog-candidate'
        if unresolved:
            data['unresolved_tiles'] = unresolved
        if name in OPENED_TILES:
            data['source']['unapplied_story_patch'] = 'OPENED_TILES: preserve decomp baseline until story state is bound'
    if include_item_identities:
        events_hash = hashlib.sha256(decomp.read(f'data/maps/{name}/map.json')).hexdigest()
        data['objects'], identity_source = enrich_objects(data['objects'], 'frlg', name, events_hash, source_revision=getattr(decomp, 'commit', COMMIT))
        if identity_source is not None:
            data['source']['item_identities'] = identity_source
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
    omission = elevation_omission_reason(tiles, elevation, data.get('warps', []), data.get('points', {}))
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
    parser.add_argument('maps', nargs='*', help='default: the maps already in --out')
    args = parser.parse_args()
    decomp = Decomp(args.commit, args.cache)
    if args.scope and not args.all_maps:
        parser.error('--scope requires --all')
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
        treatment = 'blocked unknown cells' if args.all_maps else 'floor (legacy selected-map mode)'
        print(f'Unhandled non-collision behaviors written as {treatment}: {unhandled}')
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

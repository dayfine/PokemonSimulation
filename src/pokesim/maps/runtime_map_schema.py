"""Structural contract for runtime maps; see docs/maps/runtime-maps.md.

Unknown extensions remain intact. Geometric invariants are checked here;
game-specific flag/trigger semantics belong to the replay adapter.
"""

from .npc_path import path_error
from .runtime_symbols import GLYPHS
from .runtime_map_coordinates import COMPACT, LEGACY, legacy_map

#   The step from a tile to the one it faces, by direction.
FACING = {'north': (0, -1), 'south': (0, 1), 'west': (-1, 0), 'east': (1, 0)}
ENTRIES = {'walk_into', 'step_on', 'cave_entrance', 'walk_north',
           'walk_south', 'walk_west', 'walk_east'}


def validate(data):
    """Check grid geometry and navigation fields without discarding extensions.

    Raises ValueError. Full field documentation is in docs/maps/runtime-maps.md;
    this checks the pack's structural and coordinate invariants, not whether
    decomp terrain or console observations are correct.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(isinstance(data, dict), 'map must be an object')
    if data.get('format') == COMPACT:
        validate(legacy_map(data))
        return data
    require(data.get('format', LEGACY) == LEGACY, 'unsupported runtime map format')
    require(isinstance(data.get('name'), str) and data['name'], 'name required')
    require(isinstance(data.get('source'), dict), 'source required')
    for field in ('decomp_file', 'revision', 'date'):
        require(isinstance(data['source'].get(field), str), 'source.' + field)
    rows = data.get('tiles')
    require(isinstance(rows, list) and rows and isinstance(rows[0], str) and rows[0], 'tiles required')
    width, height = len(rows[0]), len(rows)
    require(all(isinstance(row, str) and len(row) == width for row in rows), 'ragged tiles')
    require(all(set(row) <= GLYPHS for row in rows), 'unknown tile glyph')

    def tile(x, y):
        require(type(x) is int and type(y) is int and 0 <= x < width and 0 <= y < height,
                'tile outside map: ' + repr((x, y)))

    for point in data.get('points', {}).values():
        require(isinstance(point, list) and len(point) == 2, 'point must be [x,y]')
        tile(*point)
    for region in data.get('regions', {}).values():
        for point in region:
            tile(*point)
    if 'elevation' in data:
        levels = data['elevation']
        require(len(levels) == height and all(isinstance(row, str) and len(row) == width
                and set(row) <= set('0123456789abcdef') for row in levels), 'invalid elevation')
    require(type(data.get('allow_running', True)) is bool, 'allow_running must be boolean')
    for patch in data.get('patches', []):
        tile(patch['x'], patch['y'])
        require(patch['glyph'] in GLYPHS and len(patch['glyph']) == 1, 'invalid patch glyph')
        require(isinstance(patch.get('measured_by'), str) and patch['measured_by'], 'patch evidence required')
    for warp in data.get('warps', []):
        tile(warp['x'], warp['y'])
        require(warp.get('enter', 'walk_into') in ENTRIES, 'invalid warp entry')
        require(('to_map' in warp) == ('to_point' in warp), 'partial warp destination')
        require(warp.get('one_way', True) is True, 'one_way is true when present')
        require((rows[warp['y']][warp['x']] == 'H') <= (warp.get('one_way') is True),
                'a warp on a hole (H) is one_way: ' + repr((warp['x'], warp['y'])))
    for obj in data.get('objects', []):
        tile(obj['x'], obj['y'])
        require(isinstance(obj.get('name'), str) and isinstance(obj.get('kind'), str), 'object identity required')
        if 'item' in obj or 'quantity' in obj:
            require(obj['kind'] == 'item' and isinstance(obj.get('item'), str) and obj['item'], 'invalid item identity')
            require(type(obj.get('quantity', 1)) is int and obj.get('quantity', 1) > 0, 'invalid item quantity')
            require('interaction' not in obj and 'pickup' not in obj, 'conflicting pickup identity')
        if 'interaction' in obj:
            require(isinstance(obj['interaction'], dict) and isinstance(obj['interaction'].get('kind'), str),
                    'invalid interaction identity')
        if 'wander' in obj:
            box = obj['wander']
            tile(box['x0'], box['y0'])
            tile(box['x1'], box['y1'])
            require(box['x0'] <= box['x1'] and box['y0'] <= box['y1'], 'inverted wander box')
        if 'path' in obj:
            error = path_error((obj['x'], obj['y']), obj['path'], width, height)
            require(error is None, f"{obj['name']} ({obj['x']}, {obj['y']}): {error}")
    for event in data.get('coord_events', []):
        tile(event['x'], event['y'])
        require(type(event['width']) is int and type(event['length']) is int
                and event['width'] > 0 and event['length'] > 0, 'empty event')
        tile(event['x'] + event['width'] - 1, event['y'] + event['length'] - 1)
    gates, switches = data.get('gates', {}), data.get('switches', {})
    require(isinstance(gates, dict) and isinstance(switches, dict), 'gates and switches must be objects')
    claimed = {}
    for gate_id, gate in gates.items():
        require(isinstance(gate, dict) and gate.get('open_glyph') in ('.', '~', '2', '4', '6', '8'), f'gate {gate_id}: open_glyph')
        require(gate.get('new_game') in ('open', 'closed'), f'gate {gate_id}: new_game')
        require(isinstance(gate.get('tiles'), list) and gate['tiles'], f'gate {gate_id}: tiles')
        for x, y in gate['tiles']:
            tile(x, y)
            require((x, y) not in claimed, f'gate {gate_id}: tile {(x, y)} is also in gate {claimed.get((x, y))}')
            claimed[(x, y)] = gate_id
            require(rows[y][x] in ('G', '#', gate['open_glyph']), f'gate {gate_id}: tile {(x, y)} is {rows[y][x]!r}')
        if 'flag' in gate:
            require(gate.get('opens_by') == 'card_key_face_a' and gate['new_game'] == 'closed'
                    and 'switch' not in gate and 'open_when' not in gate, f'gate {gate_id}: a flag gate opens by Card Key and starts closed')
        else:
            require(gate.get('switch') in switches, f'gate {gate_id}: unknown switch {gate.get("switch")!r}')
            require(gate.get('open_when') in ('on', 'off') and 'opens_by' not in gate, f'gate {gate_id}: open_when')
            require((gate['open_when'] == 'off') == (gate['new_game'] == 'open'),
                    f'gate {gate_id}: a switch starts off, so it is open at a new game only when it opens when off')
    for y, row in enumerate(rows):
        for x, glyph in enumerate(row):
            require(glyph != 'G' or (x, y) in claimed, f'G tile {(x, y)} is in no gate')
    for switch_id, switch in switches.items():
        require(isinstance(switch.get('flag'), str) and isinstance(switch.get('toggle'), bool), f'switch {switch_id}: flag and toggle')
        require(isinstance(switch.get('floors'), list) and data['name'] in switch['floors'], f'switch {switch_id}: floors name this map')
        if switch['toggle']:
            require(isinstance(switch.get('statues'), list) and switch['statues'], f'switch {switch_id}: statues')
            for statue in switch['statues']:
                tile(*statue['coord'])
                tile(*statue['face_from'])
                dx, dy = FACING[statue['facing']]
                require([statue['face_from'][0] + dx, statue['face_from'][1] + dy] == statue['coord'],
                        f'switch {switch_id}: {statue["face_from"]} does not face {statue["coord"]} {statue["facing"]}')
        else:
            #   A Strength button: a boulder pushed onto it sets a scene VAR to
            #   `set_value` for good (until the game resets it).
            require(switch['flag'].startswith('VAR_') and type(switch.get('set_value')) is int, f'switch {switch_id}: a button sets a VAR to set_value')
            require(switch.get('pressed_by') == 'strength_boulder' and 'statues' not in switch, f'switch {switch_id}: pressed_by')
            require(isinstance(switch.get('buttons'), list) and switch['buttons'], f'switch {switch_id}: buttons')
            for button in switch['buttons']:
                tile(*button['coord'])
                require(rows[button['coord'][1]][button['coord'][0]] == 'B', f'switch {switch_id}: {button["coord"]} is not a Strength button (B)')
    for connection in data.get('connections', []):
        require(connection['side'] in {'north', 'south', 'west', 'east'}, 'invalid connection side')
        require(type(connection['offset']) is int, 'invalid connection offset')
    return data

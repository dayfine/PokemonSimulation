"""Structural contract for AutoStory runtime maps; see docs/maps/autostory.md.

Unknown extensions remain intact. Geometric invariants are checked here;
game-specific flag/trigger semantics belong to the replay adapter.
"""

GLYPHS = set('#.~w^v<>DS 8246')
ENTRIES = {'walk_into', 'step_on', 'cave_entrance', 'walk_north',
           'walk_south', 'walk_west', 'walk_east'}


def validate(data):
    """Check grid geometry and navigation fields without discarding extensions.

    Raises ValueError. Full field documentation is in docs/maps/autostory.md;
    this checks the pack's structural and coordinate invariants, not whether
    decomp terrain or console observations are correct.
    """
    def require(condition, message):
        if not condition:
            raise ValueError(message)

    require(isinstance(data, dict), 'map must be an object')
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
    for obj in data.get('objects', []):
        tile(obj['x'], obj['y'])
        require(isinstance(obj.get('name'), str) and isinstance(obj.get('kind'), str), 'object identity required')
        if 'wander' in obj:
            box = obj['wander']
            tile(box['x0'], box['y0'])
            tile(box['x1'], box['y1'])
            require(box['x0'] <= box['x1'] and box['y0'] <= box['y1'], 'inverted wander box')
    for event in data.get('coord_events', []):
        tile(event['x'], event['y'])
        require(type(event['width']) is int and type(event['length']) is int
                and event['width'] > 0 and event['length'] > 0, 'empty event')
        tile(event['x'] + event['width'] - 1, event['y'] + event['length'] - 1)
    for connection in data.get('connections', []):
        require(connection['side'] in {'north', 'south', 'west', 'east'}, 'invalid connection side')
        require(type(connection['offset']) is int, 'invalid connection offset')
    return data

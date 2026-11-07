"""Draw a computed local route with runtime glyphs and closed-side boundaries."""

from html import escape

from pokesim.grid.geometry import Direction
from pokesim.grid.maps import render
from pokesim.grid.maps.render import Overlay
from pokesim.grid.maps.schema import MapImage
from .runtime_symbols import CLOSED_SIDES


OBJECT_COLOR = (220, 135, 20, 255)
SCENE_COLOR = (160, 70, 185, 65)


def _visible_objects(view):
    return [obj for obj in view.data.get('objects', [])
            if not obj.get('hide_flag') or obj['hide_flag'] not in view.context.flags]


def _outline(image, x0, y0, x1, y1, color):
    for rect in [(x0, y0, x1, y0 + 1), (x0, y1 - 1, x1, y1),
                 (x0, y0, x0 + 1, y1), (x1 - 1, y0, x1, y1)]:
        image.fill_rect(*rect, color)


def ascii_route(view, path):
    rows = [list(row) for row in view.data['tiles']]
    for tile in view.occupied:
        rows[tile.y][tile.x] = 'O'
    for tile in view.scene_tiles:
        rows[tile.y][tile.x] = '?'
    places = path.places()
    for place in places:
        rows[place.tile.y][place.tile.x] = '*'
    first, last = places[0].tile, places[-1].tile
    rows[first.y][first.x] = '@'
    rows[last.y][last.x] = 'X'
    return '\n'.join(''.join(row) for row in rows) + '\n'


def route_image(view, path, tile_px=16, goal_tiles=()):
    if tile_px < 4:
        raise ValueError('tile size must be at least 4 pixels')
    image = render.plain_image(view.map_file.grid, tile_px)
    # Object uncertainty is not terrain or water. Keep the terrain visible.
    for tile in view.occupied:
        image.fill_rect(tile.x * tile_px, tile.y * tile_px,
                        (tile.x + 1) * tile_px, (tile.y + 1) * tile_px, (220, 135, 20, 28))
    for tile in view.scene_tiles:
        image.fill_rect(tile.x * tile_px, tile.y * tile_px,
                        (tile.x + 1) * tile_px, (tile.y + 1) * tile_px, SCENE_COLOR)
    for tile in goal_tiles:
        _outline(image, tile.x * tile_px, tile.y * tile_px,
                 (tile.x + 1) * tile_px, (tile.y + 1) * tile_px, (20, 150, 60, 180))
    for obj in _visible_objects(view):
        box = obj.get('wander')
        if box:
            _outline(image, box['x0'] * tile_px, box['y0'] * tile_px,
                     (box['x1'] + 1) * tile_px, (box['y1'] + 1) * tile_px, (145, 95, 20, 160))
        cx, cy = (obj['x'] + .5) * tile_px, (obj['y'] + .5) * tile_px
        image.fill_rect(int(cx) - 3, int(cy) - 3, int(cx) + 3, int(cy) + 3, OBJECT_COLOR)
    for x in range(view.map_file.grid.width + 1):
        image.fill_rect(x * tile_px, 0, x * tile_px + 1, image.height, (0, 0, 0, 35))
    for y in range(view.map_file.grid.height + 1):
        image.fill_rect(0, y * tile_px, image.width, y * tile_px + 1, (0, 0, 0, 35))
    overlay = Overlay(legs=[[place.tile for place in path.places()]])
    render.draw(image, MapImage('', 0, 0, tile_px), overlay)
    for y, row in enumerate(view.data['tiles']):
        for x, glyph in enumerate(row):
            side = CLOSED_SIDES.get(glyph)
            if side is None:
                continue
            x0, y0 = x * tile_px, y * tile_px
            x1, y1 = x0 + tile_px, y0 + tile_px
            if side is Direction.NORTH: y1 = y0 + 2
            if side is Direction.SOUTH: y0 = y1 - 2
            if side is Direction.WEST: x1 = x0 + 2
            if side is Direction.EAST: x0 = x1 - 2
            image.fill_rect(x0, y0, x1, y1, (0, 0, 0, 255))
    return image


def route_svg(view, path, title='', start_label='start', goal_label='goal',
              reference=None, landmarks=(), goal_facing=None, goal_tiles=(), tile_px=20):
    """Annotated collision-map diagram; the source reference identifies the task.

    This shows a Python candidate for a native goal, not a native planner replay.
    """
    grid = view.map_file.grid
    left, top = 36, 76
    width, height = grid.width * tile_px, grid.height * tile_px
    canvas_width = max(640, width + 60)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_width} {height + 174}" '
             f'width="{canvas_width}" height="{height + 174}" style="background:white">',
             f'<rect width="{canvas_width}" height="{height + 174}" fill="white"/>',
             '<style>text{font-family:monospace;fill:#222}.label{font-size:11px}</style>']
    def text(x, y, value, size=12, extra=''):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    text(left, 20, title or view.map_file.name, 14)
    text(left, 39, f'{view.map_file.name}: local tile coordinates; {len(path.moves)} presses; Python cost {path.cost}', 11)
    start, end = path.start.place.tile, path.end.place.tile
    text(left, 56, f'S {start_label} ({start.x},{start.y}) -> G {goal_label} ({end.x},{end.y})'
         + (f'; face {goal_facing}' if goal_facing else ''))
    parts.append(f'<g transform="translate({left},{top})">')
    for y, row in enumerate(grid.rows()):
        x = 0
        while x < len(row):
            color = render.cell_color(row[x])[:3]
            stop = x + 1
            while stop < len(row) and render.cell_color(row[stop])[:3] == color:
                stop += 1
            parts.append(f'<rect x="{x * tile_px}" y="{y * tile_px}" width="{(stop - x) * tile_px}" height="{tile_px}" fill="rgb{color}"/>')
            x = stop
    for obj in _visible_objects(view):
        if 'wander' in obj:
            box = obj['wander']
            parts.append(f'<rect x="{box["x0"] * tile_px}" y="{box["y0"] * tile_px}" '
                         f'width="{(box["x1"] - box["x0"] + 1) * tile_px}" height="{(box["y1"] - box["y0"] + 1) * tile_px}" '
                         'fill="#d98a13" fill-opacity=".08" stroke="#a46b16" stroke-dasharray="4 3"/>')
        parts.append(f'<circle cx="{(obj["x"] + .5) * tile_px}" cy="{(obj["y"] + .5) * tile_px}" r="4" fill="#d98a13"/>')
        if obj.get('kind') == 'item' and obj.get('item'):
            label = obj['item'].replace('_', ' ').title() + ' ×' + str(obj['quantity'])
            text((obj['x'] + 1) * tile_px + 3, (obj['y'] + .5) * tile_px, label, 10, 'class="label"')
    for tile in sorted(view.scene_tiles):
        parts.append(f'<rect x="{tile.x * tile_px}" y="{tile.y * tile_px}" width="{tile_px}" height="{tile_px}" fill="#a046b9" fill-opacity=".25"/>')
    for tile in sorted(goal_tiles):
        parts.append(f'<rect x="{tile.x * tile_px}" y="{tile.y * tile_px}" width="{tile_px}" height="{tile_px}" fill="none" stroke="#199545"/>')
    for x in range(grid.width + 1):
        parts.append(f'<path d="M{x * tile_px} 0V{height}" stroke="#000" stroke-opacity=".12"/>')
        if x < grid.width and x % 5 == 0: text(x * tile_px + 3, -5, x, 10)
    for y in range(grid.height + 1):
        parts.append(f'<path d="M0 {y * tile_px}H{width}" stroke="#000" stroke-opacity=".12"/>')
        if y < grid.height and y % 5 == 0: text(-25, y * tile_px + 13, y, 10)
    for y, row in enumerate(view.data['tiles']):
        for x, glyph in enumerate(row):
            side = CLOSED_SIDES.get(glyph)
            x0, y0 = x * tile_px, y * tile_px
            if side is not None:
                if side is Direction.NORTH: segment = f'M{x0} {y0}h{tile_px}'
                if side is Direction.SOUTH: segment = f'M{x0} {y0 + tile_px}h{tile_px}'
                if side is Direction.WEST: segment = f'M{x0} {y0}v{tile_px}'
                if side is Direction.EAST: segment = f'M{x0 + tile_px} {y0}v{tile_px}'
                parts.append(f'<path d="{segment}" stroke="black" stroke-width="3"/>')
            if glyph in '^v<>':
                dx, dy = {'^': (0, -1), 'v': (0, 1), '<': (-1, 0), '>': (1, 0)}[glyph]
                cx, cy = x0 + tile_px / 2, y0 + tile_px / 2
                tx, ty = cx + 5 * dx, cy + 5 * dy
                arrow = (f'M{cx - 5 * dx} {cy - 5 * dy}L{tx} {ty}'
                         f'M{tx - 3 * dx - 3 * dy} {ty - 3 * dy + 3 * dx}'
                         f'L{tx} {ty}L{tx - 3 * dx + 3 * dy} {ty - 3 * dy - 3 * dx}')
                parts.append(f'<path d="{arrow}" fill="none" stroke="#222" stroke-width="1.5"/>')
    points = ' '.join(f'{(p.tile.x + .5) * tile_px},{(p.tile.y + .5) * tile_px}' for p in path.places())
    parts.append(f'<polyline points="{points}" fill="none" stroke="#d92525" stroke-width="3"/>')
    for marker, tile in [('S', start), ('G', end)]:
        cx, cy = (tile.x + .5) * tile_px, (tile.y + .5) * tile_px
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="white" stroke="#c00" stroke-width="2"/>')
        text(cx, cy + 4, marker, 11, 'text-anchor="middle"')
    for landmark in landmarks:
        x, y = landmark['tile']
        text((x + 1) * tile_px + 3, (y + .5) * tile_px, landmark['label'], extra='class="label"')
    parts.append('</g>')
    text(left, top + height + 24, 'Red: route | orange dot: object spawn | dashed box: possible NPC area')
    text(left, top + height + 42, 'Purple: scene excluded | blue: water | green: goal region | arrows: ledges', 11)
    if reference:
        text(left, top + height + 62, f'Native #{reference["pr"]} / {reference["checkpoint"]} / {reference["step"]} @ {reference["revision"][:10]}')
    text(left, top + height + 80, 'Python candidate: native leg costs, battles and recovery are not replayed.', 11)
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'

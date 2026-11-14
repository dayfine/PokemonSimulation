"""Draw planned and walked routes, and what happened on them, over one runtime map.

A picture is a tile grid (walls dark, grass, water, doors, ledges), NPCs as
dots with their wander zones as dashed boxes, then lines and markers:

    Line('plan', [(11, 28), (3, 28), (3, 26)])          solid: what the planner chose
    Line('walked', [(11, 28), (3, 28)], label='1')      dashed: what the console did
    Line('alt', ...)                                    dashed grey: a re-plan or another option
    Marker('failed', (3, 26), 'old man: nobody answered')
    Marker('suspect', (3, 25), 'map couple')            a tile to check (red box)

`picture_svg` writes an annotated SVG (axes, legend, notes); `picture_png`
the same lines and markers on a plain raster, without text. Coordinates are
the runtime map's local tiles, x right and y down.
"""

from dataclasses import dataclass
from html import escape

from pokesim.grid.geometry import Tile
from pokesim.grid.maps.model import LEDGE_DIRECTION, Behavior
from pokesim.png import Image
from .runtime_symbols import CLOSED_SIDES


@dataclass
class Line:
    style: str              # plan, walked, alt
    tiles: list             # [(x, y)], corners in order
    label: str = ''         # drawn at the first tile (a walk's number)


@dataclass
class Marker:
    kind: str               # see MARKERS
    tile: tuple             # (x, y)
    text: str = ''


#  Light palette of the route sketches artifact (scratchpad routes/head.html).
TILE_COLORS = {'wall': '#59605c', 'floor': '#eef0ea', 'grass': '#9cc58f', 'water': '#8fb6d9',
               'door': '#b0743c', 'sign': '#c9b26b', 'ledge': '#d9cfa8', 'unknown': '#c8c8c8'}
LINE_STYLES = {
    'plan': ('#e0661b', ''),
    'walked': ('#1f6fd1', '6 4'),
    'alt': ('#6d7470', '4 4'),
}
LINE_NAMES = {'plan': 'planned route', 'walked': 'walked', 'alt': 're-plan / other route'}
#  kind: (glyph, fill, legend text)
MARKERS = {
    'start': ('S', '#ffffff', 'start'),
    'goal': ('G', '#ffffff', 'goal'),
    'battle': ('B', '#f2b134', 'battle'),
    'trainer': ('T', '#f2b134', 'trainer stopped us'),
    'reanchor': ('R', '#2aa198', 're-anchor (found again)'),
    'stop': ('!', '#f2b134', 'stopped early'),
    'wait': ('!', '#f2b134', 'blocked, waited'),
    'blocker': ('!', '#f2b134', 'someone in the way'),
    'obstacle': ('?', '#f2b134', 'something the map lacks'),
    'message': ('M', '#f2b134', 'message'),
    'talk': ('t', '#c9a4ef', 'talk'),
    'arrived': ('', '', ''),
    'failed': ('X', '#d62839', 'failed here'),
    'suspect': ('', '#d62839', 'suspect tile'),
    'candidate': ('', '', 'possible tile'),
}
NPC_COLOR, ZONE_EDGE = '#7b2fbf', '#d62839'
SCENE_COLOR, REGION_COLOR = '#a046b9', '#199545'

_RGB = lambda value, alpha=255: (int(value[1:3], 16), int(value[3:5], 16), int(value[5:7], 16), alpha)


def tile_class(view, x, y):
    cell = view.map_file.grid.at(Tile(x, y))
    if cell is None:
        return 'wall'
    if cell.behavior is Behavior.UNKNOWN:
        return 'unknown'
    if cell.behavior is Behavior.TALL_GRASS:
        return 'grass'
    if cell.behavior is Behavior.WATER:
        return 'water'
    if cell.behavior in (Behavior.DOOR, Behavior.WARP):
        return 'door'
    if cell.behavior is Behavior.SIGN:
        return 'sign'
    if cell.behavior in LEDGE_DIRECTION:
        return 'ledge'
    return 'wall' if cell.blocked else 'floor'


def _clip(zone, box):
    """A wander zone cut to the drawn rectangle, or None if it lies outside."""
    x0, y0, x1, y1 = box
    clipped = dict(x0=max(zone['x0'], x0), y0=max(zone['y0'], y0), x1=min(zone['x1'], x1), y1=min(zone['y1'], y1))
    return clipped if clipped['x0'] <= clipped['x1'] and clipped['y0'] <= clipped['y1'] else None


def _zones(obj, box):
    """Where a person may stand, cut to the drawn rectangle: their wander box,
    or each tile of the path they walk."""
    zones = [obj['wander']] if 'wander' in obj else [
        dict(x0=x, y0=y, x1=x, y1=y) for x, y in obj.get('path', {}).get('tiles', [])]
    return [zone for zone in (_clip(zone, box) for zone in zones) if zone]


def visible_objects(view):
    return [obj for obj in view.data.get('objects', [])
            if not obj.get('hide_flag') or obj['hide_flag'] not in view.context.flags]


def crop_box(view, lines, markers, margin=3):
    """The map rectangle (x0, y0, x1, y1) around everything drawn, `margin` tiles wider."""
    grid = view.map_file.grid
    points = [tile for line in lines for tile in line.tiles] + [marker.tile for marker in markers]
    if not points:
        return 0, 0, grid.width - 1, grid.height - 1
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    return (max(0, min(xs) - margin), max(0, min(ys) - margin),
            min(grid.width - 1, max(xs) + margin), min(grid.height - 1, max(ys) + margin))


def picture_svg(view, lines, markers=(), title='', subtitle='', notes=(), box=None,
                regions=(), tile_px=16):
    """An SVG of `lines` and `markers` over the map; `box` crops it (default: whole map)."""
    grid = view.map_file.grid
    x0, y0, x1, y1 = box or (0, 0, grid.width - 1, grid.height - 1)
    t = tile_px
    width, height = (x1 - x0 + 1) * t, (y1 - y0 + 1) * t
    px = lambda x: (x - x0) * t
    py = lambda y: (y - y0) * t
    cx = lambda x: (x - x0 + .5) * t
    cy = lambda y: (y - y0 + .5) * t
    legend = [('tile', TILE_COLORS[kind], '', kind) for kind in ('wall', 'floor', 'grass', 'water', 'door', 'ledge')]
    legend += [('npc', NPC_COLOR, '', 'person'), ('zone', ZONE_EDGE, '', 'wander zone')]
    legend += [('line', *LINE_STYLES[style], LINE_NAMES[style]) for style in LINE_STYLES
               if any(line.style == style for line in lines)]
    for kind in dict.fromkeys(marker.kind for marker in markers):
        glyph, fill, label = MARKERS.get(kind, ('', '', ''))
        if label:
            legend.append((kind if kind in ('suspect', 'candidate') else 'marker', fill, glyph, label))
    #  Suspect tiles are numbered on the map and explained under it.
    suspects = [marker for marker in markers if marker.kind == 'suspect' and marker.text]
    notes = [f'[{i}] ({m.tile[0]}, {m.tile[1]}): {m.text}' for i, m in enumerate(suspects, 1)] + list(notes)
    left, top = 34, 50 if subtitle else 34
    longest = max([len(title or view.map_file.name) * 8.2, len(subtitle) * 6.7]
                  + [len(note) * 6.7 for note in notes])
    canvas_width = int(max(width + left + 16, 560, left + longest + 16))
    #  Legend items flow left to right and wrap at the canvas edge.
    placed, x, row = [], left, top + height + 18
    for item in legend:
        item_width = (30 if item[0] == 'line' else 22) + 7 * len(item[3])
        if x > left and x + item_width > canvas_width - 8:
            x, row = left, row + 18
        placed.append((x, row, item))
        x += item_width
    canvas_height = row + 18 * len(notes) + 14
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {canvas_width} {canvas_height}" '
             f'width="{canvas_width}" height="{canvas_height}">',
             '<style>text{font-family:ui-monospace,Menlo,monospace;fill:#1d2321}'
             '.ax{font-size:9px;fill:#5b6662}.t{stroke:#f6f7f4;stroke-width:.5}'
             '.lab{font-size:10px;font-weight:600}.note{font-size:11px}</style>',
             f'<rect width="{canvas_width}" height="{canvas_height}" fill="#f6f7f4"/>',
             '<defs>' + ''.join(
                 f'<marker id="arrow-{style}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" '
                 f'markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>'
                 for style, (color, _) in LINE_STYLES.items()) + '</defs>']

    def text(x, y, value, cls='', extra=''):
        cls = f' class="{cls}"' if cls else ''
        parts.append(f'<text x="{x}" y="{y}"{cls} {extra}>{escape(str(value))}</text>')

    text(left, 18, title or view.map_file.name, extra='font-size="13" font-weight="600"')
    if subtitle:
        text(left, 36, subtitle, 'note')
    parts.append(f'<g transform="translate({left},{top})">')
    for y in range(y0, y1 + 1):
        if y % 5 == 0:
            text(-4, cy(y) + 3, y, 'ax', 'text-anchor="end"')
        for x in range(x0, x1 + 1):
            color = TILE_COLORS[tile_class(view, x, y)]
            parts.append(f'<rect class="t" x="{px(x)}" y="{py(y)}" width="{t}" height="{t}" fill="{color}"/>')
    for x in range(x0, x1 + 1):
        if x % 5 == 0:
            text(cx(x), -4, x, 'ax', 'text-anchor="middle"')
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            side = CLOSED_SIDES.get(view.data['tiles'][y][x])
            if side is not None:
                ax, ay = px(x), py(y)
                segment = {'NORTH': f'M{ax} {ay}h{t}', 'SOUTH': f'M{ax} {ay + t}h{t}',
                           'WEST': f'M{ax} {ay}v{t}', 'EAST': f'M{ax + t} {ay}v{t}'}[side.name]
                parts.append(f'<path d="{segment}" stroke="#1d2321" stroke-width="3"/>')
    inside = lambda x, y: x0 <= x <= x1 and y0 <= y <= y1
    for tile in sorted(view.scene_tiles):
        if inside(tile.x, tile.y):
            parts.append(f'<rect x="{px(tile.x)}" y="{py(tile.y)}" width="{t}" height="{t}" '
                         f'fill="{SCENE_COLOR}" fill-opacity=".25"/>')
    for region in regions:
        for tile in sorted(region):
            if inside(tile[0], tile[1]):
                parts.append(f'<rect x="{px(tile[0])}" y="{py(tile[1])}" width="{t}" height="{t}" '
                             f'fill="none" stroke="{REGION_COLOR}" stroke-width="1.5"/>')
    for obj in visible_objects(view):
        for zone in _zones(obj, (x0, y0, x1, y1)):
            parts.append(f'<rect x="{px(zone["x0"])}" y="{py(zone["y0"])}" width="{(zone["x1"] - zone["x0"] + 1) * t}" '
                         f'height="{(zone["y1"] - zone["y0"] + 1) * t}" fill="{ZONE_EDGE}" fill-opacity=".12" '
                         f'stroke="{ZONE_EDGE}" stroke-width="1.5" stroke-dasharray="4 3"/>')
        if inside(obj['x'], obj['y']):
            name = obj.get('name') or obj.get('item') or obj.get('kind', '')
            parts.append(f'<circle cx="{cx(obj["x"])}" cy="{cy(obj["y"])}" r="{t * .32:.1f}" fill="{NPC_COLOR}">'
                         f'<title>{escape(str(name))} ({obj["x"]}, {obj["y"]})</title></circle>')
    for marker in markers:
        if marker.kind == 'candidate':
            parts.append(f'<circle cx="{cx(marker.tile[0])}" cy="{cy(marker.tile[1])}" r="{t * .4:.1f}" '
                         'fill="none" stroke="#1d2321" stroke-width="1.2" opacity=".6"/>')
        elif marker.kind == 'suspect':
            parts.append(f'<rect x="{px(marker.tile[0]) + 1}" y="{py(marker.tile[1]) + 1}" width="{t - 2}" '
                         f'height="{t - 2}" fill="none" stroke="{ZONE_EDGE}" stroke-width="2"/>')
    for line in lines:
        color, dash = LINE_STYLES[line.style]
        if len(line.tiles) > 1:
            points = ' '.join(f'{cx(x)},{cy(y)}' for x, y in line.tiles)
            dashes = f' stroke-dasharray="{dash}"' if dash else ''
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3" '
                         f'stroke-linejoin="round" stroke-linecap="round"{dashes} marker-end="url(#arrow-{line.style})"/>')
        if line.tiles:
            x, y = line.tiles[0]
            parts.append(f'<circle cx="{cx(x)}" cy="{cy(y)}" r="{t * .26:.1f}" fill="{color}"/>')
            if line.label:
                text(cx(x) + t * .35, cy(y) - t * .35, line.label, 'lab', f'fill="{color}" style="fill:{color}"')
    seen = {}
    for marker in markers:
        glyph, fill, _ = MARKERS.get(marker.kind, ('', '', ''))
        x, y = marker.tile
        if glyph:
            #  Markers on one tile fan out to the upper right so each stays visible.
            k = seen[marker.tile] = seen.get(marker.tile, -1) + 1
            mx, my = cx(x) + k * t * .45, cy(y) - k * t * .45
            parts.append(f'<g><title>{escape(marker.text or marker.kind)}</title>'
                         f'<circle cx="{mx}" cy="{my}" r="{t * .42:.1f}" fill="{fill}" stroke="#1d2321" stroke-width="1"/>'
                         f'<text x="{mx}" y="{my + 3.5}" class="lab" text-anchor="middle">{escape(glyph)}</text></g>')
    for i, marker in enumerate(suspects, 1):
        text(px(marker.tile[0]) + t / 2, py(marker.tile[1]) - 2, i, 'lab', f'text-anchor="middle" style="fill:{ZONE_EDGE}"')
    parts.append('</g>')
    for x, y, (shape, color, extra, label) in placed:
        if shape == 'tile':
            parts.append(f'<rect x="{x}" y="{y - 9}" width="10" height="10" fill="{color}" stroke="#d6dbd6"/>')
        elif shape == 'npc':
            parts.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="4" fill="{color}"/>')
        elif shape == 'zone':
            parts.append(f'<rect x="{x}" y="{y - 9}" width="10" height="10" fill="{color}" '
                         f'fill-opacity=".12" stroke="{color}" stroke-dasharray="3 2"/>')
        elif shape == 'line':
            dashes = f' stroke-dasharray="{extra}"' if extra else ''
            parts.append(f'<path d="M{x} {y - 4}h18" stroke="{color}" stroke-width="3"{dashes}/>')
            x += 8
        elif shape == 'suspect':
            parts.append(f'<rect x="{x}" y="{y - 9}" width="10" height="10" fill="none" stroke="{color}" stroke-width="2"/>')
        elif shape == 'candidate':
            parts.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="5" fill="none" stroke="#1d2321"/>')
        else:
            parts.append(f'<circle cx="{x + 5}" cy="{y - 4}" r="6" fill="{color}" stroke="#1d2321"/>')
            text(x + 5, y - 0.5, extra, 'lab', 'text-anchor="middle"')
        text(x + 14, y, label, 'note')
    for i, note in enumerate(notes):
        text(left, row + 18 * (i + 1), note, 'note')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def picture_png(view, lines, markers=(), box=None, regions=(), tile_px=16):
    """The same picture as a raster, without text: tiles, zones, NPCs, lines and markers."""
    grid = view.map_file.grid
    x0, y0, x1, y1 = box or (0, 0, grid.width - 1, grid.height - 1)
    t = tile_px
    if t < 4:
        raise ValueError('tile size must be at least 4 pixels')
    image = Image((x1 - x0 + 1) * t, (y1 - y0 + 1) * t, _RGB('#f6f7f4'))
    rect = lambda x, y, color, inset=0: image.fill_rect(
        (x - x0) * t + inset, (y - y0) * t + inset, (x - x0 + 1) * t - inset, (y - y0 + 1) * t - inset, color)
    center = lambda x, y: ((x - x0) * t + t // 2, (y - y0) * t + t // 2)

    def outline(ax, ay, bx, by, color, width=1, dash=0):
        for i, edge in enumerate([(ax, ay, bx, ay + width), (ax, by - width, bx, by),
                                  (ax, ay, ax + width, by), (bx - width, ay, bx, by)]):
            if not dash:
                image.fill_rect(*edge, color)
                continue
            horizontal = i < 2
            start, stop = (edge[0], edge[2]) if horizontal else (edge[1], edge[3])
            for s in range(start, stop, 2 * dash):
                if horizontal:
                    image.fill_rect(s, edge[1], min(s + dash, stop), edge[3], color)
                else:
                    image.fill_rect(edge[0], s, edge[2], min(s + dash, stop), color)

    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            rect(x, y, _RGB(TILE_COLORS[tile_class(view, x, y)]))
            outline((x - x0) * t, (y - y0) * t, (x - x0 + 1) * t, (y - y0 + 1) * t, (246, 247, 244, 90))
    for tile in view.scene_tiles:
        if x0 <= tile.x <= x1 and y0 <= tile.y <= y1:
            rect(tile.x, tile.y, _RGB(SCENE_COLOR, 65))
    for region in regions:
        for x, y in region:
            if x0 <= x <= x1 and y0 <= y <= y1:
                outline((x - x0) * t, (y - y0) * t, (x - x0 + 1) * t, (y - y0 + 1) * t, _RGB(REGION_COLOR))
    for obj in visible_objects(view):
        for zone in _zones(obj, (x0, y0, x1, y1)):
            outline((zone['x0'] - x0) * t, (zone['y0'] - y0) * t, (zone['x1'] - x0 + 1) * t,
                    (zone['y1'] - y0 + 1) * t, _RGB(ZONE_EDGE), 2, 3)
        if x0 <= obj['x'] <= x1 and y0 <= obj['y'] <= y1:
            rect(obj['x'], obj['y'], _RGB(NPC_COLOR), t // 4)
    half = max(1, t // 8)
    for line in lines:
        color, dash = LINE_STYLES[line.style]
        on = int(dash.split()[0]) if dash else 0
        for (ax, ay), (bx, by) in zip(line.tiles, line.tiles[1:]):
            (pa, qa), (pb, qb) = center(ax, ay), center(bx, by)
            length = abs(pb - pa) + abs(qb - qa)
            step_x, step_y = (pb > pa) - (pb < pa), (qb > qa) - (qb < qa)
            for s in range(0, length + 1):
                if on and (s // on) % 2:
                    continue
                px, py = pa + step_x * s, qa + step_y * s
                image.fill_rect(px - half, py - half, px + half + 1, py + half + 1, _RGB(color))
        if line.tiles:
            rect(line.tiles[0][0], line.tiles[0][1], _RGB(color), t // 3)
    for marker in markers:
        x, y = marker.tile
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            continue
        glyph, fill, _ = MARKERS.get(marker.kind, ('', '', ''))
        if marker.kind == 'suspect':
            outline((x - x0) * t, (y - y0) * t, (x - x0 + 1) * t, (y - y0 + 1) * t, _RGB(fill), 2)
        elif marker.kind == 'candidate':
            outline((x - x0) * t + 2, (y - y0) * t + 2, (x - x0 + 1) * t - 2, (y - y0 + 1) * t - 2, (29, 35, 33, 160))
        elif glyph:
            rect(x, y, (29, 35, 33, 255), t // 5)
            rect(x, y, _RGB(fill), t // 5 + 1)
    return image

"""Draw actual native Forest recovery plans on the unchanged collision map.

    PYTHONPATH=src python3 -m pokesim.maps.frlg_native_recovery_review \
        --out data/navigation/native-recovery --png

SVG and Markdown use the standard library; PNG additionally needs CairoSVG.
"""
import argparse
from html import escape
from pathlib import Path

from pokesim.grid.geometry import Tile
from pokesim.grid.maps.render import cell_color
from .conformance import make_world
from .frlg_native_recovery_replay import BUNDLE, check_bundle, read_bundle


def panel_svg(view, case, result, recovery=False):
    """Use exported native legs, with separate physical shortfall annotations."""
    size, left, top = 33, 40, 100
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="560" height="440" viewBox="0 0 560 440">',
             '<rect width="560" height="440" fill="white"/>',
             '<style>text{font-family:Arial,sans-serif;fill:#202b36}</style>']
    for color, value in (('blue', '#1767b0'), ('green', '#168047'), ('red', '#bd3030')):
        parts.append(f'<defs><marker id="{color}" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6" fill="{value}"/></marker></defs>')

    def center(tile, offset=0):
        return left + (tile[0] - 1 + .5) * size, top + (tile[1] - 26 + .5) * size + offset

    def text(x, y, value, font=12):
        parts.append(f'<text x="{x}" y="{y}" font-size="{font}">{escape(str(value))}</text>')

    def arrow(start, end, color, offset=0):
        x, y = center(start, offset)
        ex, ey = center(end, offset)
        stroke = dict(blue='#1767b0', green='#168047', red='#bd3030')[color]
        parts.append(f'<path d="M{x},{y} L{ex},{ey}" fill="none" stroke="{stroke}" stroke-width="3" marker-end="url(#{color})"/>')

    def ring(tile, color, dashed=False):
        x, y = center(tile)
        parts.append(f'<circle cx="{x}" cy="{y}" r="12" fill="none" stroke="{color}" stroke-width="2"'
                     + (' stroke-dasharray="3 2"' if dashed else '') + '/>')

    text(20, 27, '2. Native localization and rejoin' if recovery else '1. Original route and two-tile shortfall', 18)
    text(20, 50, 'ViridianForest collision map; runtime-local coordinates')
    text(20, 71, 'Injected OverworldSim run; not camera footage')
    for y in range(26, 35):
        for x in range(1, 16):
            px, py = left + (x - 1) * size, top + (y - 26) * size
            color = cell_color(view.map_file.grid.at(Tile(x, y)))[:3]
            parts.append(f'<rect x="{px}" y="{py}" width="{size}" height="{size}" fill="rgb{color}" stroke="#999" stroke-width=".5"/>')
    for x in range(1, 16):
        text(center((x, 26))[0] - 5, top - 8, x, 10)
    for y in range(26, 35):
        text(18, center((1, y))[1] + 4, y, 10)
    for obj in view.data.get('objects', []):
        if 1 <= obj['x'] <= 15 and 26 <= obj['y'] <= 34:
            x, y = center((obj['x'], obj['y']))
            parts.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#c7770b"/>')
            text(x - 4, y + 4, 'N', 10)
    sx, sy = center((9, 29))
    parts.append(f'<rect x="{sx-7}" y="{sy-7}" width="14" height="14" fill="#e3ba24" stroke="#333"/>')
    text(sx + 13, sy + 5, 'sign', 10)
    for tile in result['possible_tiles']:
        ring(tile, '#8b40a8', True)
    if recovery:
        current = case['calls'][0]['after']['tile']
        for index, leg in enumerate(result['plans'][1]['legs']):
            end = leg['end']['tile']
            arrow(current, end, 'blue' if index == 0 else 'green', -4 if index == 0 else 4)
            current = end
        ring((3, 28), '#1767b0')
        text(42, 421, 'West wall (3,28), east 4, then south wall (7,33).')
    else:
        current = case['input']['start']['tile']
        for leg in case['route']:
            arrow(current, leg['end']['tile'], 'blue')
            current = leg['end']['tile']
        actual = case['calls'][0]['after']['tile']
        ring(actual, '#bd3030')
        arrow(actual, (9, 29), 'red')
        text(42, 421, 'Actual stop (9,28); TRUST continues into the sign.')
    ring((7, 33), '#168047')
    text(20, 438, 'Purple: possible tiles. Yellow: sign. Orange N: map object.', 11)
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def write_review(directory, png=False):
    bundle = read_bundle()
    results = check_bundle(bundle)
    world = make_world(bundle, dict(game='frlg', maps=['ViridianForest'], **bundle['context']))
    case = next(c for c in bundle['cases'] if c['id'] == 'forest-two-short')
    result = next(r for r in results if r['id'] == case['id'])
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for recovery, name in ((False, 'intended'), (True, 'recovery')):
        svg = panel_svg(world.views['ViridianForest'], case, result, recovery)
        target = directory / ('frlg-forest-' + name)
        target.with_suffix('.svg').write_text(svg)
        if png:
            import cairosvg
            cairosvg.svg2png(bytestring=svg.encode(), write_to=str(target.with_suffix('.png')), scale=2)
    ext = 'png' if png else 'svg'
    lines = ['# FRLG Forest: native recovery review', '',
             '[Readable replay data](frlg-forest.trace) · [Full diagnostic JSON](diagnostics/frlg-forest.raw.json)', '',
             '**Preconditions:** ViridianForest `(13,28)` west, ground elevation 3, no flags/variables. '
             'Walk west 6 to `(7,28)`, then south 5 to the wall at `(7,33)`. '
             'One or two steps silently fail; these are injected shortfalls, not detected battles.', '',
             '| Original route / TRUST negative control | REANCHOR: actual native repair |', '|---|---|',
             f'| ![Original and shortfall](frlg-forest-intended.{ext}) | ![Recovery and rejoin](frlg-forest-recovery.{ext}) |', '',
             '[Intended SVG](frlg-forest-intended.svg) · [Recovery SVG](frlg-forest-recovery.svg)', '',
             'The blue route in the first panel is the original plan. The red attempted south move '
             'shows the two-tile TRUST control; it stops at the sign. The second panel draws the '
             'native-inserted repair from the same physical shortfall, then the rejoin.', '',
             '| Case | Added repair | Physical final tile | Result |', '|---|---|---|---|']
    for row in results:
        lines.append('| {} | {} | `{}` | {} |'.format(row['id'], 'yes' if row['inserted'] else 'no',
            tuple(row['physical']['tile']), row['status']))
    lines += ['', 'The `next-wall` cases are synthetic extensions on the same real board: change the second '
              'leg to west 4 toward `(3,28)`. That hold already converges from all three possible tiles, '
              'so native inserts no repair. The TRUST cases intentionally disable recovery: one silently '
              'claims completion at `(7,33)` while physically at `(8,33)`; two reads the sign twice and fails.', '',
              '**Evidence:** the original Forest geometry and silent-shortfall/sign failure are reproduced '
              'from native `test_short_leg_then_sign` / `test_short_leg_unseen` '
              '(r16 Console B, 2026-11-01) in `PokemonFRLG_OverworldSim_Tests.cpp`. '
              'The new exporter invokes production `run_route()` with `OverworldSimWalker`; '
              'its `calls` capture actual planner-selected legs and physical simulated poses. '
              'Python checks these legs on identical pinned map bytes. No terrain or native recovery logic changed.', '',
              '**Limits:** `(7..9,28)` is reconstructed from the logged two-tile policy; native internal '
              'candidate storage is not exported. Wall checks are explicitly SKIP in this geometry test. '
              'Camera detectors, queue draining, stillness/timing, unknown encounter origins and larger shortfalls '
              'are unverified. Native recovery is a bounded heuristic (including next-wall and repair-cost checks), '
              'not a universal recovery guarantee. Python now rejects a vertical sign interaction as a wall anchor.', '',
              'Each `calls` line separates the planned endpoint from physical before/after poses and the '
              'facing supplied to the walker. `native` preserves plan, recovery and completion claims. '
              'The raw diagnostic checksum and every replay fact are checked when loading the readable data. '
              'The diagrams complement these facts; they do not carry timing or provenance.', '',
              'Native source revision: `' + bundle['native_revision'] + '`. '
              'This exporter remains locally committed pending native publication approval; native CI has not run.', '',
              '```sh', 'PYTHONPATH=src python3 -m pokesim.maps.frlg_native_recovery_replay check',
              'PYTHONPATH=src python3 -m pokesim.maps.frlg_native_recovery_review --out data/navigation/native-recovery --png', '```', '']
    (directory / 'FRLG_FOREST.md').write_text('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--png', action='store_true')
    args = parser.parse_args()
    write_review(args.out, args.png)


if __name__ == '__main__':
    main()

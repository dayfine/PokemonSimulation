"""Generate a visual review of verified native BDSP recovery captures.

    PYTHONPATH=src python3 -m pokesim.maps.bdsp_native_recovery_review \
        --out data/navigation/native-recovery --png

SVG/Markdown generation uses the standard library. --png additionally requires
CairoSVG; raster previews and vector diagrams come from the same SVG scene.
"""
import argparse
from html import escape
import os
from pathlib import Path

from pokesim.grid.geometry import Tile
from pokesim.grid.maps.render import cell_color
from .bdsp_native_recovery_replay import BUNDLE, check_bundle, read_bundle
from .conformance import make_world
from .runtime_map_pack import ROOT
from .runtime_symbols import CLOSED_SIDES


def point(xy):
    return '(' + ','.join(str(v) for v in xy) + ')'


def panel_svg(view, case, result, recovery=False):
    """Draw the native-selected legs over an unchanged, labeled map crop."""
    left, top, size = 52, 100, 56
    def center(xy, dy=0):
        return left + (xy[0] - 24 + .5) * size, top + (xy[1] - 3 + .5) * size + dy
    tap_call = next(c for c in case['calls'] if c['kind'] == 'taps')
    distance = sum(abs(a - b) for a, b in zip(tap_call['before']['tile'], tap_call['after']['tile']))
    hold, back = result['plans'][1]['legs']
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="620" height="415" viewBox="0 0 620 415">',
             '<rect width="620" height="415" fill="white"/>',
             '<style>text{font-family:Arial,sans-serif;fill:#202b36} .small{font-size:12px}</style>',
             '<defs><marker id="blue" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#1767b0"/></marker>',
             '<marker id="green" markerWidth="7" markerHeight="7" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#168047"/></marker></defs>']
    def text(x, y, value, size=13, **attrs):
        extra = ' '.join(f'{k.replace("_", "-")}="{escape(str(v))}"' for k, v in attrs.items())
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{escape(str(value))}</text>')
    def circle(xy, color, radius=13, dash=False):
        x, y = center(xy)
        parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="none" stroke="{color}" stroke-width="2.5"'
                     + (' stroke-dasharray="4 3"' if dash else '') + '/>')
    def arrow(start, end, color='blue', dy=0):
        x0, y0 = center(start, dy)
        x1, y1 = center(end, dy)
        stroke = '#1767b0' if color == 'blue' else '#168047'
        parts.append(f'<path d="M{x0},{y0} L{x1},{y1}" fill="none" stroke="{stroke}" stroke-width="3" marker-end="url(#{color})"/>')
    text(25, 28, '2. Native recovery and rejoin' if recovery else '1. Intended leg, interrupted', 20)
    text(25, 50, 'Route202 collision-map crop; local tile coordinates', 13)
    text(25, 70, f'Same possible origins; hold {hold["direction"]}, then return {back["direction"]}' if recovery else f'After the two-tap call: credit says {tap_call["report"]["credited_chunks"]}; actual movement is {distance}', 13)
    for y in range(3, 7):
        for x in range(24, 33):
            px, py = left + (x - 24) * size, top + (y - 3) * size
            color = cell_color(view.map_file.grid.at(Tile(x, y)))[:3]
            parts.append(f'<rect x="{px}" y="{py}" width="{size}" height="{size}" fill="rgb{color}" stroke="#9da3a5" stroke-width=".7"/>')
            side = CLOSED_SIDES.get(view.glyph(Tile(x, y)))
            if side is not None:
                dx, dy = side.dx, side.dy
                x0, y0 = px + (size if dx > 0 else 0), py + (size if dy > 0 else 0)
                x1, y1 = (x0, y0 + size) if dx else (x0 + size, y0)
                parts.append(f'<path d="M{x0},{y0}L{x1},{y1}" stroke="#111" stroke-width="3"/>')
    for x in range(24, 33):
        text(center((x, 3))[0], top - 9, x, 12, text_anchor='middle')
    for y in range(3, 7):
        text(left - 12, center((24, y))[1] + 4, y, 12, text_anchor='end')
    for obj in view.data.get('objects', []):
        if 24 <= obj['x'] <= 32 and 3 <= obj['y'] <= 6:
            x, y = center((obj['x'], obj['y']))
            parts.append(f'<circle cx="{x}" cy="{y}" r="11" fill="#c7770b"/>')
            text(x, y + 4, 'N', 12, text_anchor='middle', style='fill:white')
    for xy in result['candidate_tiles']:
        circle(xy, '#8b40a8', 21, dash=True)
    start, goal = case['input']['start']['tile'], case['input']['goal']['tile']
    if recovery:
        current = list(result['plans'][1]['from'][0])
        for leg in result['plans'][1]['legs']:
            end = leg['after'][0]
            arrow(current, end, 'blue' if leg['kind'] == 'to wall' else 'green', -7 if leg['kind'] == 'to wall' else 7)
            current = end
        anchor = result['plans'][1]['legs'][0]['after'][0]
        circle(anchor, '#1767b0')
        x, y = center(anchor)
        text(x + 15, y + 49, 'wall stop ' + point(anchor), 12, text_anchor='end')
        text(25, 349, f'Blue: {hold["direction"]} hold (max {hold["tiles"]} tiles). Green: {back["direction"]} {back["tiles"]} back to goal.', 13)
    else:
        current = start
        for leg in result['plans'][0]['legs']:
            arrow(current, leg['after'][0])
            current = leg['after'][0]
        sx, sy = center(start)
        parts.append(f'<circle cx="{sx}" cy="{sy}" r="5" fill="#1767b0"/>')
        actual = next(c['after']['tile'] for c in case['calls'] if c['kind'] == 'taps')
        x, y = center(actual)
        parts.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#bf3030"/>')
        text(x, y + 49, 'actual ' + point(actual), 12, text_anchor='middle')
        text(25, 349, f'Blue: east 2 from {point(start)}. Red: actual stop at {point(actual)}.', 13)
    circle(goal, '#168047', 13)
    gx, gy = center(goal)
    text(gx, gy - 33, 'goal ' + point(goal), 12, text_anchor='middle')
    text(25, 372, 'Purple rings: possible tiles (26..28, 5). N: nearby NPC.', 13)
    text(25, 397, 'Injected GridSim case; native-selected plan, not camera footage.', 12)
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def review_markdown(bundle, results, trace_link, raster=False):
    extension = 'png' if raster else 'svg'
    lines = ['# BDSP Route 202 recovery: review summary', '',
             'Generated from the verified [' + Path(trace_link).name + '](' + trace_link + '). Read this page for the behavior; the JSON retains the full machine-checkable evidence.', '',
             '**Preconditions:** Route202, start `(26,5)` east, goal `(28,5)` west; scene state 1, Running Shoes available, RUN policy. All encounters below are injected and already cleared.', '',
             '| Intended leg and interruption | Native recovery and rejoin |', '|---|---|',
             f'| ![Interrupted original route](bdsp-route202-intended.{extension}) | ![Native recovery route](bdsp-route202-recovery.{extension}) |', '',
             '[Intended-route SVG](bdsp-route202-intended.svg) · [Recovery SVG](bdsp-route202-recovery.svg)', '',
             'Map backgrounds: dark walls, tan floor, green grass. Orange N marks the nearby NPC. Both panels use the same coordinates.', '',
             '**Key example:** two east taps receive two credited chunks, but an encounter before the last step leaves the simulated player at `(27,5)`, only one tile from the start. Native keeps `(26,5)`, `(27,5)` and `(28,5)` possible, holds east to `(30,5)`, then returns west to the original goal `(28,5)`.', '',
             '## Seven cases', '',
             '“After tap call” and facing are simulator truth. The native API returns positions without facing evidence. All tap calls below credit two chunks. Known-origin cases retain all three possible tiles; unknown-origin cases stop without localizing from this leg.', '',
             '| Case | After tap call (sim) | Wall attempts | Outcome |', '|---|---|---:|---|']
    by_id = {r['id']: r for r in results}
    for case in bundle['cases']:
        result = by_id[case['id']]
        physical = next(c['after']['tile'] for c in case['calls'] if c['kind'] == 'taps')
        failure = result['native_failure']
        outcome = 'Stop: unknown encounter origin' if failure.startswith('encounter_origin_unknown') else 'Stop: recovery budget exhausted' if failure else 'Arrived; sim `(28,5)` west'
        lines.append('| ' + case['id'].replace('-', ' ') + ' | `' + point(physical) + '` | ' + str(result['wall_attempts']) + ' | ' + outcome + ' |')
    lines += ['', '**Retry policy:** BDSP allows an initial wall attempt plus three retries: four total. The fourth can succeed after three interruptions; four interruptions fail. Python `Session` separately defaults to three recovery calls total; these budgets are not equivalent.', '',
              '## What is in the JSON?', '',
              '| Fields | Evidence retained |', '|---|---|',
              '| `input` | Start/goal, movement policy and injected encounter phase/origin. |',
              '| `calls` | Requested turns/taps/holds; stop reason, elapsed time, battles and credited chunks; physical before/after poses. |',
              '| `notes` | Actual native plans, replan candidates, completion basis and arrival/failure logs. |',
              '| `declared`, `physical` | Positions returned by the native API versus simulated truth. Returned facing stays null because the API does not report it. |',
              '| `failure` | Exact failure reason, or an empty string on success. |',
              '| Source/map metadata | Full revisions, map-byte hash and native exporter checksum. |', '',
              'The pictures show the spatial sequence; the table covers the cases and outcomes. They do **not** replace raw reports, timings or provenance. Native facing belief, queue draining, advancing video confirmation, detector timing and a global retry budget remain unverified.', '',
              '## Regenerate', '', '```sh',
              'PYTHONPATH=src python3 -m pokesim.maps.bdsp_native_recovery_review \\',
              '  --out data/navigation/native-recovery --png', '```', '',
              'SVG/Markdown need only the standard library; PNG rendering additionally uses CairoSVG.', '',
              'Native revision: `' + bundle['native_revision'] + '`. Map revision: `' + bundle['map_revision'] + '`.', '']
    return '\n'.join(lines)


def write_review(trace, directory, root=ROOT, png=False):
    bundle = read_bundle(trace)
    results = check_bundle(bundle, root)
    view = make_world(bundle, dict(game='bdsp', maps=['Route202'], **bundle['context']), root).views['Route202']
    example = next(c for c in bundle['cases'] if c['id'] == 'last-tap-before')
    result = next(r for r in results if r['id'] == example['id'])
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for recovery, name in ((False, 'intended'), (True, 'recovery')):
        svg = panel_svg(view, example, result, recovery)
        target = directory / ('bdsp-route202-' + name)
        target.with_suffix('.svg').write_text(svg)
        if png:
            import cairosvg
            cairosvg.svg2png(bytestring=svg.encode(), write_to=str(target.with_suffix('.png')), scale=2)
    relative = Path(os.path.relpath(Path(trace).resolve(), directory.resolve())).as_posix()
    (directory / 'README.md').write_text(review_markdown(bundle, results, relative, png))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trace', type=Path, default=BUNDLE)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--png', action='store_true')
    args = parser.parse_args()
    try:
        write_review(args.trace, args.out, png=args.png)
    except (ValueError, OSError, ImportError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

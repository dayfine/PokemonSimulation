r"""Draw the walks of AutoStory runs from a SerialPrograms log, on pinned runtime maps.

    PYTHONPATH=src python3 -m pokesim.cli.run_routes SerialPrograms.log -o /tmp/runs \
        --game bdsp --start 01.11=FloaromaTown:11,28

Writes, per checkpoint attempt, one picture per map (SVG and PNG) with that
attempt's walks in order: planned legs solid, walked legs dashed and
numbered, battles, re-anchors, stops and the failure marked. Then an
index.html over them all and trace.json, the parsed trace.

Walks that log no tiles (BDSP story steps such as "8 taps west") start where
the last walk ended; at a checkpoint's start that is unknown unless --start
gives it. A walk stopped by "blocked" is drawn to the first blocked tile on
the pinned map, and listed as assumed.
"""

import argparse
from html import escape
from pathlib import Path
import re
import sys

from pokesim.formats.contract_format import json_text
from pokesim.maps.consumer_source import GitSource, lock_entry, published_pack
from pokesim.maps.local_routing import Context, load_pinned_map
from pokesim.maps.route_picture import Line, Marker, crop_box, picture_png, picture_svg
from pokesim.maps.run_trace import map_key, parse, to_json
from pokesim.maps.runtime_map_pack import ROOT

#  Log names that are not their file's name.
ALIASES = {'bdsp': {'route204': 'Route204North'}}
MARKED = ('battle', 'trainer', 'reanchor', 'stop', 'wait', 'blocker', 'obstacle', 'message', 'talk', 'failed')


class PinnedMaps:
    """Runtime maps of one game at a pinned revision, looked up by the names logs use."""

    def __init__(self, source, revision, game):
        self.source, self.revision, self.game = source, revision, game
        files = published_pack(GitSource(source), game, lock_entry(GitSource(source), revision))
        self.names = {map_key(name[:-len('.json')]): name[:-len('.json')] for name in files if name.endswith('.json')}
        self.views = {}

    def __call__(self, name):
        key = map_key(name)
        file = ALIASES.get(self.game, {}).get(key) or self.names.get(key)
        if file is None:
            return None
        if file not in self.views:
            try:
                self.views[file] = load_pinned_map(self.source, self.revision, self.game, file,
                                                   Context(acknowledge_map_state=True))
            except ValueError:
                self.views[file] = None
        return self.views[file]


def attempts(runs):
    """[(run, checkpoint, attempt, walks)], in log order."""
    result = []
    for run in runs:
        for walk in run.walks:
            key = (walk.checkpoint, walk.attempt)
            if not result or result[-1][0] is not run or result[-1][1:3] != key:
                result.append((run, walk.checkpoint, walk.attempt, []))
            result[-1][3].append(walk)
    return result


def describe(walk):
    if walk.kind == 'talk':
        return 'talk: ' + walk.note
    parts = []
    for step in walk.steps:
        text = step.leg.describe()
        if step.role not in ('plan', 'blind'):
            text += f' [{step.role}]'
        if step.basis != 'walked' or step.why:
            text += f' ({step.why or step.basis})'
        parts.append(text)
    return '; '.join(parts) or 'no steps'


def outcome_of(walks):
    failed = [walk for walk in walks if walk.outcome == 'failed']
    if failed:
        return 'failed at ' + failed[-1].label + ': ' + failed[-1].error
    return 'passed' if all(walk.outcome == 'done' for walk in walks) else 'open'


def layers(walks, lookup):
    """{map file name: dict(view, lines, markers, rows)} for one attempt; walks numbered from 1."""
    pictures = {}

    def picture(place):
        view = lookup(place[0])
        if view is None:
            return None
        return pictures.setdefault(view.map_file.name, dict(view=view, lines=[], markers=[], rows=[]))

    def on(target, place):
        return target is not None and picture(place) is target

    unplaced = []
    for number, walk in enumerate(walks, 1):
        drawn = set()
        for plan in walk.plans:
            points = list(plan.start[:1]) + [leg.ends[0] for leg in plan.legs if leg.ends]
            if not points:
                continue
            target = picture(points[0])
            tiles = []
            for place in points:
                if on(target, place) and (not tiles or tiles[-1] != place[1:]):
                    tiles.append(place[1:])
            if target is not None and tiles:
                target['lines'].append(Line('plan' if plan.reason == 'plan' else 'alt', tiles))
                drawn.add(id(target))
        label = str(number)
        for step in walk.steps:
            for place in step.start[1:]:
                target = picture(place)
                if target is not None:
                    target['markers'].append(Marker('candidate', place[1:]))
            if not (step.start and step.end) or not on(picture(step.start[0]), step.end[0]):
                continue
            target = picture(step.start[0])
            start, end = step.start[0][1:], step.end[0][1:]
            last = target['lines'][-1] if target['lines'] else None
            if last is not None and last.style == 'walked' and last.tiles[-1] == start and last.label == label:
                if end != start:
                    last.tiles.append(end)
            else:
                target['lines'].append(Line('walked', [start] if end == start else [start, end], label))
            drawn.add(id(target))
        for mark in walk.marks:
            if mark.kind in MARKED and mark.at:
                target = picture(mark.at[0])
                if target is not None:
                    target['markers'].append(Marker(mark.kind, mark.at[0][1:], mark.text))
                    drawn.add(id(target))
        row = f'{number}. {walk.label} ({walk.kind}, {walk.outcome}): {describe(walk)}'
        targets = [target for target in pictures.values() if id(target) in drawn]
        for target in targets:
            target['rows'].append(row)
        if not targets:
            unplaced.append(row + ' - not drawn: no known tile')
    return pictures, unplaced


def slug(text):
    return re.sub(r'[^0-9A-Za-z.]+', '-', text).strip('-') or 'run'


def write_pictures(runs, lookup, out_dir, marks=(), tile_px=16):
    """Write the pictures and index.html; return the written picture paths."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'trace.json').write_text(json_text(to_json(runs)))
    written, sections = [], []
    for run, checkpoint, attempt, walks in attempts(runs):
        name = f'{run.run_id}/{slug(checkpoint or "before-checkpoints")}-attempt{attempt}'
        pictures, unplaced = layers(walks, lookup)
        outcome = outcome_of(walks)
        figures = []
        for map_name, picture in pictures.items():
            view = picture['view']
            markers = picture['markers'] + [Marker('suspect', tile, text) for tile_map, tile, text in marks
                                            if map_key(tile_map) == map_key(map_name)]
            box = crop_box(view, picture['lines'], markers)
            title = f'{checkpoint or "-"} attempt {attempt}: {map_name}'
            subtitle = f'{run.program} at {walks[0].time}; {outcome}'
            notes = picture['rows'] + [f'Tiles from the log; {view.provenance.get("revision", "working tree")[:10]} map.']
            path = out_dir / f'{name}-{map_name}.svg'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(picture_svg(view, picture['lines'], markers, title, subtitle, notes, box, tile_px=tile_px))
            picture_png(view, picture['lines'], markers, box, tile_px=tile_px).write(str(path.with_suffix('.png')))
            written.append(path)
            figures.append(f'<figure><img src="{escape(str(path.relative_to(out_dir)))}" alt="{escape(title)}">'
                           f'<figcaption><a href="{escape(str(path.with_suffix(".png").relative_to(out_dir)))}">PNG</a>'
                           '</figcaption></figure>')
        rows = ''.join(f'<li>{escape(row)}</li>' for row in
                       [f'{n}. {w.label} ({w.kind}, {w.outcome}): {describe(w)}' for n, w in enumerate(walks, 1)])
        missing = ''.join(f'<li>{escape(row)}</li>' for row in unplaced)
        cls = 'failed' if outcome.startswith('failed') else 'passed' if outcome == 'passed' else 'open'
        sections.append(f'<section><h2>{escape(checkpoint or "before the first checkpoint")} attempt {attempt}'
                        f' <span class="{cls}">{escape(outcome)}</span></h2>'
                        f'<p class="meta">{escape(run.program)}, run {escape(run.run_id)}, from {escape(walks[0].time)}</p>'
                        f'<div class="figs">{"".join(figures)}</div><ol class="walks">{rows}</ol>'
                        + (f'<p class="meta">Not drawn:</p><ul>{missing}</ul>' if missing else '') + '</section>')
    (out_dir / 'index.html').write_text(INDEX.replace('{{SECTIONS}}', '\n'.join(sections)))
    return written


INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AutoStory Run Routes</title>
<style>
:root{--bg:#f6f7f4;--fg:#1d2321;--muted:#5b6662;--line:#d6dbd6;--fail:#d62839;--pass:#199545;--open:#b0743c}
body{background:var(--bg);color:var(--fg);font-family:system-ui,-apple-system,sans-serif;line-height:1.5;margin:0}
main{max-width:1100px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:1.5rem;margin:0 0 4px}h2{font-size:1.1rem;margin:0}
section{border-top:1px solid var(--line);padding-top:16px;margin-top:20px}
.meta{color:var(--muted);font-size:.85rem;margin:2px 0 8px}
.failed{color:var(--fail)}.passed{color:var(--pass)}.open{color:var(--open)}
h2 span{font-family:ui-monospace,Menlo,monospace;font-size:.85rem;font-weight:500;margin-left:8px}
.figs{display:flex;flex-wrap:wrap;gap:16px}figure{margin:0;max-width:100%;overflow-x:auto}
img{display:block;max-width:none}figcaption{font-size:.8rem;color:var(--muted)}
.walks{font-family:ui-monospace,Menlo,monospace;font-size:.8rem;padding-left:24px}
</style></head><body><main>
<h1>AutoStory run routes</h1>
<p class="meta">Per checkpoint attempt, one picture per map. Planned legs solid orange, walked legs dashed blue and
numbered in order, re-plans dashed grey. <a href="trace.json">trace.json</a> holds the parsed trace.</p>
{{SECTIONS}}
</main></body></html>
"""


def parse_place(text, default_map=''):
    """'Map:x,y' or 'x,y' -> (map, x, y)."""
    name, _, tile = text.rpartition(':')
    x, y = tile.split(',')
    return (name or default_map, int(x), int(y))


def parse_start(text):
    """'01.11=FloaromaTown:11,28' (or ':11,27/11,28') -> ('01.11', [(map, x, y)])."""
    checkpoint, _, places = text.partition('=')
    name, _, tiles = places.rpartition(':')
    if not checkpoint or not name or not tiles:
        raise ValueError('--start wants CHECKPOINT=MAP:x,y[/x,y...]: ' + text)
    return checkpoint, [parse_place(tile, name) for tile in tiles.split('/')]


def parse_mark(text):
    """'Map:x,y[=label]' -> (map, (x, y), label)."""
    place, _, label = text.partition('=')
    name, x, y = parse_place(place)
    if not name:
        raise ValueError('--mark wants MAP:x,y[=label]: ' + text)
    return name, (x, y), label


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('log', type=Path, help='a SerialPrograms log')
    parser.add_argument('-o', '--out', type=Path, required=True, help='directory for the pictures and index.html')
    parser.add_argument('--game', choices=('bdsp', 'frlg'), help='default: from the log')
    parser.add_argument('--start', action='append', default=[], help='CHECKPOINT=MAP:x,y[/x,y...]')
    parser.add_argument('--mark', action='append', default=[], help='suspect tile, MAP:x,y[=label]')
    parser.add_argument('--source', type=Path, default=ROOT, help='full-history publishing repository/cache')
    parser.add_argument('--revision', help='full approved commit; default: cached origin/main tip')
    parser.add_argument('--tile-px', type=int, default=16)
    args = parser.parse_args(argv)
    try:
        starts = dict(parse_start(text) for text in args.start)
        marks = [parse_mark(text) for text in args.mark]
        lines = args.log.read_text(encoding='utf-8', errors='replace').splitlines()
        game = args.game or ('frlg' if any('Starting Program: PokemonFRLG' in line for line in lines) else 'bdsp')
        revision = args.revision or GitSource(args.source).git('rev-parse', 'origin/main').decode().strip()
        lookup = PinnedMaps(args.source, revision, game)
        runs = parse(lines, lookup, starts)
        written = write_pictures(runs, lookup, args.out, marks, args.tile_px)
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    sys.stdout.write(f'{len(runs)} run(s), {len(written)} picture(s): {args.out / "index.html"}\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

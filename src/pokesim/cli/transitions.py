"""Replay a semantic transition regression and optionally draw its local slices.

    PYTHONPATH=src python3 -m pokesim.cli.transitions --case forest-north-gate \
        --output /tmp/forest-trace.json --draw-dir /tmp/forest-views
    PYTHONPATH=src python3 -m pokesim.cli.transitions --case mine-pack-gap

Maps are verified at the catalog's immutable publishing revision. No fetch or
native story/controller execution occurs. An expected failure can pass its
regression assertions while still reporting failure and can_resume=false.
"""
import argparse
import json
from pathlib import Path
import sys

from pokesim.grid.geometry import Tile
from pokesim.maps.route_drawing import route_image, route_svg
from pokesim.maps.transition_replay import CATALOG, pinned_world, read_catalog, replay


def draw(case, world, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for index, panel in enumerate(case.get('drawings', [])):
        view = world.views[panel['map']]
        path = view.route(Tile(*panel['start']), Tile(*panel['goal']))
        if path is None:
            raise ValueError('scenario drawing has no local candidate')
        target = directory / (case['id'] + '-' + str(index + 1))
        target.with_suffix('.svg').write_text(route_svg(view, path,
            title=case['id'] + ': derived checkpoint slice', reference=case['evidence'],
            start_label=panel['start_label'], goal_label=panel['goal_label'], landmarks=panel['landmarks']))
        route_image(view, path).write(str(target.with_suffix('.png')))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', required=True)
    parser.add_argument('--catalog', type=Path, default=CATALOG)
    parser.add_argument('--source', type=Path, default=Path('.'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--draw-dir', type=Path)
    args = parser.parse_args(argv)
    try:
        catalog = read_catalog(args.catalog)
        case = next((c for c in catalog['cases'] if c['id'] == args.case), None)
        if case is None:
            raise ValueError('unknown scenario: ' + args.case)
        world = pinned_world(args.source, catalog['map_revision'], case)
        report = replay(case, world, catalog['map_revision'])
        result = json.dumps(report, indent=2) + '\n'
        if args.output:
            args.output.write_text(result)
        else:
            print(result, end='')
        if args.draw_dir:
            draw(case, world, args.draw_dir)
        return 0
    except (ValueError, KeyError, AssertionError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

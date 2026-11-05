r"""Plan and draw a local route on a pinned FRLG or BDSP runtime map.

Run from the repository root with a full-history publishing checkout/cache:

    PYTHONPATH=src python3 -m pokesim.cli.route \
        --game frlg --map PalletTown --start 6,8 --goal 12,2 \
        --svg /tmp/pallet-route.svg --png /tmp/pallet-route.png --json /tmp/pallet-route.json

    PYTHONPATH=src python3 -m pokesim.cli.route \
        --game bdsp --map Route202 --start save_spot --goal-region jubilife_exit \
        --var VAR_ROUTE_202_STATE=1 --svg /tmp/route202-route.svg --json /tmp/route202-route.json

The default pin is cached origin/main; --revision accepts a full approved SHA.
Routes stay inside one map. See docs/navigation/RUNTIME_ROUTES.md for limits.
"""

import argparse
import json
import math
from pathlib import Path
import sys

from pokesim.grid.geometry import Tile
from pokesim.grid.routing.shortest import Costs
from pokesim.maps.consumer_source import GitSource
from pokesim.maps.local_routing import Context, load_pinned_map
from pokesim.maps.route_drawing import ascii_route, route_image, route_svg
from pokesim.maps.runtime_map_pack import ROOT


def position(view, text):
    if ',' in text:
        x, y = text.split(',')
        return Tile(int(x), int(y))
    return view.point(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', choices=('frlg', 'bdsp'), required=True)
    parser.add_argument('--map', required=True)
    parser.add_argument('--start', required=True, help='named point or x,y')
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument('--goal', help='named point or x,y')
    target.add_argument('--goal-region', help='native region name; any stable tile is a goal')
    parser.add_argument('--source', type=Path, default=ROOT, help='full-history publishing repository/cache')
    parser.add_argument('--revision', help='full approved commit; default: cached origin/main tip')
    parser.add_argument('--flag', action='append', default=[])
    parser.add_argument('--var', action='append', default=[], help='scene variable NAME=INTEGER')
    parser.add_argument('--acknowledge-map-state', action='store_true')
    parser.add_argument('--elevation', type=int)
    parser.add_argument('--grass-cost', type=float, default=5.0)
    parser.add_argument('--png', type=Path)
    parser.add_argument('--svg', type=Path, help='annotated diagram with coordinates and legend')
    parser.add_argument('--json', type=Path, help='write route/provenance/conditions JSON')
    args = parser.parse_args(argv)
    try:
        if not math.isfinite(args.grass_cost) or args.grass_cost < 0:
            raise ValueError('grass cost must be finite and nonnegative')
        revision = args.revision or GitSource(args.source).git('rev-parse', 'origin/main').decode().strip()
        variables = {}
        for assignment in args.var:
            name, value = assignment.split('=', 1)
            if not name or name in variables:
                raise ValueError('empty or duplicate scene variable')
            variables[name] = int(value)
        context = Context(frozenset(args.flag), variables, args.acknowledge_map_state)
        view = load_pinned_map(args.source, revision, args.game, args.map, context)
        start = position(view, args.start)
        if args.goal_region:
            path = view.route_region(start, args.goal_region, Costs(grass=args.grass_cost), args.elevation)
        else:
            path = view.route(start, position(view, args.goal), Costs(grass=args.grass_cost), args.elevation)
        if path is None:
            parser.exit(2, 'No local route under the supplied conditions.\n')
        if args.png:
            route_image(view, path, goal_tiles=view.region(args.goal_region) if args.goal_region else ()).write(str(args.png))
        if args.svg:
            args.svg.write_text(route_svg(view, path, start_label=args.start,
                goal_label=args.goal_region or args.goal,
                goal_tiles=view.region(args.goal_region) if args.goal_region else ()))
        if args.json:
            report = dict(format='pokesim-local-route/1', source=view.provenance,
                goal=dict(region=args.goal_region) if args.goal_region else dict(tile=list(position(view, args.goal))),
                preconditions=view.preconditions,
                context=dict(flags=sorted(context.flags), variables=variables,
                             acknowledge_map_state=context.acknowledge_map_state),
                start=dict(tile=list(path.start.place.tile), elevation=path.start.elevation),
                cost=path.cost, costs=Costs(grass=args.grass_cost)._asdict(),
                moves=[dict(direction=move.direction.name.lower(), kind=move.kind.value,
                            tile=list(move.to.place.tile), elevation=move.to.elevation) for move in path.moves],
                limitations=['single-map static route; transitions excluded',
                    'NPC wander boxes conservatively occupied; trainer sight and omitted NPCs not simulated',
                    'scene effects, encounters and recovery not simulated'])
            args.json.write_text(json.dumps(report, indent=2) + '\n')
        sys.stdout.write(ascii_route(view, path))
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, str(error) + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main())

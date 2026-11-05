r"""Golden routes and PNG pixels for checked-in FRLG/BDSP maps; no Git/network.

Run the checks or explicitly regenerate after reviewing a deliberate change:

    PYTHONPATH=src python3 -m pokesim.maps.test_route_goldens
    PYTHONPATH=src python3 -m pokesim.maps.test_route_goldens --update

Normal discovery never rewrites goldens. Failures save actual output under
build/route-goldens for review; PNG comparisons use decoded pixels, not zlib bytes.
"""

import json
from pathlib import Path
import re
import sys
import unittest

from pokesim.grid.geometry import Tile
from pokesim.png import Image
from .consumer_source import sha256
from .local_routing import Context, LocalMap
from .route_drawing import route_image, route_svg
from .runtime_map_pack import ROOT


GOLDENS = Path(__file__).parent / 'goldens'
ACTUAL = ROOT / 'build/route-goldens'


def cases():
    return json.loads((GOLDENS / 'cases.json').read_text())


def render_case(case):
    path = ROOT / 'data/games' / case['game'] / 'maps/runtime' / (case['map'] + '.json')
    raw = path.read_bytes()
    manifest = json.loads((ROOT / 'data/maps/runtime-manifest.json').read_text())
    entry = next(entry for entry in manifest['games'][case['game']]['maps'] if entry['name'] == case['map'])
    context = Context(frozenset(case.get('flags', [])), case.get('variables', {}),
                      case.get('acknowledge_map_state', False))
    view = LocalMap(json.loads(raw), case['game'], context, entry['preconditions'])
    if 'goal_region' in case:
        route = view.route_region(Tile(*case['start']), case['goal_region'], elevation=case.get('elevation'))
    else:
        route = view.route(Tile(*case['start']), Tile(*case['goal']), elevation=case.get('elevation'))
    if route is None:
        raise AssertionError('golden route is unreachable: ' + case['id'])
    if case.get('goal_facing') and route.moves[-1].direction.name.lower() != case['goal_facing']:
        raise AssertionError('route does not finish facing the native interaction target')
    snapshot = dict(format='pokesim-route-golden/1', game=case['game'], map=case['map'],
        map_sha256=sha256(raw), coordinate_frame=entry['coordinate_frame'],
        preconditions=entry['preconditions'],
        native_reference=case['source'],
        goal=dict(region=case['goal_region']) if 'goal_region' in case else dict(tile=case['goal'], facing=case.get('goal_facing')),
        context=dict(flags=sorted(context.flags), variables=dict(context.variables),
                     acknowledge_map_state=context.acknowledge_map_state),
        start=dict(tile=list(route.start.place.tile), elevation=route.start.elevation),
        cost=route.cost,
        moves=[dict(direction=move.direction.name.lower(), kind=move.kind.value,
                    to=[*move.to.place.tile, move.to.elevation]) for move in route.moves])
    target_tiles = view.region(case['goal_region']) if 'goal_region' in case else ()
    svg = route_svg(view, route, title=case['source']['checkpoint'] + ' / ' + case['source']['step'],
        start_label=case['start_label'], goal_label=case['goal_label'], reference=case['source'],
        landmarks=case.get('landmarks', ()), goal_facing=case.get('goal_facing'), goal_tiles=target_tiles)
    return snapshot, route_image(view, route, goal_tiles=target_tiles), svg


def write_snapshot(path, snapshot):
    # Keep coordinate triples compact for review; comparison parses the JSON.
    text = json.dumps(snapshot, indent=2) + '\n'
    text = re.sub(r'\[\s*(-?\d+),\s*(-?\d+),\s*(\d+)\s*\]', r'[\1, \2, \3]', text)
    path.write_text(text)


def update_goldens():
    for case in cases():
        snapshot, image, svg = render_case(case)
        write_snapshot(GOLDENS / (case['id'] + '.json'), snapshot)
        image.write(str(GOLDENS / (case['id'] + '.png')))
        (GOLDENS / (case['id'] + '.svg')).write_text(svg)
        print(f'{case["id"]}: {len(snapshot["moves"])} presses, cost {snapshot["cost"]}')


class RouteGoldenTest(unittest.TestCase):
    def test_checked_in_maps_route_and_draw_as_reviewed(self):
        for case in cases():
            with self.subTest(case=case['id']):
                snapshot, image, svg = render_case(case)
                expected = json.loads((GOLDENS / (case['id'] + '.json')).read_text())
                expected_image = Image.read(str(GOLDENS / (case['id'] + '.png')))
                same_pixels = ((image.width, image.height) == (expected_image.width, expected_image.height)
                               and image.pixels == expected_image.pixels)
                expected_svg = (GOLDENS / (case['id'] + '.svg')).read_text()
                if snapshot != expected or not same_pixels or svg != expected_svg:
                    ACTUAL.mkdir(parents=True, exist_ok=True)
                    write_snapshot(ACTUAL / (case['id'] + '.json'), snapshot)
                    image.write(str(ACTUAL / (case['id'] + '.png')))
                    (ACTUAL / (case['id'] + '.svg')).write_text(svg)
                self.assertEqual(snapshot, expected, 'route changed; actual output: ' + str(ACTUAL))
                self.assertTrue(same_pixels, 'drawing changed; actual PNG: ' + str(ACTUAL / (case['id'] + '.png')))
                self.assertEqual(svg, expected_svg, 'annotated drawing changed; actual output: ' + str(ACTUAL))


if __name__ == '__main__':
    if sys.argv[1:] == ['--update']:
        update_goldens()
    else:
        unittest.main()

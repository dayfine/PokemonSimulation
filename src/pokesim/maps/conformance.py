"""Replay exact navigation fixtures; predictions do not confirm execution.

From the repository root (checks exact pinned map bytes against the fixture hashes):
    PYTHONPATH=src python3 -m pokesim.maps.conformance
    PYTHONPATH=src python3 -m pokesim.maps.conformance --game bdsp

The fixture's map_revision identifies the reviewed source. This local runner
checks bytes, not publication approval; map consumers still use consumer_sync.
"""
import argparse
import re
from pathlib import Path

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Hop, Moved, Warped, WorldState, world_step
from .consumer_source import DIGEST, NAME, SHA, read_json
from .pinned_runtime_map import read_pinned_map
from .local_routing import Context, LocalMap
from .runtime_map_pack import ROOT
from .runtime_world import RuntimeWorld
from .transition_state import Pose, clip_plan

PACK = ROOT / 'data/navigation/conformance/v1/cases.json'
DIRECTIONS = {'north', 'south', 'west', 'east'}


def fields(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError('unexpected fixture fields: ' + repr(value))


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('integer outside fixture bounds: ' + repr(value))


def pose_check(value, maps):
    fields(value, 'map tile facing elevation')
    if value['map'] not in maps or value['facing'] not in DIRECTIONS:
        raise ValueError('unknown pose map/direction')
    if not isinstance(value['tile'], list) or len(value['tile']) != 2:
        raise ValueError('tile must contain x,y')
    for coordinate in value['tile']:
        integer(coordinate, 0, 4095)
    integer(value['elevation'], 0, 15)


def validate(pack):
    """Reject unsupported semantics instead of skipping cases or fields."""
    fields(pack, 'format coordinate_frame map_revision maps cases')
    if pack['format'] != 'pokesim-navigation-conformance/1' or pack['coordinate_frame'] != 'runtime-local':
        raise ValueError('unsupported conformance format/frame')
    if not isinstance(pack['map_revision'], str) or not SHA.fullmatch(pack['map_revision']):
        raise ValueError('map revision must be an immutable SHA')
    maps = set()
    for entry in pack['maps']:
        fields(entry, 'game name sha256')
        if (entry['game'] not in ('frlg', 'bdsp') or not NAME.fullmatch(entry['name'])
                or not DIGEST.fullmatch(entry['sha256']) or (entry['game'], entry['name']) in maps):
            raise ValueError('invalid/duplicate map identity')
        maps.add((entry['game'], entry['name']))
    if not pack['cases'] or not maps:
        raise ValueError('empty fixture pack')
    ids = set()
    used = set()
    for case in pack['cases']:
        fields(case, 'input expectation')
        value, expected = case['input'], case['expectation']
        fields(value, 'id game operation maps flags variables initial legs')
        if not isinstance(value['id'], str) or not re.fullmatch(r'[a-z0-9-]+', value['id']) or value['id'] in ids:
            raise ValueError('invalid/duplicate case id')
        ids.add(value['id'])
        names = value['maps']
        if (not isinstance(names, list) or not names or len(set(names)) != len(names)
                or any((value['game'], name) not in maps for name in names)):
            raise ValueError('case references unknown/duplicate maps')
        used.update((value['game'], name) for name in names)
        if (not isinstance(value['flags'], list) or any(not isinstance(f, str) for f in value['flags'])
                or len(set(value['flags'])) != len(value['flags']) or not isinstance(value['variables'], dict)
                or any(not isinstance(k, str) or type(v) is not int for k, v in value['variables'].items())):
            raise ValueError('invalid story context')
        # Only context supported by BOTH initial native adapters is admitted.
        if ((value['game'] == 'frlg' and value['variables'])
                or (value['game'] == 'bdsp' and (value['flags'] or names != ['Route202']
                    or value['variables'] != {'VAR_ROUTE_202_STATE': 1}))):
            raise ValueError('unsupported native story context')
        if not isinstance(value['initial'], list) or not value['initial'] or not value['legs']:
            raise ValueError('empty belief/legs')
        for pose in value['initial']:
            pose_check(pose, names)
            if value['game'] == 'bdsp' and pose['elevation'] != 0:
                raise ValueError('BDSP adapter uses flat elevation 0')
        if value['operation'] == 'walk':
            if len(value['initial']) != 1:
                raise ValueError('walk requires a known pose')
            for leg in value['legs']:
                fields(leg, 'kind direction tiles')
                if leg['kind'] != 'press_tiles' or leg['direction'] not in DIRECTIONS:
                    raise ValueError('unsupported walk leg')
                integer(leg['tiles'], 1, 127)
            fields(expected, 'status trace')
            if expected['status'] != 'complete' or len(expected['trace']) != sum(l['tiles'] for l in value['legs']):
                raise ValueError('incomplete trace')
            for step in expected['trace']:
                fields(step, 'outcome pose')
                if step['outcome'] not in ('moved', 'warped'):
                    raise ValueError('unsupported step result')
                pose_check(step['pose'], names)
        elif value['operation'] == 'clip':
            if value['game'] != 'bdsp' or len(value['initial']) < 2 or len(value['legs']) != 1:
                raise ValueError('clip requires BDSP uncertain pose and one hold')
            leg = value['legs'][0]
            fields(leg, 'kind direction max_tiles')
            if leg['kind'] != 'hold_until_blocked' or leg['direction'] not in DIRECTIONS:
                raise ValueError('unsupported clip leg')
            integer(leg['max_tiles'], 1, 127)
            if expected.get('status') == 'anchor':
                fields(expected, 'status pose leg')
                pose_check(expected['pose'], names)
                fields(expected['leg'], 'kind direction walk_tiles')
                if expected['leg']['kind'] != leg['kind'] or expected['leg']['direction'] != leg['direction']:
                    raise ValueError('anchor leg differs from requested hold')
                integer(expected['leg']['walk_tiles'], 0, leg['max_tiles'])
            else:
                fields(expected, 'status')
                if expected['status'] != 'no_anchor':
                    raise ValueError('unsupported clip result')
        else:
            raise ValueError('unsupported fixture operation')
    if used != maps:
        raise ValueError('unused maps in fixture manifest')
    return pack


def read_pack(path=PACK):
    return validate(read_json(Path(path).read_bytes()))


def make_world(pack, value, root=ROOT):
    """Verify exact local or historical bytes before decoding a fixture map."""
    hashes = {(m['game'], m['name']): m['sha256'] for m in pack['maps']}
    views = []
    for name in value['maps']:
        raw = read_pinned_map(pack['map_revision'], value['game'], name, hashes[value['game'], name], root)
        context = Context(flags=frozenset(value['flags']), variables=value['variables'])
        views.append(LocalMap(read_json(raw), value['game'], context))
    return RuntimeWorld(views)


def pose_from(data):
    return Pose(WorldState(Place(data['map'], Tile(*data['tile'])), data['elevation']), Direction[data['facing'].upper()])


def pose_json(pose):
    return dict(map=pose.state.place.map, tile=list(pose.state.place.tile),
                facing=pose.facing.name.lower(), elevation=pose.state.elevation)


def run_case(value, world):
    belief = [pose_from(p) for p in value['initial']]
    for pose in belief:
        world.validate_state(pose.state)
    if value['operation'] == 'clip':
        leg = value['legs'][0]
        direction = Direction[leg['direction'].upper()]
        # Python counts the final blocked press; native Hold.tiles counts walking.
        plan = clip_plan(world, belief, direction, leg['max_tiles'] + 1)
        if plan is None:
            return dict(status='no_anchor')
        return dict(status='anchor', pose=pose_json(plan.arrival),
                    leg=dict(kind='hold_until_blocked', direction=leg['direction'], walk_tiles=len(plan.actions) - 1))
    if value['operation'] != 'walk':
        raise ValueError('unsupported fixture operation')
    at = belief[0]
    trace = []
    for leg in value['legs']:
        direction = Direction[leg['direction'].upper()]
        for _ in range(leg['tiles']):
            result = world_step(world, at.state, direction)
            if not isinstance(result, (Moved, Warped)) or isinstance(result, Hop):
                raise ValueError('walk requires a completed ordinary or warp step')
            at = Pose(result.state, result.facing if isinstance(result, Warped) else direction)
            trace.append(dict(outcome='warped' if isinstance(result, Warped) else 'moved', pose=pose_json(at)))
    return dict(status='complete', trace=trace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pack', type=Path, default=PACK)
    parser.add_argument('--game', choices=('frlg', 'bdsp'))
    args = parser.parse_args()
    pack = read_pack(args.pack)
    for case in pack['cases']:
        value = case['input']
        if args.game and value['game'] != args.game:
            continue
        actual = run_case(value, make_world(pack, value))
        if actual != case['expectation']:
            parser.exit(1, value['id'] + ': expected ' + repr(case['expectation']) + ', got ' + repr(actual) + '\n')
        print('PASS ' + value['id'])


if __name__ == '__main__':
    main()

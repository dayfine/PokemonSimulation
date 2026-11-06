"""Check native FRLG Forest shortfall/recovery exports on pinned map bytes.

    PYTHONPATH=src python3 -m pokesim.maps.frlg_native_recovery_replay check
    PYTHONPATH=src python3 -m pokesim.maps.frlg_native_recovery_replay capture \
        --stdout /tmp/frlg-native-tests.log --native-source /path/to/Arduino-Source

A completed native leg is a claim, not proof of physical arrival. TRUST cases
are explicit negative controls. Timings, camera detectors and queued controller
requests are not independently validated by this geometry replay.
"""
import argparse
import hashlib
from pathlib import Path
import re

from pokesim.grid.geometry import Direction
from pokesim.grid.maps.model import Behavior
from pokesim.grid.maps.world import Place
from .conformance import fields, make_world, pose_from, pose_json
from .consumer_source import DIGEST, SHA, GitSource, read_json
from .native_recovery_capture import format_trace, native_git, same, advance
from .runtime_map_pack import ROOT
from .transition_state import Pose, Session, clip_plan

BUNDLE = ROOT / 'data/navigation/native-recovery/frlg-forest.trace'
CASE_ORDER = ('forest-one-short', 'forest-two-short', 'next-wall-one-short',
              'next-wall-two-short', 'trust-one-short-control', 'trust-two-short-control')
EXPORTER = 'SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/PokemonFRLG_NativeRecoveryReplay_Tests.cpp'
NATIVE_MAP = 'SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/Maps/ViridianForest.json'
PREFIX = '[Route] native-recovery: '


def tile_list(text):
    values = [(int(x), int(y)) for x, y in re.findall(r'ViridianForest \((\d+), (\d+)\)', text)]
    same(text, ', '.join(f'ViridianForest ({x}, {y})' for x, y in values), 'native Forest coordinates')
    if not values:
        raise ValueError('empty native tile list')
    return values


def parse_plans(notes):
    result = []
    for note in notes:
        if not note.startswith(PREFIX + 'plan from '):
            continue
        header, *rows = note.splitlines()
        origin = header[len(PREFIX + 'plan from '):-1]
        start = None if origin == 'an unknown tile' else tile_list(origin)
        legs = []
        for row in rows:
            match = re.fullmatch(r'    (north|south|east|west) (\d+) \((open|to wall)\) to (.+)', row)
            if not match:
                raise ValueError('unsupported Forest leg: ' + row)
            legs.append(dict(direction=match[1], tiles=int(match[2]), to_wall=match[3] == 'to wall',
                             warps=False, end=dict(map='ViridianForest', tile=list(tile_list(match[4])[0]),
                                 facing=match[1], elevation=3)))
        if not legs:
            raise ValueError('empty native Forest plan')
        result.append(dict(start=start, legs=legs))
    return result


def expected_route(value):
    goal = dict(map='ViridianForest', tile=[3, 28] if value['next_direction'] == 'west' else [7, 33],
                facing=value['next_direction'], elevation=3)
    return [dict(direction='west', tiles=6, to_wall=False, warps=False,
                 end=dict(map='ViridianForest', tile=[7, 28], facing='west', elevation=3)),
            dict(direction=value['next_direction'], tiles=4 if value['next_direction'] == 'west' else 5,
                 to_wall=True, warps=False, end=goal)]


def replay_plan(world, steps, belief):
    """Prove the supplied native steps; do not select a replacement plan."""
    for step in steps:
        direction = Direction[step['direction'].upper()]
        if step['to_wall']:
            clip = clip_plan(world, belief, direction, 128, 'recover')
            if clip is None or len(clip.actions) - 1 > step['tiles'] + 2:
                raise ValueError('native hold does not safely converge within its two-tile slack')
            belief = [clip.arrival]
        else:
            belief = [advance(world, p, direction, step['tiles']) for p in belief]
        same(sorted({tuple(p.state.place.tile) for p in belief}), [tuple(step['end']['tile'])], 'native plan end')
    return belief


def check_case(case, world):
    fields(case, 'id input route calls notes simulator_notes physical failure signs_read violations')
    value = case['input']
    if case['id'] not in CASE_ORDER:
        raise ValueError('unknown Forest case')
    expected_shortfall = 1 if '-one-' in case['id'] else 2
    expected_policy = 'trust' if case['id'].startswith('trust-') else 'reanchor'
    expected_direction = 'west' if case['id'].startswith('next-wall-') else 'south'
    same([value['shortfall'], value['policy'], value['next_direction']],
         [expected_shortfall, expected_policy, expected_direction], 'case identity and injected inputs')
    fields(value, 'shortfall next_direction policy start goal')
    if type(value['shortfall']) is not int or value['shortfall'] not in (1, 2):
        raise ValueError('only one/two-tile shortfall injections are supported')
    if value['next_direction'] not in ('west', 'south') or value['policy'] not in ('reanchor', 'trust'):
        raise ValueError('unsupported native recovery policy/direction')
    same(value['start'], dict(map='ViridianForest', tile=[13, 28], facing='west', elevation=3), 'Forest start')
    route = expected_route(value)
    same(case['route'], route, 'explicit original route')
    same(value['goal'], route[-1]['end'], 'native goal')
    same(case['violations'], [], 'native simulator violations')
    physical = pose_from(value['start'])
    session = Session(world, [physical])
    session.propose([Direction.WEST] * 6, min_completed=6, missed_presses=2)
    candidates = sorted(session.belief, key=lambda p: p.state.place.tile)
    plans = parse_plans(case['notes'])
    if not plans:
        raise ValueError('missing original native plan')
    same(plans[0], dict(start=[(13, 28)], legs=route), 'native initial plan log')
    replay_plan(world, route, [physical])
    next_clip = clip_plan(world, candidates, Direction[value['next_direction'].upper()], 128, 'recover')
    next_converges = next_clip is not None and pose_json(next_clip.arrival) == value['goal']
    inserted = value['policy'] == 'reanchor' and not next_converges
    checks = [n for n in case['notes'] if n.startswith('Route: position check:')]
    if inserted:
        same(len(plans), 2, 'inserted native plan count')
        same(plans[1]['start'], None, 'native reanchor origin is explicitly unknown')
        if len(checks) != 1 or 'up to 2 tiles short' not in checks[0]:
            raise ValueError('missing native shortfall-policy evidence')
        replay_plan(world, plans[1]['legs'], candidates)
        execution = [route[0]] + plans[1]['legs']
    else:
        same(len(plans), 1, 'next hold reuse / TRUST must not insert a plan')
        same(checks, [], 'unexpected native position check')
        execution = route
    same([c['step'] for c in case['calls']], execution, 'executed native legs')
    facing = 'west'
    sign_stop = False
    for index, call in enumerate(case['calls']):
        fields(call, 'step before after facing_input outcome')
        if call['outcome'] not in ('done', 'stopped'):
            raise ValueError('unsupported native step outcome')
        same(call['before'], pose_json(physical), 'native physical start')
        same(call['facing_input'], facing, 'facing passed to native walker')
        step = call['step']
        direction = Direction[step['direction'].upper()]
        if index == 0:
            physical = advance(world, physical, direction, step['tiles'] - value['shortfall'])
            same(call['outcome'], 'done', 'silent shortfall has no reported interruption')
        elif call['outcome'] == 'stopped':
            ahead = world.at(Place('ViridianForest', physical.state.place.tile.step(direction)))
            if not direction.is_vertical or ahead.behavior is not Behavior.SIGN:
                raise ValueError('unsupported native stopped-leg source')
            same(clip_plan(world, [physical], direction, 128, 'recover'), None, 'sign is not a wall anchor')
            physical = Pose(physical.state, direction)
            sign_stop = True
        elif step['to_wall']:
            clip = clip_plan(world, [physical], direction, step['tiles'] + 3, 'recover')
            if clip is None:
                raise ValueError('native physical hold lacks a safe wall')
            physical = clip.arrival
        else:
            physical = advance(world, physical, direction, step['tiles'])
        same(call['after'], pose_json(physical), 'native physical displacement/facing')
        facing = None if call['outcome'] != 'done' else step['end']['facing']
    same(case['physical'], pose_json(physical), 'final physical pose')
    expected_stop = value['policy'] == 'trust' and value['shortfall'] == 2
    same(sign_stop, expected_stop, 'negative sign control')
    same(case['signs_read'], 2 if expected_stop else 0, 'bounded native sign reads')
    if expected_stop:
        if 'interrupted right away, again' not in case['failure']:
            raise ValueError('native sign loop must fail explicitly')
        status = 'stopped-control'
    else:
        same(case['failure'], '', 'unexpected native failure')
        correct = pose_json(physical) == value['goal']
        same(correct, value['policy'] != 'trust', 'goal truth versus negative control')
        status = 'arrived' if correct else 'mislocalized-control'
    endings = [n for n in case['notes'] if ': ended at ' in n]
    same(len(endings), sum(c['outcome'] == 'done' for c in case['calls']), 'native completion record count')
    for note, call in zip(endings, (c for c in case['calls'] if c['outcome'] == 'done')):
        if call['outcome'] == 'done':
            claim = call['step']['end']['tile']
            expected = PREFIX + '{} {} ({}): ended at ViridianForest ({}, {}) (walked).'.format(
                call['step']['direction'], call['step']['tiles'], 'to wall' if call['step']['to_wall'] else 'open', *claim)
            same(note, expected, 'native completion claim (not physical proof)')
    found = [n for n in case['notes'] if ': found again at ' in n]
    same(len(found), int(inserted), 'native localization record')
    if inserted:
        anchor = plans[1]['legs'][0]['end']['tile']
        same(found[0], PREFIX + 'found again at ViridianForest ({}, {}), after 1 hold(s).'.format(*anchor), 'native anchor record')
    return dict(id=case['id'], status=status, inserted=inserted, next_hold_converges=next_converges,
                possible_tiles=[list(p.state.place.tile) for p in candidates], physical=pose_json(physical),
                goal=value['goal'], plans=plans, call_count=len(case['calls']), signs=case['signs_read'],
                unchecked=['native_candidate_storage', 'camera_detectors', 'queue_drain', 'stop_timing', 'unbounded_shortfall'])


def read_bundle(path=BUNDLE):
    if Path(path).suffix == '.trace':
        from .frlg_native_recovery_text import read_text
        bundle = read_text(path)
    else:
        bundle = read_json(Path(path).read_bytes())
    fields(bundle, 'format profile coordinate_frame native_revision native_exporter map_revision maps context cases')
    same(bundle['format'], 'pokesim-native-route-replay/1', 'bundle version')
    same(bundle['profile'], 'frlg-forest-shortfall/1', 'native profile')
    same(bundle['coordinate_frame'], 'runtime-local', 'coordinate frame')
    for key in ('native_revision', 'map_revision'):
        if not SHA.fullmatch(bundle[key]):
            raise ValueError('revisions must be immutable SHAs')
    fields(bundle['native_exporter'], 'path sha256')
    if bundle['native_exporter']['path'] != EXPORTER or not DIGEST.fullmatch(bundle['native_exporter']['sha256']):
        raise ValueError('invalid native exporter identity')
    same(len(bundle['maps']), 1, 'profile map inventory')
    fields(bundle['maps'][0], 'game name sha256')
    if bundle['maps'][0]['game'] != 'frlg' or bundle['maps'][0]['name'] != 'ViridianForest' or not DIGEST.fullmatch(bundle['maps'][0]['sha256']):
        raise ValueError('invalid native map identity')
    same(bundle['context'], dict(flags=[], variables={}), 'Forest context')
    ids = [c['id'] for c in bundle['cases']]
    if len(ids) != len(set(ids)) or set(ids) != set(CASE_ORDER):
        raise ValueError('missing/duplicate Forest case inventory')
    return bundle


def check_bundle(bundle, root=ROOT):
    world = make_world(bundle, dict(game='frlg', maps=['ViridianForest'], **bundle['context']), root)
    return [check_case(case, world) for case in bundle['cases']]


def verify_native_source(bundle, root):
    """Verify recorded Git blobs; this does not attest the built executable."""
    raw = native_git(root, 'show', bundle['native_revision'] + ':' + EXPORTER)
    same(hashlib.sha256(raw).hexdigest(), bundle['native_exporter']['sha256'], 'native exporter checksum')
    raw = native_git(root, 'show', bundle['native_revision'] + ':' + NATIVE_MAP)
    same(hashlib.sha256(raw).hexdigest(), bundle['maps'][0]['sha256'], 'native pinned map checksum')


def capture(stdout, native_root, source_root, output):
    if native_git(native_root, 'status', '--porcelain').strip():
        raise ValueError('capture requires a clean committed native tree')
    lines = Path(stdout).read_text().splitlines()
    if any(n.startswith('FAIL ') for n in lines):
        raise ValueError('native tests failed')
    marker = 'POKESIM_FRLG_REPLAY '
    cases = [read_json(n.split(marker, 1)[1]) for n in lines if marker in n]
    source = GitSource(source_root)
    revision = source.git('rev-parse', 'refs/remotes/origin/main').decode().strip()
    source.approved(revision)
    raw = source.read(revision, 'data/games/frlg/maps/runtime/ViridianForest.json')
    native_revision = native_git(native_root, 'rev-parse', 'HEAD').decode().strip()
    same(hashlib.sha256(native_git(native_root, 'show', native_revision + ':' + NATIVE_MAP)).hexdigest(), hashlib.sha256(raw).hexdigest(), 'native/published map bytes')
    exporter = native_git(native_root, 'show', native_revision + ':' + EXPORTER)
    bundle = dict(format='pokesim-native-route-replay/1', profile='frlg-forest-shortfall/1', coordinate_frame='runtime-local',
        native_revision=native_revision, native_exporter=dict(path=EXPORTER, sha256=hashlib.sha256(exporter).hexdigest()),
        map_revision=revision, maps=[dict(game='frlg', name='ViridianForest', sha256=hashlib.sha256(raw).hexdigest())],
        context=dict(flags=[], variables={}), cases=sorted(cases, key=lambda c: CASE_ORDER.index(c['id'])))
    if len(cases) != len(CASE_ORDER) or len({c['id'] for c in cases}) != len(CASE_ORDER):
        raise ValueError('incomplete native capture')
    check_bundle(bundle, source_root)
    from .frlg_native_recovery_text import write_text
    write_text(bundle, output, format_trace(bundle))
    return bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('check', 'capture'))
    parser.add_argument('--trace', type=Path, default=BUNDLE)
    parser.add_argument('--stdout', type=Path)
    parser.add_argument('--native-source', type=Path)
    parser.add_argument('--source', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        if args.command == 'capture':
            if not args.stdout or not args.native_source:
                parser.error('capture requires --stdout and --native-source')
            capture(args.stdout, args.native_source, args.source, args.trace)
        bundle = read_bundle(args.trace)
        if args.native_source:
            verify_native_source(bundle, args.native_source)
        for row in check_bundle(bundle, args.source):
            print(f'{row["id"]}: {row["status"]}; {row["call_count"]} calls; inserted={row["inserted"]}')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

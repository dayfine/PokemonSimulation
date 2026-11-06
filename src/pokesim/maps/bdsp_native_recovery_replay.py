"""Replay exported BDSP Route202 native walker/GridSim facts.

    PYTHONPATH=src python3 -m pokesim.maps.bdsp_native_recovery_replay \
        check --trace data/navigation/native-recovery/bdsp-route202.trace

This bounded profile replays actual native plans; it does not choose an optimal
route or prove detector timing, queue draining or native facing beliefs.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import WorldState
from .native_recovery_capture import same, native_git, format_trace, advance
from .bdsp_native_recovery_text import CASE_ORDER
from .conformance import fields, integer, make_world, pose_from, pose_json
from .consumer_source import DIGEST, SHA, read_json
from .runtime_map_pack import ROOT
from .transition_state import Observation, Pose, Session, clip_plan

BUNDLE = ROOT / 'data/navigation/native-recovery/bdsp-route202.trace'
RAW_BUNDLE = BUNDLE.parent / 'diagnostics/bdsp-route202.raw.json'


def tiles(text):
    result = [(int(x), int(y)) for x, y in re.findall(r'Route202 \((\d+), (\d+)\)', text)]
    rendered = ', '.join(f'Route202 ({x}, {y})' for x, y in result)
    if not result or text != rendered or len(set(result)) != len(result):
        raise ValueError('unsupported/duplicate native map coordinates: ' + text)
    return result


def parse_plans(notes):
    """Decode the existing native route_plan_line grammar; never infer legs."""
    result = []
    for note in notes:
        if not note.startswith('[Route] native-recovery: plan from '):
            continue
        match = re.fullmatch(r'\[Route\] native-recovery: plan from ([^\n]+):\n(.+)', note, re.S)
        if not match:
            raise ValueError('unsupported native plan record')
        legs = []
        for line in match[2].splitlines():
            leg = re.fullmatch(r'    (north|south|west|east) (\d+) \((open|to wall)\) to (.+)', line)
            if not leg or not 1 <= int(leg[2]) <= 127:
                raise ValueError('unsupported native leg: ' + line)
            legs.append(dict(direction=leg[1], tiles=int(leg[2]), kind=leg[3], after=tiles(leg[4])))
        result.append({'from': tiles(match[1]), 'legs': legs})
    return result


def replay_plan(world, plan):
    """Replay supplied native legs, including wall safety, without choosing them."""
    belief = frozenset(Pose(WorldState(Place('Route202', Tile(*xy)), 0)) for xy in plan['from'])
    for leg in plan['legs']:
        direction = Direction[leg['direction'].upper()]
        if leg['kind'] == 'to wall':
            clip = clip_plan(world, belief, direction, leg['tiles'] + 1, encounter_policy='recover')
            if clip is None or len(clip.actions) - 1 != leg['tiles']:
                raise ValueError('native wall leg lacks a common safe anchor or has wrong distance')
            belief = frozenset([clip.arrival])
        else:
            belief = frozenset(advance(world, pose, direction, leg['tiles']) for pose in belief)
        if sorted({tuple(p.state.place.tile) for p in belief}) != sorted(leg['after']):
            raise ValueError('native planned endpoint disagrees with Python map geometry')
    return belief


def replay_case(case, world):
    """Check observable native facts; omitted native state is not reconstructed."""
    fields(case, 'id input calls notes declared physical failure')
    value = case['input']
    fields(value, 'start goal phase tap origin interrupted_walls running_shoes move_speed')
    same(value['start'], dict(map='Route202', tile=[26, 5], facing='east', elevation=0), 'profile start')
    same(value['goal'], dict(map='Route202', tile=[28, 5], facing='west', elevation=0), 'profile goal')
    if value['phase'] not in ('before', 'after') or value['origin'] not in ('current_leg', 'may_precede_leg'):
        raise ValueError('unsupported encounter report')
    integer(value['tap'], 1, 2)
    integer(value['interrupted_walls'], 0, 4)
    if value['running_shoes'] is not True or value['move_speed'] != 'run':
        raise ValueError('native pace requires Running Shoes and RUN policy')
    physical = pose_from(value['start'])
    uncertain = Session(world, [physical])
    uncertain.propose([Direction.EAST] * 2)
    uncertain.observe(Observation(screen='battle', hp_box=True))
    candidate_tiles = sorted(tuple(p.state.place.tile) for p in uncertain.belief)
    plans = parse_plans(case['notes'])
    if not plans:
        raise ValueError('native trace has no planner records')
    same(plans[0]['from'], [(26, 5)], 'native initial plan origin')
    for plan in plans:
        replay_plan(world, plan)
    replan = [n for n in case['notes'] if n.endswith('; planning again.')]
    unknown_origin = value['tap'] == 1 or value['origin'] == 'may_precede_leg'
    if unknown_origin:
        same(len(plans), 1, 'unknown origin must not replan')
        same(replan, [], 'unknown origin must not localize from this leg')
    else:
        same(len(plans), 2, 'one native recovery plan required')
        same(plans[1]['from'], candidate_tiles, 'native interrupted candidate tiles')
        same(len(replan), 1, 'interrupted replan log count')
        marker = 'encounter: credited taps do not establish pose, at '
        if marker not in replan[0]:
            raise ValueError('unsupported native replan reason')
        logged = replan[0].split(marker, 1)[1][:-len('; planning again.')]
        same(sorted(tiles(logged)), candidate_tiles, 'native replan tiles')
    physical, wall_calls, pauses = replay_calls(case, world, physical)
    same(pauses, value['interrupted_walls'], 'injected wall encounters consumed')
    same(wall_calls, 0 if unknown_origin else min(pauses + 1, 4), 'native per-wall retry bound')
    if unknown_origin:
        same(len(case['calls']), 2, 'unknown origin must stop immediately after the counted leg')
    failure = 'encounter_origin_unknown:' if unknown_origin else 'recovery budget exhausted:' if pauses == 4 else ''
    if failure:
        if not case['failure'].startswith(failure):
            raise ValueError('native failure disagrees with explicit origin/retry policy')
        same(case['declared'], [], 'failed route must not return a declared pose')
    else:
        same(case['failure'], '', 'unexpected native failure')
        same(pose_json(physical), value['goal'], 'native physical arrival')
        same(case['declared'], [dict(value['goal'], facing=None)], 'native declared positions (facing unreported)')
    same(case['physical'], pose_json(physical), 'final native physical pose')
    arrivals = [n for n in case['notes'] if n.startswith('[Route] native-recovery: arrived at ')]
    same(arrivals, [] if failure else ['[Route] native-recovery: arrived at Route202 (28, 5).'], 'native arrival log')
    ended = [n for n in case['notes'] if ': ended at ' in n]
    for note in ended:
        if not note.endswith(' (walked).'):
            raise ValueError('assumed/unknown leg end is unsupported; cannot treat it as walked')
    same(len(ended), 0 if failure else 2, 'completed native recovery leg count')
    return dict(id=case['id'], native_failure=case['failure'], candidate_tiles=[] if unknown_origin else candidate_tiles,
                wall_attempts=wall_calls, physical=pose_json(physical), plans=plans,
                unchecked=['native_facing_belief', 'queue_drain', 'video_confirmation', 'detector_timing', 'global_retry_budget'])


def replay_calls(case, world, physical):
    first_taps = True
    wall_calls = pauses = 0
    for call in case['calls']:
        same(call['before'], pose_json(physical), 'native I/O starting pose')
        direction = Direction[call['direction'].upper()]
        if call['kind'] == 'turn':
            fields(call, 'kind direction before after hold_ms queued')
            if call['hold_ms'] != 50 or call['queued'] is not False:
                raise ValueError('only completed 50 ms D-pad turns are supported')
            physical = Pose(physical.state, direction)
        elif call['kind'] == 'taps':
            fields(call, 'kind direction before after tiles report')
            integer(call['tiles'], 1, 127)
            report = checked_report(call['report'])
            injected = first_taps
            if injected:
                same((call['direction'], call['tiles']), ('east', 2), 'injected tap leg')
            for tap in range(1, call['tiles'] + 1):
                if not (injected and case['input']['phase'] == 'before' and tap == case['input']['tap']):
                    physical = advance(world, physical, direction, 1)
            origin = 'may_precede_leg' if injected and (case['input']['tap'] == 1 or case['input']['origin'] == 'may_precede_leg') else 'current_leg'
            same(report['origin'], origin, 'native encounter origin')
            same(report['wild_battles'], int(injected), 'native tap encounter count')
            # Keep credited chunks distinct from actual movement: BEFORE still credits a chunk.
            same(report['credited_chunks'], call['tiles'], 'native credited tap chunks')
            same(report['stop'], 'limit', 'clear counted leg result')
            first_taps = False
        elif call['kind'] == 'wall':
            fields(call, 'kind direction before after limit_ms injected_pause report')
            integer(call['limit_ms'], 1, 60000)
            report = checked_report(call['report'])
            wall_calls += 1
            if call['injected_pause'] is True:
                pauses += 1
                same((report['stop'], report['wild_battles'], report['credited_chunks']), ('limit', 1, 0), 'interrupted wall report')
            elif call['injected_pause'] is False:
                plan = clip_plan(world, [physical], direction, 128, encounter_policy='recover')
                if plan is None:
                    raise ValueError('native physical wall motion lacks safe map support')
                physical = plan.arrival
                same((report['stop'], report['wild_battles'], report['credited_chunks']), ('blocked', 0, len(plan.actions) - 1), 'wall arrival report')
            else:
                raise ValueError('wall injection flag must be boolean')
            same(report['origin'], 'current_leg', 'wall encounter origin')
        else:
            raise ValueError('unsupported native I/O event: ' + str(call['kind']))
        same(call['after'], pose_json(physical), 'native physical displacement/facing')
    if first_taps:
        raise ValueError('native trace omitted the interrupted leg')
    return physical, wall_calls, pauses


def checked_report(report):
    fields(report, 'stop origin walked_ms wild_battles credited_chunks')
    integer(report['walked_ms'], 0, 60000)
    integer(report['wild_battles'], 0, 1)
    integer(report['credited_chunks'], 0, 127)
    return report


EXPORTER = 'SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_NativeRecoveryReplay_Tests.cpp'
NATIVE_MAP = 'SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Maps/Route202.json'
CASE_IDS = set(CASE_ORDER)


def read_bundle(path=BUNDLE):
    if Path(path).suffix == '.trace':
        from .bdsp_native_recovery_text import read_text
        bundle = read_text(path)
    else:
        bundle = read_json(Path(path).read_bytes())
    fields(bundle, 'format profile coordinate_frame native_revision native_exporter map_revision maps context cases')
    if (bundle['format'] != 'pokesim-native-route-replay/1' or bundle['profile'] != 'bdsp-route202-gridsim/1'
            or bundle['coordinate_frame'] != 'runtime-local'):
        raise ValueError('unsupported native replay format/profile/frame')
    for key in ('native_revision', 'map_revision'):
        if not isinstance(bundle[key], str) or not SHA.fullmatch(bundle[key]):
            raise ValueError('native and map revisions must be immutable full SHAs')
    fields(bundle['native_exporter'], 'path sha256')
    if bundle['native_exporter']['path'] != EXPORTER or not DIGEST.fullmatch(bundle['native_exporter']['sha256']):
        raise ValueError('invalid native exporter identity')
    same(len(bundle['maps']), 1, 'profile map count')
    entry = bundle['maps'][0]
    fields(entry, 'game name sha256')
    if entry['game'] != 'bdsp' or entry['name'] != 'Route202' or not DIGEST.fullmatch(entry['sha256']):
        raise ValueError('unsupported native map identity')
    same(bundle['context'], dict(flags=[], variables={'VAR_ROUTE_202_STATE': 1}), 'profile context')
    if type(bundle['context']['variables']['VAR_ROUTE_202_STATE']) is not int:
        raise ValueError('scene variable must be an integer')
    ids = [c['id'] for c in bundle['cases']]
    if len(ids) != len(set(ids)) or set(ids) != CASE_IDS:
        raise ValueError('incomplete/duplicate native case inventory')
    return bundle


def check_bundle(bundle, root=ROOT):
    value = dict(game='bdsp', maps=['Route202'], **bundle['context'])
    world = make_world(bundle, value, root)
    return [replay_case(case, world) for case in bundle['cases']]


def verify_native_source(bundle, root):
    raw = native_git(root, 'show', bundle['native_revision'] + ':' + EXPORTER)
    same(hashlib.sha256(raw).hexdigest(), bundle['native_exporter']['sha256'], 'native exporter checksum')
    raw = native_git(root, 'show', bundle['native_revision'] + ':' + NATIVE_MAP)
    same(hashlib.sha256(raw).hexdigest(), bundle['maps'][0]['sha256'], 'native pinned map checksum')


def capture(stdout, native_root, source_root, output):
    """Wrap complete, passing per-case exports; does not run/attest the binary."""
    from .consumer_source import GitSource
    if native_git(native_root, 'status', '--porcelain').strip():
        raise ValueError('native capture requires a clean committed worktree')
    marker = 'POKESIM_NATIVE_REPLAY '
    lines = Path(stdout).read_text().splitlines()
    if any(line.startswith('FAIL ') for line in lines):
        raise ValueError('native run contains failed tests')
    cases = [read_json(line.split(marker, 1)[1]) for line in lines if marker in line]
    source = GitSource(source_root)
    revision = source.git('rev-parse', 'refs/remotes/origin/main').decode().strip()
    source.approved(revision)
    raw = source.read(revision, 'data/games/bdsp/maps/runtime/Route202.json')
    native_revision = native_git(native_root, 'rev-parse', 'HEAD').decode().strip()
    exporter = native_git(native_root, 'show', native_revision + ':' + EXPORTER)
    bundle = dict(format='pokesim-native-route-replay/1', profile='bdsp-route202-gridsim/1', coordinate_frame='runtime-local',
                  native_revision=native_revision, native_exporter=dict(path=EXPORTER, sha256=hashlib.sha256(exporter).hexdigest()),
                  map_revision=revision, maps=[dict(game='bdsp', name='Route202', sha256=hashlib.sha256(raw).hexdigest())],
                  context=dict(flags=[], variables={'VAR_ROUTE_202_STATE': 1}), cases=sorted(cases, key=lambda c: c['id']))
    # Validate before writing a reviewed artifact, including the independent replay.
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp) / 'trace.json'
        candidate.write_text(json.dumps(bundle))
        read_bundle(candidate)
    verify_native_source(bundle, native_root)
    check_bundle(bundle, source_root)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    if Path(output).suffix == '.trace':
        from .bdsp_native_recovery_text import write_text
        write_text(bundle, output, format_trace(bundle))
    else:
        Path(output).write_text(format_trace(bundle))
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
            bundle = capture(args.stdout, args.native_source, args.source, args.trace)
        else:
            bundle = read_bundle(args.trace)
            if args.native_source:
                verify_native_source(bundle, args.native_source)
        for result in check_bundle(bundle, args.source):
            print(result['id'] + ': ' + ('safe failure' if result['native_failure'] else 'arrived')
                  + '; wall attempts=' + str(result['wall_attempts']))
        print('Unverified native fields: facing belief, queue drain, video confirmation, timing, global retry budget')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

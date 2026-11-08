"""Replay the bound Parcel diagnostic, with predictions separate from evidence.

    PYTHONPATH=src python3 -m pokesim.story.parcel_replay \
        data/story/parcel-pilot/cases.json --case complete --summary --out /tmp/parcel-trace.json

This is an offline model with scripted observations, not native execution parity
or console evidence. It stops on interruptions; it does not invent recovery,
save/retry options, scene observations, inventory or battle outcomes.
"""

import argparse
import copy
from pathlib import Path

from pokesim.formats.contract_format import json_text
from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Edge, Warp, WorldState, world_step
from pokesim.grid.routing.shortest import as_move, shortest_path
from pokesim.maps.consumer_source import read_json
from .parcel_binding import PROFILE, exact, load_binding


def pose(state, facing):
    """A model-local pose, including arrival-facing and elevation semantics."""
    return {'map': state.place.map, 'tile': list(state.place.tile),
            'elevation': state.elevation, 'facing': facing.name.lower()}


def state_from(value, world):
    """Reject unknown/out-of-map/inconsistent pose data rather than localizing it."""
    exact(value, 'map tile elevation facing')
    if (not isinstance(value['tile'], list) or len(value['tile']) != 2
            or not isinstance(value['map'], str)
            or any(type(n) is not int for n in value['tile'])
            or value['facing'] not in ('north', 'east', 'south', 'west')):
        raise ValueError('expected a known runtime-local pose')
    state = WorldState(Place(value['map'], Tile(*value['tile'])), value['elevation'])
    world.validate_state(state)
    return state, Direction[value['facing'].upper()]


def declared_pose(wire, world):
    """Convert a single authored tile; conversion itself provides no observation."""
    where = wire['where']
    if wire['certainty'] != 'tile' or where['kind'] != 'tiles' or len(where['tiles']) != 1 or 'facing' not in where:
        raise ValueError('Parcel binding requires a single tile and known facing')
    place = Place(wire['map'], Tile(*where['tiles'][0]))
    cell = world.at(place)
    if cell is None:
        raise ValueError('authored pose outside bound maps')
    result = {'map': place.map, 'tile': list(place.tile), 'elevation': cell.elevation, 'facing': where['facing']}
    state_from(result, world)
    return result


def preflight(binding, scenario):
    """Validate all supplied inputs before the first modeled action."""
    exact(scenario, 'entry signals')
    entry = exact(scenario['entry'], 'basis screen pose')
    if entry['basis'] != 'scripted':
        raise ValueError('this pilot accepts only explicitly scripted observations')
    state_from(entry['pose'], binding.world)
    if not isinstance(scenario['signals'], dict):
        raise ValueError('signals must be keyed by event ID')
    events = {e['id']: e for e in binding.checkpoint['events']}
    for name, signal in scenario['signals'].items():
        if name not in events or not isinstance(signal, dict):
            raise ValueError('signal references an unknown event')
        kind = signal.get('kind')
        if kind == 'wild-encounter' and events[name]['kind'] == 'route':
            exact(signal, 'kind from direction')
            state_from(signal['from'], binding.world)
            if signal['direction'] not in ('north', 'east', 'south', 'west'):
                raise ValueError('encounter injection needs a known direction')
        elif kind == 'unconfirmed-transition' and events[name]['kind'] == 'step':
            exact(signal, 'kind')
        elif kind == 'scene-observation' and events[name]['kind'] == 'scene':
            exact(signal, 'kind basis screen pose received')
            if signal['basis'] != 'scripted' or not isinstance(signal['received'], dict):
                raise ValueError('scene evidence must be explicitly scripted')
            if any(not isinstance(k, str) or type(v) is not int or v <= 0 for k, v in signal['received'].items()):
                raise ValueError('receipt quantities must be positive integers')
            if set(signal['received']) - {'oak-parcel'}:
                raise ValueError('unsupported receipt item')
            state_from(signal['pose'], binding.world)
        else:
            raise ValueError('unsupported signal/capability combination')


def interruption_press(path, facing, signal, world):
    """Locate a physical injection point; a different route must not skip it."""
    if not signal:
        return None
    state = path.start
    matches = []
    for number, move in enumerate(path.moves, 1):
        if pose(state, facing) == signal['from'] and move.direction.name.lower() == signal['direction']:
            matches.append(number)
        result = world_step(world, state, move.direction, world.rules)
        state, facing = move.to, getattr(result, 'facing', move.direction)
    if len(matches) != 1:
        raise ValueError('encounter injection must match exactly one physical route step')
    return matches[0]


def run(binding, scenario):
    """Execute only the supported offline bindings; failed events do not advance."""
    scenario = copy.deepcopy(scenario)
    preflight(binding, scenario)
    world = binding.world
    entry = scenario['entry']
    state, facing = state_from(entry['pose'], world)
    current = copy.deepcopy(entry['pose'])
    basis = 'scripted-observation'
    trace, completed, received, candidates = [], [], {}, []
    failure = None
    active = None
    if entry['screen'] != 'overworld' or current != declared_pose(binding.checkpoint['start'], world):
        failure = 'entry_requirement_failed'
    else:
        for event in binding.checkpoint['events']:
            active = event['id']
            signal = scenario['signals'].get(active)
            trace.append({'event': active, 'phase': 'started', 'pose': current, 'basis': basis})
            if event['kind'] == 'route':
                target = declared_pose(event['target'], world)
                goal = Place(target['map'], Tile(*target['tile']))
                path = shortest_path(world, state, goal, binding.costs, world.rules)
                if path is None:
                    failure = 'no_route'
                    break
                if len(path.moves) > binding.max_route_presses:
                    failure = 'route_press_budget_exceeded'
                    break
                interrupted_at = interruption_press(path, facing, signal, world)
                for number, move in enumerate(path.moves, 1):
                    result = world_step(world, state, move.direction, world.rules)
                    end_facing = getattr(result, 'facing', move.direction)
                    predicted = pose(move.to, end_facing)
                    if interrupted_at == number:
                        # A battle does not confirm whether this interrupted press
                        # displaced the player. Facing is invalidated in both cases.
                        candidates = [dict(current, facing=None), dict(predicted, facing=None)]
                        current, basis = None, 'unknown-after-interruption'
                        failure = 'encounter_requires_recovery'
                        trace.append({'event': active, 'phase': 'interrupted', 'before_press': number,
                                      'candidates': candidates, 'basis': basis})
                        break
                    state, facing, current, basis = move.to, end_facing, predicted, 'model-prediction'
                    trace.append({'event': active, 'phase': 'press', 'number': number,
                                  'direction': move.direction.name.lower(), 'pose': current, 'basis': basis})
                if failure:
                    break
                # The shared Python spatial search does not include final facing.
                # Model an explicit in-place turn; do not pretend it was movement.
                if facing.name.lower() != target['facing']:
                    facing = Direction[target['facing'].upper()]
                    current, basis = pose(state, facing), 'model-prediction'
                    trace.append({'event': active, 'phase': 'turn', 'pose': current, 'basis': basis})
            elif event['kind'] == 'step':
                if signal:
                    current, basis = None, 'unknown-after-transition'
                    failure = 'transition_unconfirmed'
                    break
                direction = Direction[event.get('direction', 'north').upper()]
                result = world_step(world, state, direction, world.rules)
                move = as_move(direction, result)
                if move is None:
                    if isinstance(result, (Warp, Edge)):
                        current, basis = None, 'unknown-after-transition'
                    failure = 'step_unresolved'
                    break
                state, facing = move.to, getattr(result, 'facing', direction)
                current, basis = pose(state, facing), 'model-prediction'
                trace.append({'event': active, 'phase': 'step', 'direction': direction.name.lower(),
                              'pose': current, 'basis': basis})
            else:
                # A declared_after is an authored expectation, never a receipt.
                if (not signal or signal['screen'] != 'overworld'
                        or signal['pose'] != declared_pose(event['declared_after'], world)
                        or signal['received'].get('oak-parcel') != 1):
                    current, basis = None, 'unknown-after-scene'
                    failure = 'scene_evidence_missing_or_mismatched'
                    break
                current, basis = copy.deepcopy(signal['pose']), 'scripted-observation'
                state, facing = state_from(current, world)
                received = copy.deepcopy(signal['received'])
                trace.append({'event': active, 'phase': 'observation', 'pose': current,
                              'received': received, 'basis': basis})
            completed.append(active)
            trace.append({'event': active, 'phase': 'completed', 'pose': current, 'basis': basis})
    if failure and active:
        trace.append({'event': active, 'phase': 'failed', 'failure': failure, 'pose': current, 'basis': basis})
    return {'format': 'pokesim-parcel-replay-report/1', 'status': 'stopped' if failure else 'model_complete',
            'checkpoint': binding.checkpoint['id'], 'profile_sha256': binding.profile_sha256,
            'native_source_revision': binding.capture['source_revision'],
            'native_parity': 'not-established', 'native_unbound': list(binding.capture['unbound']),
            'policy_basis': 'synthetic-offline-policy', 'failure': failure,
            'active_event': active if failure else None, 'completed_events': completed,
            'pose': current, 'pose_basis': basis, 'candidates': candidates,
            'received': received, 'save_performed': False, 'trace': trace}


def read_cases(path):
    """Read the diagnostic inventory; reject unknown versions and duplicate IDs."""
    data = exact(read_json(Path(path).read_bytes()), 'format evidence_status coordinate_frame cases')
    if (data['format'] != 'pokesim-parcel-pilot-cases/1'
            or data['evidence_status'] != 'synthetic-scripted-observations'
            or data['coordinate_frame'] != 'runtime-local'
            or not isinstance(data['cases'], list) or not data['cases']):
        raise ValueError('unsupported or empty Parcel case inventory')
    names = set()
    for case in data['cases']:
        exact(case, 'id input expectation')
        if not isinstance(case['id'], str) or not case['id'] or case['id'] in names:
            raise ValueError('empty/duplicate case ID')
        names.add(case['id'])
    return data['cases']


def summary(report):
    """Readable event-level view; the JSON report retains the full movement trace."""
    lines = ['{}: {} (offline diagnostic; native parity not established)'.format(
        report['checkpoint'], report['status'])]
    for row in report['trace']:
        if row['phase'] == 'completed':
            p = row['pose']
            lines.append('{} -> {} {} {}, elevation {} [{}]'.format(
                row['event'], p['map'], p['tile'], p['facing'], p['elevation'], row['basis']))
    if report['failure']:
        lines.append('Stopped: {} at {}'.format(report['failure'], report['active_event'] or 'entry'))
    if report['candidates']:
        lines.append('Candidates: ' + '; '.join('{} {} (facing unknown)'.format(p['map'], p['tile'])
                                               for p in report['candidates']))
    lines.append('Save: never; retry: none (synthetic policy).')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('cases', type=Path)
    parser.add_argument('--case', required=True)
    parser.add_argument('--binding', type=Path, default=PROFILE)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--summary', action='store_true', help='print readable event outcomes instead of full JSON')
    args = parser.parse_args()
    try:
        cases = read_cases(args.cases)
        matches = [c for c in cases if c['id'] == args.case]
        if len(matches) != 1:
            raise ValueError('case ID must select exactly one scenario')
        report = run(load_binding(args.binding), matches[0]['input'])
        formatted = json_text(report)
        if args.out:
            args.out.write_text(formatted, encoding='utf-8')
        if args.summary:
            print(summary(report), end='')
        elif not args.out:
            print(formatted, end='')
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    if report['status'] != 'model_complete':
        parser.exit(1)


if __name__ == '__main__':
    main()

"""Replay versioned semantic regression inputs against a supplied runtime world.

These are source-grounded reductions and labeled diagnostics, not imports of
native story plans. Unsupported event kinds stop; expected failures are reported
as failures, even when their regression assertions pass.
"""
import json
import re
from pathlib import Path

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import WorldState
from .local_routing import Context, load_pinned_map
from .runtime_world import ArrivalContract, RuntimeWorld
from .transition_state import Observation, Pose, Session, StateFailure

CATALOG = Path(__file__).parent / 'scenarios/transition-cases.json'


def read_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text())
    if (data.get('format') != 'pokesim-transition-cases/1'
            or data.get('coordinate_frame') != 'runtime-local'
            or not re.fullmatch('[0-9a-f]{40}', data.get('map_revision', ''))):
        raise ValueError('unsupported transition catalog or map pin')
    ids = [c['id'] for c in data['cases']]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError('empty or duplicate scenario IDs')
    return data


def direction(name):
    return Direction[name.upper()]


def place(data):
    return Place(data['map'], Tile(*data['tile']))


def contracts(case):
    return [ArrivalContract(place(c['source']), place(c['destination']), direction(c['enter_direction']), direction(c['facing']), c['evidence'])
            for c in case.get('arrival_contracts', [])]


def pinned_world(source, revision, case):
    context = Context(frozenset(case['flags']), case['variables'])
    return RuntimeWorld([load_pinned_map(source, revision, case['game'], name, context) for name in case['maps']], contracts(case), case.get('encounter_maps', ()))


def pose_json(pose):
    return dict(map=pose.state.place.map, tile=list(pose.state.place.tile),
                elevation=pose.state.elevation, facing=pose.facing.name.lower() if pose.facing else None)


def replay(case, world, map_revision):
    initial = [Pose(WorldState(place(p), p['elevation']), direction(p['facing']) if p['facing'] else None)
               for p in case['initial']]
    session = Session(world, initial)
    trace = []
    for index, event in enumerate(case['events']):
        kind = event['event']
        details = {}
        expected_failure = event.get('expect_failure')
        try:
            if kind == 'movement':
                session.propose([direction(d) for d in event['actions']], event.get('min_completed', 0),
                                [direction(d) for d in event.get('queued', [])], event.get('edge_stall', False), event.get('missed_presses', 0))
            elif kind == 'observation':
                fields = {k: v for k, v in event.items() if k not in ('event', 'expect_failure')}
                if 'tiles' in fields:
                    fields['tiles'] = tuple(Tile(*t) for t in fields['tiles'])
                if fields.get('still_direction'):
                    fields['still_direction'] = direction(fields['still_direction'])
                if fields.get('facing'):
                    fields['facing'] = direction(fields['facing'])
                session.observe(Observation(**fields))
            elif kind == 'clip':
                plan = session.clip(direction(event['direction']), event['max_presses'], event.get('encounter_policy', 'stop'))
                details = dict(clip_actions=[d.name.lower() for d in plan.actions], predicted_arrival=pose_json(plan.arrival))
            elif kind == 'recovery':
                plan = session.recover(event['max_presses'], event['max_states'])
                details = dict(recovery_actions=[d.name.lower() for d in plan.actions],
                               predicted_arrival=pose_json(plan.arrival))
            elif kind == 'expect':
                if len(session.belief) != event['candidates'] or session.can_resume != event['can_resume']:
                    raise AssertionError(f'{case["id"]} event {index}: unexpected pose count/resume state')
            else:
                raise ValueError('unsupported semantic event: ' + kind)
        except StateFailure as exc:
            if not expected_failure or expected_failure not in str(exc):
                raise
            details['expected_failure'] = str(exc)
        else:
            if expected_failure:
                raise AssertionError('expected failure was not raised: ' + expected_failure)
        belief = sorted((pose_json(p) for p in session.belief), key=lambda p: (p['map'], p['tile'], p['elevation'], p['facing'] or ''))
        trace.append(dict(index=index, event=event, belief=belief, can_resume=session.can_resume,
                          screen=session.screen, queue_drained=session.queue_drained, remaining_recoveries=session.remaining_recoveries, failure=session.failure, **details))
    return dict(format='pokesim-transition-trace/1', scenario=case['id'], map_revision=map_revision,
                evidence=case['evidence'], derivation=case['derivation'],
                context=dict(flags=case['flags'], variables=case['variables']),
                maps={name: view.provenance for name, view in world.views.items()},
                arrival_contracts=case.get('arrival_contracts', []), encounter_maps=sorted(world.encounter_maps),
                checks_passed=True, failure=session.failure, can_resume=session.can_resume, trace=trace)

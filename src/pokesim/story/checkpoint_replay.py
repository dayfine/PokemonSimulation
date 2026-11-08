"""Run captured checkpoints through registered offline game/action handlers.

    PYTHONPATH=src python3 -m pokesim.story.checkpoint_replay \
        data/story/parcel-pilot/cases.json --case parcel-all-events --summary --out /tmp/parcel-trace.json

Only registered capabilities execute. Expectations never drive execution;
check_actions changes assertions, not the commands requested by replay.
"""

import argparse
import copy
from pathlib import Path

from pokesim.formats.contract_format import json_text
from .replay_binding import PROFILE, load_binding
from .replay_handlers import exact
from .replay_state import ReplayState


def preflight(binding, scenario):
    """Validate entry and every signal before asking any handler to execute."""
    if not isinstance(scenario, dict) or set(scenario) - {'entry', 'signals', 'check_actions'}:
        raise ValueError('unsupported scenario fields')
    if type(scenario.get('check_actions', False)) is not bool:
        raise ValueError('check_actions must be boolean')
    entry = exact(scenario['entry'], 'basis screen pose')
    if entry['basis'] != 'scripted':
        raise ValueError('replay currently accepts only scripted observations')
    binding.adapter.validate_pose(entry['pose'])
    if not isinstance(scenario['signals'], dict):
        raise ValueError('signals must be keyed by event ID')
    events = {e['id']: e for e in binding.checkpoint['events']}
    for name, signal in scenario['signals'].items():
        if name not in events or not isinstance(signal, dict):
            raise ValueError('signal references an unknown event')
        binding.actions[name].preflight(events[name], signal)


def run(binding, scenario):
    """Apply shared event ordering/failure policy; action details belong to handlers."""
    scenario = copy.deepcopy(scenario)
    preflight(binding, scenario)
    state = ReplayState(copy.deepcopy(scenario['entry']['pose']))
    completed, active, failure = [], None, None
    if (scenario['entry']['screen'] != 'overworld'
            or state.pose != binding.adapter.authored_pose(binding.checkpoint['start'])):
        failure = 'entry_requirement_failed'
    else:
        for event in binding.checkpoint['events']:
            active = event['id']
            state.record(active, 'started')
            failure = binding.actions[active].execute(state, event, scenario['signals'].get(active))
            if failure:
                state.record(active, 'failed', failure=failure)
                break
            completed.append(active)
            state.record(active, 'completed')
    return {'format': 'pokesim-checkpoint-replay-report/1', 'status': 'stopped' if failure else 'model_complete',
            'checkpoint': binding.checkpoint['id'], 'profile_sha256': binding.profile_sha256,
            'native_source_revision': binding.capture['source_revision'],
            'native_parity': 'not-established', 'native_unbound': list(binding.capture['unbound']),
            'policy_basis': 'synthetic-offline-policy', 'failure': failure,
            'active_event': active if failure else None, 'completed_events': completed,
            'pose': state.pose, 'pose_basis': state.basis, 'candidates': state.candidates,
            'received': state.received, 'save_performed': False, 'actions': state.actions, 'trace': state.trace}


def summary(report):
    """Small event-level view; full actions and movement remain in the report."""
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
    from .replay_cases import check_case, read_cases
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('cases', type=Path)
    parser.add_argument('--case', required=True)
    parser.add_argument('--binding', type=Path, default=PROFILE)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    try:
        matches = [c for c in read_cases(args.cases) if c['id'] == args.case]
        if len(matches) != 1:
            raise ValueError('case ID must select exactly one scenario')
        report = run(load_binding(args.binding), matches[0]['input'])
        # Retain the actual trace even if an expectation/action assertion fails.
        if args.out:
            args.out.write_text(json_text(report), encoding='utf-8')
        report['case_check'] = check_case(matches[0], report)
        if args.out:
            args.out.write_text(json_text(report), encoding='utf-8')
        if args.summary:
            print(summary(report), end='')
            print('Expected action sequence: {}.'.format(report['case_check']['actions']))
        elif not args.out:
            print(json_text(report), end='')
    except (OSError, ValueError, KeyError, TypeError, AssertionError) as error:
        parser.exit(1, str(error) + '\n')
    if report['status'] != 'model_complete':
        parser.exit(1)


if __name__ == '__main__':
    main()

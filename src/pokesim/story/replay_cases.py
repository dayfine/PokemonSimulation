"""Read/assert replay cases and render their inputs and expected actions.

    PYTHONPATH=src python3 -m pokesim.story.replay_cases \
        data/story/parcel-pilot/cases.json --out data/story/parcel-pilot/CASES.md
    PYTHONPATH=src python3 -m pokesim.story.replay_cases \
        data/story/parcel-pilot/cases.json --check-doc data/story/parcel-pilot/CASES.md

Rendering never runs replay or updates expectations from actual output.
"""

import argparse
import json
from itertools import zip_longest
from pathlib import Path

from pokesim.maps.consumer_source import read_json
from .replay_handlers import exact


def validate_action(action):
    """Reject ambiguous assertions such as boolean tile distances or unknown fields."""
    if not isinstance(action, dict):
        raise ValueError('expected an action record')
    kind = action.get('kind')
    if kind in ('walk', 'hop'):
        exact(action, 'event kind map direction tiles')
        if type(action['tiles']) is not int or action['tiles'] <= 0:
            raise ValueError('walk/hop tiles must be a positive integer')
    elif kind == 'transition':
        exact(action, 'event kind map direction to_map via')
        if (action['via'] not in ('warp', 'edge') or action['to_map'] is not None
                and (not isinstance(action['to_map'], str) or not action['to_map'])):
            raise ValueError('transition needs a destination or explicit unknown, and warp/edge mode')
    elif kind == 'door':
        exact(action, 'event kind map direction to_map')
        if not isinstance(action['to_map'], str) or not action['to_map']:
            raise ValueError('door needs a destination map')
    elif kind == 'talk':
        exact(action, 'event kind npc')
        if not isinstance(action['npc'], str) or not action['npc']:
            raise ValueError('talk needs a named NPC')
    elif kind == 'heal':
        exact(action, 'event kind')
    elif kind == 'turn':
        exact(action, 'event kind map direction')
    elif kind == 'scene':
        exact(action, 'event kind capability')
        if not isinstance(action['capability'], str) or not action['capability']:
            raise ValueError('scene capability required')
    else:
        raise ValueError('unsupported action kind')
    if not isinstance(action['event'], str) or not action['event']:
        raise ValueError('action event required')
    if kind not in ('scene', 'talk', 'heal') and (not isinstance(action['map'], str) or not action['map']
            or action['direction'] not in ('north', 'east', 'south', 'west')):
        raise ValueError('action map and direction required')


def action_contract(case):
    """An enabled check requires an explicit full list; disabled checks omit it."""
    enabled = case['input'].get('check_actions', False)
    if type(enabled) is not bool:
        raise ValueError('check_actions must be boolean')
    supplied = 'actions' in case['expectation']
    if enabled != supplied or supplied and not isinstance(case['expectation']['actions'], list):
        raise ValueError('expectation.actions is required exactly when input.check_actions is true')
    if supplied:
        for action in case['expectation']['actions']:
            validate_action(action)
    return enabled


def read_cases(path):
    """Reject unknown versions, duplicate IDs and ambiguous action assertions."""
    data = exact(read_json(Path(path).read_bytes()), 'format evidence_status coordinate_frame cases')
    if (data['format'] != 'pokesim-story-replay-cases/1'
            or data['evidence_status'] != 'synthetic-scripted-observations'
            or data['coordinate_frame'] != 'runtime-local'
            or not isinstance(data['cases'], list) or not data['cases']):
        raise ValueError('unsupported or empty case inventory')
    names = set()
    for case in data['cases']:
        exact(case, 'id description input expectation')
        if not isinstance(case['id'], str) or not case['id'] or case['id'] in names:
            raise ValueError('empty/duplicate case ID')
        if not isinstance(case['description'], str) or not case['description']:
            raise ValueError('case description required')
        names.add(case['id'])
        action_contract(case)
    return data['cases']


def check_case(case, report):
    """Assert outcomes and optionally every ordered action, independently of run()."""
    enabled = action_contract(case)
    for key, expected in case['expectation'].items():
        if key != 'actions' and (key not in report or report[key] != expected):
            raise AssertionError('{}: {} expected {!r}, got {!r}'.format(case['id'], key, expected, report.get(key)))
    if enabled:
        if not isinstance(report.get('actions'), list):
            raise AssertionError(case['id'] + ': actual report has no action list')
        for index, actual in enumerate(report['actions']):
            try:
                validate_action(actual)
            except ValueError as error:
                raise AssertionError('{}: invalid actions[{}]: {}'.format(case['id'], index, error)) from error
        for index, (expected, actual) in enumerate(zip_longest(case['expectation']['actions'], report['actions'])):
            if expected != actual:
                raise AssertionError('{}: actions[{}] expected {!r}, got {!r}'.format(case['id'], index, expected, actual))
    return {'id': case['id'], 'outcomes': 'matched', 'actions': 'matched' if enabled else 'not-checked'}


def place(value):
    """Readable state spelling shared by the case document's input/output views."""
    if value is None:
        return 'unknown'
    return '{} {} facing {} (elevation {})'.format(value['map'], value['tile'], value['facing'] or 'unknown', value['elevation'])


def receipts(value):
    return ', '.join('{} × {}'.format(count, item) for item, count in value.items()) or 'nothing'


def action_text(action):
    """Describe semantic movement intents, separate from confirmed displacement."""
    if action['kind'] in ('walk', 'hop'):
        return '{} {} for {} {} on {}'.format(action['kind'].capitalize(), action['direction'], action['tiles'],
                                               'tile' if action['tiles'] == 1 else 'tiles', action['map'])
    if action['kind'] == 'transition':
        return 'Take {} {}: {} → {}'.format(action['via'], action['direction'], action['map'], action['to_map'] or 'unknown destination')
    if action['kind'] == 'door':
        return 'Follow the {} corridor {} through the door to {}.'.format(action['map'], action['direction'], action['to_map'])
    if action['kind'] == 'talk':
        return 'Talk to {}.'.format(action['npc'])
    if action['kind'] == 'heal':
        return 'Heal at the Pokemon Center and return outside.'
    if action['kind'] == 'turn':
        return 'Face {} on {}'.format(action['direction'], action['map'])
    return 'Request scene via ' + action['capability']


def render_cases(cases):
    """Generate a review view from authored inputs/expectations, without execution."""
    lines = ['# Replay scenarios', '',
             'Generated from [cases.json](cases.json); edit that file and regenerate this view.', '',
             'All observations and interruptions are synthetic. Actions are modeled requests,',
             'not controller timing or verified console behavior. Walk distances are requested, not confirmed displacement.',
             'An interrupted walk keeps its requested distance; uncertainty/progress is checked separately.',
             'Scene contents are supplied observations, not simulated button-by-button dialogue.',
             'A signal is consumed only if its event is reached; listing a receipt does not grant the item at entry.', '']
    for case in cases:
        inp, expected = case['input'], case['expectation']
        lines += ['## ' + case['id'], '', case['description'], '',
                  '**Start:** ' + place(inp['entry']['pose']) + '; screen: ' + inp['entry']['screen'] + '.', '',
                  '**Injected observations / interruptions:**', '']
        if not inp['signals']:
            lines += ['- None.']
        for event, signal in inp['signals'].items():
            if signal['kind'] == 'scene-observation':
                lines += ['- `{}`: {} scene result at {}; received: {}.'.format(
                    event, signal['screen'], place(signal['pose']), receipts(signal['received']))]
            elif signal['kind'] == 'bdsp-observation':
                lines += ['- `{}`: scripted {} at {}; result: `{}`.'.format(
                    event, signal['screen'], place(signal['pose']), json.dumps(signal['result']))]
            elif signal['kind'] == 'movement-script':
                lines += ['- `{}`: synthetic clearance window for {}; encounter: `{}`.'.format(
                    event, ', '.join(signal['clear_npcs']) or 'no wandering NPCs', json.dumps(signal['encounter']))]
            elif signal['kind'] == 'wild-encounter':
                lines += ['- `{}`: encounter interrupts a {}ward walk from {}.'.format(event, signal['direction'], place(signal['from']))]
            else:
                lines += ['- `{}`: transition cannot be confirmed.'.format(event)]
        lines += ['', '**Expected result:** `{}`{}.'.format(expected['status'],
                  ' / ' + expected['failure'] if expected['failure'] else ''), '',
                  '- Completed events: ' + (', '.join('`' + e + '`' for e in expected['completed_events']) or 'none') + '.',
                  '- Pose: ' + place(expected['pose']) + '.',
                  '- Received: ' + receipts(expected['received']) + '.']
        if expected['candidates']:
            lines += ['- Candidates: ' + '; '.join(place(p) for p in expected['candidates']) + '.']
        lines += ['', '**Exact action checking:** ' + ('enabled; the entire ordered list follows.' if action_contract(case)
                                                      else 'disabled; this case checks outcomes only.'), '']
        if 'actions' in expected:
            if not expected['actions']:
                lines += ['No actions may be requested.', '']
            else:
                lines += ['| # | Event | Expected request |', '|---|---|---|']
                lines += ['| {} | `{}` | {} |'.format(i, a['event'], action_text(a))
                          for i, a in enumerate(expected['actions'], 1)]
                lines += ['']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('cases', type=Path)
    output = parser.add_mutually_exclusive_group()
    output.add_argument('--out', type=Path)
    output.add_argument('--check-doc', type=Path)
    args = parser.parse_args()
    text = render_cases(read_cases(args.cases))
    if args.check_doc:
        if args.check_doc.read_text() != text:
            parser.exit(1, 'Case documentation differs; regenerate with replay_cases --out.\n')
    elif args.out:
        args.out.write_text(text, encoding='utf-8')
    else:
        print(text, end='')


if __name__ == '__main__':
    main()

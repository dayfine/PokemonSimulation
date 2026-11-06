"""Readable, versioned native replay data using strict INI sections.

Context is shared explicitly. Calls retain before/after poses and every report
field, including zero values. Only replay-relevant native log facts are inline;
the complete original bundle is retained as a checksummed diagnostic artifact.
"""
import configparser
import copy
import json
import re

from .consumer_source import read_json
from .native_recovery_capture import (keys, boolean, pose_text, parse_pose, milliseconds,
                                      assignments, diagnostic_source, read_checked_text, write_checked_text)

CASE_ORDER = ('last-tap-before', 'last-tap-after', 'interrupted-wall-retry',
              'last-wall-retry-succeeds', 'interrupted-wall-budget',
              'first-tap-unknown-origin', 'reported-unknown-origin')
PREFIX = '[Route] native-recovery: '


def call_text(call):
    kind = call['kind']
    amount = str(call['tiles']) if kind == 'taps' else str(call['hold_ms'] if kind == 'turn' else call['limit_ms']) + 'ms'
    start = kind + ' ' + call['direction'] + ' ' + amount
    movement = pose_text(call['before']) + ' -> ' + pose_text(call['after'])
    if kind == 'turn':
        end = 'queued=' + str(call['queued']).lower()
    else:
        report = call['report']
        end = '{} {}ms battles={} credited={} origin={}'.format(report['stop'], report['walked_ms'],
            report['wild_battles'], report['credited_chunks'], report['origin'])
        if kind == 'wall':
            end += ' pause=' + str(call['injected_pause']).lower()
    return start + ' | ' + movement + ' | ' + end


def parse_call(text, context):
    action, movement, outcome = text.split(' | ')
    kind, direction, amount = action.split()
    before, after = movement.split(' -> ')
    call = dict(kind=kind, direction=direction, before=parse_pose(before, context), after=parse_pose(after, context))
    if kind == 'turn':
        fields = assignments(outcome.split())
        keys(fields, 'queued')
        call.update(hold_ms=milliseconds(amount), queued=boolean(fields['queued']))
    elif kind in ('taps', 'wall'):
        stop, walked, *tokens = outcome.split()
        fields = assignments(tokens)
        keys(fields, 'battles credited origin' + (' pause' if kind == 'wall' else ''))
        call['report'] = dict(stop=stop, walked_ms=milliseconds(walked), wild_battles=int(fields['battles']),
                              credited_chunks=int(fields['credited']), origin=fields['origin'])
        if kind == 'taps':
            if not amount.isdecimal():
                raise ValueError('tap count must be an integer')
            call['tiles'] = int(amount)
        else:
            call.update(limit_ms=milliseconds(amount), injected_pause=boolean(fields['pause']))
    else:
        raise ValueError('unknown call kind: ' + kind)
    return call


def replay_notes(notes):
    """Exactly the native fact categories consumed by the current replay profile."""
    return [n for n in notes if n.startswith(PREFIX + 'plan from ')
            or n.endswith('; planning again.') or ': ended at ' in n
            or n.startswith(PREFIX + 'arrived at ')]


def canonical(bundle):
    result = copy.deepcopy(bundle)
    result['cases'].sort(key=lambda c: c['id'])
    for case in result['cases']:
        case['notes'] = replay_notes(case['notes'])
    return result


def note_lines(notes, map_name):
    result = []
    for note in replay_notes(notes):
        if not note.startswith(PREFIX):
            raise ValueError('unsupported native fact prefix')
        note = note[len(PREFIX):].replace(map_name + ' ', '')
        note = re.sub(r'\((\d+), (\d+)\)', r'(\1,\2)', note)
        for index, line in enumerate(note.splitlines()):
            result.append(('> ' + line.strip()) if index else line)
    return result


def parse_notes(text, map_name):
    result = []
    for line in text.splitlines():
        if not line:
            continue
        continuation = line.startswith('> ')
        value = line[2:] if continuation else line
        value = re.sub(r'\((\d+),(\d+)\)', lambda m: f'{map_name} ({m[1]}, {m[2]})', value)
        if continuation:
            if not result or not result[-1].startswith(PREFIX + 'plan from '):
                raise ValueError('native leg without a plan')
            result[-1] += '\n    ' + value
        else:
            result.append(PREFIX + value)
    if replay_notes(result) != result:
        raise ValueError('unsupported native fact category')
    return result


def format_text(bundle, diagnostic, digest):
    common = bundle['cases'][0]['input']
    entry = bundle['maps'][0]
    lines = ['# Native BDSP recovery capture: shared context, then one row per action.',
             '# Pose: (x,y) facing; ? = unreported facing. Zero/false are explicit.',
             '# Calls: action | physical before -> after | native report.',
             '# Native facts: > is a leg belonging to the preceding plan.', '',
             '[trace]', 'format = pokesim-native-route-text/1', 'bundle_format = ' + bundle['format'],
             'profile = ' + bundle['profile'], 'coordinate_frame = ' + bundle['coordinate_frame'], '',
             '[context]', 'map = ' + entry['name'], 'elevation = ' + str(common['start']['elevation']),
             'start = ' + pose_text(common['start']), 'goal = ' + pose_text(common['goal']),
             'running_shoes = ' + str(common['running_shoes']).lower(), 'move_speed = ' + common['move_speed'],
             'flags = ' + json.dumps(bundle['context']['flags']), 'variables = ' + json.dumps(bundle['context']['variables']), '']
    cases = {c['id']: c for c in bundle['cases']}
    if set(cases) != set(CASE_ORDER) or len(cases) != len(bundle['cases']):
        raise ValueError('unsupported text-trace case inventory')
    for name in CASE_ORDER:
        case = cases[name]
        value = case['input']
        for field in ('start', 'goal', 'running_shoes', 'move_speed'):
            if value[field] != common[field]:
                raise ValueError('text profile requires explicit shared ' + field)
        lines += ['[case ' + name + ']', 'encounter = {} tap {}; origin={}'.format(value['phase'], value['tap'], value['origin']),
                  'wall_interruptions = ' + str(value['interrupted_walls']), 'calls =']
        lines += ['    ' + call_text(c) for c in case['calls']]
        lines += ['native ='] + ['    ' + n for n in note_lines(case['notes'], entry['name'])]
        lines += ['declared = ' + ('; '.join(pose_text(p) for p in case['declared']) or 'none'),
                  'physical = ' + pose_text(case['physical']), 'failure = ' + json.dumps(case['failure']), '']
    lines += ['[source]', 'native_revision = ' + bundle['native_revision'], 'exporter = ' + bundle['native_exporter']['path'],
              'exporter_sha256 = ' + bundle['native_exporter']['sha256'], 'map_revision = ' + bundle['map_revision'],
              'game = ' + entry['game'], 'map_sha256 = ' + entry['sha256'],
              'diagnostic = ' + diagnostic, 'diagnostic_sha256 = ' + digest, '']
    return '\n'.join(lines)


def write_text(bundle, path, raw_text):
    return write_checked_text(bundle, path, raw_text, format_text, parse_text, canonical)


def parse_text(text):
    parser = configparser.ConfigParser(interpolation=None, delimiters=('=',), empty_lines_in_values=False)
    parser.optionxform = str
    try:
        parser.read_string(text)
        if parser.defaults():
            raise ValueError('implicit DEFAULT values are not allowed')
        if set(parser.sections()) != {'trace', 'context', 'source'} | {'case ' + c for c in CASE_ORDER}:
            raise ValueError('missing or unknown text-trace sections')
        trace, context, source = (parser[s] for s in ('trace', 'context', 'source'))
        keys(trace, 'format bundle_format profile coordinate_frame')
        keys(context, 'map elevation start goal running_shoes move_speed flags variables')
        keys(source, 'native_revision exporter exporter_sha256 map_revision game map_sha256 diagnostic diagnostic_sha256')
        if trace['format'] != 'pokesim-native-route-text/1':
            raise ValueError('unsupported text-trace format')
        bundle = dict(format=trace['bundle_format'], profile=trace['profile'], coordinate_frame=trace['coordinate_frame'],
                      native_revision=source['native_revision'], map_revision=source['map_revision'],
                      native_exporter=dict(path=source['exporter'], sha256=source['exporter_sha256']),
                      maps=[dict(game=source['game'], name=context['map'], sha256=source['map_sha256'])],
                      context=dict(flags=read_json(context['flags']), variables=read_json(context['variables'])), cases=[])
        for name in CASE_ORDER:
            section = parser['case ' + name]
            keys(section, 'encounter wall_interruptions calls native declared physical failure')
            encounter = re.fullmatch(r'(before|after) tap (\d+); origin=(current_leg|may_precede_leg)', section['encounter'])
            if not encounter:
                raise ValueError('invalid encounter: ' + name)
            value = dict(start=parse_pose(context['start'], context), goal=parse_pose(context['goal'], context),
                         running_shoes=boolean(context['running_shoes']), move_speed=context['move_speed'],
                         phase=encounter[1], tap=int(encounter[2]), origin=encounter[3], interrupted_walls=int(section['wall_interruptions']))
            declared = [] if section['declared'] == 'none' else [parse_pose(p, context) for p in section['declared'].split('; ')]
            bundle['cases'].append(dict(id=name, input=value,
                calls=[parse_call(row, context) for row in section['calls'].splitlines() if row],
                notes=parse_notes(section['native'], context['map']), declared=declared,
                physical=parse_pose(section['physical'], context), failure=read_json(section['failure'])))
        return bundle
    except (configparser.Error, KeyError, TypeError) as error:
        raise ValueError('invalid text trace: ' + str(error)) from error


def read_text(path):
    return read_checked_text(path, parse_text, canonical)

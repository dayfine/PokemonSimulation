"""FRLG shortfall profile of the readable native-recovery trace format."""
import configparser
import copy
import json
from .consumer_source import read_json
from .frlg_native_recovery_replay import CASE_ORDER, PREFIX
from .native_recovery_capture import (keys, pose_text, parse_pose,
                                      read_checked_text, write_checked_text)


def canonical(bundle):
    result = copy.deepcopy(bundle)
    result['cases'].sort(key=lambda c: c['id'])
    for case in result['cases']:
        case['simulator_notes'] = []
        case['notes'] = [n for n in case['notes'] if n.startswith(PREFIX) or n.startswith('Route:')]
    return result


def step_text(step):
    return '{} {} {} -> {}'.format(step['direction'], step['tiles'], 'wall' if step['to_wall'] else 'open', pose_text(step['end']))


def parse_step(value, context):
    action, end = value.split(' -> ')
    direction, count, kind = action.split()
    if kind not in ('wall', 'open') or not count.isdecimal():
        raise ValueError('unsupported native leg')
    return dict(direction=direction, tiles=int(count), to_wall=kind == 'wall', warps=False, end=parse_pose(end, context))


def note_lines(notes):
    import re
    result = []
    for note in notes:
        if note.startswith(PREFIX):
            note = note[len(PREFIX):]
        elif note.startswith('Route:'):
            note = '! ' + note[len('Route: '):]
        else:
            continue
        note = re.sub(r'ViridianForest \((\d+), (\d+)\)', r'(\1,\2)', note)
        for index, line in enumerate(note.splitlines()):
            result.append('> ' + line.strip() if index else line)
    return result


def parse_notes(text):
    import re
    result = []
    for row in text.splitlines():
        if not row:
            continue
        if row.startswith('> '):
            if not result or not result[-1].startswith(PREFIX + 'plan from '):
                raise ValueError('leg without a native plan')
            result[-1] += '\n    ' + re.sub(r'\((\d+),(\d+)\)', r'ViridianForest (\1, \2)', row[2:])
        else:
            prefix, text = ('Route: ', row[2:]) if row.startswith('! ') else (PREFIX, row)
            result.append(prefix + re.sub(r'\((\d+),(\d+)\)', r'ViridianForest (\1, \2)', text))
    return result


def format_text(bundle, diagnostic, digest):
    source, entry = bundle['native_exporter'], bundle['maps'][0]
    lines = ['# Actual FRLG Forest native runs; TRUST cases are negative controls.',
             '# Pose (x,y) facing; ? is unreported. Source/replay facts are checked.',
             '# Calls: planned step | physical before -> after | outcome and facing passed in.',
             '# Native: > is a plan leg; ! is a native recovery diagnostic.', '',
             '[trace]', 'format = pokesim-native-route-text/1', 'bundle_format = ' + bundle['format'],
             'profile = ' + bundle['profile'], 'coordinate_frame = ' + bundle['coordinate_frame'], '',
             '[context]', 'map = ViridianForest', 'elevation = 3', 'start = (13,28) west',
             'flags = ' + json.dumps(bundle['context']['flags']), 'variables = ' + json.dumps(bundle['context']['variables']), '']
    for case in bundle['cases']:
        value = case['input']
        lines += ['[case ' + case['id'] + ']', 'shortfall = ' + str(value['shortfall']), 'policy = ' + value['policy'],
                  'goal = ' + pose_text(value['goal']), 'next_direction = ' + value['next_direction'],
                  'route = ' + '; '.join(step_text(s) for s in case['route']), 'calls =']
        for call in case['calls']:
            lines.append('    ' + step_text(call['step']) + ' | ' + pose_text(call['before']) + ' -> '
                         + pose_text(call['after']) + ' | ' + call['outcome'] + ' facing_in=' + (call['facing_input'] or '?'))
        lines += ['native ='] + ['    ' + n for n in note_lines(case['notes'])]
        lines += ['physical = ' + pose_text(case['physical']), 'signs_read = ' + str(case['signs_read']),
                  'violations = ' + json.dumps(case['violations']), 'failure = ' + json.dumps(case['failure']), '']
    lines += ['[source]', 'native_revision = ' + bundle['native_revision'], 'exporter = ' + source['path'],
              'exporter_sha256 = ' + source['sha256'], 'map_revision = ' + bundle['map_revision'], 'game = frlg',
              'map_sha256 = ' + entry['sha256'], 'diagnostic = ' + diagnostic, 'diagnostic_sha256 = ' + digest, '']
    return '\n'.join(lines)


def parse_text(text):
    parser = configparser.ConfigParser(interpolation=None, delimiters=('=',), empty_lines_in_values=False)
    parser.optionxform = str
    try:
        parser.read_string(text)
        if parser.defaults() or set(parser.sections()) != {'trace', 'context', 'source'} | {'case ' + n for n in CASE_ORDER}:
            raise ValueError('implicit defaults or missing/unknown Forest cases')
        trace, context, source = (parser[n] for n in ('trace', 'context', 'source'))
        keys(trace, 'format bundle_format profile coordinate_frame')
        keys(context, 'map elevation start flags variables')
        keys(source, 'native_revision exporter exporter_sha256 map_revision game map_sha256 diagnostic diagnostic_sha256')
        if trace['format'] != 'pokesim-native-route-text/1':
            raise ValueError('unsupported text version')
        bundle = dict(format=trace['bundle_format'], profile=trace['profile'], coordinate_frame=trace['coordinate_frame'],
            native_revision=source['native_revision'], native_exporter=dict(path=source['exporter'], sha256=source['exporter_sha256']),
            map_revision=source['map_revision'], maps=[dict(game=source['game'], name=context['map'], sha256=source['map_sha256'])],
            context=dict(flags=read_json(context['flags']), variables=read_json(context['variables'])), cases=[])
        for name in CASE_ORDER:
            section = parser['case ' + name]
            keys(section, 'shortfall policy goal next_direction route calls native physical signs_read violations failure')
            value = dict(start=parse_pose(context['start'], context), goal=parse_pose(section['goal'], context),
                shortfall=int(section['shortfall']), policy=section['policy'], next_direction=section['next_direction'])
            calls = []
            for row in section['calls'].splitlines():
                if not row:
                    continue
                step, motion, report = row.split(' | ')
                before, after = motion.split(' -> ')
                outcome, facing = report.split(' facing_in=')
                calls.append(dict(step=parse_step(step, context), before=parse_pose(before, context), after=parse_pose(after, context),
                                  outcome=outcome, facing_input=None if facing == '?' else facing))
            bundle['cases'].append(dict(id=name, input=value, route=[parse_step(s, context) for s in section['route'].split('; ')],
                calls=calls, notes=parse_notes(section['native']), simulator_notes=[], physical=parse_pose(section['physical'], context),
                signs_read=int(section['signs_read']), violations=read_json(section['violations']), failure=read_json(section['failure'])))
        return bundle
    except (configparser.Error, KeyError, TypeError) as error:
        raise ValueError('invalid readable Forest capture: ' + str(error)) from error


def write_text(bundle, path, raw_text):
    return write_checked_text(bundle, path, raw_text, format_text, parse_text, canonical)


def read_text(path):
    return read_checked_text(path, parse_text, canonical)

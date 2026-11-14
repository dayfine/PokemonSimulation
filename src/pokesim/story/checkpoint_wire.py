"""Read the shared story records without executing any action.

    PYTHONPATH=src python3 -m pokesim.story.checkpoint_wire checkpoint.json

read_grid_pose, read_declared_pose, read_story_step and read_story_checkpoint
read the records Arduino-Source's native reader (Pokemon_StoryStepJson) reads: a
step names an action and its typed args, checked against the action's spec.
data/story/wire-conformance.json holds the cases both readers share.

read_pose, read_step and read_checkpoint read the older authored record (poses
with certainty/where, per-kind step fields, sections and notes) that the
authored plans and the replay still use.

Entry requirements, tracked state, save/failure/handoff policy and game bindings
belong to the plan envelope; these records alone do not establish a runnable
plan or observations.
"""

import argparse
import json
from pathlib import Path

from pokesim.formats.contract_format import json_text

KINDS = ('new_game', 'options', 'route', 'legs', 'step', 'talk', 'answer',
         'scene', 'battle', 'train', 'heal', 'shop', 'save', 'ready', 'game_action')
DIRECTIONS = ('north', 'east', 'south', 'west')
CERTAINTIES = ('tile', 'column', 'row', 'set', 'unknown')


def fields(value, allowed):
    if not isinstance(value, dict):
        raise ValueError('expected record')
    unsupported = set(value) - set(allowed)
    if unsupported:
        raise ValueError('unsupported field: ' + str(min(unsupported, key=str)))
    return value


def field(value, name, reader):
    """Read required field `name`, naming it when absent or malformed."""
    if name not in value:
        raise ValueError('missing field: ' + name)
    try:
        return reader(value[name])
    except ValueError as error:
        raise ValueError(name + ': ' + str(error)) from error


def text(value):
    if not isinstance(value, str):
        raise ValueError('expected string')
    return value


def choice(value, values):
    if text(value) not in values:
        raise ValueError('unsupported value: ' + value)
    return value


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('integer outside native range')
    return value


def array(value):
    if not isinstance(value, list):
        raise ValueError('expected array')
    return value


def boolean(value):
    if type(value) is not bool:
        raise ValueError('expected boolean')
    return value


def read_args(value):
    """A step's args: flags, whole numbers and words by name, as the step's
    action declares them in the game's C++ (StoryArgSpec); this reader checks
    only the value types."""
    if not isinstance(value, dict):
        raise ValueError('expected args object')
    result = {}
    for key, item in value.items():
        if type(item) is int:
            integer(item, -9223372036854775808, 9223372036854775807)
        elif type(item) is not bool and not isinstance(item, str):
            raise ValueError('arg is not a flag, whole number or word: ' + key)
        result[key] = item
    return result


def read_notes(root, result):
    """Copy non-empty `notes` paragraphs; no executor reads them."""
    notes = [text(v) for v in array(root.get('notes', []))]
    if notes:
        result['notes'] = notes


def read_pose(value):
    root = fields(value, ('map', 'certainty', 'where'))
    result = dict(map=text(root['map']), certainty=choice(root['certainty'], CERTAINTIES))
    where = fields(root['where'], ('kind', 'tiles', 'facing'))
    kind = choice(where['kind'], ('unknown', 'tiles'))
    if kind == 'unknown':
        if set(where) != {'kind'}:
            raise ValueError('unknown position has extra fields')
        result['where'] = dict(kind='unknown')
    else:
        tiles = []
        for tile in array(where['tiles']):
            if len(array(tile)) != 2:
                raise ValueError('tile needs two coordinates')
            tiles.append([integer(n, -2147483648, 2147483647) for n in tile])
        result['where'] = dict(kind='tiles', tiles=tiles)
        if 'facing' in where:
            result['where']['facing'] = choice(where['facing'], DIRECTIONS)
    return result


def read_step(value):
    root = fields(value, ('id', 'kind', 'why', 'target', 'direction', 'legs', 'fight_wild',
                         'yes', 'may_lose', 'battles', 'items', 'variant', 'args', 'skip_if', 'declared_after',
                         'once_per_save', 'notes'))
    result = dict(id=text(root['id']), kind=choice(root['kind'], KINDS))
    if not result['id']:
        raise ValueError('empty story step id')
    for key in ('why', 'variant'):
        if key in root and text(root[key]):
            result[key] = root[key]
    for key in ('target', 'declared_after'):
        if key in root:
            result[key] = read_pose(root[key])
    direction = choice(root.get('direction', 'north'), DIRECTIONS)
    if direction != 'north':
        result['direction'] = direction
    for key, default in (('fight_wild', False), ('yes', True), ('may_lose', False), ('once_per_save', False)):
        flag = root.get(key, default)
        if type(flag) is not bool:
            raise ValueError('expected boolean: ' + key)
        if flag != default:
            result[key] = flag
    battles = integer(root.get('battles', 0), 0, 9223372036854775807)
    if battles:
        result['battles'] = battles
    legs = []
    for leg in array(root.get('legs', [])):
        fields(leg, ('direction', 'tiles'))
        legs.append(dict(direction=choice(leg['direction'], DIRECTIONS),
                         tiles=integer(leg['tiles'], -2147483648, 2147483647)))
    if legs:
        result['legs'] = legs
    items = []
    for item in array(root.get('items', [])):
        fields(item, ('item', 'quantity'))
        items.append(dict(item=text(item['item']), quantity=integer(item['quantity'], 0, 9223372036854775807)))
    if items:
        result['items'] = items
    args = read_args(root.get('args', {}))
    if args:
        result['args'] = args
    skip = [text(v) for v in array(root.get('skip_if', []))]
    if skip:
        result['skip_if'] = skip
    read_notes(root, result)
    return result


def read_section(value):
    root = fields(value, ('id', 'title', 'notes', 'events'))
    result = dict(id=text(root['id']), title=text(root['title']))
    if not result['id']:
        raise ValueError('empty section id')
    read_notes(root, result)
    result['events'] = [read_step(value) for value in array(root['events'])]
    if not result['events']:
        raise ValueError('section has no events: ' + result['id'])
    return result


def read_checkpoint(value):
    """Read `events`, or named `sections` of events (exactly one of the two)."""
    root = fields(value, ('id', 'title', 'notes', 'start', 'events', 'sections'))
    result = dict(id=text(root['id']), title=text(root['title']))
    if not result['id']:
        raise ValueError('empty checkpoint id')
    read_notes(root, result)
    if 'start' in root:
        result['start'] = read_pose(root['start'])
    if ('events' in root) == ('sections' in root):
        raise ValueError('a checkpoint has events or sections, not both or neither')
    if 'events' in root:
        result['events'] = [read_step(value) for value in array(root['events'])]
        steps = result['events']
    else:
        result['sections'] = [read_section(value) for value in array(root['sections'])]
        if not result['sections']:
            raise ValueError('no sections')
        ids = [section['id'] for section in result['sections']]
        if len(ids) != len(set(ids)):
            raise ValueError('duplicate story section ids')
        steps = [step for section in result['sections'] for step in section['events']]
    names = [step['id'] for step in steps]
    if len(names) != len(set(names)):
        raise ValueError('duplicate story event ids')
    return result


# The records Arduino-Source's Pokemon_StoryStepJson reads.

ARG_TYPES = ('boolean', 'integer', 'word', 'direction', 'grid_pose', 'legs', 'words', 'items',
             'integer_rows', 'timed_legs')
PHASES = ('testing', 'verification', 'reproduction')
INT_MIN, INT_MAX = -2147483648, 2147483647
INT64_MIN, INT64_MAX = -9223372036854775808, 9223372036854775807


def required(key, type_):
    return dict(key=key, type=type_, required=True)


def optional(key, type_, fallback=None):
    spec = dict(key=key, type=type_, required=False)
    if fallback is not None:
        spec['fallback'] = fallback
    return spec


# Pokemon_BuiltinStoryActions.cpp: each kind's usual way; a kind's first
# action is its default.
BUILTIN_ACTIONS = (
    dict(kind='route', name='route', args=[required('target', 'grid_pose'), optional('fight_wild', 'boolean', False)]),
    dict(kind='ready', name='ready', args=[required('target', 'grid_pose')]),
    dict(kind='legs', name='legs', args=[required('legs', 'legs'), optional('fight_wild', 'boolean', False)]),
    dict(kind='step', name='face', args=[required('direction', 'direction')]),
    dict(kind='answer', name='answer', args=[optional('yes', 'boolean', True)]),
    dict(kind='battle', name='fight', args=[optional('may_lose', 'boolean', False)]),
    dict(kind='train', name='train', args=[required('battles', 'integer')]),
    dict(kind='shop', name='shop', args=[required('items', 'items')]),
)


def read_tiles(value):
    tiles = []
    for tile in array(value):
        if len(array(tile)) != 2:
            raise ValueError('a tile needs two coordinates')
        tiles.append([integer(n, INT_MIN, INT_MAX) for n in tile])
    return tiles


def read_grid_pose(value):
    """{"map", "tiles"?, "facing"?}; no tiles reads as none (any tile, or a zone game)."""
    root = fields(value, ('map', 'tiles', 'facing'))
    result = dict(map=field(root, 'map', text), tiles=[])
    if 'tiles' in root:
        result['tiles'] = field(root, 'tiles', read_tiles)
    if 'facing' in root:
        result['facing'] = field(root, 'facing', lambda item: choice(item, DIRECTIONS))
    return result


def read_declared_pose(value):
    """A tile pose (grid pose with "map") or a zone one ({"place", "spot"?, "heading"?})."""
    if not isinstance(value, dict):
        raise ValueError('expected declared pose object')
    if ('map' in value) == ('place' in value):
        raise ValueError('a declared pose has a "map" or a "place", not both or neither')
    if 'map' in value:
        return read_grid_pose(value)
    root = fields(value, ('place', 'spot', 'heading'))
    result = dict(place=field(root, 'place', text))
    if 'spot' in root:
        result['spot'] = field(root, 'spot', text)
    if 'heading' in root:
        result['heading'] = field(root, 'heading', lambda item: integer(item, INT_MIN, INT_MAX))
    return result


def read_strings(value):
    return [text(v) for v in array(value)]


def read_items(value):
    items = []
    for item in array(value):
        fields(item, ('item', 'quantity'))
        items.append(dict(item=field(item, 'item', text),
                          quantity=field(item, 'quantity', lambda number: integer(number, 0, INT64_MAX))))
    return items


def read_arg(value, type_):
    """One arg's value read as `type_` (StoryArgType)."""
    if type_ == 'boolean':
        if type(value) is not bool:
            raise ValueError('expected boolean')
        return value
    if type_ == 'integer':
        return integer(value, INT64_MIN, INT64_MAX)
    if type_ == 'word':
        return text(value)
    if type_ == 'direction':
        return choice(value, DIRECTIONS)
    if type_ == 'grid_pose':
        return read_grid_pose(value)
    if type_ == 'legs':
        legs = []
        for leg in array(value):
            fields(leg, ('direction', 'tiles'))
            legs.append(dict(direction=field(leg, 'direction', lambda item: choice(item, DIRECTIONS)),
                             tiles=field(leg, 'tiles', lambda number: integer(number, INT_MIN, INT_MAX))))
        return legs
    if type_ == 'words':
        return read_strings(value)
    if type_ == 'items':
        return read_items(value)
    if type_ == 'integer_rows':
        return [[integer(n, INT64_MIN, INT64_MAX) for n in array(row)] for row in array(value)]
    if type_ == 'timed_legs':
        legs = []
        for leg in array(value):
            if len(array(leg)) != 2:
                raise ValueError('a timed leg is [turn degrees, ms]')
            legs.append([integer(n, INT_MIN, INT_MAX) for n in leg])
        return legs
    raise ValueError('unsupported story arg type: ' + str(type_))


def read_action_specs(value):
    """Actions a game adds to the built-in ones: [{"kind", "name", "args": [{"key",
    "type", "required"?, "fallback"?}]}], the fallbacks read as their types."""
    actions = []
    for action in array(value):
        fields(action, ('kind', 'name', 'args'))
        args = []
        for arg in field(action, 'args', array):
            fields(arg, ('key', 'type', 'required', 'fallback'))
            spec = dict(key=field(arg, 'key', text),
                        type=field(arg, 'type', lambda item: choice(item, ARG_TYPES)),
                        required=field(arg, 'required', boolean) if 'required' in arg else False)
            if spec['required'] and 'fallback' in arg:
                raise ValueError('fallback: required argument cannot have a fallback: ' + spec['key'])
            if 'fallback' in arg:
                spec['fallback'] = field(arg, 'fallback', lambda item: read_arg(item, spec['type']))
            args.append(spec)
        actions.append(dict(kind=field(action, 'kind', lambda item: choice(item, KINDS)),
                            name=field(action, 'name', text), args=args))
    return tuple(BUILTIN_ACTIONS) + tuple(actions)


def find_action(actions, kind, name):
    """The action of `kind` named `name`; for no name, the kind's first."""
    for action in actions:
        if action['kind'] == kind and (not name or action['name'] == name):
            return action
    return None


def read_step_args(value, action):
    """The args read against `action`'s spec, with its fallbacks filled in."""
    specs = {arg['key']: arg for arg in (action['args'] if action else [])}
    if not isinstance(value, dict):
        raise ValueError('expected args object')
    result = {}
    for key, item in value.items():
        if key not in specs:
            raise ValueError('unknown argument: ' + key)
        try:
            result[key] = read_arg(item, specs[key]['type'])
        except ValueError as error:
            raise ValueError('argument ' + key + ': ' + str(error)) from error
    for key, spec in specs.items():
        if spec['required'] and key not in result:
            raise ValueError('missing argument: ' + key)
        if key not in result and 'fallback' in spec:
            result[key] = spec['fallback']
    return dict(sorted(result.items()))


def read_story_step(value, actions=BUILTIN_ACTIONS):
    """A step: its action among `actions` (the kind's default when it names none),
    its args read against that action's spec. Empty why, action and skip_if and a
    false once_per_save read as absent."""
    root = fields(value, ('id', 'kind', 'why', 'action', 'args', 'skip_if', 'declared_after', 'once_per_save'))
    result = dict(id=field(root, 'id', text), kind=field(root, 'kind', lambda item: choice(item, KINDS)))
    if not result['id']:
        raise ValueError('empty story step id')
    for key in ('why', 'action'):
        if key in root and field(root, key, text):
            result[key] = root[key]
    name = result.get('action', '')
    if result['kind'] == 'game_action' and not name:
        raise ValueError('game_action step names no action: ' + result['id'])
    action = find_action(actions, result['kind'], name)
    if action is None and name:
        raise ValueError('action: unknown action: ' + name)
    try:
        args = read_step_args(root.get('args', {}), action)
    except ValueError as error:
        raise ValueError('args: ' + str(error)) from error
    if args:
        result['args'] = args
    skip = field(root, 'skip_if', read_strings) if 'skip_if' in root else []
    if skip:
        result['skip_if'] = skip
    if 'declared_after' in root:
        result['declared_after'] = field(root, 'declared_after', read_declared_pose)
    once = field(root, 'once_per_save', boolean) if 'once_per_save' in root else False
    if once:
        result['once_per_save'] = True
    return result


def read_metadata(value):
    root = fields(value, ('phase', 'verified', 'source', 'postconditions'))
    result = {}
    if 'phase' in root:
        result['phase'] = field(root, 'phase', lambda item: choice(item, PHASES))
    if 'verified' in root:
        verified = field(root, 'verified', lambda item: fields(item, ('steps_hash', 'build', 'date', 'runs')))
        result['verified'] = {'steps_hash': field(verified, 'steps_hash', text)}
        for key in ('build', 'date', 'runs'):
            if key in verified:
                result['verified'][key] = field(verified, key, text)
    if 'source' in root:
        result['source'] = field(root, 'source', text)
    if 'postconditions' in root:
        post = field(root, 'postconditions', lambda item: fields(item, ('position', 'items', 'flags')))
        result['postconditions'] = {}
        if 'position' in post:
            result['postconditions']['position'] = field(post, 'position', read_grid_pose)
        if 'items' in post:
            result['postconditions']['items'] = field(post, 'items', read_items)
        if 'flags' in post:
            result['postconditions']['flags'] = field(post, 'flags', read_strings)
    return result


def read_story_checkpoint(value, actions=BUILTIN_ACTIONS):
    """A checkpoint's id, title, start, events (unique ids) and metadata."""
    root = fields(value, ('id', 'title', 'start', 'events', 'metadata'))
    result = dict(id=field(root, 'id', text), title=field(root, 'title', text))
    if not result['id']:
        raise ValueError('empty checkpoint id')
    if 'start' in root:
        result['start'] = field(root, 'start', read_declared_pose)
    events = field(root, 'events', array)
    result['events'] = [read_story_step(event, actions) for event in events]
    names = [step['id'] for step in result['events']]
    if len(names) != len(set(names)):
        raise ValueError('duplicate story event ids')
    if 'metadata' in root:
        result['metadata'] = field(root, 'metadata', read_metadata)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('checkpoint', type=Path)
    args = parser.parse_args()
    try:
        value = read_checkpoint(json.loads(args.checkpoint.read_text()))
    except (ValueError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    print(json_text(value), end='')


if __name__ == '__main__':
    main()

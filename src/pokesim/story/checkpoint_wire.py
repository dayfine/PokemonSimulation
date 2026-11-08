"""Read the shared native checkpoint wire records without executing any action.

    PYTHONPATH=src python3 -m pokesim.story.checkpoint_wire checkpoint.json

The common record preserves all StoryStep/TilePose fields. Entry requirements,
tracked state, save/failure/handoff policy and game bindings belong to the plan
envelope; these records alone do not establish a runnable plan or observations.
"""

import argparse
import json
from pathlib import Path

KINDS = ('new_game', 'options', 'route', 'legs', 'step', 'talk', 'answer',
         'scene', 'battle', 'train', 'heal', 'shop', 'save', 'ready', 'game_action')
DIRECTIONS = ('north', 'east', 'south', 'west')
CERTAINTIES = ('tile', 'column', 'row', 'set', 'unknown')


def fields(value, allowed):
    if not isinstance(value, dict) or set(value) - set(allowed):
        raise ValueError('expected record with only fields: ' + ', '.join(allowed))
    return value


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
                         'yes', 'may_lose', 'battles', 'items', 'variant', 'skip_if', 'declared_after'))
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
    for key, default in (('fight_wild', False), ('yes', True), ('may_lose', False)):
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
    skip = [text(v) for v in array(root.get('skip_if', []))]
    if skip:
        result['skip_if'] = skip
    return result


def read_checkpoint(value):
    root = fields(value, ('id', 'title', 'start', 'events'))
    result = dict(id=text(root['id']), title=text(root['title']))
    if not result['id']:
        raise ValueError('empty checkpoint id')
    if 'start' in root:
        result['start'] = read_pose(root['start'])
    result['events'] = [read_step(value) for value in array(root['events'])]
    names = [step['id'] for step in result['events']]
    if len(names) != len(set(names)):
        raise ValueError('duplicate story event ids')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('checkpoint', type=Path)
    args = parser.parse_args()
    try:
        value = read_checkpoint(json.loads(args.checkpoint.read_text()))
    except (ValueError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    print(json.dumps(value, indent=2))


if __name__ == '__main__':
    main()

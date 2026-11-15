"""Convert FRLG authored plans from the older checkpoint record to v2.

    python3 -I tools/frlg_plans_v2.py data/story/frlg-authored/*.plan.json

One-off: rewrites each plan in place. The older record spells a step with
per-kind fields and a `variant` (for a game_action, its action name and words
such as "mart CeruleanCity_Mart budget=3000 potion=5"); v2 names an `action`
and typed `args` (src/pokesim/story/checkpoint_wire.py). Poses lose
`certainty`/`where`; `sections` are flattened into `events`, their titles
dropped; `notes` move to the envelope's `execution.notes`, keyed by step id or
"checkpoint", as Arduino-Source's FRLG plans keep them (a section's notes go to
its first step). Each converted checkpoint is read back with read_story_checkpoint
against data/story/frlg-authored/frlg-actions.json. Anything without a v2
spelling raises instead of being guessed.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from pokesim.formats.contract_format import json_text  # noqa: E402
from pokesim.story.authored_checkpoint import frlg_actions  # noqa: E402
from pokesim.story.checkpoint_wire import read_checkpoint, read_story_checkpoint  # noqa: E402

# Step fields each kind may carry besides id, kind, why, variant, skip_if,
# declared_after, once_per_save and notes.
KIND_FIELDS = {
    'route': {'target', 'fight_wild'},
    'ready': {'target'},
    'legs': {'legs', 'fight_wild'},
    'step': {'direction'},
    'answer': {'yes'},
    'battle': {'may_lose'},
    'train': {'battles'},
    'shop': {'items'},
}
COMMON_FIELDS = {'id', 'kind', 'why', 'variant', 'args', 'skip_if', 'declared_after', 'once_per_save', 'notes'}

# A game_action variant's leading words, before its key=value pairs.
POSITIONAL = {'mart': ('map',), 'teach': ('item', 'move'), 'pc': ('do',), 'fossil': ('fossil',),
              'capture': ('species',)}
# Bare words that are flags.
FLAGS = {'pc': ('if_present',)}
NUMBER = re.compile(r'-?[0-9]+\Z')


def pose(value):
    """{certainty: tile, map, where: {kind: tiles, tiles, facing?}} -> {map, tiles, facing?}."""
    where = value['where']
    if value['certainty'] != 'tile' or where['kind'] != 'tiles':
        raise ValueError('no v2 pose for certainty {} / where {}'.format(value['certainty'], where['kind']))
    result = dict(map=value['map'], tiles=where['tiles'])
    if 'facing' in where:
        result['facing'] = where['facing']
    return result


def word_value(text):
    return int(text) if NUMBER.match(text) else text


def game_args(step):
    """A game_action's action name and args from its variant words and fields."""
    words = step['variant'].split()
    action, rest = words[0], words[1:]
    args = {}
    positional = POSITIONAL.get(action, ())
    if len(rest) < len(positional) or any('=' in word for word in rest[:len(positional)]):
        raise ValueError('{}: {} needs {}'.format(step['id'], action, ' '.join(positional)))
    for key, word in zip(positional, rest):
        args[key] = word
    items = []
    for word in rest[len(positional):]:
        if '=' not in word:
            if word not in FLAGS.get(action, ()):
                raise ValueError('{}: no v2 arg for word {!r} of {}'.format(step['id'], word, action))
            args[word] = True
            continue
        key, value = word.split('=', 1)
        if action == 'mart' and key not in ('budget', 'floor'):
            items.append(dict(item=key, quantity=int(value)))
        else:
            args[key] = word_value(value)
    if items or 'items' in step:
        args['items'] = items + step.get('items', [])
    if 'direction' in step:
        args['direction'] = step['direction']
    if 'target' in step:
        if action != 'grind':
            raise ValueError('{}: no v2 arg for the target of {}'.format(step['id'], action))
        args['nurse'] = pose(step['target'])
    if step.get('args'):
        args.update(step['args'])
    return action, args


def step_args(step):
    kind = step['kind']
    args = {}
    if 'target' in step:
        args['target'] = pose(step['target'])
    if 'legs' in step:
        args['legs'] = step['legs']
    if kind == 'step':
        args['direction'] = step.get('direction', 'north')
    for key, default in (('fight_wild', False), ('yes', True), ('may_lose', False)):
        if key in step and step[key] != default:
            args[key] = step[key]
    if 'battles' in step:
        args['battles'] = step['battles']
    if 'items' in step:
        args['items'] = step['items']
    if step.get('args'):
        raise ValueError('{}: args on a {} step'.format(step['id'], kind))
    return args


def convert_step(step):
    kind = step['kind']
    extra = set(step) - COMMON_FIELDS - KIND_FIELDS.get(kind, set())
    if kind == 'game_action':
        extra -= {'target', 'direction', 'items'}
    if extra:
        raise ValueError('{}: no v2 field for {} on a {} step'.format(step['id'], ', '.join(sorted(extra)), kind))
    result = dict(id=step['id'], kind=kind)
    if kind == 'game_action':
        action, args = game_args(step)
    else:
        action, args = step.get('variant', ''), step_args(step)
    if action:
        result['action'] = action
    if args:
        result['args'] = args
    if step.get('skip_if'):
        result['skip_if'] = step['skip_if']
    if 'declared_after' in step:
        result['declared_after'] = pose(step['declared_after'])
    if step.get('once_per_save'):
        result['once_per_save'] = True
    if step.get('why'):
        result['why'] = step['why']
    return result


def convert_plan(plan, actions=None):
    """The plan with its checkpoint in v2 and its notes in execution.notes."""
    old = plan['checkpoint']
    read_checkpoint(old)
    notes = {}
    if old.get('notes'):
        notes['checkpoint'] = list(old['notes'])
    steps = []
    for section in old.get('sections', [dict(events=old.get('events', []))]):
        for index, step in enumerate(section['events']):
            lines = (section.get('notes', []) if index == 0 else []) + step.get('notes', [])
            if lines:
                notes[step['id']] = lines
            steps.append(convert_step(step))
    checkpoint = dict(id=old['id'], title=old['title'])
    if 'start' in old:
        checkpoint['start'] = pose(old['start'])
    checkpoint['events'] = steps
    read_story_checkpoint(checkpoint, frlg_actions() if actions is None else actions)
    execution = dict(plan['execution'])
    if notes:
        execution['notes'] = notes
    return dict(format=plan['format'], game=plan['game'], checkpoint=checkpoint, execution=execution)


def main(paths):
    actions = frlg_actions()
    for path in map(Path, paths):
        plan = json.loads(path.read_text())
        try:
            converted = convert_plan(plan, actions)
        except (ValueError, KeyError) as error:
            raise SystemExit('{}: {}'.format(path, error))
        path.write_text(json_text(converted))


if __name__ == '__main__':
    main(sys.argv[1:])

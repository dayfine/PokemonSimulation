"""Read a small authored checkpoint; execution settings are not observed state.

An FRLG checkpoint is the v2 record (read_story_checkpoint) with FRLG's
actions, data/story/frlg-authored/frlg-actions.json; BDSP's is still the older
record (read_checkpoint).
"""

import copy
import json
from pathlib import Path

from .checkpoint_wire import read_action_specs, read_checkpoint, read_story_checkpoint
from .replay_handlers import exact

FRLG_ACTIONS_PATH = Path(__file__).resolve().parents[3] / 'data/story/frlg-authored/frlg-actions.json'


FRLG_HANDOFFS = ('none', 'sid_helper', 'starter_rng', 'gift_rng')


def frlg_actions():
    """The built-in actions plus FRLG's (data/story/frlg-authored/frlg-actions.json)."""
    return read_action_specs(json.loads(FRLG_ACTIONS_PATH.read_text())['actions'])


def read_frlg_notes(notes, checkpoint):
    """Notes keyed by "checkpoint" or a step's id, each a list of lines; no executor reads them."""
    if not isinstance(notes, dict):
        raise ValueError('FRLG notes must be an object')
    ids = {'checkpoint'} | {step['id'] for step in checkpoint['events']}
    for key, lines in notes.items():
        if key not in ids:
            raise ValueError('notes for unknown step: ' + key)
        if not isinstance(lines, list) or not all(isinstance(line, str) for line in lines):
            raise ValueError('FRLG notes must be lists of strings: ' + key)


def read_frlg_execution(execution):
    """FRLG's save menu, plus supplies, live start and handoff when not a new game's."""
    if not isinstance(execution, dict) or 'menu' not in execution or (
            set(execution) - {'menu', 'supplies', 'live_start', 'handoff', 'notes'}):
        raise ValueError('FRLG execution needs menu and allows supplies, live_start, handoff, notes')
    if execution['menu'] not in ('before_pokemon', 'before_pokedex', 'full'):
        raise ValueError('unsupported authored checkpoint menu')
    supplies = execution.get('supplies', {})
    if not isinstance(supplies, dict) or set(supplies) - {'potions', 'antidotes', 'parlyz_heals', 'lead'}:
        raise ValueError('unsupported FRLG supplies')
    for key in ('potions', 'antidotes', 'parlyz_heals'):
        if key in supplies and (type(supplies[key]) is not int or not -2147483648 <= supplies[key] <= 2147483647):
            raise ValueError('FRLG supply count outside native int: ' + key)
    if supplies.get('lead', 'after_brock') != 'after_brock':
        raise ValueError('unsupported FRLG lead')
    if type(execution.get('live_start', False)) is not bool:
        raise ValueError('FRLG live_start must be boolean')
    if execution.get('handoff', 'none') not in FRLG_HANDOFFS:
        raise ValueError('unsupported FRLG handoff')


def read_authored_checkpoint(value):
    """Reject unsupported fields/game/menu before binding an authored checkpoint."""
    exact(value, 'format game checkpoint execution')
    if value['format'] != 'pokesim-authored-checkpoint/1' or value['game'] not in ('frlg', 'bdsp'):
        raise ValueError('unsupported authored checkpoint format/game')
    if value['game'] == 'frlg':
        read_frlg_execution(value['execution'])
        checkpoint = read_story_checkpoint(value['checkpoint'], frlg_actions())
        read_frlg_notes(value['execution'].get('notes', {}), checkpoint)
    else:
        execution = exact(value['execution'], 'on_failure saves_in')
        if (execution['on_failure'] not in ('reload_and_retry', 'stop')
                or not isinstance(execution['saves_in'], str)
                or (execution['on_failure'] == 'reload_and_retry') != bool(execution['saves_in'])):
            raise ValueError('BDSP needs a save-card guard exactly when saving/retrying')
        read_checkpoint(value['checkpoint'])
    return copy.deepcopy(value)

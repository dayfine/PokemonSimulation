"""Read a small authored checkpoint; execution settings are not observed state."""

import copy
from .checkpoint_wire import read_checkpoint
from .replay_handlers import exact


def read_authored_checkpoint(value):
    """Reject unsupported fields/game/menu before binding an authored checkpoint."""
    exact(value, 'format game checkpoint execution')
    if value['format'] != 'pokesim-authored-checkpoint/1' or value['game'] not in ('frlg', 'bdsp'):
        raise ValueError('unsupported authored checkpoint format/game')
    if value['game'] == 'frlg':
        execution = exact(value['execution'], 'menu')
        if execution['menu'] not in ('before_pokemon', 'before_pokedex', 'full'):
            raise ValueError('unsupported authored checkpoint menu')
    else:
        execution = exact(value['execution'], 'on_failure saves_in')
        if (execution['on_failure'] not in ('reload_and_retry', 'stop')
                or not isinstance(execution['saves_in'], str)
                or (execution['on_failure'] == 'reload_and_retry') != bool(execution['saves_in'])):
            raise ValueError('BDSP needs a save-card guard exactly when saving/retrying')
    read_checkpoint(value['checkpoint'])
    return copy.deepcopy(value)

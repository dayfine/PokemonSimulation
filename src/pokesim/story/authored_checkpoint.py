"""Read a small authored checkpoint; execution settings are not observed state."""

import copy
from .checkpoint_wire import read_checkpoint
from .replay_handlers import exact


def read_authored_checkpoint(value):
    """Reject unsupported fields/game/menu before binding an authored checkpoint."""
    exact(value, 'format game checkpoint execution')
    if value['format'] != 'pokesim-authored-checkpoint/1' or value['game'] != 'frlg':
        raise ValueError('unsupported authored checkpoint format/game')
    execution = exact(value['execution'], 'menu')
    if execution['menu'] not in ('before_pokemon', 'before_pokedex', 'full'):
        raise ValueError('unsupported authored checkpoint menu')
    read_checkpoint(value['checkpoint'])
    return copy.deepcopy(value)

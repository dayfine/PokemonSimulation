"""Canonical symbols for pokesim-runtime-map/1.

Validation, routing, drawing and builder helpers share this table. The older
pokenav-map/1 text-grid legend is a separate format: its digits mean forced
movement, whereas these digits close one side of a stationary tile.
"""

from types import MappingProxyType
from typing import NamedTuple, Optional

from pokesim.grid.geometry import Direction
from pokesim.grid.maps.model import LEDGE_DIRECTION, Behavior, Cell


class TileSymbol(NamedTuple):
    blocked: bool = False
    behavior: Behavior = Behavior.NONE
    closed_side: Optional[Direction] = None


SYMBOLS = MappingProxyType({
    '#': TileSymbol(blocked=True),
    '.': TileSymbol(),
    '~': TileSymbol(behavior=Behavior.TALL_GRASS),
    'w': TileSymbol(blocked=True, behavior=Behavior.WATER),
    '^': TileSymbol(behavior=Behavior.LEDGE_NORTH),
    'v': TileSymbol(behavior=Behavior.LEDGE_SOUTH),
    '<': TileSymbol(behavior=Behavior.LEDGE_WEST),
    '>': TileSymbol(behavior=Behavior.LEDGE_EAST),
    'D': TileSymbol(behavior=Behavior.DOOR),
    'S': TileSymbol(blocked=True, behavior=Behavior.SIGN),
    ' ': TileSymbol(behavior=Behavior.UNKNOWN),
    'u': TileSymbol(behavior=Behavior.FORCED_NORTH),
    'd': TileSymbol(behavior=Behavior.FORCED_SOUTH),
    'l': TileSymbol(behavior=Behavior.FORCED_WEST),
    'r': TileSymbol(behavior=Behavior.FORCED_EAST),
    'o': TileSymbol(behavior=Behavior.STOP_SPIN),
    'H': TileSymbol(behavior=Behavior.FALL_WARP),
    'B': TileSymbol(behavior=Behavior.STRENGTH_BUTTON),
    #   A gate: a barrier the story opens (Silph Co. Card Key door, Pokemon
    #   Mansion switch barrier). Closed to a consumer that does not resolve the
    #   map's `gates` table against its story state.
    'G': TileSymbol(blocked=True),
    '8': TileSymbol(closed_side=Direction.NORTH),
    '2': TileSymbol(closed_side=Direction.SOUTH),
    '4': TileSymbol(closed_side=Direction.WEST),
    '6': TileSymbol(closed_side=Direction.EAST),
})
GLYPHS = frozenset(SYMBOLS)
CLOSED_SIDES = MappingProxyType({glyph: spec.closed_side for glyph, spec in SYMBOLS.items()
                                if spec.closed_side is not None})
LEDGE_GLYPHS = MappingProxyType({LEDGE_DIRECTION[spec.behavior]: glyph
                                for glyph, spec in SYMBOLS.items() if spec.behavior in LEDGE_DIRECTION})


def cell_for(glyph, elevation=0):
    spec = SYMBOLS[glyph]
    return Cell(spec.blocked, elevation, spec.behavior)

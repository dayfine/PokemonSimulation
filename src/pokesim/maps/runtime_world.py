"""Predict movement across explicit runtime-map links; never confirm execution.

FRLG warp entry/arrival follows the native OverworldMap/OverworldRoute contract.
BDSP links lack an arrival policy in the current pack and remain unresolved.
Unloaded/unknown exits stay Warp/Edge, never become wall anchors. Coordinate
translation uses explicit local edge offsets, never overlapping crop rectangles.
"""
import copy
from dataclasses import dataclass

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.model import Behavior
from pokesim.grid.maps.schema import Connection
from pokesim.grid.maps.world import Place, World
from pokesim.grid.movement import Blocked, BlockReason, Edge, Moved, Warp, Warped, WorldState
from .runtime_symbols import CLOSED_SIDES


@dataclass(frozen=True)
class ArrivalContract:
    """Reviewed BDSP arrival for an existing link, with mandatory evidence.

    This does not add/repair terrain or invent missing mine/house links.
    Destination is a runtime-local stable tile, including any scripted walk-out.
    """
    source: Place
    destination: Place
    enter_direction: Direction
    facing: Direction
    evidence: str


class RuntimeWorld(World):
    """A single game's LocalMaps, preserving their context and safety exclusions.

    Use shared world_step/shortest_path with this world. The result is a model
    prediction. Observation/recovery belongs to transition_state, not routing.
    """

    def __init__(self, maps, arrival_contracts=(), encounter_maps=()):
        maps = list(maps)
        if not maps or len({m.game for m in maps}) != 1:
            raise ValueError('a runtime world needs maps from exactly one game')
        super().__init__(m.map_file for m in maps)
        self.views = {m.map_file.name: m for m in maps}
        self.encounter_maps = frozenset(encounter_maps)
        if not self.encounter_maps <= self.views.keys():
            raise ValueError('encounter map must be loaded')
        self.game = maps[0].game
        self.rules = maps[0].rules
        self.arrival_contracts = {}
        for contract in arrival_contracts:
            source = self.views.get(contract.source.map)
            warp = source.warps.get(contract.source.tile) if source else None
            if (self.game != 'bdsp' or not warp or not contract.evidence.strip()
                    or warp.get('to_map') != contract.destination.map
                    or contract.destination.map not in self.views
                    or warp.get('to_point') not in self.views[contract.destination.map].data.get('points', {})
                    or not isinstance(contract.enter_direction, Direction)
                    or not isinstance(contract.facing, Direction)
                    or contract.source in self.arrival_contracts):
                raise ValueError('arrival contract needs a unique existing BDSP link and source evidence')
            self.arrival_contracts[contract.source] = contract
        # Do not mutate the LocalMap's legacy projection to attach connections.
        # connection_at/across_edge are shared, with only the metadata adapted.
        for name, view in self.views.items():
            self.maps[name] = copy.copy(view.map_file)
            self.maps[name].connections = [Connection(Direction[c['side'].upper()], c['to_map'], c['offset'])
                                           for c in view.data.get('connections', [])]

    def connection_at(self, beyond):
        """An ambiguous edge remains unresolved instead of choosing a first link."""
        edge = self.grid(beyond.map).edge_crossed(beyond.tile)
        if edge is None:
            return None
        along = beyond.tile.x if edge.is_vertical else beyond.tile.y
        matches = [c for c in self.maps[beyond.map].connections
                   if c.direction is edge and self._spans(c, along)]
        return matches[0] if len(matches) == 1 else None

    def validate_state(self, state):
        """Require a known stationary pose, including a just-arrived-on ladder."""
        if state.place.map not in self.views or not self._stable(state.place, frozenset(), allow_step_on=True):
            raise ValueError('pose is not a known unoccupied runtime tile')
        level = state.elevation
        if type(level) is not int or not 0 <= level <= 15:
            raise ValueError('player elevation must be 0..15')
        cell = self.at(state.place)
        if cell.elevation not in self.rules.any_level | self.rules.keep_level and cell.elevation != level:
            raise ValueError('pose elevation disagrees with terrain')

    def try_step(self, state, direction, rules, objects):
        view = self.views[state.place.map]
        result = view.try_step(state, direction, view.rules, objects)
        if isinstance(result, Edge):
            return self._edge(state, direction, objects)
        if not isinstance(result, Warp):
            return result
        warp = view.warps.get(result.tile)
        if self.game == 'bdsp':
            contract = self.arrival_contracts.get(Place(state.place.map, result.tile))
            if contract and direction is contract.enter_direction and self._stable(contract.destination, objects):
                return Warped(WorldState(contract.destination, self.at(contract.destination).elevation), contract.facing)
            return result  # No inferred BDSP arrival facing or walk-out rule.
        glyph = view.glyph(result.tile)
        # Animated doors only open northwards. A step-on/cave warp triggers on
        # entry; a directional mat triggers only when pressing out from it.
        mode = warp.get('enter') if warp else None
        active = ((glyph == 'D' and direction is Direction.NORTH)
                  or mode in ('step_on', 'cave_entrance')
                  or mode == 'walk_' + direction.name.lower())
        if not active:
            return Blocked(BlockReason.UNKNOWN)
        return self._warp(direction, warp, result, objects)

    def _warp(self, direction, warp, unresolved, objects):
        if not warp or warp.get('to_map') not in self.views:
            return unresolved
        target = self.views[warp['to_map']]
        point = target.data.get('points', {}).get(warp.get('to_point'))
        if point is None:
            return unresolved
        tile = Tile(*point)
        if target.map_file.grid.at(tile) is None:
            return unresolved
        entry = target.warps.get(tile, {}).get('enter')
        walked_out = target.glyph(tile) == 'D' or entry == 'cave_entrance'
        if walked_out:
            tile = tile.step(Direction.SOUTH)
        place = Place(target.map_file.name, tile)
        if not self._stable(place, objects, allow_step_on=True):
            return unresolved
        # Native FRLG resets elevation to the arrival tile (no surfing here).
        return Warped(WorldState(place, self.at(place).elevation),
                      Direction.SOUTH if walked_out else direction)

    def _stable(self, place, objects, allow_step_on=False):
        view = self.views[place.map]
        cell = self.at(place)
        return (cell is not None and not cell.blocked
                and cell.behavior not in (Behavior.UNKNOWN, Behavior.DOOR,
                    Behavior.LEDGE_NORTH, Behavior.LEDGE_SOUTH, Behavior.LEDGE_EAST, Behavior.LEDGE_WEST)
                and (cell.behavior is not Behavior.WARP or allow_step_on
                     and view.warps.get(place.tile, {}).get('enter') == 'step_on')
                and place.tile not in view.occupied | view.scene_tiles and place not in objects)

    def _edge(self, state, direction, objects):
        beyond = state.place.step(direction)
        target = self.across_edge(beyond)
        if target is None:
            return Edge(direction)
        view = self.views[target.map]
        cell = self.at(target)
        if cell is None or cell.behavior in (Behavior.UNKNOWN, Behavior.DOOR, Behavior.WARP):
            return Edge(direction)
        if target.tile in view.scene_tiles:
            return Blocked(BlockReason.UNKNOWN)
        if target.tile in view.occupied or target in objects:
            return Blocked(BlockReason.OBJECT)
        if cell.blocked or CLOSED_SIDES.get(view.glyph(target.tile)) is direction.opposite:
            return Blocked(BlockReason.WALL)
        # Edge arrivals onto a ledge need a game-specific landing calculation.
        if cell.behavior in (Behavior.LEDGE_NORTH, Behavior.LEDGE_SOUTH, Behavior.LEDGE_EAST, Behavior.LEDGE_WEST):
            return Blocked(BlockReason.UNKNOWN)
        if (state.elevation not in self.rules.any_level and cell.elevation not in
                self.rules.any_level | self.rules.keep_level and cell.elevation != state.elevation):
            return Blocked(BlockReason.ELEVATION)
        level = state.elevation if cell.elevation in self.rules.keep_level else cell.elevation
        return Moved(WorldState(target, level))

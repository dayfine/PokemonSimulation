"""Static routes inside one runtime map, using the shared Dijkstra planner.

Transitions end the local search, including unresolved warps and map edges.
This does not simulate scene effects, NPC movement, trainer sight or recovery.
"""

import copy
from dataclasses import dataclass, field
from typing import Mapping

from pokesim.games.frlg import ELEVATION_RULES
from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.model import LEDGE_DIRECTION, Behavior, GridMap2D
from pokesim.grid.maps.schema import MapFile, NamedPoint
from pokesim.grid.maps.world import Place, World
from pokesim.grid.movement import (FLAT, Blocked, BlockReason, Edge, Hop, Moved,
                                   PlayerState, Warp, WorldState, step)
from pokesim.grid.routing.shortest import Costs, shortest_path
from .consumer_source import GitSource, lock_entry, published_pack, read_json
from .runtime_map_pack import effective_map
from .runtime_symbols import CLOSED_SIDES, cell_for


DIRECTIONAL_WARPS = {'walk_' + direction.name.lower() for direction in Direction}


@dataclass
class Context:
    """Caller-supplied static state; flags absent from `flags` are unset.

    Unknown or active scene variables block their entire trigger rectangle.
    `acknowledge_map_state` accepts the pack's documented baked-in assumptions;
    it does not verify them against a console or execute their story events.
    """

    flags: frozenset = frozenset()
    variables: Mapping = field(default_factory=dict)
    acknowledge_map_state: bool = False


class LocalMap(World):
    """Runtime metadata plus a legacy grid view for shared routing/rendering.

    Keep `raw` for provenance. The grid is a projection, never a replacement
    JSON format: exporting it would lose runtime fields and closed sides.
    """

    def __init__(self, data, game, context=None, preconditions=(), provenance=None):
        if game not in ('frlg', 'bdsp'):
            raise ValueError('unsupported game: ' + game)
        self.raw = copy.deepcopy(data)
        self.data = effective_map(data)
        self.game = game
        self.context = copy.deepcopy(context or Context())
        self.preconditions = list(preconditions)
        self.provenance = copy.deepcopy(provenance or {})
        if self.preconditions and not self.context.acknowledge_map_state:
            raise ValueError('map state needs explicit acknowledgement: ' + '; '.join(self.preconditions))
        if self.data.get('triggers'):
            raise ValueError('generic story triggers need an adapter; local routing cannot evaluate them')
        self.rules = ELEVATION_RULES if game == 'frlg' else FLAT
        self.warps = {Tile(w['x'], w['y']): w for w in self.data.get('warps', [])}
        if len(self.warps) != len(self.data.get('warps', [])):
            raise ValueError('duplicate warp tiles need an explicit game adapter')
        rows = []
        wild = {Tile(*p) for p in self.data.get('regions', {}).get('wild', [])}
        for y, row in enumerate(self.data['tiles']):
            cells = []
            # Native FRLG uses ground level 3 when the optional grid is absent.
            default_level = '3' if game == 'frlg' else '0'
            levels = self.data.get('elevation', [default_level * len(row)] * len(self.data['tiles']))[y]
            for x, glyph in enumerate(row):
                tile = Tile(x, y)
                cell = cell_for(glyph, int(levels[x], 16))
                behavior = cell.behavior
                if tile in wild:
                    behavior = Behavior.TALL_GRASS
                warp = self.warps.get(tile)
                if warp:
                    behavior = Behavior.NONE if warp.get('enter') in DIRECTIONAL_WARPS else Behavior.WARP
                cells.append(cell._replace(behavior=behavior))
            rows.append(cells)
        self.map_file = MapFile(GridMap2D(self.data['name'], rows), game=game,
            points=[NamedPoint(name, Tile(*tile)) for name, tile in self.data.get('points', {}).items()])
        super().__init__([self.map_file])
        self.occupied = self._objects()
        self.scene_tiles = self._scene_tiles()

    def _objects(self):
        occupied = set()
        for obj in self.data.get('objects', []):
            if obj.get('hide_flag') and obj['hide_flag'] in self.context.flags:
                continue
            box = obj.get('wander')
            if box:
                occupied.update(Tile(x, y) for y in range(box['y0'], box['y1'] + 1)
                                for x in range(box['x0'], box['x1'] + 1))
            elif 'path' in obj:
                occupied.update(Tile(x, y) for x, y in obj['path']['tiles'])
            else:
                occupied.add(Tile(obj['x'], obj['y']))
        return occupied

    def _scene_tiles(self):
        tiles = set()
        for event in self.data.get('coord_events', []):
            variable = event['var']
            if variable in self.context.variables and self.context.variables[variable] != event['value']:
                continue
            tiles.update(Tile(x, y) for y in range(event['y'], event['y'] + event['length'])
                         for x in range(event['x'], event['x'] + event['width']))
        return tiles

    def glyph(self, tile):
        return self.data['tiles'][tile.y][tile.x]

    def try_step(self, state, direction, rules, objects):
        if state.place.map != self.map_file.name:
            raise ValueError('local route left its selected map')
        current = state.place.tile
        grid = self.map_file.grid
        if not grid.contains(current) or grid.at(current).behavior is Behavior.UNKNOWN:
            return Blocked(BlockReason.UNKNOWN)
        if (grid.at(current).behavior is Behavior.DOOR
                or grid.at(current).behavior is Behavior.WARP
                and self.warps.get(current, {}).get('enter') != 'step_on'):
            return Warp(current)
        # A ladder fires on entry. After arriving on it, walking off does not
        # immediately activate it again (used by RuntimeWorld cross-map routes).
        warp = self.warps.get(current)
        if warp and warp.get('enter') == 'walk_' + direction.name.lower():
            return Warp(current)
        target = current.step(direction)
        if CLOSED_SIDES.get(self.glyph(current)) is direction:
            return Blocked(BlockReason.WALL)
        if not grid.contains(target):
            return Edge(direction)
        if CLOSED_SIDES.get(self.glyph(target)) is direction.opposite:
            return Blocked(BlockReason.WALL)
        occupied = self.occupied | {place.tile for place in objects if place.map == self.map_file.name}
        if target in occupied:
            return Blocked(BlockReason.OBJECT)
        if target in self.scene_tiles:
            return Blocked(BlockReason.UNKNOWN)
        result = step(grid, PlayerState(current, state.elevation), direction, self.rules, occupied)
        if isinstance(result, (Moved, Hop)):
            landing = result.state.tile
            if (landing in self.scene_tiles or grid.at(landing).behavior is Behavior.UNKNOWN
                    or isinstance(result, Hop) and (landing in self.warps
                        or grid.at(landing).behavior in (Behavior.DOOR, Behavior.WARP)
                        or CLOSED_SIDES.get(self.glyph(landing)) is direction.opposite)):
                return Blocked(BlockReason.UNKNOWN)
            return type(result)(WorldState(Place(self.map_file.name, landing), result.state.elevation))
        return result

    def point(self, name):
        return self.map_file.point(name).tile

    def region(self, name):
        if name in self.data.get('regions', {}):
            return {Tile(*tile) for tile in self.data['regions'][name]}
        # BDSP's current runtime format encodes regions as numbered points.
        numbered = {int(key[len(name) + 1:]): Tile(*tile)
                    for key, tile in self.data.get('points', {}).items()
                    if key.startswith(name + '.') and key[len(name) + 1:].isdigit()}
        if not numbered or set(numbered) != set(range(1, len(numbered) + 1)):
            raise ValueError('missing or incomplete region: ' + name)
        return set(numbered.values())

    def route_region(self, start, name, costs=Costs(), elevation=None):
        """Reach any stable tile in the native goal region, not an arbitrary point."""
        initial = self.route(start, start, costs, elevation).start
        targets = set()
        for tile in self.region(name):
            cell = self.map_file.grid.at(tile)
            if (cell is not None and not cell.blocked
                    and cell.behavior not in (*LEDGE_DIRECTION, Behavior.UNKNOWN, Behavior.DOOR, Behavior.WARP)
                    and tile not in self.occupied and tile not in self.scene_tiles):
                targets.add(tile)
        if not targets:
            raise ValueError('goal region has no stable unoccupied tile: ' + name)
        return shortest_path(self, initial, lambda state: state.place.tile in targets, costs, self.rules)

    def route(self, start, goal, costs=Costs(), elevation=None):
        grid = self.map_file.grid
        for label, tile in [('start', start), ('goal', goal)]:
            cell = grid.at(tile)
            if cell is None or cell.blocked or cell.behavior is Behavior.UNKNOWN:
                raise ValueError(label + ' is not a known walkable tile')
            if tile in self.occupied or tile in self.scene_tiles:
                raise ValueError(label + ' is occupied or has an active/unknown scene trigger')
            if cell.behavior in (Behavior.DOOR, Behavior.WARP):
                raise ValueError(label + ' is a transition, not a stable local position')
            if cell.behavior in LEDGE_DIRECTION:
                raise ValueError(label + ' is a ledge, not a stable local position')
        if elevation is None:
            elevation = grid.at(start).elevation
            if self.game == 'frlg' and elevation == 15:
                raise ValueError('bridge start requires an explicit player elevation')
        if type(elevation) is not int or not 0 <= elevation <= 15:
            raise ValueError('player elevation must be 0..15')
        start_level = grid.at(start).elevation
        if start_level not in self.rules.any_level | self.rules.keep_level and elevation != start_level:
            raise ValueError('player elevation disagrees with the starting tile')
        place = lambda tile: Place(self.map_file.name, tile)
        return shortest_path(self, WorldState(place(start), elevation), place(goal), costs, self.rules)


def load_pinned_map(source_root, revision, game, name, context=None):
    source = GitSource(source_root)
    pin = lock_entry(source, revision)
    files = published_pack(source, game, pin)
    if name + '.json' not in files:
        raise ValueError('map not in pinned pack: ' + name)
    manifest = read_json(source.read(revision, pin['manifest_path']))
    entry = next(entry for entry in manifest['games'][game]['maps'] if entry['name'] == name)
    provenance = dict(pin, game=game, map=name, map_sha256=entry['sha256'],
                      coordinate_frame=entry['coordinate_frame'], decomp_source=entry['source'],
                      source_game=entry['source_game'],
                      source_revision_resolved=entry['source_revision_resolved'],
                      verification=entry['verification'])
    return LocalMap(read_json(files[name + '.json']), game, context,
                    entry.get('preconditions', []), provenance)

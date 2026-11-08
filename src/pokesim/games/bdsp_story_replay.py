"""BDSP story actions on pinned terrain with explicitly scripted observations.

Doors traverse their source corridor, then require arrival evidence: the pack
has no complete mine warp links. Dynamic NPC clearance and scene/heal outcomes
are scenario inputs, never inferred from authored fallback poses.
"""

from functools import partial

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Blocked, BlockReason, Moved, PlayerState, Warp, WorldState, step as tile_step, world_step
from pokesim.grid.routing.shortest import as_move, shortest_path
from pokesim.story.replay_handlers import BoundAction, exact
from pokesim.story.spatial_replay import RuntimeSpatialReplay, pose


def dynamic_objects(world):
    """Keep wandering regions separate from permanent wall/occupancy geometry."""
    regions = {}
    for name, view in world.views.items():
        static = set()
        for obj in view.data.get('objects', []):
            box = obj.get('wander')
            if box:
                regions[name, obj['name']] = {Tile(x, y) for y in range(box['y0'], box['y1'] + 1)
                                             for x in range(box['x0'], box['x1'] + 1)}
            else:
                static.add(Tile(obj['x'], obj['y']))
        view.occupied = static  # State projection only; raw map bytes/terrain remain untouched.
    return regions


class BDSPReplay(RuntimeSpatialReplay):
    """Supported BDSP profiles; native robust cost/timing parity is unclaimed."""
    def __init__(self, world, costs, max_route_moves):
        super().__init__(world, costs, max_route_moves)
        self.dynamic = dynamic_objects(world)

    def validate_event(self, event):
        kind, variant = event['kind'], event.get('variant', '')
        if kind == 'route' and variant not in ('', 'town'):
            raise ValueError('unsupported BDSP route profile')
        if kind == 'legs':
            if variant not in ('', 'to_wall', 'counted_wall') or not event.get('legs'):
                raise ValueError('unsupported BDSP legs profile')
            if (any(not 1 <= leg['tiles'] <= self.max_route_moves for leg in event['legs'])
                    or sum(leg['tiles'] for leg in event['legs']) > self.max_route_moves):
                raise ValueError('leg distance outside bound')
            if variant == 'counted_wall' and len(event['legs']) != 1:
                raise ValueError('counted-wall requires exactly one leg')
        if kind in ('step', 'scene', 'heal', 'legs') and 'declared_after' not in event:
            raise ValueError('BDSP pilot action requires explicit arrival data')

    def handlers(self):
        return {}

    def bind_action(self, kind, spec):
        profiles = {'bdsp-runtime-route/1': ('route', self.movement_signal, self.route),
                    'bdsp-runtime-legs/1': ('legs', self.movement_signal, self.legs),
                    'bdsp-door-observation/1': ('step', self.observation, self.door),
                    'bdsp-dialogue-observation/1': ('talk', self.observation, self.talk),
                    'bdsp-scene-observation/1': ('scene', self.observation, self.scene),
                    'bdsp-heal-observation/1': ('heal', self.observation, self.heal)}
        if spec['capability'] not in profiles:
            return None
        supported, preflight, execute = profiles[spec['capability']]
        params = spec['parameters']
        exact(params, 'npc' if kind in ('talk', 'scene') else '')
        if kind != supported or ('npc' in params and (not isinstance(params['npc'], str) or not params['npc'])):
            raise ValueError('unsupported BDSP kind/parameters')
        return BoundAction(spec['capability'], params, preflight, partial(execute, params=params))

    def validate_pose(self, value):
        exact(value, 'map tile elevation facing')
        if (not isinstance(value['map'], str) or not isinstance(value['tile'], list)
                or len(value['tile']) != 2 or any(type(n) is not int for n in value['tile'])
                or value['facing'] not in ('north', 'east', 'south', 'west')
                or type(value['elevation']) is not int or value['elevation'] != 0):
            raise ValueError('expected a known flat BDSP pose')
        state = WorldState(Place(value['map'], Tile(*value['tile'])), 0)
        view = self.world.views.get(value['map'])
        if view is None or self.world.at(state.place) is None:
            raise ValueError('pose outside bound maps')
        if view.glyph(state.place.tile) != 'D':
            self.world.validate_state(state)
        return state, Direction[value['facing'].upper()]

    def authored_poses(self, wire):
        where = wire['where']
        if wire['certainty'] not in ('tile', 'set') or where['kind'] != 'tiles' or not where['tiles'] or 'facing' not in where:
            raise ValueError('BDSP replay requires explicit tile alternatives and facing')
        result = []
        for tile in where['tiles']:
            location = Place(wire['map'], Tile(*tile))
            cell = self.world.at(location)
            if cell is None:
                raise ValueError('authored pose outside bound maps')
            observed = pose(WorldState(location, cell.elevation), Direction[where['facing'].upper()])
            self.validate_pose(observed)
            result.append(observed)
        return result

    def authored_pose(self, wire):
        alternatives = self.authored_poses(wire)
        if len(alternatives) != 1:
            raise ValueError('this action needs one authored target, not an arbitrary first alternative')
        return alternatives[0]

    def matches_authored_pose(self, actual, wire):
        return actual in self.authored_poses(wire)

    def movement_signal(self, event, signal):
        if signal is None:
            return
        exact(signal, 'kind clear_npcs encounter')
        if signal['kind'] != 'movement-script' or not isinstance(signal['clear_npcs'], list):
            raise ValueError('movement scripts must declare their synthetic clearance window')
        names = {name for _, name in self.dynamic}
        if any(not isinstance(name, str) or name not in names for name in signal['clear_npcs']):
            raise ValueError('unknown dynamic NPC clearance')
        if signal['encounter'] is not None:
            exact(signal['encounter'], 'kind from direction')
            self.route_signal(event, signal['encounter'])

    def observation(self, event, signal):
        if signal is None:
            return
        exact(signal, 'kind basis screen pose result')
        if signal['kind'] != 'bdsp-observation' or signal['basis'] != 'scripted' or not isinstance(signal['result'], dict):
            raise ValueError('BDSP observations must be explicitly scripted')
        self.validate_pose(signal['pose'])
        key = {'step': 'transition', 'talk': 'npc', 'scene': 'departed', 'heal': 'party_healed'}[event['kind']]
        exact(signal['result'], key)
        expected_type = bool if key in ('transition', 'party_healed') else str
        if type(signal['result'][key]) is not expected_type:
            raise ValueError('unsupported observation result type')

    def hazard(self, current, signal):
        clear = signal['clear_npcs'] if signal else []
        return any(map == current.place.map and current.place.tile in tiles and name not in clear
                   for (map, name), tiles in self.dynamic.items())

    def route(self, state, event, signal, params):
        current, _ = self.validate_pose(state.pose)
        target = self.authored_pose(event['target'])
        path = shortest_path(self.world, current, Place(target['map'], Tile(*target['tile'])), self.costs, self.world.rules)
        if path and any(self.hazard(move.to, signal) for move in path.moves):
            return 'dynamic_npc_clearance_unconfirmed'
        return super().route(state, event, signal['encounter'] if signal else None)

    def press(self, current, direction):
        # A confirmed arrival can stand on a cave mat. Leaving it toward the
        # interior does not reactivate the source warp merely by standing there.
        view = self.world.views[current.place.map]
        if view.glyph(current.place.tile) == 'D':
            local = tile_step(view.map_file.grid, PlayerState(current.place.tile, 0), direction,
                              self.world.rules, view.occupied)
            return Moved(WorldState(Place(current.place.map, local.state.tile), 0)) if isinstance(local, Moved) else local
        return world_step(self.world, current, direction, self.world.rules)

    def advance(self, state, direction, count, event, signal, wall=False):
        """Requested distance stays in the action log when a battle invalidates pose."""
        current, facing = self.validate_pose(state.pose)
        state.action(event['id'], 'walk', map=current.place.map, direction=direction.name.lower(), tiles=count)
        for number in range(count):
            result = self.press(current, direction)
            move = as_move(direction, result)
            if move is None:
                if wall and isinstance(result, Blocked) and result.reason == BlockReason.WALL:
                    return None
                return 'movement_blocked_or_unresolved'
            if self.hazard(move.to, signal):
                return 'dynamic_npc_clearance_unconfirmed'
            predicted = pose(move.to, getattr(result, 'facing', direction))
            encounter = signal['encounter'] if signal else None
            if encounter and state.pose == encounter['from'] and direction.name.lower() == encounter['direction']:
                state.candidates = [dict(state.pose, facing=None), dict(predicted, facing=None)]
                state.pose, state.basis = None, 'unknown-after-interruption'
                return 'encounter_requires_recovery'
            current, facing = move.to, direction
            state.pose, state.basis = predicted, 'model-prediction'
        if wall:
            result = self.press(current, direction)
            if not isinstance(result, Blocked) or result.reason != BlockReason.WALL:
                return 'wall_not_reached'
        return None

    def wall_distance(self, observed, direction):
        current, _ = self.validate_pose(observed)
        for distance in range(self.max_route_moves + 1):
            result = self.press(current, direction)
            move = as_move(direction, result)
            if move is None:
                if isinstance(result, Blocked) and result.reason == BlockReason.WALL:
                    return distance, pose(current, direction)
                raise ValueError('counted-wall corridor ends at an NPC, unknown tile or transition')
            current = move.to
        raise ValueError('counted-wall exceeds bounded movement budget')

    def legs(self, state, event, signal, params):
        variant = event.get('variant', '')
        if variant not in ('', 'to_wall', 'counted_wall'):
            return 'unsupported_legs_variant'
        for leg in event['legs']:
            direction = Direction[leg['direction'].upper()]
            count = leg['tiles']
            if variant == 'counted_wall':
                # The native executor uses its declared belief, not a guessed first tile.
                beliefs = state.declared_belief or [state.pose]
                distances = [self.wall_distance(p, direction)[0] for p in beliefs]
                if not min(distances) <= count <= max(distances):
                    return 'counted_wall_map_mismatch'
                ends = [self.wall_distance(p, direction)[1] for p in beliefs]
                if any(p != ends[0] for p in ends):
                    return 'wall_does_not_relocalize'
                count = self.wall_distance(state.pose, direction)[0]
                state.record(event['id'], 'wall_bounds', fewest=min(distances), most=max(distances))
            failure = self.advance(state, direction, count, event, signal, wall=bool(variant))
            if failure:
                return failure
        if signal and signal['encounter'] is not None:
            raise ValueError('injected leg encounter was not reached')
        target = event.get('declared_after')
        if target and not any(state.pose['map'] == p['map'] and state.pose['tile'] == p['tile'] for p in self.authored_poses(target)):
            return 'declared_arrival_disagrees_with_model'
        state.declared_belief = []
        return None

    def accept(self, state, event, signal, result):
        target = event.get('declared_after')
        if (not signal or signal['screen'] != 'overworld' or signal['result'] != result
                or not target or not self.matches_authored_pose(signal['pose'], target)):
            state.pose, state.basis = None, 'unknown-after-observation'
            return 'observation_missing_or_mismatched'
        state.pose, state.basis = dict(signal['pose']), 'scripted-observation'
        state.record(event['id'], 'observation', result=dict(result), declared_belief=target)
        # Retain the native declared alternatives separately from this scripted physical pose.
        state.declared_belief = self.authored_poses(target)
        return None

    def door(self, state, event, signal, params):
        direction = Direction[event.get('direction', 'north').upper()]
        current, _ = self.validate_pose(state.pose)
        state.action(event['id'], 'door', map=current.place.map, direction=direction.name.lower(),
                     to_map=event['declared_after']['map'])
        for distance in range(self.max_route_moves):
            result = self.press(current, direction)
            if isinstance(result, Warp):
                state.record(event['id'], 'doorway_reached', tile=list(result.tile), walked=distance)
                return self.accept(state, event, signal, {'transition': True})
            move = as_move(direction, result)
            if move is None or self.hazard(move.to, None):
                return 'door_corridor_blocked_or_unresolved'
            current = move.to
            state.pose, state.basis = pose(current, direction), 'model-prediction'
        return 'door_move_budget_exceeded'

    def talk(self, state, event, signal, params):
        current, facing = self.validate_pose(state.pose)
        view = self.world.views[current.place.map]
        actors = [o for o in view.data.get('objects', []) if o['name'] == params['npc'] and not o.get('wander')]
        if len(actors) != 1:
            return 'dialogue_target_unbound'
        target = Tile(actors[0]['x'], actors[0]['y'])
        directions = [d for d in Direction if current.place.tile.step(d) == target]
        if not directions:
            return 'not_adjacent_to_dialogue_target'
        if directions[0] != facing:
            state.action(event['id'], 'turn', map=current.place.map, direction=directions[0].name.lower())
        state.pose = pose(current, directions[0])
        state.action(event['id'], 'talk', npc=params['npc'])
        if not signal or signal['screen'] != 'dialogue' or signal['pose'] != state.pose or signal['result'] != {'npc': params['npc']}:
            return 'dialogue_unconfirmed'
        state.basis = 'scripted-observation'
        return None

    def scene(self, state, event, signal, params):
        state.action(event['id'], 'scene', capability='bdsp-scene-observation/1')
        return self.accept(state, event, signal, {'departed': params['npc']})

    def heal(self, state, event, signal, params):
        state.action(event['id'], 'heal')
        return self.accept(state, event, signal, {'party_healed': True})

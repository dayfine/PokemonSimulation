"""Tile-game route/step replay using the existing runtime world and movement rules.

Predictions are not console confirmations. Unknown transitions and encounters
stop with invalidated pose; no recovery or controller timing is invented.
"""

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Edge, Warp, WorldState, world_step
from pokesim.grid.routing.shortest import MoveKind, as_move, shortest_path
from .replay_handlers import exact


def pose(state, facing):
    return {'map': state.place.map, 'tile': list(state.place.tile),
            'elevation': state.elevation, 'facing': facing.name.lower()}


def movement_action(current, move, direction, unresolved=None):
    """Describe a straight walk, hop or map transition, without input timings."""
    result = dict(map=current.place.map, direction=direction.name.lower())
    if move and (move.kind is MoveKind.WARP or move.to.place.map != current.place.map):
        return dict(result, kind='transition', to_map=move.to.place.map,
                    via='warp' if move.kind is MoveKind.WARP else 'edge')
    if isinstance(unresolved, (Warp, Edge)):
        return dict(result, kind='transition', to_map=None, via='warp' if isinstance(unresolved, Warp) else 'edge')
    if move and move.kind is MoveKind.HOP:
        start, end = current.place.tile, move.to.place.tile
        return dict(result, kind='hop', tiles=abs(end.x - start.x) + abs(end.y - start.y))
    return dict(result, kind='walk', tiles=1)


def route_legs(path):
    """Group planned same-map walking into requested straight legs.

    Transitions/hops stay separate. A leg is logged before any of its model
    steps execute, so an interruption cannot shrink its requested distance.
    """
    legs, current = [], path.start
    for number, move in enumerate(path.moves, 1):
        action = movement_action(current, move, move.direction)
        if (action['kind'] == 'walk' and legs
                and {k: v for k, v in legs[-1][0].items() if k != 'tiles'}
                == {k: v for k, v in action.items() if k != 'tiles'}):
            legs[-1][0]['tiles'] += 1
            legs[-1][1].append((number, move))
        else:
            legs.append((action, [(number, move)]))
        current = move.to
    return legs


class RuntimeSpatialReplay:
    """Spatial handlers driven by the supplied runtime world and movement rules."""
    def __init__(self, world, costs, max_route_moves):
        self.world, self.costs, self.max_route_moves = world, costs, max_route_moves

    def validate_pose(self, value):
        exact(value, 'map tile elevation facing')
        if (not isinstance(value['map'], str) or not isinstance(value['tile'], list)
                or len(value['tile']) != 2 or any(type(n) is not int for n in value['tile'])
                or value['facing'] not in ('north', 'east', 'south', 'west')):
            raise ValueError('expected a known runtime-local pose')
        state = WorldState(Place(value['map'], Tile(*value['tile'])), value['elevation'])
        self.world.validate_state(state)
        return state, Direction[value['facing'].upper()]

    def authored_pose(self, wire):
        where = wire['where']
        if wire['certainty'] != 'tile' or where['kind'] != 'tiles' or len(where['tiles']) != 1 or 'facing' not in where:
            raise ValueError('spatial replay requires one authored tile and known facing')
        place = Place(wire['map'], Tile(*where['tiles'][0]))
        cell = self.world.at(place)
        if cell is None:
            raise ValueError('authored pose outside bound maps')
        result = pose(WorldState(place, cell.elevation), Direction[where['facing'].upper()])
        self.validate_pose(result)
        return result

    def route_signal(self, event, signal):
        if signal is not None:
            exact(signal, 'kind from direction')
            if signal['kind'] != 'wild-encounter' or signal['direction'] not in ('north', 'east', 'south', 'west'):
                raise ValueError('unsupported route signal')
            self.validate_pose(signal['from'])

    def step_signal(self, event, signal):
        if signal is not None:
            exact(signal, 'kind')
            if signal['kind'] != 'unconfirmed-transition':
                raise ValueError('unsupported step signal')

    def interruption_move(self, path, facing, signal):
        if not signal:
            return None
        current, matches = path.start, []
        for number, move in enumerate(path.moves, 1):
            if pose(current, facing) == signal['from'] and move.direction.name.lower() == signal['direction']:
                matches.append(number)
            result = world_step(self.world, current, move.direction, self.world.rules)
            current, facing = move.to, getattr(result, 'facing', move.direction)
        if len(matches) != 1:
            raise ValueError('encounter injection must match exactly one physical route step')
        return matches[0]

    def route(self, state, event, signal):
        current, facing = self.validate_pose(state.pose)
        target = self.authored_pose(event['target'])
        path = shortest_path(self.world, current, Place(target['map'], Tile(*target['tile'])), self.costs, self.world.rules)
        if path is None:
            return 'no_route'
        if len(path.moves) > self.max_route_moves:
            return 'route_move_budget_exceeded'
        interrupted_at = self.interruption_move(path, facing, signal)
        for action, moves in route_legs(path):
            state.action(event['id'], **action)
            for number, move in moves:
                result = world_step(self.world, current, move.direction, self.world.rules)
                actual = as_move(move.direction, result)
                if actual is None or actual.to != move.to:
                    state.pose, state.basis = None, 'unknown-after-route-mismatch'
                    return 'route_model_mismatch'
                end_facing = getattr(result, 'facing', move.direction)
                predicted = pose(actual.to, end_facing)
                if interrupted_at == number:
                    state.candidates = [dict(state.pose, facing=None), dict(predicted, facing=None)]
                    state.pose, state.basis = None, 'unknown-after-interruption'
                    state.record(event['id'], 'interrupted', before_move=number, candidates=state.candidates)
                    return 'encounter_requires_recovery'
                current, facing = actual.to, end_facing
                state.pose, state.basis = predicted, 'model-prediction'
                state.record(event['id'], 'move', number=number, direction=move.direction.name.lower())
        if facing.name.lower() != target['facing']:
            state.action(event['id'], 'turn', map=current.place.map, direction=target['facing'])
            state.pose = pose(current, Direction[target['facing'].upper()])
            state.basis = 'model-prediction'
            state.record(event['id'], 'turn')
        return None

    def step(self, state, event, signal):
        current, facing = self.validate_pose(state.pose)
        direction = Direction[event.get('direction', 'north').upper()]
        result = world_step(self.world, current, direction, self.world.rules)
        move = as_move(direction, result)
        state.action(event['id'], **movement_action(current, move, direction, result))
        if signal:
            state.pose, state.basis = None, 'unknown-after-transition'
            return 'transition_unconfirmed'
        if move is None:
            if isinstance(result, (Warp, Edge)):
                state.pose, state.basis = None, 'unknown-after-transition'
            return 'step_unresolved'
        state.pose, state.basis = pose(move.to, getattr(result, 'facing', direction)), 'model-prediction'
        state.record(event['id'], 'step', direction=direction.name.lower())
        return None

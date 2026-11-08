"""FRLG route/step replay using the existing runtime world and movement rules.

Predictions are not console confirmations. Unknown transitions and encounters
stop with invalidated pose; no recovery or controller timing is invented.
"""

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Edge, Warp, WorldState, world_step
from pokesim.grid.routing.shortest import as_move, shortest_path
from pokesim.story.replay_handlers import exact


def pose(state, facing):
    return {'map': state.place.map, 'tile': list(state.place.tile),
            'elevation': state.elevation, 'facing': facing.name.lower()}


class FRLGReplay:
    """Game-owned spatial handlers, reusable across checkpoints and event IDs."""
    def __init__(self, world, costs, max_route_presses):
        self.world, self.costs, self.max_route_presses = world, costs, max_route_presses

    def handlers(self):
        return {'frlg-runtime-route/1': ('route', self.route_signal, self.route),
                'frlg-runtime-step/1': ('step', self.step_signal, self.step)}

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

    def interruption_press(self, path, facing, signal):
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
        if len(path.moves) > self.max_route_presses:
            return 'route_press_budget_exceeded'
        interrupted_at = self.interruption_press(path, facing, signal)
        for number, move in enumerate(path.moves, 1):
            result = world_step(self.world, current, move.direction, self.world.rules)
            actual = as_move(move.direction, result)
            if actual is None or actual.to != move.to:
                state.action(event['id'], 'press', map=current.place.map, direction=move.direction.name.lower())
                state.pose, state.basis = None, 'unknown-after-route-mismatch'
                return 'route_model_mismatch'
            end_facing = getattr(result, 'facing', move.direction)
            predicted = pose(actual.to, end_facing)
            details = dict(map=current.place.map, direction=move.direction.name.lower())
            if interrupted_at == number:
                state.action(event['id'], 'press', **details, outcome='interrupted')
                state.candidates = [dict(state.pose, facing=None), dict(predicted, facing=None)]
                state.pose, state.basis = None, 'unknown-after-interruption'
                state.record(event['id'], 'interrupted', before_press=number, candidates=state.candidates)
                return 'encounter_requires_recovery'
            state.action(event['id'], 'press', **details)
            current, facing = actual.to, end_facing
            state.pose, state.basis = predicted, 'model-prediction'
            state.record(event['id'], 'press', number=number, direction=move.direction.name.lower())
        if facing.name.lower() != target['facing']:
            state.action(event['id'], 'turn', map=current.place.map, direction=target['facing'])
            state.pose = pose(current, Direction[target['facing'].upper()])
            state.basis = 'model-prediction'
            state.record(event['id'], 'turn')
        return None

    def step(self, state, event, signal):
        current, facing = self.validate_pose(state.pose)
        direction = Direction[event.get('direction', 'north').upper()]
        state.action(event['id'], 'press', map=current.place.map, direction=direction.name.lower())
        if signal:
            state.pose, state.basis = None, 'unknown-after-transition'
            return 'transition_unconfirmed'
        result = world_step(self.world, current, direction, self.world.rules)
        move = as_move(direction, result)
        if move is None:
            if isinstance(result, (Warp, Edge)):
                state.pose, state.basis = None, 'unknown-after-transition'
            return 'step_unresolved'
        state.pose, state.basis = pose(move.to, getattr(result, 'facing', direction)), 'model-prediction'
        state.record(event['id'], 'step', direction=direction.name.lower())
        return None

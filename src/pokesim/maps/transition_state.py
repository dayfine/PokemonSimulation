"""Offline pose beliefs, observations and bounded localization candidates.

No detector/controller runs here. Callers supply normalized runtime-local
observations and explicitly attest that queued movement has drained. A model
prediction never establishes execution. Budgets are hard bounds, not timing
estimates. See docs/navigation/TRANSITION_SCENARIOS.md for evidence and limits.
"""
from collections import deque
from dataclasses import dataclass
from typing import Optional, Tuple

from pokesim.grid.geometry import CLOCKWISE, Direction, Tile
from pokesim.grid.maps.model import Behavior
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Blocked, BlockReason, Edge, Hop, Moved, Warp, Warped, WorldState, world_step

MAX_PRESSES = 128
MAX_HYPOTHESES = 4096


class StateFailure(ValueError):
    """Unsupported movement, contradictory evidence, or exhausted recovery."""


@dataclass(frozen=True)
class Pose:
    state: WorldState
    facing: Optional[Direction] = None


@dataclass(frozen=True)
class Observation:
    screen: str = 'unknown'
    map: Optional[str] = None
    tiles: Optional[Tuple[Tile, ...]] = None
    facing: Optional[Direction] = None
    elevation: Optional[int] = None
    frame: str = 'runtime-local'
    queue_drained: bool = False
    fade: bool = False
    hp_box: bool = False
    still_direction: Optional[Direction] = None
    video_advanced: bool = False


@dataclass(frozen=True)
class AnchorPlan:
    start: frozenset
    actions: tuple
    arrival: Pose


def _budget(value, maximum, label):
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(label + ' must be 1..' + str(maximum))


def _press(world, pose, direction):
    result = world_step(world, pose.state, direction)
    if isinstance(result, (Warp, Edge)):
        raise StateFailure('unresolved transition at ' + str(pose.state.place))
    if isinstance(result, Blocked):
        if result.reason is BlockReason.UNKNOWN:
            raise StateFailure('unknown movement at ' + str(pose.state.place))
        return Pose(pose.state, direction), result
    if isinstance(result, (Moved, Hop, Warped)):
        return Pose(result.state, result.facing if isinstance(result, Warped) else direction), result
    raise StateFailure('unsupported movement result')


def _predictions(world, belief, actions, minimum, edge_stall, missed_presses):
    frontier = {(pose, False, 0) for pose in belief}
    candidates = set(belief) if minimum == 0 else set()
    for count, direction in enumerate(actions, 1):
        following = set()
        for pose, stalled, missed in frontier:
            after, result = _press(world, pose, direction)
            following.add((after, stalled, missed))
            if missed < missed_presses:
                following.add((Pose(pose.state, direction), stalled, missed + 1))
            # Native hold timing can lose one tile at a connection (#219).
            # This is an optional missed press, not a changed edge geometry.
            if edge_stall and not stalled and isinstance(result, Moved) and after.state.place.map != pose.state.place.map:
                following.add((Pose(pose.state, direction), True, missed))
        frontier = following
        if count >= minimum:
            candidates.update(pose for pose, _, _ in frontier)
        if len(candidates) > MAX_HYPOTHESES or len(frontier) > MAX_HYPOTHESES:
            raise StateFailure('pose hypothesis budget exhausted')
    return frozenset(candidates)


class Session:
    """One offline movement transaction at a time; failures latch until restart.

    Initial poses are caller-asserted, established preconditions. propose()
    invalidates certainty before movement. min_completed describes evidence
    about completed inputs, not an assumption that each tap moved a tile.
    queued inputs can execute or be cancelled; every prefix remains possible.
    Recovery plans are conditional on static terrain and supplied hazard tiles.
    """

    def __init__(self, world, belief, max_recoveries=3):
        _budget(max_recoveries, MAX_PRESSES, 'recovery attempts')
        self.remaining_recoveries = max_recoveries
        self.world = world
        self.belief = frozenset(belief)
        if not self.belief or len(self.belief) > MAX_HYPOTHESES:
            raise ValueError('initial belief is empty or too large')
        for pose in self.belief:
            world.validate_state(pose.state)
        self.screen = 'overworld'
        self.queue_drained = True
        self.awaiting = False
        self.failure = None

    @property
    def can_resume(self):
        return (self.failure is None and self.screen == 'overworld' and self.queue_drained
                and not self.awaiting and len(self.belief) == 1
                and next(iter(self.belief)).facing is not None)

    def _fail(self, message):
        self.failure = message
        self.belief = frozenset()
        raise StateFailure(message)

    def propose(self, actions, min_completed=0, queued=(), edge_stall=False, missed_presses=0):
        if not self.can_resume:
            raise StateFailure('route requires a confirmed unique pose and drained inputs')
        self._propose(tuple(actions), min_completed, tuple(queued), edge_stall, missed_presses)

    def _propose(self, actions, minimum, queued, edge_stall, missed_presses):
        all_actions = actions + queued
        _budget(len(all_actions), MAX_PRESSES, 'movement presses')
        if type(missed_presses) is not int or not 0 <= missed_presses <= len(all_actions):
            raise ValueError('invalid missed-input budget')
        if type(minimum) is not int or not 0 <= minimum <= len(actions):
            raise ValueError('invalid completed-input lower bound')
        if any(not isinstance(d, Direction) for d in all_actions):
            raise ValueError('movement actions must be directions')
        self.awaiting = True
        self.queue_drained = False
        try:
            self.belief = _predictions(self.world, self.belief, all_actions, minimum, edge_stall, missed_presses)
        except StateFailure as exc:
            self._fail(str(exc))

    def observe(self, observation):
        if observation.frame != 'runtime-local':
            raise ValueError('observation must use the runtime-local coordinate frame')
        if observation.still_direction is not None and not isinstance(observation.still_direction, Direction):
            raise ValueError('still observation requires a direction')
        if observation.screen not in ('overworld', 'battle', 'unknown'):
            raise ValueError('unsupported screen observation')
        if observation.tiles is not None and (not observation.map or not observation.tiles):
            raise ValueError('tile observations require a map and a nonempty candidate set')
        if self.failure:
            raise StateFailure(self.failure)
        self.screen = observation.screen
        if self.screen == 'battle' and not observation.hp_box:
            self.screen = 'unknown'
        elif self.screen == 'battle':
            # Trainer approach/battle handling can turn the player; native
            # FRLG also invalidates facing after a stop. Do not retain it.
            self.belief = frozenset(Pose(p.state, None) for p in self.belief)
        # A fade, text-box-like black region or battle proves no map/tile.
        # Do not use even a precise early pose while queued inputs can run.
        if observation.queue_drained:
            self.queue_drained = True
        if self.screen != 'overworld' or not self.queue_drained:
            self.awaiting = True
            return
        if observation.still_direction is not None and not observation.video_advanced:
            self.awaiting = True
            return  # Frozen video is not evidence of a collision.
        candidates = frozenset(p for p in self.belief
            if (observation.map is None or p.state.place.map == observation.map)
            and (observation.tiles is None or p.state.place.tile in observation.tiles)
            and (observation.facing is None or p.facing is None or p.facing is observation.facing)
            and (observation.elevation is None or p.state.elevation == observation.elevation)
            and (observation.still_direction is None or isinstance(
                world_step(self.world, p.state, observation.still_direction), Blocked)))
        if not candidates:
            self._fail('observation contradicts all predicted poses; stop and relocalize externally')
        # Unknown facing can be established by a supplied observation.
        self.belief = frozenset(Pose(p.state, observation.facing or observation.still_direction or p.facing) for p in candidates)
        self.awaiting = False

    def _recovery_ready(self):
        if self.failure or self.screen != 'overworld' or not self.queue_drained or self.awaiting:
            raise StateFailure('recovery requires a stable overworld observation and drained inputs')
        if self.remaining_recoveries == 0:
            self._fail('recovery attempt budget exhausted')

    def recover(self, max_presses=32, max_states=512, forbidden=frozenset()):
        self._recovery_ready()
        plan = anchor_plan(self.world, self.belief, max_presses, max_states, forbidden)
        if plan is None:
            self._fail('no safe static localization candidate within budget')
        # Every prefix stays possible if interrupted. The predicted convergence
        # is confirmed only by a subsequent observation, never by this return.
        self.remaining_recoveries -= 1
        self._propose(plan.actions, 0, (), False, 0)
        return plan

    def clip(self, direction, max_presses=32, encounter_policy='stop', forbidden=frozenset()):
        """Hold toward one proven wall; interruptions still require observation.

        With encounter_policy='recover', an encounter may stop at any prefix.
        After escaping, observe a stable overworld, then clip again within the
        shared attempt budget. A still observation needs advancing video and
        drained inputs. No still frames are generated or classified here.
        """
        self._recovery_ready()
        plan = clip_plan(self.world, self.belief, direction, max_presses, encounter_policy, forbidden)
        if plan is None:
            self._fail('clip does not converge safely to one known wall within budget')
        self.remaining_recoveries -= 1
        self._propose(plan.actions, 0, (), False, 0)
        return plan


def clip_plan(world, belief, direction, max_presses=32, encounter_policy='stop', forbidden=frozenset()):
    """Prove one-direction convergence, including NPC/warp/ledge safety checks.

    Recovering encounters is an explicit caller policy. This proof concerns
    static movement only; it never credits a battle-interrupted press as moved.
    """
    _budget(max_presses, MAX_PRESSES, 'clip presses')
    if not isinstance(direction, Direction) or encounter_policy not in ('stop', 'recover'):
        raise ValueError('unsupported clip direction or encounter policy')
    initial = frozenset(belief)
    if not initial or len({p.state.place.map for p in initial}) != 1:
        return None
    hazards = set(forbidden) | trainer_hazards(world)
    ends, longest = set(), 0
    for pose in initial:
        at = pose
        for count in range(1, max_presses + 1):
            if _aims_at_warp(world, at, direction):
                return None
            try:
                after, result = _press(world, at, direction)
            except StateFailure:
                return None
            if (after.state.place.map != at.state.place.map
                    or isinstance(result, (Warped, Hop)) or after.state.place in hazards
                    or after.state.place.tile in world.views[after.state.place.map].warps):
                return None
            wild = (after.state.place.map in world.encounter_maps
                    or world.at(after.state.place).behavior is Behavior.TALL_GRASS)
            if wild and encounter_policy != 'recover':
                return None
            if isinstance(result, Blocked):
                if result.reason is not BlockReason.WALL:
                    return None
                ends.add(after)
                longest = max(longest, count)
                break
            at = after
        else:
            return None
    if len(ends) != 1:
        return None
    return AnchorPlan(initial, (direction,) * longest, next(iter(ends)))


def anchor_plan(world, belief, max_presses=32, max_states=512, forbidden=frozenset()):
    """Search common inputs that merge every pose on static, non-encounter floor.

    Never crosses a map/warp, hops a ledge, meets an NPC, enters an unknown or
    scene cell, or touches caller-supplied hazards. Moving NPCs, missing trainer
    sights and detector quality remain caller obligations, not proven safe here.
    Budgets cap both depth and examined belief states; None means stop.
    """
    _budget(max_presses, MAX_PRESSES, 'recovery presses')
    _budget(max_states, MAX_HYPOTHESES, 'recovery states')
    initial = frozenset(belief)
    if not initial or len({p.state.place.map for p in initial}) != 1:
        return None
    forbidden = set(forbidden) | trainer_hazards(world)
    frontier = deque([(initial, ())])
    seen = {initial}
    while frontier:
        poses, actions = frontier.popleft()
        if len(poses) == 1 and actions:
            return AnchorPlan(initial, actions, next(iter(poses)))
        if len(actions) >= max_presses:
            continue
        for direction in CLOCKWISE:
            after = set()
            for pose in poses:
                if _aims_at_warp(world, pose, direction):
                    break
                try:
                    moved, result = _press(world, pose, direction)
                except StateFailure:
                    break
                if moved.state.place.map != pose.state.place.map or not _safe_anchor_step(world, moved, result, forbidden):
                    break
                after.add(moved)
            else:
                next_poses = frozenset(after)
                if next_poses not in seen:
                    if len(seen) >= max_states:
                        return None
                    seen.add(next_poses)
                    frontier.append((next_poses, actions + (direction,)))
    return None


def _aims_at_warp(world, pose, direction):
    view = world.views[pose.state.place.map]
    # Metadata can declare a warp even on a blocked glyph. Do not use that
    # mismatch as a wall anchor; the terrain/link must be reviewed first.
    return pose.state.place.tile.step(direction) in view.warps


def _safe_anchor_step(world, pose, result, forbidden):
    if isinstance(result, (Warped, Hop)) or isinstance(result, Blocked) and result.reason is not BlockReason.WALL:
        return False
    place = pose.state.place
    view = world.views[place.map]
    return (place.map not in world.encounter_maps and place not in forbidden and place.tile not in view.warps
            and world.at(place).behavior not in (Behavior.TALL_GRASS, Behavior.WATER)
            and place.tile not in view.occupied | view.scene_tiles)


def trainer_hazards(world):
    """Conservative declared sight rays; missing BDSP sight data stays a limit."""
    hazards = set()
    for name, view in world.views.items():
        for obj in view.data.get('objects', []):
            if obj.get('hide_flag') in view.context.flags:
                continue
            trainer = obj.get('trainer')
            if not trainer:
                continue
            looks = trainer.get('looks') or ([obj['facing']] if obj.get('facing') else [d.name.lower() for d in CLOCKWISE])
            for look in looks:
                direction = Direction[look.upper()]
                for distance in range(1, trainer['sight'] + 1):
                    tile = Tile(obj['x'], obj['y']).step(direction, distance)
                    cell = view.map_file.grid.at(tile)
                    if cell is None or cell.blocked:
                        break
                    hazards.add(Place(name, tile))
    return hazards

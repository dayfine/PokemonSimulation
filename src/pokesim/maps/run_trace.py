"""Read the route walks of AutoStory runs from a SerialPrograms log, for BDSP and FRLG.

Ported from dayfine/Arduino-Source draft #125 (devtools/maps/route_trace.py)
and extended with BDSP's story-step lines. A trace is a list of runs (one per
"Starting Program" line); a run is a list of walks in order; a walk has the
plan(s) it walked by, the steps it took and where they ended, and marks for
what happened on the way. `to_json()` gives the same as plain data.

Positions are lists of (map, x, y): a plan may start from several tiles. Map
names are as the log writes them ("Route 204", "FloaromaTown").

Shared route lines (Pokemon/Navigation/Pokemon_RouteLog.h), both games:
    [Route] <label>: plan from Route 204 (20, 27):                    ("an unknown tile" after a stop)
        west 9 (open) to Route 204 (11, 27)                           (continuation lines)
    [Route] Leg 1/1: west 9 (open) to Route 204 (11, 27)
    [Walk] <label>: west 9 (open): blocked after 4800ms, 4 moved chunks, 0 wild battle(s).
    [Route] <label>: west 9 (open): something the map lacks is at Route 204 (15, 27); marked it.
    [Route] <label>: west 9 (open): blocked after 4 of 9 tiles, at Route 204 (16, 27); planning again.
    [Route] <label>: west 8 (to wall): ended at Route 202 (23, 25) (walked).     (or assumed / unknown)
    [Route] <label>: found again at Route1 (12, 21), after 2 hold(s).
    [Route] <label>: Youngster Tristan stopped us about Route 202 (20, 10).
    [Route] <label>: arrived at Route 204 (11, 27).

BDSP story steps that walk without a plan (PokemonBDSP_AutoStory_StoryWalkSteps.cpp):
    [01.11] LEGS west_along_the_field: 8 taps west along the row we stopped on
    [Route] Turning west.
    [Walk] west_along_the_field: limit after 6400ms, 8 moved chunks, 0 wild battle(s).
    [01.11] west_along_the_field: taps west moved 8 of 8 tiles.
    [01.11] TALK old_man: he gives Jirachi with a Sword/Shield save
These log no tiles. Their walk starts where the last one ended, or at the
checkpoint's start given by the caller (`starts`); a tap count moves that
many tiles, a walk stopped by "blocked" runs to the first blocked tile on the
map (`maps`), and anything else ends on an unknown tile.

Older FRLG lines (before the shared ones) are read too:
    Route: plan, 3 steps: walk east 4 -> PalletTown (10, 6); walk north 4 (to wall) -> ...
    Route: walk north 8 -> Route1 (12, 21)
    Leg: a wild battle after 1253ms, stopping the leg.
    Route: stopped part-way, finding the player again at Route1 (12, 21); walk north 8 (to wall) -> Route1 (12, 21)
"""

import re
from dataclasses import asdict, dataclass, field

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Moved, WorldState

DIRECTIONS = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}

PLACE = re.compile(r"([A-Z][\w' .-]*?) \((-?\d+), (-?\d+)\)")
PREFIX = re.compile(r'^\ufeff?(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\.\d+ - \[[^\]]*\]: (.*)$')
PROGRAM = re.compile(r'Starting Program: (\w+?):(\w+)')
CHECKPOINT = re.compile(r'^\[Checkpoint\] (\S+): (start|done|failed)(?:.*?: (.*))?')
EVENT = re.compile(r'^\[Event\] (\S+ \S+): (start|done|failed|skipped)(?:: (.*))?')
RELOAD = re.compile(r'reloading for attempt (\d+)|Soft reset completed|Loading the save')
FAILURE = re.compile(r'(?:OperationFailedException\w*|FatalProgramException|InternalProgramError): (.*)')

#  FRLG, older lines.
F_STEP = re.compile(r'(walk|surf|face) (north|south|east|west)(?: (\d+))?((?: \((?:warp|to wall)\))*) -> (\w+) \((-?\d+), (-?\d+)\)')
F_STEP_LINE = re.compile(r'^Route: ' + F_STEP.pattern + r'\s*$')
F_PLAN = re.compile(r'^Route: plan, \d+ steps?: (.*)$')
F_ANCHOR = re.compile(r'^Route: stopped part-way, finding the player again at (\w+) \((-?\d+), (-?\d+)\)(.*)$')
F_LEG = re.compile(r'^Leg: (.+?)( \(seen late\))?(?: after \d+ms,)? (stopping the leg|walking to the wall again|at the end of the leg)')
F_WARP_HOLD = re.compile(r'^Route: (.+) on the way to the warp\.')

#  The shared route log. A leg: "east 15 (to wall)", "south 1 (warp)", "north 8 (open)", "surf east", "face west".
LEG_TEXT = r'(?:(?:north|south|east|west) \d+ \((?:to wall|open|warp)\)|(?:surf|face) (?:north|south|east|west))'
SHORT_LEG = r'(?:north|south|east|west) \d+(?: \([a-z ]+\))?'
B_PLAN = re.compile(r'^\[Route\] (.+?): plan from (.+?):\s*$')
B_PLAN_LEG = re.compile(r'^\s+(' + LEG_TEXT + r') to (.+?)\s*$')
B_LEG = re.compile(r'^\[Route\] Leg (\d+)/(\d+): (' + LEG_TEXT + r') to (.+?)\s*$')
B_END = re.compile(r'^\[Route\] (.+?): (' + LEG_TEXT + r'): ended at (.+?) \((walked|assumed|unknown)(?:: (.*))?\)\.\s*$')
B_FOUND = re.compile(r'^\[Route\] (.+?): found again at (.+?), after (\d+) hold')
B_WALK = re.compile(r'^\[Walk\] (.+?): (?:' + SHORT_LEG + r'(?:: [^:]+?)?: )?'
                    r'(blocked|limit|dialog|transition|arrived)(?: after (?:a )?(\d+)ms(?: hold)?)?'
                    r'(?:, (\d+) moved chunks)?, (\d+) wild battle')
B_STOPPED = re.compile(r'^\[Route\] (.+?): ' + SHORT_LEG + r': (.+?)[,;] at (.+?); planning again')
B_WAIT = re.compile(r'^\[Route\] (.+?): ' + SHORT_LEG + r': (stopped after about \d+ tiles, short of the wall|blocked after \d+ of \d+ tiles); ')
B_OBSTACLE = re.compile(r'^\[Route\] (.+?): ' + SHORT_LEG + r': something the map lacks is at (.+?); ')
B_BLOCKER = re.compile(r'^\[Route\] (.+?): ' + SHORT_LEG + r': (someone is in the way)')
B_ARRIVED = re.compile(r'^\[Route\] (.+?): arrived at (.+?)\.\s*$')
B_TRAINER = re.compile(r'^\[Route\] (.+?): (.+?) stopped us about (.+?)\.\s*$')
B_BATTLE = re.compile(r'^\[Walk\] (.+?): (wild battle.*|a battle started.*)$')
B_TURN = re.compile(r'^\[Route\] Turning (north|south|east|west)\.')
#  BDSP story steps.
S_STEP = re.compile(r'^\[(\d\d\.\d+\w*)\] ([A-Z]+) (\S+): (.*)$')
S_TAPS = re.compile(r'^\[\d\d\.\d+\w*\] (\S+): taps (north|south|east|west) moved (\d+) of (\d+) tiles')
S_BANNER = re.compile(r"^\[Story\] (\S+): ran (north|south|east|west) to (\w+)'s banner: (\w+)")


@dataclass
class Leg:
    action: str                 # walk, surf, face
    direction: str
    tiles: int
    to_wall: bool = False
    warp: bool = False
    ends: list = field(default_factory=list)    # [(map, x, y)]: the tiles it may end on

    def describe(self):
        if self.action == 'face':
            return f'face {self.direction}'
        flags = (' (warp)' if self.warp else '') + (' (to wall)' if self.to_wall else '')
        return f'{self.action} {self.direction} {self.tiles}{flags}'


@dataclass
class Plan:
    start: list                 # [(map, x, y)], empty when not known
    legs: list
    reason: str = 'plan'        # plan, replan (from where it stopped)
    inferred_start: bool = False


@dataclass
class Step:
    leg: Leg
    role: str = 'plan'          # plan, replan, hold, back, again, blind (a story step without a plan)
    start: list = field(default_factory=list)
    end: list = field(default_factory=list)
    outcome: str = ''           # done, stopped, blocked, limit, dialog, ...
    certain: bool = True        # False: where it went isn't known (a hold from an unknown tile)
    basis: str = 'walked'       # walked (as planned, seen or counted), assumed, unknown
    why: str = ''
    time: str = ''


@dataclass
class Mark:
    kind: str                   # battle, message, trainer, stop, wait, obstacle, blocker, reanchor, arrived, talk, failed
    at: list                    # [(map, x, y)]
    text: str
    step: int = -1              # index into Walk.steps, -1 if none


@dataclass
class Walk:
    label: str
    checkpoint: str = ''
    event: str = ''
    kind: str = 'route'         # route (planned), legs (a story step's blind legs), talk
    note: str = ''              # the story step's description
    plans: list = field(default_factory=list)
    steps: list = field(default_factory=list)
    marks: list = field(default_factory=list)
    outcome: str = 'open'       # done, failed, open
    error: str = ''
    time: str = ''
    attempt: int = 1


@dataclass
class Run:
    run_id: str
    game: str
    program: str
    time: str
    walks: list = field(default_factory=list)


def places(text):
    return [(m.group(1).strip(), int(m.group(2)), int(m.group(3))) for m in PLACE.finditer(text)]


def map_key(name):
    """The name a map is looked up by: logs write "Route 202", files "Route202"."""
    return re.sub(r'[^0-9a-z]', '', name.lower())


def _same_label(a, b):
    return a.replace('_', ' ').lower() == b.replace('_', ' ').lower()


def _leg_from_frlg(match):
    action, direction, tiles, flags, name, x, y = match.groups()
    return Leg(action, direction, int(tiles or 0), '(to wall)' in flags, '(warp)' in flags, [(name, int(x), int(y))])


def leg_from_text(text, ends):
    """A Leg from the route log's leg text ("east 15 (to wall)", "face west", ...)."""
    words = text.split()
    if words[0] in ('surf', 'face'):
        return Leg(words[0], words[1], 0, False, False, ends)
    return Leg('walk', words[0], int(words[1]), '(to wall)' in text, '(warp)' in text, ends)


def step_back(place, direction, tiles):
    dx, dy = DIRECTIONS[direction]
    return (place[0], place[1] - dx * tiles, place[2] - dy * tiles)


def shift(place, direction, tiles):
    return step_back(place, direction, -tiles)


class _Parser:
    def __init__(self, maps=None, starts=None):
        self.maps = maps or (lambda name: None)
        self.starts = starts or {}
        self.runs = []
        self.run = None
        self.checkpoint = ''
        self.event = ''
        self.walk = None
        self.pos = []
        self.time = ''
        self.attempt = 1
        self.holds = []
        self.back_to = None
        self.explicit_plan = False
        self.plan_pending = None
        self.replan_expected = False
        self.story_kind = ''

    #  Runs and walks.
    def start_run(self, game, program):
        self.close_walk()
        stamp = re.sub(r'[^0-9]', '', self.time)
        self.run = Run(f'{game.lower().replace("pokemon", "")}-{stamp[:8]}-{stamp[8:14]}', game, program, self.time)
        self.runs.append(self.run)
        self.checkpoint = self.event = ''
        self.pos = []
        self.attempt = 1

    def ensure_run(self, game):
        if self.run is None:
            self.start_run(game, 'unknown')

    def new_walk(self, label, kind='route', note=''):
        self.close_walk()
        self.walk = Walk(label, self.checkpoint, self.event, kind, note, time=self.time, attempt=self.attempt)
        self.run.walks.append(self.walk)
        self.holds, self.back_to, self.explicit_plan = [], None, False
        return self.walk

    def close_walk(self, outcome=None):
        walk = self.walk
        if walk is None:
            return
        self.finish_step()
        if walk.kind == 'route' and not self.explicit_plan and walk.steps and not walk.plans:
            self.implicit_plan(walk)
        if outcome and walk.outcome == 'open':
            walk.outcome = outcome
        self.walk = None
        self.plan_pending = None

    def finish_step(self):
        """The current step ended as planned unless something said otherwise."""
        if self.walk is None or not self.walk.steps:
            return
        step = self.walk.steps[-1]
        if step.role == 'blind':
            return
        if step.outcome in ('', 'late', 'blocked', 'limit', 'arrived', 'transition'):
            if not step.outcome or step.outcome == 'late':
                step.outcome = 'done'
            if not step.end:
                step.end = list(step.leg.ends)
            self.pos = list(step.end)
        elif step.outcome == 'stopped' and not step.end:
            self.pos = []

    def mark(self, kind, at, text):
        if self.walk is None:
            return
        self.walk.marks.append(Mark(kind, list(at), text, len(self.walk.steps) - 1))

    def fail(self, text):
        walk = self.walk or (self.run.walks[-1] if self.run and self.run.walks else None)
        if walk is None or (walk is not self.walk and walk.event != self.event):
            return
        if walk.outcome == 'failed' and walk.error:
            return
        last = walk.steps[-1] if walk.steps else None
        if walk is self.walk and last is not None and last.outcome == '' and 'walk_overworld_route' in text:
            last.outcome = 'failed'
            last.basis, last.why = 'unknown', 'failed on this step'
            self.pos = list(last.start)
        elif walk is self.walk:
            self.finish_step()
        at = self.pos or (last.start or last.leg.ends if last else [])
        walk.marks.append(Mark('failed', list(at), text, len(walk.steps) - 1))
        walk.outcome, walk.error = 'failed', text

    #  FRLG, older lines.
    def frlg_plan(self, text):
        self.ensure_run('PokemonFRLG')
        walk = self.new_walk(self.event or 'route')
        self.explicit_plan = True
        legs = [_leg_from_frlg(m) for m in F_STEP.finditer(text)]
        start = self.infer_start(legs[0]) if legs else []
        walk.plans.append(Plan(start, legs, 'plan', True))

    def infer_start(self, leg):
        """Where a walk's first step started: worked back from its end, or where the last walk ended."""
        if leg.action == 'face':
            return list(leg.ends)
        end = leg.ends[0]
        back = step_back(end, leg.direction, leg.tiles)
        known = self.maps(end[0])
        inside = back[1] >= 0 and back[2] >= 0 and (
            known is None or known.map_file.grid.contains(Tile(back[1], back[2])))
        if not leg.warp and inside:
            return [back]
        return list(self.pos)

    def frlg_step(self, leg):
        self.ensure_run('PokemonFRLG')
        if self.walk is None:
            self.new_walk(self.event or 'route')
        walk = self.walk
        self.finish_step()
        if not walk.steps:
            planned = walk.plans[0].start if walk.plans else []
            self.pos = list(planned) or self.infer_start(leg)
        step = Step(leg, start=list(self.pos), time=self.time)
        last = walk.steps[-1] if walk.steps else None
        if self.holds:
            self.holds.pop(0)
            step.role = 'hold'
            step.certain = not self.holds       # only the last hold ends on a known tile
            step.basis, step.why = 'unknown', 'found again here' if step.certain else 'hold from an unknown tile'
            if not step.certain:
                step.end = []
        elif self.back_to is not None:
            step.role = 'back'
            if leg.ends and leg.ends[0] == self.back_to:
                self.back_to = None
        elif last is not None and last.role == 'plan' and _same_leg(last.leg, leg) and leg.to_wall:
            step.role = 'again'
        walk.steps.append(step)
        if not step.certain:
            step.outcome = 'done'
            self.pos = []

    def frlg_anchor(self, at, rest):
        walk = self.walk
        if walk is None or not walk.steps:
            return
        stopped = walk.steps[-1]
        stopped.outcome = 'stopped'
        stopped.end = []
        self.pos = []
        self.holds = [_leg_from_frlg(m) for m in F_STEP.finditer(rest)]
        self.back_to = stopped.leg.ends[0] if stopped.leg.ends and stopped.leg.ends[0] != at else None
        self.mark('reanchor', [at], f'found again at {at[0]} ({at[1]}, {at[2]}) after {len(self.holds)} hold(s)')

    def frlg_leg_event(self, what, late, how):
        walk = self.walk
        if walk is None or not walk.steps:
            return
        step = walk.steps[-1]
        kind = 'battle' if 'battle' in what else 'message' if 'message' in what else 'interrupt'
        text = what + (' (seen late)' if late else '') + ', ' + how
        if how == 'stopping the leg':
            step.outcome = 'stopped'
            step.basis, step.why = 'unknown', f'stopped by {kind}: tile unknown'
            self.mark(kind, step.start, text)
        elif how == 'at the end of the leg':
            if late and step.leg.to_wall:
                step.outcome = 'late'
            step.basis, step.why = 'assumed', f'assumed: {kind} at leg end'
            self.mark(kind, step.leg.ends, text)
        else:
            step.basis, step.why = 'assumed', f'assumed after {kind}'
            self.mark(kind, step.start, text)

    def implicit_plan(self, walk):
        legs = [step.leg for step in walk.steps if step.role == 'plan']
        start = walk.steps[0].start if walk.steps else []
        walk.plans.append(Plan(list(start), legs, 'plan', True))

    #  Shared route lines.
    def bdsp_plan(self, label, start_text):
        self.ensure_run('PokemonBDSP')
        start = places(start_text)
        replan = self.replan_expected or self.run.game != 'PokemonFRLG'
        self.replan_expected = False
        if (self.walk is not None and self.walk.kind == 'route' and self.walk.label == label
                and self.walk.outcome == 'open' and replan):
            self.finish_step()
            plan = Plan(start, [], 'replan')
        else:
            self.new_walk(label)
            self.explicit_plan = True
            plan = Plan(start, [], 'plan')
        self.walk.plans.append(plan)
        self.plan_pending = plan
        self.pos = list(start)

    def bdsp_leg(self, leg_text, ends_text):
        if self.walk is None or self.walk.kind != 'route':
            self.ensure_run('PokemonBDSP')
            self.new_walk(self.event or 'route')
            self.explicit_plan = True
            self.walk.plans.append(Plan(list(self.pos), [], 'plan'))
        self.finish_step()
        leg = leg_from_text(leg_text, places(ends_text))
        plan = self.walk.plans[-1] if self.walk.plans else None
        if plan is not None and not any(_same_leg(leg, other) for other in plan.legs):
            plan.legs.append(leg)
        role = 'plan' if plan is None or plan.reason == 'plan' else 'replan'
        self.walk.steps.append(Step(leg, role, list(self.pos), time=self.time))

    def leg_end(self, step, at, basis, why):
        step.basis = basis
        step.why = f'{basis}: {why}' if why and basis != 'walked' else why
        if basis == 'unknown':
            step.outcome, step.end = 'stopped', []
            self.pos = []
            self.replan_expected = 'stopped' in why
            if not step.start:
                step.role = 'hold'
                step.certain = False
            return
        step.outcome, step.end = 'done', at
        self.pos = list(at)

    #  Story steps without a plan.
    def story_step(self, kind, name, note):
        self.ensure_run('PokemonBDSP')
        self.story_kind = kind
        if kind == 'LEGS':
            self.new_walk(name, 'legs', note)
        elif kind == 'TALK':
            self.new_walk(name, 'talk', note)
        else:
            self.close_walk()

    def turn(self, direction):
        walk = self.walk
        if walk is None or walk.kind == 'route':
            return
        if walk.kind == 'talk':
            self.mark('talk', self.pos, f'{walk.label}, facing {direction}: {walk.note}')
            return
        if walk.steps and walk.steps[-1].leg.direction == direction and walk.steps[-1].outcome == '':
            return
        walk.steps.append(Step(Leg('walk', direction, 0), 'blind', list(self.pos), outcome='', time=self.time))

    def blind_end(self, step, how, chunks, tiles=None):
        """Where a blind step ended: a tap count, the first blocked tile on the map, or unknown."""
        step.outcome = how
        if tiles is not None:
            step.leg.tiles = tiles
            step.end = [shift(p, step.leg.direction, tiles) for p in step.start]
            step.basis, step.why = 'walked', f'counted: {tiles} tap(s)'
        elif how == 'blocked' and step.start and self.maps(step.start[0][0]) is not None:
            view = self.maps(step.start[0][0])
            step.end = [run_until_blocked(view, p, step.leg.direction) for p in step.start]
            step.leg.tiles = abs(step.end[0][1] - step.start[0][1]) + abs(step.end[0][2] - step.start[0][2])
            step.basis, step.why = 'assumed', 'assumed: to the first blocked tile on the map'
        elif how == 'limit' and chunks is not None and step.start:
            step.leg.tiles = chunks
            step.end = [shift(p, step.leg.direction, chunks) for p in step.start]
            step.basis, step.why = 'assumed', f'assumed: {chunks} moved chunk(s), a tile each'
        else:
            step.end = []
            step.basis, step.why = 'unknown', f'unknown: {how}' + ('' if step.start else ', from an unknown tile')
        self.pos = list(step.end)

    def bdsp_line(self, text):
        m = B_PLAN.match(text)
        if m:
            self.bdsp_plan(m.group(1), m.group(2))
            return
        self.plan_pending = None
        m = B_LEG.match(text)
        if m:
            self.bdsp_leg(m.group(3), m.group(4))
            return
        m = B_TURN.match(text)
        if m:
            self.turn(m.group(1))
            return
        walk = self.walk
        if walk is None:
            return
        step = walk.steps[-1] if walk.steps else None
        m = B_WALK.match(text)
        if m and _same_label(m.group(1), walk.label) and step is not None:
            how, chunks, battles = m.group(2), m.group(4), int(m.group(5))
            if step.role == 'blind':
                self.blind_end(step, how, int(chunks) if chunks is not None else None)
            elif how in ('blocked', 'limit', 'arrived', 'transition') and step.outcome != 'stopped':
                step.outcome = how
            if how == 'dialog':
                step.basis, step.why = 'assumed', 'assumed after a dialog'
                self.mark('message', step.start, 'a dialog stopped the leg')
            if battles:
                step.basis, step.why = 'assumed', f'assumed after {battles} battle(s)'
                self.mark('battle', step.end or step.leg.ends, f'{battles} wild battle(s) on {step.leg.describe()}')
            return
        if walk.kind != 'route':
            return
        m = B_END.match(text)
        if m and m.group(1) == walk.label and step is not None:
            self.leg_end(step, places(m.group(3)), m.group(4), m.group(5) or '')
            return
        m = B_FOUND.match(text)
        if m and m.group(1) == walk.label:
            at = places(m.group(2))
            self.pos = at
            self.mark('reanchor', at, f'found again after {m.group(3)} hold(s)')
            return
        m = B_OBSTACLE.match(text)
        if m and m.group(1) == walk.label:
            self.mark('obstacle', places(m.group(2)), 'something the map lacks; marked it')
            return
        m = B_BLOCKER.match(text)
        if m and m.group(1) == walk.label and step is not None:
            waits = [mark.at for mark in walk.marks if mark.kind == 'wait']
            self.mark('blocker', waits[-1] if waits else step.start, 'someone is in the way; talked to them')
            return
        m = B_STOPPED.match(text)
        if m and m.group(1) == walk.label and step is not None:
            at = places(m.group(3))
            step.outcome, step.end = 'stopped', at
            step.basis, step.why = 'walked', ''
            self.pos = at
            self.replan_expected = True
            self.mark('stop', at, m.group(2))
            return
        m = B_WAIT.match(text)
        if m and m.group(1) == walk.label and step is not None:
            step.basis, step.why = 'assumed', 'assumed after a stall'
            moved = re.search(r'(?:after|about) (\d+)', m.group(2))
            at = [shift(p, step.leg.direction, int(moved.group(1))) for p in step.start] if moved else step.start
            self.mark('wait', at, m.group(2) + '; waited')
            return
        m = B_ARRIVED.match(text)
        if m and m.group(1) == walk.label:
            at = places(m.group(2))
            if step is not None:
                if step.outcome in ('', 'blocked', 'limit'):
                    step.outcome = step.outcome or 'done'
                step.end = at
            self.pos = at
            walk.outcome = 'done'
            return
        m = B_TRAINER.match(text)
        if m and m.group(1) == walk.label:
            self.mark('trainer', places(m.group(3)), f'{m.group(2)} stopped us')
            return
        m = B_BATTLE.match(text)
        if m and m.group(1) == walk.label:
            self.mark('battle', self.pos or (step.start if step else []), m.group(2))

    def story_line(self, text):
        m = S_TAPS.match(text)
        if m:
            walk = self.walk
            if walk is not None and walk.kind == 'legs' and _same_label(m.group(1), walk.label) and walk.steps:
                step = walk.steps[-1]
                self.blind_end(step, step.outcome or 'limit', None, int(m.group(3)))
            return
        m = S_STEP.match(text)
        if m:
            self.story_step(m.group(2), m.group(3), m.group(4))

    #  Lines.
    def feed(self, raw):
        m = PREFIX.match(raw)
        if not m:
            if self.plan_pending is not None:
                leg = B_PLAN_LEG.match(raw)
                if leg:
                    self.plan_pending.legs.append(leg_from_text(leg.group(1), places(leg.group(2))))
            return
        self.time, text = m.group(1), m.group(2)
        p = PROGRAM.search(text)
        if p and '<b>' in text:
            self.start_run(p.group(1), f'{p.group(1)}:{p.group(2)}')
            return
        if self.run is None and not (text.startswith('Route: ') or text.startswith('[Route]')):
            return
        r = RELOAD.search(text)
        if r:
            self.close_walk()
            self.pos = []
            if r.group(1):
                self.attempt = int(r.group(1))
            return
        c = CHECKPOINT.match(text)
        if c:
            if c.group(2) == 'start':
                self.close_walk()
                self.checkpoint, self.event = c.group(1), ''
                if self.checkpoint in self.starts:
                    self.pos = list(self.starts[self.checkpoint])
            elif c.group(2) == 'failed':
                self.fail(c.group(3) or text)
            else:
                self.attempt = 1
            return
        e = EVENT.match(text)
        if e:
            if e.group(2) == 'start':
                self.close_walk()
                self.event = e.group(1)
            elif e.group(2) == 'done':
                self.close_walk('done')
            elif e.group(2) == 'failed':
                self.fail(e.group(3) or 'failed')
                self.close_walk('failed')
            return
        f = FAILURE.search(text)
        if f:
            self.fail(f.group(1))
            return
        b = S_BANNER.match(text)
        if b:
            #  Ran onto another map; where on it isn't logged.
            if self.walk is not None and self.walk.steps:
                self.walk.steps[-1].end = []
                self.walk.steps[-1].basis = 'unknown'
                self.walk.steps[-1].why = f'unknown: ran into {b.group(3)}'
            self.pos = []
            return
        if text.startswith('Route: ') or text.startswith('Leg: '):
            self.frlg_line(text)
        elif text.startswith('[Route]') or text.startswith('[Walk]'):
            self.bdsp_line(text)
        elif text.startswith('['):
            self.story_line(text)

    def frlg_line(self, text):
        m = F_PLAN.match(text)
        if m:
            self.frlg_plan(m.group(1))
            return
        m = F_STEP_LINE.match(text)
        if m:
            self.frlg_step(_leg_from_frlg(m))
            return
        m = F_ANCHOR.match(text)
        if m:
            self.frlg_anchor((m.group(1), int(m.group(2)), int(m.group(3))), m.group(4))
            return
        m = F_LEG.match(text)
        if m:
            self.frlg_leg_event(m.group(1), bool(m.group(2)), m.group(3))
            return
        m = F_WARP_HOLD.match(text)
        if m and self.walk is not None:
            self.mark('message', self.walk.steps[-1].start if self.walk.steps else [], m.group(1) + ' on the way to the warp')


def _same_leg(a, b):
    return a.direction == b.direction and a.tiles == b.tiles and a.ends == b.ends


def run_until_blocked(view, place, direction):
    """Where a walk from `place` toward `direction` stops on `view`: the last tile before a wall, person or edge."""
    name, x, y = place
    heading = Direction[direction.upper()]
    state = WorldState(Place(view.map_file.name, Tile(x, y)), 0)
    for _ in range(view.map_file.grid.width + view.map_file.grid.height):
        try:
            result = view.try_step(state, heading, view.rules, ())
        except (ValueError, KeyError, IndexError):
            break
        if not isinstance(result, Moved):
            break
        state = result.state
    return (name, state.place.tile.x, state.place.tile.y)


def parse(lines, maps=None, starts=None):
    """The runs in `lines` (a log's lines), each with its walks.

    `maps(name)` gives the LocalMap a log map name is drawn on, or None.
    `starts` maps a checkpoint ("01.11") to the tiles it starts on, [(map, x, y)].
    """
    parser = _Parser(maps, starts)
    for line in lines:
        parser.feed(line.rstrip('\r\n'))
    parser.close_walk()
    return [run for run in parser.runs if run.walks]


def to_json(runs):
    return [asdict(run) for run in runs]

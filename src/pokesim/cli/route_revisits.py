r"""Grade AutoStory walks from a SerialPrograms log: the tiles each walked again.

    PYTHONPATH=src python3 -m pokesim.cli.route_revisits SerialPrograms.log [--after "Lab: running r5"]

A route that crosses a tile twice walks back over its own way, which is
usually a planner or recovery choice worth a look. For each walk (a story
event's route, from its first leg to its last) it prints the legs, the
re-plans, the tiles walked against the tiles first planned, and the tiles
walked onto again.

It reads the walker's [Leg] lines (each leg's direction, tile count and end
tile) and its "[Route] <event>: plan from ..." lines. A leg is laid back
from its end along its direction. A leg that ended at an unknown tile places
nothing, and the next leg is laid back from its own end. A warp or a map
connection counts the tiles on the map left, short of the warp, and the end.
"""

import argparse
import json
import re
import sys

LEG = re.compile(r'\[Leg\] (\{.*\})\s*$')
PLAN = re.compile(r'\[Route\] (.+?): plan from (.+?): (.*)$')
PLACE = re.compile(r'^(\S+) \((\d+), (\d+)\)$')
PLANNED_LEG = re.compile(r'\b(north|south|east|west) (\d+)\b')
STEP = {'north': (0, -1), 'south': (0, 1), 'east': (1, 0), 'west': (-1, 0)}


class Grade:
    """One walk: a story event's legs from its first on."""

    def __init__(self, checkpoint, event):
        self.checkpoint, self.event = checkpoint, event
        self.legs = 0
        self.replans = 0
        self.planned_tiles = 0
        self.walked_tiles = 0
        self.revisited = []
        self.plans = 0
        self.at = None
        self.visited = set()

    def plan(self, start, legs):
        if self.plans == 0:
            self.planned_tiles = sum(int(tiles) for _, tiles in PLANNED_LEG.findall(legs))
            place = PLACE.match(start)
            if place and self.at is None:
                self.at = (place.group(1), int(place.group(2)), int(place.group(3)))
                self.visited.add(self.at)
        else:
            self.replans += 1
        self.plans += 1

    def visit(self, tile):
        if tile in self.visited:
            self.revisited.append(tile)
        else:
            self.visited.add(tile)

    def leg(self, record):
        self.legs += 1
        tiles = int(record.get('tiles', 0))
        self.walked_tiles += tiles
        end = record.get('end') or []
        if not end:
            self.at = None
            return
        end = (end[0][0], int(end[0][1]), int(end[0][2]))
        dx, dy = STEP.get(record.get('dir'), (0, 0))
        if tiles == 0 or end == self.at:
            self.at = end
            return
        if self.at is not None and self.at[0] != end[0]:
            # A warp or a connection: the map left, short of the warp, then the end.
            for c in range(1, tiles):
                self.visit((self.at[0], self.at[1] + dx * c, self.at[2] + dy * c))
            self.visit(end)
        else:
            # Laid back from the end; where it starts, a leg that ended short
            # of a known start doesn't say.
            line = [(end[0], end[1] - dx * c, end[2] - dy * c) for c in range(tiles)]
            if self.at is not None and self.at in line:
                line = line[:line.index(self.at)]
            for tile in reversed(line):
                self.visit(tile)
        self.at = end


def grade(lines):
    """[Grade] per walk in `lines`, in log order."""
    grades = []
    pending = []
    for line in lines:
        plan = PLAN.search(line)
        if plan:
            pending.append(plan.groups())
            continue
        found = LEG.search(line)
        if not found:
            continue
        try:
            record = json.loads(found.group(1))
        except ValueError:
            continue
        current = grades[-1] if grades else None
        key = (record.get('checkpoint'), record.get('event'))
        if current is None or int(record.get('leg', 0)) == 1 or (current.checkpoint, current.event) != key:
            current = Grade(*key)
            grades.append(current)
        for event, start, legs in pending:
            if event == current.event:
                current.plan(start, legs)
        pending = []
        current.leg(record)
    return grades


def place_text(tile):
    return '{} ({}, {})'.format(*tile)


def report(grades):
    for g in grades:
        revisited = '{} revisited'.format(len(g.revisited))
        if g.revisited:
            revisited += ': ' + ', '.join(place_text(tile) for tile in g.revisited)
        print('{} {}: {} legs, {} re-plan{}, walked {} of {} planned tiles, {}'.format(
            g.checkpoint, g.event, g.legs, g.replans, '' if g.replans == 1 else 's',
            g.walked_tiles, g.planned_tiles, revisited))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('log')
    parser.add_argument('--after', help='read the log from the last line containing this text on')
    args = parser.parse_args(argv)
    with open(args.log, encoding='utf-8', errors='replace') as file:
        lines = file.readlines()
    if args.after:
        starts = [c for c, line in enumerate(lines) if args.after in line]
        if not starts:
            print('No line contains: ' + args.after, file=sys.stderr)
            return 1
        lines = lines[starts[-1]:]
    report(grade(lines))
    return 0


if __name__ == '__main__':
    sys.exit(main())

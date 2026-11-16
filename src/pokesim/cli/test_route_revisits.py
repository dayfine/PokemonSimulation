"""Grades of AutoStory walks read from a SerialPrograms log's [Leg] lines."""

import io
import unittest
from contextlib import redirect_stdout

from pokesim.cli import route_revisits

PREFIX = '2026-11-15 15:04:35.057665 - [Console 0]: '


def leg(number, direction, tiles, end, planned_end=None, known='dead_reckoned', event='below_center_door'):
    def place(at):
        return '[]' if at is None else '[["{}",{},{}]]'.format(*at)
    return PREFIX + ('[Leg] {{"checkpoint":"16.06","dir":"{}","end":{},"event":"{}","known":"{}","leg":{},'
                     '"planned_end":{},"tiles":{}}}').format(
        direction, place(end), event, known, number, place(planned_end or end), tiles)


def plan(start, legs, event='below_center_door'):
    return PREFIX + '[Route] {}: plan from {}: {}'.format(event, start, legs)


#  16.06 on console B (2026-11-15 15:04, r5), cut down: a position check after
#  "west 4 (open)" on SilphCo_7F re-plans from an unknown tile, and the walk
#  goes back east onto (1, 9), off the wall it was held to, and north onto
#  (1, 7), where the leg checked had ended.
SILPH_7F = [
    plan('SilphCo_7F (5, 8)', 'north 1 (to wall) to SilphCo_7F (5, 7); west 4 (open) to SilphCo_7F (1, 7); '
         'north 3 (to wall) to SilphCo_7F (1, 4)'),
    leg(1, 'north', 1, ('SilphCo_7F', 5, 7)),
    leg(2, 'west', 4, ('SilphCo_7F', 1, 7)),
    plan('an unknown tile', 'south 2 (to wall) to SilphCo_7F (3, 9); west 3 (to wall) to SilphCo_7F (0, 9); '
         'east 1 (open) to SilphCo_7F (1, 9); north 2 (open) to SilphCo_7F (1, 7); north 3 (to wall) to SilphCo_7F (1, 4)'),
    leg(3, 'south', 2, None, planned_end=('SilphCo_7F', 3, 9), known='unknown'),
    leg(4, 'west', 3, ('SilphCo_7F', 0, 9)),
    leg(5, 'east', 1, ('SilphCo_7F', 1, 9)),
    leg(6, 'north', 2, ('SilphCo_7F', 1, 7)),
    leg(7, 'north', 3, ('SilphCo_7F', 1, 4)),
]


class RouteRevisitsTest(unittest.TestCase):
    def test_replan_walks_back_over_its_tiles(self):
        grades = route_revisits.grade(SILPH_7F)
        self.assertEqual(len(grades), 1)
        grade = grades[0]
        self.assertEqual((grade.checkpoint, grade.event), ('16.06', 'below_center_door'))
        self.assertEqual(grade.legs, 7)
        self.assertEqual(grade.replans, 1)
        self.assertEqual(grade.planned_tiles, 8)
        self.assertEqual(grade.walked_tiles, 16)
        self.assertEqual(grade.revisited, [('SilphCo_7F', 1, 9), ('SilphCo_7F', 1, 7)])

    def test_planned_walk_crosses_no_tile_twice(self):
        grade = route_revisits.grade(SILPH_7F[:3] + SILPH_7F[-1:])[0]
        self.assertEqual((grade.replans, grade.walked_tiles, grade.revisited), (0, 8, []))

    def test_warp_starts_the_next_map(self):
        lines = [
            plan('SilphCo_11F (2, 19)', 'north 14 (warp) to SilphCo_7F (5, 8); north 1 (to wall) to SilphCo_7F (5, 7)'),
            leg(1, 'north', 14, ('SilphCo_7F', 5, 8), known='fade'),
            leg(2, 'north', 1, ('SilphCo_7F', 5, 7)),
        ]
        grade = route_revisits.grade(lines)[0]
        self.assertEqual((grade.planned_tiles, grade.walked_tiles, grade.revisited), (15, 15, []))

    def test_a_new_first_leg_starts_another_walk(self):
        lines = SILPH_7F[:3] + [leg(1, 'north', 1, ('SilphCo_7F', 5, 7))]
        self.assertEqual([grade.legs for grade in route_revisits.grade(lines)], [2, 1])

    def test_report(self):
        out = io.StringIO()
        with redirect_stdout(out):
            route_revisits.report(route_revisits.grade(SILPH_7F))
        self.assertEqual(out.getvalue().splitlines(), [
            '16.06 below_center_door: 7 legs, 1 re-plan, walked 16 of 8 planned tiles, 2 revisited: SilphCo_7F (1, 9), SilphCo_7F (1, 7)',
        ])


if __name__ == '__main__':
    unittest.main()

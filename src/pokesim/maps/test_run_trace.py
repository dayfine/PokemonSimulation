"""Run logs to walked traces: BDSP's 01.10/01.11 console runs (2026-11-08), and the FRLG formats."""

import json
import os
from pathlib import Path
import unittest

from pokesim._test_paths import GAMES
from pokesim.maps import run_trace
from pokesim.maps.local_routing import Context, LocalMap

TESTDATA = Path(__file__).parent / 'testdata'
FLOAROMA_START = {'01.11': [('FloaromaTown', 11, 28)]}


def bdsp_maps():
    views = {}

    def lookup(name):
        key = run_trace.map_key(name)
        file = {'route204': 'Route204North', 'floaromatown': 'FloaromaTown'}.get(key)
        if file is None:
            return None
        if file not in views:
            data = json.loads(Path(os.path.join(GAMES, 'bdsp', 'maps', 'runtime', file + '.json')).read_text())
            views[file] = LocalMap(data, 'bdsp', Context(acknowledge_map_state=True))
        return views[file]
    return lookup


def read_log(name):
    return (TESTDATA / name).read_text(encoding='utf-8').splitlines()


def stamp(lines):
    return [f'2026-11-01 09:00:{i:02d}.000000 - [Console 0]: {line}' if not line.startswith('    ') else line
            for i, line in enumerate(lines)]


def walked(walk):
    return [(step.leg.describe(), step.start[0][1:] if step.start else None,
             step.end[0][1:] if step.end else None, step.basis) for step in walk.steps]


class FailingRunTest(unittest.TestCase):
    """18:38-18:41: 01.10 passes; 01.11's walk ends a tile west of the old man and nobody answers."""

    def setUp(self):
        runs = run_trace.parse(read_log('bdsp-0110-0111-fail.log'), bdsp_maps(), FLOAROMA_START)
        self.assertEqual(len(runs), 1)
        self.run = runs[0]
        self.walks = {(walk.checkpoint, walk.label): walk for walk in self.run.walks}

    def test_run_and_checkpoints(self):
        self.assertEqual(self.run.game, 'PokemonBDSP')
        self.assertEqual(self.run.run_id, 'bdsp-20261108-183821')
        self.assertEqual([walk.label for walk in self.run.walks if walk.checkpoint == '01.11'],
                         ['west_along_the_field', 'up_to_the_old_woman', 'old_woman', 'below_the_old_man', 'old_man'])

    def test_planned_route_with_a_replan(self):
        walk = self.walks['01.10', 'line 2']
        self.assertEqual([(plan.reason, plan.start, [leg.describe() for leg in plan.legs]) for plan in walk.plans], [
            ('plan', [('Route 204', 20, 27)], ['walk west 9']),
            ('replan', [('Route 204', 16, 27)], ['walk south 2', 'walk west 5', 'walk north 2'])])
        self.assertEqual([step.end[0][1:] for step in walk.steps], [(16, 27), (16, 29), (11, 29), (11, 27)])
        self.assertEqual(walk.steps[0].outcome, 'stopped')
        marks = [(mark.kind, mark.at[0][1:]) for mark in walk.marks]
        self.assertEqual(marks, [('wait', (16, 27)), ('blocker', (16, 27)), ('obstacle', (15, 27)), ('stop', (16, 27))])
        self.assertEqual(walk.outcome, 'done')

    def test_blind_legs_from_the_checkpoint_start(self):
        self.assertEqual(walked(self.walks['01.11', 'west_along_the_field']),
                         [('walk west 8', (11, 28), (3, 28), 'walked')])
        # North until blocked: the pinned map's old man (3, 25) stops it below him.
        self.assertEqual(walked(self.walks['01.11', 'up_to_the_old_woman']),
                         [('walk north 2', (3, 28), (3, 26), 'assumed')])
        self.assertEqual(walked(self.walks['01.11', 'below_the_old_man']),
                         [('walk west 1', (3, 26), (2, 26), 'walked')])

    def test_failure_is_marked_where_the_walk_ended(self):
        walk = self.walks['01.11', 'old_man']
        self.assertEqual(walk.kind, 'talk')
        self.assertEqual(walk.outcome, 'failed')
        self.assertEqual(walk.error, 'old man: nobody answered.')
        self.assertEqual([(mark.kind, mark.at) for mark in walk.marks],
                         [('talk', [('FloaromaTown', 2, 26)]), ('failed', [('FloaromaTown', 2, 26)])])

    def test_run_onto_another_map_loses_the_tile(self):
        step = self.walks['01.10', 'into_floaroma'].steps[0]
        self.assertEqual((step.end, step.basis), ([], 'unknown'))
        self.assertIn('FloaromaTown', step.why)

    def test_without_a_start_blind_legs_are_not_placed(self):
        runs = run_trace.parse(read_log('bdsp-0110-0111-fail.log'), bdsp_maps())
        walk = next(walk for walk in runs[0].walks if walk.label == 'west_along_the_field')
        self.assertEqual((walk.steps[0].start, walk.steps[0].end, walk.steps[0].basis), ([], [], 'walked'))

    def test_json_is_plain_data(self):
        data = json.loads(json.dumps(run_trace.to_json([self.run])))
        self.assertEqual(data[0]['walks'][-1]['error'], 'old man: nobody answered.')


class PassingRunTest(unittest.TestCase):
    """19:09-19:10: west to the field's edge, 4 taps east, north to her; both talks answer."""

    def test_walks(self):
        runs = run_trace.parse(read_log('bdsp-0111-pass.log'), bdsp_maps(), FLOAROMA_START)
        walks = runs[0].walks
        self.assertEqual([walked(walk) for walk in walks if walk.kind == 'legs'], [
            [('walk west 11', (11, 28), (0, 28), 'assumed')],
            [('walk east 4', (0, 28), (4, 28), 'walked')],
            [('walk north 2', (4, 28), (4, 26), 'assumed')],
            [('walk west 1', (4, 26), (3, 26), 'walked')]])
        self.assertTrue(all(walk.outcome == 'done' for walk in walks))
        talks = [(walk.label, walk.marks[0].at[0][1:]) for walk in walks if walk.kind == 'talk']
        self.assertEqual(talks, [('old_woman', (4, 26)), ('old_man', (3, 26))])


FRLG_LOG = stamp([
    '<b>Starting Program: PokemonFRLG:AutoStory</b>',
    '[Checkpoint] 00.05: start, 2 events',
    '[Event] 00.05/2 to_route: start',
    'Route: walk west 4 -> TestTown (4, 1)',
    'Route: walk south 3 -> TestTown (4, 4)',
    'Leg: a wild battle after 900ms, stopping the leg.',
    'Route: stopped part-way, finding the player again at TestTown (8, 3); walk east 6 (to wall) -> TestTown (6, 2); walk south 9 (to wall) -> TestTown (8, 3)',
    'Route: walk east 6 (to wall) -> TestTown (6, 2)',
    'Route: walk south 9 (to wall) -> TestTown (8, 3)',
    'Route: walk west 4 -> TestTown (4, 3)',
    'Route: walk south 1 -> TestTown (4, 4)',
    'Route: walk north 4 -> Route9 (4, 3)',
    '[Event] 00.05/2 to_route: done',
    '[Event] 00.05/3 house: start',
    'Route: plan, 3 steps: walk south 4 -> TestTown (4, 4); walk east 3 -> TestTown (7, 4); walk south 1 (warp) -> TestHouse (3, 3)',
    'Route: walk south 4 -> TestTown (4, 4)',
    'Route: walk east 3 -> TestTown (7, 4)',
    'Leg: a message after 400ms, stopping the leg.',
    'OperationFailedExceptionWithScreenshot: walk_overworld_route(): stopped part-way on walk east 3 -> TestTown (7, 4), with no walls near it to find the player again.',
    '[Event] 00.05/3 house: failed: operation_failed: walk_overworld_route(): stopped part-way',
])

SHARED_FRLG_LOG = stamp([
    '<b>Starting Program: PokemonFRLG:AutoStory</b>',
    '[Event] 00.05/2 to_route: start',
    '[Route] to_route: plan from TestTown (8, 1):',
    '    west 4 (open) to TestTown (4, 1)',
    '    south 3 (open) to TestTown (4, 4)',
    '[Route] Leg 1/2: west 4 (open) to TestTown (4, 1)',
    '[Route] to_route: west 4 (open): ended at TestTown (4, 1) (walked).',
    '[Route] Leg 2/2: south 3 (open) to TestTown (4, 4)',
    'Leg: a wild battle after 900ms, stopping the leg.',
    '[Route] to_route: south 3 (open): ended at an unknown tile (unknown: stopped part-way).',
    '[Route] to_route: plan from an unknown tile:',
    '    south 9 (to wall) to TestTown (4, 5)',
    '[Route] Leg 1/1: south 9 (to wall) to TestTown (4, 5)',
    '[Route] to_route: south 9 (to wall): ended at TestTown (4, 5) (walked).',
    '[Route] to_route: found again at TestTown (4, 5), after 1 hold(s).',
    '[Route] to_route: arrived at TestTown (4, 5).',
    '[Event] 00.05/2 to_route: done',
])


class FrlgTraceTest(unittest.TestCase):
    """The older FRLG lines (from Arduino-Source #125's tests)."""

    def setUp(self):
        runs = run_trace.parse(FRLG_LOG)
        self.assertEqual(len(runs), 1)
        self.run = runs[0]

    def test_walks_are_story_events(self):
        self.assertEqual(self.run.game, 'PokemonFRLG')
        self.assertEqual([walk.event for walk in self.run.walks], ['00.05/2 to_route', '00.05/3 house'])
        self.assertEqual([walk.outcome for walk in self.run.walks], ['done', 'failed'])

    def test_plan_leaves_out_the_holds_and_the_way_back(self):
        walk = self.run.walks[0]
        self.assertEqual([step.role for step in walk.steps], ['plan', 'plan', 'hold', 'hold', 'back', 'back', 'plan'])
        self.assertEqual([leg.describe() for leg in walk.plans[0].legs], ['walk west 4', 'walk south 3', 'walk north 4'])
        self.assertEqual(walk.plans[0].start, [('TestTown', 8, 1)])

    def test_stop_reanchor_and_failure(self):
        walk = self.run.walks[0]
        self.assertEqual((walk.steps[1].outcome, walk.steps[1].end), ('stopped', []))
        kinds = [(mark.kind, mark.at) for mark in walk.marks]
        self.assertIn(('battle', [('TestTown', 4, 1)]), kinds)
        self.assertIn(('reanchor', [('TestTown', 8, 3)]), kinds)
        house = self.run.walks[1]
        self.assertIn('no walls near it', house.error)
        self.assertEqual([mark.at for mark in house.marks if mark.kind == 'failed'], [[('TestTown', 4, 4)]])

    def test_shared_lines(self):
        walk = run_trace.parse(SHARED_FRLG_LOG)[0].walks[0]
        self.assertEqual([plan.reason for plan in walk.plans], ['plan', 'replan'])
        self.assertEqual([(step.end, step.basis) for step in walk.steps],
                         [([('TestTown', 4, 1)], 'walked'), ([], 'unknown'), ([('TestTown', 4, 5)], 'walked')])
        self.assertIn(('reanchor', [('TestTown', 4, 5)]), [(mark.kind, mark.at) for mark in walk.marks])
        self.assertEqual(walk.outcome, 'done')


if __name__ == '__main__':
    unittest.main()

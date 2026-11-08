"""FRLG spatial fidelity under the shared checkpoint runner; no console input."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pokesim.maps.runtime_map_pack import ROOT
from pokesim.story.replay_binding import PROFILE, load_binding
from pokesim.story.checkpoint_replay import run
from pokesim.story.replay_cases import read_cases

CASES = ROOT / 'data/story/parcel-pilot/cases.json'


class FRLGStoryReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = load_binding()
        cls.cases = read_cases(CASES)

    def test_semantic_legs_split_hops_and_warps_from_straight_walking(self):
        from pokesim.grid.geometry import Direction, Tile
        from pokesim.grid.maps.world import Place
        from pokesim.grid.movement import WorldState
        from pokesim.grid.routing.shortest import Move, MoveKind, Path as RoutePath
        from pokesim.story.spatial_replay import route_legs
        # Synthetic geometry diagnostic, not a measured/source map route.
        start = WorldState(Place('A', Tile(0, 0)), 3)
        endpoints = [('A', 1, MoveKind.STEP), ('A', 2, MoveKind.STEP),
                     ('A', 4, MoveKind.HOP), ('A', 5, MoveKind.STEP),
                     ('B', 1, MoveKind.WARP), ('B', 2, MoveKind.STEP)]
        moves = [Move(Direction.SOUTH, kind, WorldState(Place(name, Tile(0, y)), 3))
                 for name, y, kind in endpoints]
        actions = [a for a, _ in route_legs(RoutePath(start, moves, 0))]
        self.assertEqual([
            {'map': 'A', 'direction': 'south', 'kind': 'walk', 'tiles': 2},
            {'map': 'A', 'direction': 'south', 'kind': 'hop', 'tiles': 2},
            {'map': 'A', 'direction': 'south', 'kind': 'walk', 'tiles': 1},
            {'map': 'A', 'direction': 'south', 'kind': 'transition', 'to_map': 'B', 'via': 'warp'},
            {'map': 'B', 'direction': 'south', 'kind': 'walk', 'tiles': 1}], actions)

    def test_execution_rejects_a_planner_endpoint_that_the_move_did_not_reach(self):
        from pokesim.grid.geometry import Direction, Tile
        from pokesim.grid.maps.world import Place
        from pokesim.grid.movement import WorldState
        from pokesim.grid.routing.shortest import Move, MoveKind, Path as RoutePath
        initial, _ = self.binding.adapter.validate_pose(self.cases[0]['input']['entry']['pose'])
        wrong = WorldState(Place('ViridianCity', Tile(36, 20)), 3)
        # Synthetic broken planner: one west input cannot teleport from the lab
        # to Viridian. Execution must check movement, not copy the planned goal.
        planned = RoutePath(initial, [Move(Direction.WEST, MoveKind.STEP, wrong)], 1)
        with patch('pokesim.story.spatial_replay.shortest_path', return_value=planned):
            report = run(self.binding, self.cases[0]['input'])
        self.assertEqual('route_model_mismatch', report['failure'])
        self.assertEqual([], report['completed_events'])
        self.assertIsNone(report['pose'])
        self.assertEqual(1, len(report['actions']))
        self.assertEqual('west', report['actions'][0]['direction'])

    def test_real_cross_map_geometry_and_final_turn(self):
        result = run(self.binding, self.cases[0]['input'])
        completed = [r for r in result['trace'] if r['phase'] == 'completed']
        self.assertEqual(['below_mart_door', 'mart_door', 'parcel_from_clerk'],
                         [r['event'] for r in completed])
        self.assertEqual({'map': 'ViridianCity', 'tile': [36, 20], 'facing': 'north', 'elevation': 3},
                         completed[0]['pose'])
        self.assertEqual({'map': 'ViridianCity_Mart', 'tile': [4, 7], 'facing': 'north', 'elevation': 3},
                         completed[1]['pose'])
        self.assertEqual('model-prediction', completed[1]['basis'])
        self.assertEqual('scripted-observation', completed[2]['basis'])
        self.assertTrue(any(r['phase'] == 'turn' for r in result['trace']))
        moves = [r for r in result['trace'] if r['phase'] == 'move']
        self.assertEqual(120, len(moves))  # Python costs, not native leg-cost parity.
        self.assertEqual({'PalletTown_ProfessorOaksLab', 'PalletTown', 'Route1', 'ViridianCity'},
                         {r['pose']['map'] for r in moves})
        self.assertEqual(117, sum(a['tiles'] for a in result['actions']
                                 if a['kind'] == 'walk' and a['event'] == 'below_mart_door'))
        self.assertEqual(4, sum(a['kind'] == 'transition' for a in result['actions']))


    def test_interruption_preserves_both_tiles_and_stops_before_later_events(self):
        case = next(c for c in self.cases if c['id'] == 'interrupted-route1-grass')
        result = run(self.binding, case['input'])
        self.assertIsNone(result['pose'])
        self.assertEqual([None, None], [p['facing'] for p in result['candidates']])
        self.assertEqual(25, sum(r['phase'] == 'move' for r in result['trace']))
        self.assertEqual({'below_mart_door'}, {r['event'] for r in result['trace']})
        self.assertEqual({'event': 'below_mart_door', 'kind': 'walk', 'map': 'Route1',
                          'direction': 'north', 'tiles': 7}, result['actions'][-1])
        # Seven tiles were requested; no tile after the interrupted move is
        # confirmed, and the full leg's endpoint must not become our pose.
        self.assertEqual([[12, 39], [12, 38]], [p['tile'] for p in result['candidates']])
        # Actual source grass at the injected destination, not a synthetic board.
        from pokesim.grid.geometry import Tile
        self.assertEqual('~', self.binding.adapter.world.views['Route1'].glyph(Tile(12, 38)))


    def test_route_budget_stops_without_claiming_the_target(self):
        with tempfile.TemporaryDirectory() as directory:
            config = json.loads(PROFILE.read_text())
            config['max_route_moves'] = 1
            path = Path(directory, 'binding.json')
            path.write_text(json.dumps(config))
            result = run(load_binding(path), self.cases[0]['input'])
        self.assertEqual('route_move_budget_exceeded', result['failure'])
        self.assertEqual([], result['completed_events'])
        self.assertEqual(self.cases[0]['input']['entry']['pose'], result['pose'])
        self.assertEqual(0, sum(r['phase'] == 'move' for r in result['trace']))

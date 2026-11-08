"""Real captured events/maps; explicitly synthetic observations and interruptions."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pokesim.maps.runtime_map_pack import ROOT
from .parcel_binding import PROFILE, load_binding
from .parcel_replay import read_cases, run, summary

CASES = ROOT / 'data/story/parcel-pilot/cases.json'


class ParcelReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = load_binding()
        cls.cases = read_cases(CASES)

    def test_shared_input_expectation_table(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                result = run(self.binding, case['input'])
                actual = {key: result[key] for key in case['expectation']}
                self.assertEqual(case['expectation'], actual)
                self.assertEqual('not-established', result['native_parity'])
                self.assertEqual(self.binding.capture['unbound'], result['native_unbound'])
                if result['status'] == 'stopped':
                    self.assertFalse(result['save_performed'])
                    self.assertNotIn('parcel_from_clerk', result['completed_events'])

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
        presses = [r for r in result['trace'] if r['phase'] == 'press']
        self.assertEqual(120, len(presses))  # Python costs, not native leg-cost parity.
        self.assertEqual({'PalletTown_ProfessorOaksLab', 'PalletTown', 'Route1', 'ViridianCity'},
                         {r['pose']['map'] for r in presses})

    def test_interruption_preserves_both_tiles_and_stops_before_later_events(self):
        case = next(c for c in self.cases if c['id'] == 'interrupted-route1-grass')
        result = run(self.binding, case['input'])
        self.assertIsNone(result['pose'])
        self.assertEqual([None, None], [p['facing'] for p in result['candidates']])
        self.assertEqual(25, sum(r['phase'] == 'press' for r in result['trace']))
        self.assertEqual({'below_mart_door'}, {r['event'] for r in result['trace']})
        # Actual source grass at the injected destination, not a synthetic board.
        from pokesim.grid.geometry import Tile
        self.assertEqual('~', self.binding.world.views['Route1'].glyph(Tile(12, 38)))

    def test_route_budget_stops_without_claiming_the_target(self):
        binding = copy.copy(self.binding)
        binding.max_route_presses = 1
        result = run(binding, self.cases[0]['input'])
        self.assertEqual('route_press_budget_exceeded', result['failure'])
        self.assertEqual([], result['completed_events'])
        self.assertEqual(self.cases[0]['input']['entry']['pose'], result['pose'])
        self.assertEqual(0, sum(r['phase'] == 'press' for r in result['trace']))

    def test_wrong_entry_does_not_use_capture_start_as_observation(self):
        scenario = copy.deepcopy(self.cases[0]['input'])
        scenario['entry']['pose']['tile'] = [6, 8]
        result = run(self.binding, scenario)
        self.assertEqual('entry_requirement_failed', result['failure'])
        self.assertEqual([], result['trace'])
        self.assertEqual([6, 8], result['pose']['tile'])

    def test_inputs_and_capture_bookkeeping_are_not_mutated_or_promoted(self):
        scenario = copy.deepcopy(self.cases[0]['input'])
        capture_before = copy.deepcopy(self.binding.capture)
        scenario_before = copy.deepcopy(scenario)
        report = run(self.binding, scenario)
        self.assertEqual(scenario_before, scenario)
        report['native_unbound'].clear()
        self.assertEqual(capture_before, self.binding.capture)
        self.assertNotIn('hp', report)
        self.assertNotIn('potions', report)

    def test_unsupported_observations_and_injections_are_rejected(self):
        changes = [
            lambda s: s['entry'].update(extra='ignored'),
            lambda s: s['entry'].update(basis='console'),
            lambda s: s['signals'].update(unknown={'kind': 'scene-observation'}),
            lambda s: s['signals']['parcel_from_clerk'].update(kind='assume-declared'),
            lambda s: s['signals']['parcel_from_clerk'].update(received={'oak-parcel': True}),
            lambda s: s['signals']['parcel_from_clerk'].update(received={'master-ball': 1}),
            lambda s: s['signals'].update(below_mart_door={'kind': 'wild-encounter',
                'from': dict(s['entry']['pose'], tile=[6, 8]), 'direction': 'north'}),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                scenario = copy.deepcopy(self.cases[0]['input'])
                change(scenario)
                with self.assertRaises(ValueError):
                    run(self.binding, scenario)

    def test_binding_failures_precede_execution(self):
        changes = [
            lambda b: b['capture'].update(sha256='0' * 64),
            lambda b: b['maps'].update(Route1='0' * 64),
            lambda b: b['capabilities'].update(parcel_from_clerk='assume-success/1'),
            lambda b: b['capabilities'].pop('mart_door'),
            lambda b: b['policy'].update(save='after'),
            lambda b: b['policy'].update(attempts=True),
            lambda b: b.update(max_route_presses=True),
            lambda b: b['costs'].update(tile=float('nan')),
            lambda b: b.update(extra='ignored'),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'binding.json')
            for change in changes:
                with self.subTest(change=changes.index(change)):
                    binding = json.loads(PROFILE.read_text())
                    change(binding)
                    path.write_text(json.dumps(binding))
                    with self.assertRaises(ValueError):
                        load_binding(path)

    def test_cli_writes_an_explicit_failure_report_and_nonzero_status(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'trace.json')
            result = subprocess.run([sys.executable, '-m', 'pokesim.story.parcel_replay',
                                     str(CASES), '--case', 'missing-scene-evidence', '--out', str(path)],
                                    capture_output=True, text=True)
            self.assertEqual(1, result.returncode, result.stderr)
            self.assertEqual('stopped', json.loads(path.read_text())['status'])

    def test_readable_summary_keeps_evidence_and_policy_limits(self):
        rendered = summary(run(self.binding, self.cases[0]['input']))
        self.assertIn('native parity not established', rendered)
        self.assertIn('mart_door -> ViridianCity_Mart [4, 7] north, elevation 3 [model-prediction]', rendered)
        self.assertIn('parcel_from_clerk -> ViridianCity_Mart [4, 3] west, elevation 3 [scripted-observation]', rendered)
        self.assertIn('synthetic policy', rendered)

    def test_invalid_inventory_version_or_duplicate_ids_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'cases.json')
            for invalid in ('version', 'duplicate'):
                data = json.loads(CASES.read_text())
                if invalid == 'version':
                    data['format'] = 'future/2'
                else:
                    data['cases'].append(copy.deepcopy(data['cases'][0]))
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    read_cases(path)

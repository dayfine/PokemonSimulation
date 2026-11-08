"""Real captured events/maps; explicitly synthetic observations and interruptions."""

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pokesim.maps.runtime_map_pack import ROOT
from .replay_binding import PROFILE, load_binding
from .checkpoint_replay import run, summary
from .replay_cases import read_cases, check_case, render_cases

CASES = ROOT / 'data/story/parcel-pilot/cases.json'


class CheckpointReplayTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binding = load_binding()
        cls.cases = read_cases(CASES)

    def test_shared_input_expectation_table(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                result = run(self.binding, case['input'])
                check_case(case, result)
                self.assertEqual('not-established', result['native_parity'])
                self.assertEqual(self.binding.capture['unbound'], result['native_unbound'])
                if result['status'] == 'stopped':
                    self.assertFalse(result['save_performed'])
                    self.assertNotIn('parcel_from_clerk', result['completed_events'])


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
            result = subprocess.run([sys.executable, '-m', 'pokesim.story.checkpoint_replay',
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

    def test_exact_action_check_catches_missing_extra_reordered_and_wrong_requests(self):
        case = self.cases[0]
        self.assertTrue(case['input']['check_actions'])
        report = run(self.binding, case['input'])
        changes = [
            lambda a: a.pop(),
            lambda a: a.append(copy.deepcopy(a[-1])),
            lambda a: a.reverse(),
            lambda a: a[0].update(direction='east'),
            lambda a: a[0].update(count=2),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                wrong = copy.deepcopy(report)
                change(wrong['actions'])
                self.assertEqual('model_complete', wrong['status'])
                with self.assertRaisesRegex(AssertionError, r'actions\['):
                    check_case(case, wrong)

    def test_action_check_option_does_not_drive_replay(self):
        scenario = copy.deepcopy(self.cases[0]['input'])
        checked = run(self.binding, scenario)
        scenario['check_actions'] = False
        self.assertEqual(checked, run(self.binding, scenario))
        case = copy.deepcopy(self.cases[0])
        case['input']['check_actions'] = False
        case['expectation'].pop('actions')
        check_case(case, checked)

    def test_action_contract_requires_list_only_when_enabled(self):
        from .replay_cases import action_contract
        changes = [lambda c: c['expectation'].pop('actions'),
                   lambda c: c['input'].update(check_actions=False),
                   lambda c: c['input'].update(check_actions=1),
                   lambda c: c['expectation']['actions'][0].update(count=True)]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                case = copy.deepcopy(self.cases[0])
                change(case)
                with self.assertRaises(ValueError):
                    action_contract(case)

    def test_failed_transition_requests_entry_but_never_the_scene(self):
        case = next(c for c in self.cases if c['id'] == 'unconfirmed-mart-transition')
        result = run(self.binding, case['input'])
        check_case(case, result)
        self.assertEqual('mart_door', result['actions'][-1]['event'])
        self.assertFalse(any(a['kind'] == 'scene' for a in result['actions']))

    def test_case_document_matches_authored_expectations(self):
        path = CASES.with_name('CASES.md')
        self.assertEqual(path.read_text(), render_cases(self.cases))

    def test_second_checkpoint_uses_same_loader_and_runner_without_parcel_names(self):
        # Synthetic capture, never published as native run evidence. Different
        # ID/order, repeated STEP and another receipt prove this is not 00.05 code.
        capture = copy.deepcopy(self.binding.capture)
        start = capture['checkpoint']['start']
        capture['checkpoint'] = {'id': 'synthetic-second', 'title': 'Scene then two steps', 'start': start,
            'events': [{'id': 'get-pass', 'kind': 'scene', 'declared_after': start},
                       {'id': 'down', 'kind': 'step', 'direction': 'south'},
                       {'id': 'left', 'kind': 'step', 'direction': 'west'}]}
        profile = json.loads(PROFILE.read_text())
        profile['capabilities'] = {
            'get-pass': {'capability': 'scripted-scene/1', 'parameters': {'require_received': {'test-pass': 2}}},
            'down': {'capability': 'frlg-runtime-step/1', 'parameters': {}},
            'left': {'capability': 'frlg-runtime-step/1', 'parameters': {}}}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = json.dumps(capture).encode()
            (root / 'capture.json').write_bytes(raw)
            profile['capture']['file'] = 'capture.json'
            profile['capture']['sha256'] = hashlib.sha256(raw).hexdigest()
            for name in profile['maps']:
                relative = Path('data/games/frlg/maps/runtime', name + '.json')
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                (root / relative).write_bytes((ROOT / relative).read_bytes())
            path = root / 'binding.json'
            path.write_text(json.dumps(profile))
            binding = load_binding(path, root)
            scenario = copy.deepcopy(self.cases[0]['input'])
            scenario['signals'] = {'get-pass': {'kind': 'scene-observation', 'basis': 'scripted',
                'screen': 'overworld', 'pose': copy.deepcopy(scenario['entry']['pose']), 'received': {'test-pass': 2}}}
            report = run(binding, scenario)
        self.assertEqual('model_complete', report['status'])
        self.assertEqual(['get-pass', 'down', 'left'], report['completed_events'])
        self.assertEqual({'test-pass': 2}, report['received'])
        self.assertEqual([6, 9], report['pose']['tile'])
        self.assertEqual('west', report['pose']['facing'])

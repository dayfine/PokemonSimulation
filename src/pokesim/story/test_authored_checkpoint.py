"""Run the data-authored native Parcel checkpoint through the Python simulator."""

import copy
import hashlib
import json
import unittest

from pokesim.maps.runtime_map_pack import ROOT
from .authored_checkpoint import read_authored_checkpoint
from .replay_binding import load_binding
from .checkpoint_replay import run
from .replay_cases import read_cases, check_case

FOLDER = ROOT / 'data/story/parcel-pilot'


class AuthoredCheckpointTests(unittest.TestCase):
    def test_same_authored_plan_passes_all_shared_scenarios(self):
        binding = load_binding(FOLDER / 'authored-binding.json')
        for case in read_cases(FOLDER / 'cases.json'):
            with self.subTest(case=case['id']):
                report = run(binding, case['input'])
                check_case(case, report)
                self.assertIsNone(report['native_source_revision'])
                self.assertEqual(report['authored_plan_sha256'], hashlib.sha256(
                    (FOLDER / 'frlg-parcel-02.01.plan.json').read_bytes()).hexdigest())

    def test_rejects_snapshot_fields_and_unsupported_executor_configuration(self):
        original = json.loads((FOLDER / 'frlg-parcel-02.01.plan.json').read_text())
        mutations = [lambda p: p.update(native_fields={}),
                     lambda p: p.update(game='bdsp'),
                     lambda p: p['execution'].update(menu='guess'),
                     lambda p: p['execution'].update(supplies={'hp_fill': 1.0}),
                     lambda p: p['checkpoint']['events'].append(p['checkpoint']['events'][0])]
        for mutate in mutations:
            plan = copy.deepcopy(original)
            mutate(plan)
            with self.assertRaises(ValueError):
                read_authored_checkpoint(plan)

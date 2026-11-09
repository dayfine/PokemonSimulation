"""Pinned Git input and semantic replay checks for the native plan boundary."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from pokesim.maps.runtime_map_pack import ROOT
from .native_plan import read_pinned_plan, replay_plan

FOLDER = ROOT / 'data/story/bdsp-mine-pilot'


class NativePlanTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.checkout = Path(self.temporary.name)
        self.raw = (FOLDER / 'bdsp-mine-01.03.plan.json').read_bytes()
        (self.checkout / 'plan.json').write_bytes(self.raw)
        self.git('init', '-q')
        self.git('remote', 'add', 'origin', 'https://github.com/dayfine/Arduino-Source.git')
        self.git('add', 'plan.json')
        self.git('-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-qm', 'plan')
        self.pin = {'format': 'pokesim-native-plan-source/1', 'repository': 'dayfine/Arduino-Source',
                    'revision': self.git('rev-parse', 'HEAD').decode().strip(), 'file': 'plan.json',
                    'sha256': hashlib.sha256(self.raw).hexdigest()}
        self.pin_path = self.checkout / 'source.json'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.checkout), *args])

    def read(self):
        self.pin_path.write_text(json.dumps(self.pin))
        return read_pinned_plan(self.pin_path, self.checkout)

    def test_reads_commit_not_dirty_worktree(self):
        (self.checkout / 'plan.json').write_text('not JSON')
        self.assertEqual(self.read(), self.raw)

    def test_rejects_bad_identity_revision_path_and_hash(self):
        for key, value in [('repository', 'wrong/repo'), ('revision', 'main'),
                           ('file', '../plan.json'), ('sha256', '0' * 64)]:
            with self.subTest(key=key):
                before = self.pin[key]
                self.pin[key] = value
                with self.assertRaises(ValueError):
                    self.read()
                self.pin[key] = before

    def test_semantic_replay_accepts_different_bytes(self):
        plan = json.loads(self.raw)
        plan['checkpoint']['events'][0]['why'] = 'A new native authoring note'
        raw = json.dumps(plan, indent=4).encode()
        results = replay_plan(raw, FOLDER / 'binding.json', FOLDER / 'cases.json')
        self.assertEqual(len(results), 9)
        self.assertTrue(all(result['outcomes'] == 'matched' for result in results))

    def test_wrong_leg_count_fails_independent_expectations(self):
        plan = json.loads(self.raw)
        event = next(e for e in plan['checkpoint']['events'] if e['id'] == 'below_roark')
        event['legs'][0]['tiles'] = 1
        with self.assertRaises((AssertionError, ValueError)):
            replay_plan(json.dumps(plan).encode(), FOLDER / 'binding.json', FOLDER / 'cases.json')

"""Check process-parallel trials preserve seeded results and joint intervals."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pokesim.games.frlg.battle.engine import REPO
from pokesim.games.frlg.battle.test_battle import HAS_ENGINE


@unittest.skipUnless(HAS_ENGINE, 'Install pinned battle engine')
class RunBattleCLITest(unittest.TestCase):
    def test_worker_count_does_not_change_rates_traces_or_confidence_family(self):
        with tempfile.TemporaryDirectory() as directory:
            reports = []
            for workers in (1, 2):
                out = Path(directory) / ('run-' + str(workers) + '.json')
                subprocess.run([sys.executable, '-m', 'pokesim.cli.frlg_run_battles',
                    '--workers', str(workers), '--battles', '20', '--case', 'lab-rival',
                    '--case', 'forest-sammy', '--out', str(out)], cwd=str(REPO), check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    env={**os.environ, 'PYTHONPATH': str(REPO / 'src')})
                reports.append(json.loads(out.read_text()))
            self.assertEqual(reports[0], reports[1])
            self.assertAlmostEqual(reports[0]['sampling']['alpha_per_case'], .05 / 2)

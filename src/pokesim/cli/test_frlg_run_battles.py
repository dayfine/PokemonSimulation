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

    def test_complex_only_selects_c_and_reserves_confidence_for_baseline_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / 'complex.json'
            subprocess.run([sys.executable, '-m', 'pokesim.cli.frlg_run_battles',
                '--complex-only', '--case', 'bruno', '--workers', '1', '--battles', '20', '--out', str(out)],
                cwd=str(REPO), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env={**os.environ, 'PYTHONPATH': str(REPO / 'src')})
            report = json.loads(out.read_text())
            self.assertEqual(report['seed'], 4)
            self.assertEqual([r['id'] for r in report['results']], ['bruno'])
            self.assertTrue(report['results'][0]['inputs']['enable_complex_planning'])
            self.assertAlmostEqual(report['sampling']['alpha_per_case'], .025 / 12)
            self.assertEqual(report['sampling']['confidence_all_cases_all_looks'], .975)

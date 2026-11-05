"""CLI reports expected failures honestly and draws sourced local slices."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pokesim.maps.local_routing import Context, LocalMap
from pokesim.maps.runtime_map_pack import ROOT
from pokesim.maps.runtime_world import RuntimeWorld
from pokesim.maps.transition_replay import contracts, read_catalog
from .transitions import main


class TransitionsCliTests(unittest.TestCase):
    def world(self, source, revision, case):
        return RuntimeWorld([LocalMap(json.loads((ROOT / 'data/games' / case['game'] /
            'maps/runtime' / (name + '.json')).read_text()), case['game'],
            Context(frozenset(case['flags']), case['variables'])) for name in case['maps']],
            contracts(case), case.get('encounter_maps', ()))

    def test_trace_and_annotated_source_drawings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / 'trace.json'
            with patch('pokesim.cli.transitions.pinned_world', side_effect=self.world) as loader:
                self.assertEqual(main(['--case', 'forest-north-gate', '--output', str(target),
                                       '--draw-dir', str(root)]), 0)
            report = json.loads(target.read_text())
            self.assertTrue(report['checks_passed'])
            self.assertTrue(report['can_resume'])
            self.assertEqual(loader.call_args[0][1], read_catalog()['map_revision'])
            svg = (root / 'forest-north-gate-1.svg').read_text()
            self.assertIn('Native #216', svg)
            self.assertIn('Python candidate', svg)
            self.assertTrue((root / 'forest-north-gate-1.png').read_bytes().startswith(b'\x89PNG'))

    def test_expected_failure_remains_in_report(self):
        output = io.StringIO()
        with patch('pokesim.cli.transitions.pinned_world', side_effect=self.world), contextlib.redirect_stdout(output):
            self.assertEqual(main(['--case', 'mine-pack-gap']), 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report['checks_passed'])
        self.assertIn('unresolved transition', report['failure'])
        self.assertFalse(report['can_resume'])

    def test_unknown_scenario_errors_before_loading_any_maps(self):
        with patch('pokesim.cli.transitions.pinned_world') as loader, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--case', 'not-a-case']), 1)
        loader.assert_not_called()


if __name__ == '__main__':
    unittest.main()

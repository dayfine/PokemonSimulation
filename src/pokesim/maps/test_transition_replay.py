"""Data-driven source-grounded regressions, using unchanged local map bytes."""
import copy
import json
import unittest

from .consumer_source import sha256
from .local_routing import Context, LocalMap
from .runtime_map_pack import ROOT
from .runtime_world import RuntimeWorld
from .transition_replay import contracts, read_catalog, replay


class TransitionReplayTests(unittest.TestCase):
    def test_reviewed_scenario_inventory(self):
        catalog = read_catalog()
        manifest = json.loads((ROOT / 'data/maps/runtime-manifest.json').read_text())
        for case in catalog['cases']:
            with self.subTest(case=case['id']):
                views = []
                for name in case['maps']:
                    entry = next(e for e in manifest['games'][case['game']]['maps'] if e['name'] == name)
                    raw = (ROOT / 'data/games' / case['game'] / 'maps/runtime' / (name + '.json')).read_bytes()
                    self.assertEqual(sha256(raw), entry['sha256'])
                    views.append(LocalMap(json.loads(raw), case['game'],
                        Context(frozenset(case['flags']), case['variables']), entry['preconditions']))
                world = RuntimeWorld(views, contracts(case), case.get('encounter_maps', ()))
                report = replay(case, world, catalog['map_revision'])
                self.assertTrue(report['checks_passed'])
                if case['id'] == 'mine-pack-gap':
                    self.assertIn('unresolved transition', report['failure'])
                    self.assertFalse(report['can_resume'])
                self.assertEqual(len(case['evidence']['revision']), 40)
                self.assertTrue(case['evidence']['symbol'])

    def test_unsupported_story_events_are_not_skipped(self):
        case = copy.deepcopy(read_catalog()['cases'][0])
        case['events'] = [dict(event='native_story_magic')]
        maps = [LocalMap(json.loads((ROOT / 'data/games/frlg/maps/runtime' / (name + '.json')).read_text()), 'frlg')
                for name in case['maps']]
        with self.assertRaisesRegex(ValueError, 'unsupported semantic event'):
            replay(case, RuntimeWorld(maps), '0' * 40)


if __name__ == '__main__':
    unittest.main()

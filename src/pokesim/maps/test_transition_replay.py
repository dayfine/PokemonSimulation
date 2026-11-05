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

    def test_exact_expectation_rejects_wrong_tile_with_same_count(self):
        case = copy.deepcopy(read_catalog()['cases'][0])
        # A count-only assertion would accept this one-tile localization error.
        expected = dict(belief=[dict(case['initial'][0], tile=[5, 19])],
            can_resume=True, screen='overworld', queue_drained=True, awaiting=False,
            remaining_recoveries=3, failure=None)
        case['events'] = [dict(event='expect', state=expected)]
        maps = [LocalMap(json.loads((ROOT / 'data/games/frlg/maps/runtime' / (name + '.json')).read_text()), 'frlg')
                for name in case['maps']]
        with self.assertRaisesRegex(AssertionError, 'state mismatch'):
            replay(case, RuntimeWorld(maps), '0' * 40)

    def test_exact_expectations_require_complete_typed_state(self):
        case = copy.deepcopy(read_catalog()['cases'][0])
        baseline = dict(belief=case['initial'], can_resume=True, screen='overworld',
                        queue_drained=True, awaiting=False, remaining_recoveries=3, failure=None)
        maps = [LocalMap(json.loads((ROOT / 'data/games/frlg/maps/runtime' / (name + '.json')).read_text()), 'frlg')
                for name in case['maps']]
        changes = [
            (lambda s: s.pop('remaining_recoveries'), ValueError),
            (lambda s: s.update(extra='silently ignored'), ValueError),
            (lambda s: s.update(awaiting=0), AssertionError),
            (lambda s: s['belief'][0].update(facing=None), AssertionError),
        ]
        for change, error in changes:
            with self.subTest(change=changes.index((change, error))):
                expected = copy.deepcopy(baseline)
                change(expected)
                case['events'] = [dict(event='expect', state=expected)]
                with self.assertRaises(error):
                    replay(case, RuntimeWorld(maps), '0' * 40)

    def test_unsupported_story_events_are_not_skipped(self):
        case = copy.deepcopy(read_catalog()['cases'][0])
        case['events'] = [dict(event='native_story_magic')]
        maps = [LocalMap(json.loads((ROOT / 'data/games/frlg/maps/runtime' / (name + '.json')).read_text()), 'frlg')
                for name in case['maps']]
        with self.assertRaisesRegex(ValueError, 'unsupported semantic event'):
            replay(case, RuntimeWorld(maps), '0' * 40)


if __name__ == '__main__':
    unittest.main()

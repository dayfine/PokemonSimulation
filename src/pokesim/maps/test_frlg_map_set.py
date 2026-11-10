"""FRLG map set: status records, candidate sync, promotion and link rules."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from . import frlg_map_set as map_set
from . import runtime_map_pack as pack


class MapSetTest(unittest.TestCase):
    def setUp(self):
        self.manifest = map_set.read_manifest()

    def entry(self, manifest, name):
        return next(e for e in manifest['games']['frlg']['maps'] if e['name'] == name)

    def test_every_frlg_map_has_one_file_and_a_status(self):
        status = map_set.statuses(self.manifest)
        files = {p.stem for p in (map_set.ROOT / map_set.DIRECTORY).glob('*.json')}
        self.assertEqual(set(status), files)
        self.assertFalse((map_set.ROOT / 'data/games/frlg/maps/source-candidate').exists())
        self.assertEqual(list(status.values()).count('verified'), 57)
        self.assertEqual(list(status.values()).count('candidate'), 95)

    def test_centers_and_elevators_are_scripted_not_candidates(self):
        status = map_set.statuses(self.manifest)
        excluded = map_set.read_excluded(status)
        for name in ('CeladonCity_PokemonCenter_1F', 'RocketHideout_Elevator', 'SilphCo_Elevator',
                     'CeladonCity_DepartmentStore_Elevator', 'SaffronCity_PokemonCenter_1F'):
            with self.subTest(map=name):
                self.assertNotIn(name, status)
                self.assertEqual(excluded[name], 'scripted-in-autostory')
        # Verified before the decision; kept with their status.
        self.assertEqual(status['PewterCity_PokemonCenter_1F'], 'verified')
        self.assertEqual(status['IndigoPlateau_PokemonCenter_1F'], 'candidate')

    def test_candidate_entries_match_their_files(self):
        manifest = copy.deepcopy(self.manifest)
        self.assertEqual(map_set.sync_candidates(manifest), [])
        self.assertEqual(manifest, self.manifest)

    def test_sync_never_rewrites_verified_entries(self):
        manifest = copy.deepcopy(self.manifest)
        self.entry(manifest, 'Route3')['sha256'] = 'stale'
        self.assertEqual(map_set.sync_candidates(manifest), [])
        self.assertEqual(self.entry(manifest, 'Route3')['sha256'], 'stale')

    def test_promote_records_the_console_run_and_keeps_bytes(self):
        manifest = copy.deepcopy(self.manifest)
        before = copy.deepcopy(self.entry(manifest, 'Route11'))
        map_set.promote(manifest, 'Route11', 'runs/frlg/2026-11-10-00.14.md', '2026-11-10', '00.14',
                        'a' * 40)
        after = self.entry(manifest, 'Route11')
        self.assertEqual(after['status'], 'verified')
        self.assertEqual(after['verified'], dict(basis='console-run', run='runs/frlg/2026-11-10-00.14.md',
                                                 date='2026-11-10', checkpoint='00.14', consumer_revision='a' * 40))
        self.assertEqual({k: v for k, v in after.items() if k not in ('status', 'verified')},
                         {k: v for k, v in before.items() if k != 'status'})
        self.assertEqual(map_set.statuses(manifest)['Route11'], 'verified')
        with self.assertRaisesRegex(ValueError, 'already verified'):
            map_set.promote(manifest, 'Route11', 'r', '2026-11-10', '00.14')

    def test_invalid_status_records_fail(self):
        for change, message in ((lambda e: e.update(status='approved'), 'status must be'),
                                (lambda e: e.pop('verified'), 'needs a verified record'),
                                (lambda e: e['verified'].update(basis='hunch'), 'unknown verified basis'),
                                (lambda e: e.update(verified=dict(basis='console-run', run='r', date='11/10',
                                                                  checkpoint='00.14')), 'YYYY-MM-DD')):
            manifest = copy.deepcopy(self.manifest)
            change(self.entry(manifest, 'Route3'))
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                map_set.statuses(manifest)
        manifest = copy.deepcopy(self.manifest)
        self.entry(manifest, 'Route11')['verified'] = self.entry(manifest, 'Route3')['verified']
        with self.assertRaisesRegex(ValueError, 'candidate has no verified record'):
            map_set.statuses(manifest)

    def test_link_rules_allow_only_boundaries_and_pending_relinks(self):
        maps = {e['name']: pack.load(pack.ROOT / e['file']) for e in self.manifest['games']['frlg']['maps']}
        status = map_set.statuses(self.manifest)
        excluded = map_set.read_excluded(maps)
        boundary, pending, errors = map_set.link_gaps(maps, status, excluded)
        self.assertEqual((len(boundary), len(pending), errors), (61, 31, []))
        self.assertIn(('ViridianCity_Gym', 'ViridianCity', 'warp_2'), pending)
        # A verified map may not depend on a missing point, even in a candidate.
        broken = copy.deepcopy(maps)
        broken['ViridianCity']['warps'][0].update(to_map='Route11', to_point='warp_99')
        self.assertEqual(len(map_set.link_gaps(broken, status, excluded)[2]), 1)
        # Excluded only counts as a boundary while the map is absent.
        broken = copy.deepcopy(maps)
        del broken['Route11']
        self.assertTrue(map_set.link_gaps(broken, status, excluded)[2])


if __name__ == '__main__':
    unittest.main()

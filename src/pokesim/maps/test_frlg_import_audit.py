"""Full pinned source candidate integrity and conservative unresolved-state tests."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from .frlg_import_audit import audit
from .frlg_decomp_map_builder import COMMIT
from pokesim.formats.json_schema import ROOT

CANDIDATE = ROOT / 'data/games/frlg/maps/source-candidate'
SCOPE = CANDIDATE.parent / 'pokeguy-map-scope.json'


class FullImportAuditTest(unittest.TestCase):
    def test_checked_full_catalog_has_fixed_links_and_visible_gaps(self):
        report = audit(CANDIDATE, scope=SCOPE)
        self.assertEqual(report['map_count'], 141)
        self.assertEqual(report['excluded_map_count'], 284)
        self.assertEqual(report['source_revision'], COMMIT)
        self.assertEqual(report['totals']['dynamic_warps'], 0)
        self.assertEqual(report['totals']['unlinked_warps'], 0)
        self.assertEqual(report['totals']['scope_boundary_warps'], 103)
        self.assertEqual(report['totals']['unknown_tiles'], 3140)
        self.assertEqual(report['totals']['unresolved_pickups'], 84)
        self.assertEqual(report['totals']['unapplied_story_patches'], 1)
        self.assertEqual(report['elevation_grids_retained'], 14)
        self.assertEqual(report['elevation_grids_omitted'], 127)
        self.assertFalse(report['schema_checked'])

    def test_missing_destinations_require_an_explicit_scope(self):
        with self.assertRaisesRegex(ValueError, 'missing fixed warp destination'):
            audit(CANDIDATE)

    def test_required_reward_and_recovery_rooms_survive_pruning(self):
        for name in ('SSAnne_1F_Room6', 'CeladonCity_Condominiums_1F',
                     'Route16_House', 'Route25_SeaCottage',
                     'SafariZone_SecretHouse', 'FuchsiaCity_WardensHouse',
                     'CeruleanCity_House1', 'CeruleanCity_House2'):
            with self.subTest(map=name):
                self.assertTrue((CANDIDATE / (name + '.json')).is_file())

    def test_unresolved_terrain_cannot_be_silently_opened(self):
        source = json.loads((CANDIDATE / 'RocketHideout_B2F.json').read_text())
        name = next(iter(source['unresolved_tiles']))
        x, y = source['unresolved_tiles'][name][0]
        changed = copy.deepcopy(source)
        changed['tiles'][y] = changed['tiles'][y][:x] + '.' + changed['tiles'][y][x + 1:]
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, source['name'] + '.json').write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'unresolved terrain'):
                audit(directory)

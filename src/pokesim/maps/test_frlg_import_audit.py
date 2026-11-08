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


class FullImportAuditTest(unittest.TestCase):
    def test_checked_full_catalog_has_fixed_links_and_visible_gaps(self):
        report = audit(CANDIDATE)
        self.assertEqual(report['map_count'], 425)
        self.assertEqual(report['source_revision'], COMMIT)
        self.assertEqual(report['totals']['dynamic_warps'], 19)
        self.assertEqual(report['totals']['unlinked_warps'], 19)
        self.assertEqual(report['totals']['unknown_tiles'], 6038)
        self.assertEqual(report['totals']['unresolved_pickups'], 145)
        self.assertEqual(report['totals']['unapplied_story_patches'], 1)
        self.assertFalse(report['schema_checked'])

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

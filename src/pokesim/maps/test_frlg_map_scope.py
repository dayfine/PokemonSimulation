"""Exclusion inventories must be explicit, pinned and internally consistent."""

import json
from pathlib import Path
import tempfile
import unittest

from .frlg_map_scope import read_scope


class MapScopeTest(unittest.TestCase):
    def test_checked_inventory_and_invalid_exclusions(self):
        baseline = {'format': 'pokesim-frlg-map-scope/1', 'source_revision': 'rev',
                    'catalog_count': 2, 'excluded': [
                        {'reason': 'unused', 'basis': 'review notes', 'maps': ['Room']}]}
        cases = [(['Room'], 'rev', 2, {'Room': 'unused'}),
                 (['Missing'], 'rev', 2, None),
                 (['Room', 'Room'], 'rev', 2, None),
                 (['Room'], 'other', 2, None),
                 (['Room'], 'rev', 3, None)]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, 'scope.json')
            for names, revision, count, expected in cases:
                with self.subTest(names=names, revision=revision, count=count):
                    data = json.loads(json.dumps(baseline))
                    data['excluded'][0]['maps'] = names
                    data['source_revision'] = revision
                    data['catalog_count'] = count
                    path.write_text(json.dumps(data))
                    if expected is None:
                        with self.assertRaises(ValueError):
                            read_scope(path, ['Town', 'Room'], 'rev')
                    else:
                        self.assertEqual(read_scope(path, ['Town', 'Room'], 'rev'), expected)

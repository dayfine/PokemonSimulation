"""Parity diagnostics read immutable Git blobs and distinguish content/format drift."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from pokesim.maps.map_parity import compare_maps, read_map_tree
from pokesim.maps.runtime_map_coordinates import compact_map


def raw(data):
    return json.dumps(data).encode()


class MapParityTest(unittest.TestCase):
    def test_coordinate_encoding_and_whitespace_are_only_format_drift(self):
        old = dict(name='test', objects=[dict(x=0, y=1, name='npc', kind='npc')])
        report = compare_maps({'a.json': raw(old)}, {'a.json': raw(compact_map(old))})
        self.assertEqual(report['differences'][0]['status'], 'format-only')
        self.assertEqual(report['differences'][0]['fields'], [])
        self.assertEqual(report['identical_bytes'], 0)

    def test_tile_drift_reports_rows_and_preserves_inputs(self):
        old = dict(tiles=['..', '..'])
        new = dict(tiles=['..', '.#'])
        report = compare_maps({'a.json': raw(old)}, {'a.json': raw(new)})
        self.assertEqual(report['differences'][0]['fields'], ['tiles'])
        self.assertEqual(report['differences'][0]['changed_tile_rows'], [1])
        self.assertEqual(report['differences'][0]['status'], 'content-drift')
        self.assertEqual(old['tiles'], ['..', '..'])

    def test_inventory_and_identical_bytes(self):
        report = compare_maps({'same.json': b'{}', 'missing.json': b'{}'},
                              {'same.json': b'{}', 'extra.json': b'{}'})
        self.assertEqual(report['identical_bytes'], 1)
        self.assertEqual(report['differences'], [dict(name='extra.json', status='extra'),
                                               dict(name='missing.json', status='missing')])

    def test_reads_committed_blobs_not_pending_worktree_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.DEVNULL)
            git('init', '-q')
            git('config', 'user.name', 'Parity test')
            git('config', 'user.email', 'parity@example.invalid')
            path = root / 'maps/map.json'
            path.parent.mkdir()
            path.write_bytes(b'{"name":"committed"}')
            git('add', '.')
            git('commit', '-qm', 'fixture')
            revision = git('rev-parse', 'HEAD').decode().strip()
            path.write_bytes(b'{"name":"uncommitted"}')
            self.assertEqual(read_map_tree(root, revision, 'maps'),
                             {'map.json': b'{"name":"committed"}'})
            with self.assertRaisesRegex(ValueError, 'full lowercase commit'):
                read_map_tree(root, 'HEAD', 'maps')
            with self.assertRaisesRegex(ValueError, 'no map JSON'):
                read_map_tree(root, revision, 'missing')
            path.unlink()
            path.symlink_to('not-a-map.json')
            git('add', '.')
            git('commit', '-qm', 'symlink')
            with self.assertRaisesRegex(ValueError, 'regular map JSON'):
                read_map_tree(root, git('rev-parse', 'HEAD').decode().strip(), 'maps')


if __name__ == '__main__':
    unittest.main()

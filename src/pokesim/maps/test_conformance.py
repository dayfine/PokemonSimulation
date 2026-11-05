"""Common fixtures check exact poses, not merely candidate counts."""
import copy
import tempfile
import unittest
from pathlib import Path

from .conformance import make_world, read_pack, run_case, validate


class ConformanceTests(unittest.TestCase):
    def test_all_shared_cases(self):
        pack = read_pack()
        self.assertEqual(8, len(pack['cases']))
        for case in pack['cases']:
            with self.subTest(case=case['input']['id']):
                self.assertEqual(case['expectation'], run_case(case['input'], make_world(pack, case['input'])))

    def test_rejects_unsupported_or_incomplete_contract(self):
        original = read_pack()
        changes = [
            lambda p: p.update(coordinate_frame='decomp-global'),
            lambda p: p.update(format='future/2'),
            lambda p: p['cases'].append(copy.deepcopy(p['cases'][0])),
            lambda p: p['cases'][0]['input'].update(operation='teleport'),
            lambda p: p['cases'][0]['input']['legs'][0].update(tiles=True),
            lambda p: p['cases'][0]['expectation']['trace'].pop(),
            lambda p: p['cases'][0]['input']['initial'][0].update(facing='up'),
            lambda p: p['cases'][0]['input'].update(extra='ignored'),
            lambda p: p['cases'][-1]['input']['legs'][0].update(max_tiles=128),
            lambda p: p['cases'][-1]['input'].update(variables={}),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                pack = copy.deepcopy(original)
                change(pack)
                with self.assertRaises(ValueError):
                    validate(pack)

    def test_rejects_map_drift(self):
        pack = read_pack()
        pack['maps'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'map hash mismatch'):
            make_world(pack, pack['cases'][-1]['input'])

    def test_exact_pose_comparison_detects_one_tile_error(self):
        pack = read_pack()
        case = pack['cases'][0]
        wrong = copy.deepcopy(case['expectation'])
        wrong['trace'][0]['pose']['tile'][1] -= 1
        self.assertNotEqual(wrong, run_case(case['input'], make_world(pack, case['input'])))

    def test_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.json'
            path.write_text('{"format": "a", "format": "b"}')
            with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
                read_pack(path)

"""Shared semantic data vectors, also consumed by the native codec executable."""
import json
from pathlib import Path
import unittest
from .checkpoint_wire import read_pose, read_step, read_checkpoint

ROOT = Path(__file__).resolve().parents[3]


class CheckpointWireTest(unittest.TestCase):
    def test_shared_native_vectors(self):
        data = json.loads((ROOT / 'data/story/wire-conformance.json').read_text())
        readers = dict(pose=read_pose, step=read_step, checkpoint=read_checkpoint)
        for case in data['cases']:
            value, expected = case['input'], case['expectation']
            with self.subTest(name=value['name']):
                if expected.get('rejected'):
                    with self.assertRaises((ValueError, KeyError, TypeError)):
                        readers[value['record']](value['value'])
                else:
                    actual = readers[value['record']](value['value'])
                    self.assertEqual(actual, expected['canonical'])
                    self.assertEqual(readers[value['record']](actual), actual)


if __name__ == '__main__':
    unittest.main()

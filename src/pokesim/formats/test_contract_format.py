"""Native capture formatting keeps events readable without changing their data."""

import json
import unittest

from .contract_format import json_text


class NativeCaptureFormatTests(unittest.TestCase):
    def test_short_native_events_remain_separate_blocks(self):
        value = {'format': 'pokesim-native-checkpoint-export/1', 'checkpoint': {
            'id': '00.05', 'title': 'Parcel', 'start': {'tiles': [[7, 8]]},
            'events': [{'id': 'door', 'kind': 'step'}, {'id': 'answer', 'kind': 'answer', 'yes': False}]}}
        text = json_text(value)
        self.assertNotIn('{"id": "door"', text)
        self.assertNotIn('{"id": "answer"', text)
        self.assertIn('"tiles": [[7, 8]]', text)
        self.assertEqual(json.loads(text), value)
        self.assertEqual(list(json.loads(text)['checkpoint']), ['id', 'title', 'start', 'events'])
        self.assertEqual(json_text(json.loads(text)), text)

    def test_other_short_objects_stay_compact(self):
        self.assertEqual(json_text({'id': 'tile', 'kind': 'marker', 'coord': [0, 0]}),
                         '{"id": "tile", "kind": "marker", "coord": [0, 0]}\n')

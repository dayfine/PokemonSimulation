"""Coordinate codec, readable serialization and real pack round-trip coverage."""

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from pokesim.maps.runtime_map_coordinates import COMPACT, LEGACY, compact_map, legacy_map
from pokesim.maps.runtime_map_format import map_text
from pokesim.maps import runtime_map_pack as pack


class CoordinateFormatTest(unittest.TestCase):
    def test_all_75_real_maps_round_trip_without_changing_content(self):
        for game, info in pack.audit()['games'].items():
            for entry in info['maps']:
                with self.subTest(game=game, map=entry['name']):
                    original = json.loads((pack.ROOT / entry['file']).read_text())
                    before = copy.deepcopy(original)
                    compact = compact_map(original)
                    self.assertEqual(compact['format'], COMPACT)
                    self.assertEqual(legacy_map(compact), before)
                    self.assertEqual(original, before)
                    pack.validate(compact)
                    self.assertEqual(json.loads(map_text(compact)), compact)
                    self.assertEqual(map_text(json.loads(map_text(compact))), map_text(compact))
                    self.assertEqual(pack.effective_map(compact), pack.effective_map(original))

    def test_explicit_v1_marker_normalizes_to_the_existing_unmarked_representation(self):
        data = dict(name='Example', objects=[dict(name='npc', kind='npc', x=0, y=1)])
        self.assertEqual(legacy_map(dict(format=LEGACY, **data)), data)
        self.assertEqual(legacy_map(compact_map(dict(format=LEGACY, **data))), data)

    def test_zero_coordinates_wander_and_extensions_are_preserved(self):
        original = dict(name='Example', objects=[dict(name='npc', kind='npc', x=0, y=1,
                        wander=dict(x0=0, y0=0, x1=2, y1=2), enabled=False)],
                        extension=dict(x=7, y=9, zero=0))
        compact = compact_map(original)
        self.assertEqual(compact['objects'][0]['coord'], [0, 1])
        self.assertEqual(compact['objects'][0]['wander'], dict(min=[0, 0], max=[2, 2]))
        self.assertEqual(compact['extension'], original['extension'])
        self.assertIs(compact['objects'][0]['enabled'], False)
        self.assertEqual(legacy_map(compact), original)

    def test_conflicting_partial_and_malformed_coordinates_fail(self):
        for record in (dict(x=1), dict(x=1, y=2, coord=[1, 2]),
                       dict(x=True, y=2), dict(x=1.0, y=2)):
            with self.subTest(record=record), self.assertRaises(ValueError):
                compact_map(dict(objects=[record]))
        for record in (dict(coord=[1]), dict(coord=[1, 2, 3]), dict(coord=[False, 2]),
                       dict(coord=[1, 2], x=1), dict(x=1, y=2)):
            with self.subTest(record=record), self.assertRaises(ValueError):
                legacy_map(dict(format=COMPACT, objects=[record]))
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            legacy_map(dict(format='pokesim-runtime-map/99'))

    def test_compact_records_and_coordinate_pairs_share_lines(self):
        data = compact_map(dict(points=dict(roark=[18, 28]),
                objects=[dict(name='roark', kind='npc', x=18, y=28, facing='east')]))
        text = map_text(data)
        self.assertIn('"roark": [18, 28]', text)
        self.assertIn('{"name": "roark", "kind": "npc", "coord": [18, 28], "facing": "east"}', text)
        self.assertEqual(json.loads(text), data)

    def test_cli_previews_both_formats_but_refuses_in_place_replacement(self):
        data = dict(name='Example', source=dict(decomp_file='fixture', revision='fixture', date='fixture'),
                    tiles=['..', '..'], objects=[dict(name='npc', kind='npc', x=0, y=1)])
        with tempfile.TemporaryDirectory() as folder:
            source, preview, back = [Path(folder) / name for name in ('source.json', 'v2.json', 'v1.json')]
            source.write_text(json.dumps(data))
            before = source.read_bytes()
            command = [sys.executable, '-m', 'pokesim.maps.runtime_map_format']
            rejected = subprocess.run(command + ['--input', str(source), '--out', str(source)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(rejected.returncode, 2)
            self.assertIn(b'must differ', rejected.stderr)
            self.assertEqual(source.read_bytes(), before)
            subprocess.run(command + ['--input', str(source), '--out', str(preview)], check=True)
            self.assertEqual(json.loads(preview.read_text()), compact_map(data))
            subprocess.run(command + ['--input', str(preview), '--out', str(back), '--legacy'], check=True)
            self.assertEqual(json.loads(back.read_text()), data)
            self.assertEqual(source.read_bytes(), before)

    def test_load_normalizes_v2_for_existing_route_and_recovery_code(self):
        original = pack.load(pack.ROOT / 'data/games/bdsp/maps/runtime/OreburghMine.json')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'map.json'
            path.write_text(map_text(compact_map(original)))
            self.assertEqual(pack.load(path), original)


if __name__ == '__main__':
    unittest.main()

"""Coordinate codec, readable serialization and real pack round-trip coverage."""

import copy
from collections import Counter
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from pokesim.maps.runtime_map_coordinates import COMPACT, LEGACY, compact_map, legacy_map
from pokesim.maps.runtime_map_format import map_text
from pokesim.maps import runtime_map_pack as pack
from pokesim.maps.local_routing import LocalMap
from pokesim.maps.runtime_world import RuntimeWorld
from pokesim.maps.transition_state import trainer_hazards


class CoordinateFormatTest(unittest.TestCase):
    def test_all_75_real_maps_round_trip_without_changing_content(self):
        for game, info in pack.audit()['games'].items():
            for entry in info['maps']:
                with self.subTest(game=game, map=entry['name']):
                    original = json.loads((pack.ROOT / entry['file']).read_text())
                    before = legacy_map(original)
                    compact = compact_map(original)
                    self.assertEqual(compact['format'], COMPACT)
                    restored = legacy_map(compact)
                    old_objects = before.pop('objects', [])
                    new_objects = restored.pop('objects', [])
                    self.assertEqual(restored, before)
                    self.assertEqual(Counter(json.dumps(o, sort_keys=True) for o in old_objects),
                                     Counter(json.dumps(o, sort_keys=True) for o in new_objects))
                    for kind in ('npc', 'item', 'sign'):
                        self.assertEqual([o for o in old_objects if o['kind'] == kind],
                                         [o for o in new_objects if o['kind'] == kind])
                    self.assertEqual(original, json.loads((pack.ROOT / entry['file']).read_text()))
                    pack.validate(compact)
                    self.assertEqual(json.loads(map_text(compact)), compact)
                    self.assertEqual(map_text(json.loads(map_text(compact))), map_text(compact))
                    effective = pack.effective_map(compact)
                    expected = pack.effective_map(original)
                    effective.pop('objects', None)
                    expected.pop('objects', None)
                    self.assertEqual(effective, expected)

    def test_explicit_v1_marker_normalizes_to_the_existing_unmarked_representation(self):
        data = dict(name='Example', objects=[dict(name='npc', kind='npc', x=0, y=1)])
        self.assertEqual(legacy_map(dict(format=LEGACY, **data)), data)
        self.assertEqual(legacy_map(compact_map(dict(format=LEGACY, **data))), data)

    def test_zero_coordinates_wander_and_extensions_are_preserved(self):
        original = dict(name='Example', objects=[dict(name='npc', kind='npc', x=0, y=1,
                        wander=dict(x0=0, y0=0, x1=2, y1=2), enabled=False)],
                        extension=dict(x=7, y=9, zero=0))
        compact = compact_map(original)
        self.assertEqual(compact['npcs'][0]['coord'], [0, 1])
        self.assertEqual(compact['npcs'][0]['wander'], dict(min=[0, 0], max=[2, 2]))
        self.assertEqual(compact['extension'], original['extension'])
        self.assertIs(compact['npcs'][0]['enabled'], False)
        self.assertEqual(legacy_map(compact), original)

    def test_groups_preserve_duplicates_and_order_within_each_kind(self):
        data = dict(objects=[dict(name='same', kind='item', x=0, y=0),
                             dict(name='same', kind='npc', x=1, y=0),
                             dict(name='same', kind='item', x=2, y=0),
                             dict(name='board', kind='sign', x=3, y=0)])
        compact = compact_map(data)
        self.assertNotIn('objects', compact)
        self.assertEqual(list(compact), ['format', 'npcs', 'items', 'signs'])
        self.assertEqual([o['coord'] for o in compact['items']], [[0, 0], [2, 0]])
        self.assertTrue(all('kind' not in o for group in ('npcs', 'items', 'signs') for o in compact[group]))
        self.assertEqual(len(legacy_map(compact)['objects']), 4)
        self.assertEqual(compact_map(legacy_map(compact)), compact)

    def test_grouping_preserves_real_map_occupancy_and_trainer_sight(self):
        for game, name in (('bdsp', 'OreburghMine'), ('frlg', 'ViridianForest')):
            with self.subTest(game=game, map=name):
                original = pack.load(pack.ROOT / ('data/games/' + game + '/maps/runtime/' + name + '.json'))
                before = LocalMap(original, game)
                after = LocalMap(compact_map(original), game)
                self.assertEqual(before.occupied, after.occupied)
                self.assertEqual(before.scene_tiles, after.scene_tiles)
                self.assertEqual(before.warps, after.warps)
                self.assertEqual(trainer_hazards(RuntimeWorld([before])),
                                 trainer_hazards(RuntimeWorld([after])))

    def test_grouped_schema_rejects_conflicting_and_unknown_kinds(self):
        for data in (dict(objects=[dict(name='x', kind='tree', x=0, y=0)]),
                     dict(objects=[], npcs=[])):
            with self.subTest(data=data), self.assertRaises(ValueError):
                compact_map(data)
        for fields in (dict(objects=[]), dict(npcs={}), dict(items=[dict(coord=[0, 0], kind='item')])):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                legacy_map(dict(format=COMPACT, **fields))
        self.assertEqual(compact_map(dict(objects=[])), dict(format=COMPACT))

    def test_conflicting_partial_and_malformed_coordinates_fail(self):
        for record in (dict(x=1), dict(x=1, y=2, coord=[1, 2]),
                       dict(x=True, y=2), dict(x=1.0, y=2)):
            with self.subTest(record=record), self.assertRaises(ValueError):
                compact_map(dict(objects=[record]))
        for record in (dict(coord=[1]), dict(coord=[1, 2, 3]), dict(coord=[False, 2]),
                       dict(coord=[1, 2], x=1), dict(x=1, y=2)):
            with self.subTest(record=record), self.assertRaises(ValueError):
                legacy_map(dict(format=COMPACT, npcs=[record]))
        with self.assertRaisesRegex(ValueError, 'unsupported'):
            legacy_map(dict(format='pokesim-runtime-map/99'))

    def test_compact_records_and_coordinate_pairs_share_lines(self):
        data = compact_map(dict(points=dict(roark=[18, 28]),
                objects=[dict(name='roark', kind='npc', x=18, y=28, facing='east')]))
        text = map_text(data)
        self.assertIn('"roark": [18, 28]', text)
        self.assertIn('{"name": "roark", "coord": [18, 28], "facing": "east"}', text)
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
            restored = pack.load(path)
            self.assertEqual(compact_map(restored), compact_map(original))


if __name__ == '__main__':
    unittest.main()

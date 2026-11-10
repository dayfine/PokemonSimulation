"""Migration integrity and runtime-format regression checks, without network."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pokesim.maps import bdsp_decomp_map_builder as bdsp, map_overlays as overlays, runtime_map_pack as pack


class PackTest(unittest.TestCase):
    def test_inventory_checksums_geometry_and_graph(self):
        manifest = pack.audit()
        self.assertEqual({game: len(data['maps']) for game, data in manifest['games'].items()},
                         {'frlg': 152, 'bdsp': 22})
        for game, data in manifest['games'].items():
            for entry in data['maps']:
                raw = pack.load(pack.ROOT / entry['file'])
                self.assertEqual(entry['terrain_corrections'], raw.get('patches', []))
                if game == 'bdsp':
                    self.assertEqual(entry['coordinate_frame']['origin'], list(bdsp.MAPS[entry['name']]['rect'][:2]))
                    # JSON object keys become strings in the manifest.
                    overrides = json.loads(json.dumps(bdsp.OBJECTS.get(entry['name'], {})))
                    self.assertEqual(entry['generation_overrides']['objects'], overrides)
                    self.assertEqual(entry['generation_overrides']['warp_doors'],
                                     [list(tile) for tile in bdsp.WARP_DOORS.get(entry['name'], [])])
                    self.assertEqual(entry['generation_overrides']['coord_events'],
                                     json.loads(json.dumps(bdsp.COORD_EVENTS.get(entry['name'], {}))))
                else:
                    # Authored changes are overlay operations now (map_overlays), not generator tables.
                    self.assertEqual(entry['generation_overrides']['opened_tiles'], [])
                    self.assertEqual({k: entry[k] for k in ('base', 'overlay') if k in entry},
                                     overlays.pack_refs(entry['name']))

    def test_corrections_apply_to_copy_and_keep_evidence_and_extensions(self):
        raw = pack.load(pack.ROOT / 'data/games/bdsp/maps/runtime/Route202.json')
        raw['future_extension'] = {'unknown': [1, 2]}
        before = copy.deepcopy(raw)
        effective = pack.effective_map(raw)
        self.assertEqual(raw, before)
        self.assertNotEqual(effective['tiles'], raw['tiles'])
        for patch in raw['patches']:
            self.assertEqual(effective['tiles'][patch['y']][patch['x']], patch['glyph'])
        self.assertEqual(effective['patches'], raw['patches'])
        self.assertEqual(effective['future_extension'], raw['future_extension'])

    def test_invalid_geometry_and_warp_entry_rejected(self):
        raw = {'name': 'test', 'source': dict(decomp_file='x', revision='x', date='x'), 'tiles': ['..', '..']}
        for change in ({'tiles': ['..', '.']}, {'points': {'bad': [-1, 0]}},
                       {'patches': [dict(x=0, y=2, glyph='#', measured_by='probe')]},
                       {'warps': [dict(x=0, y=0, enter='teleport')]},
                       {'elevation': ['00']},
                       {'coord_events': [dict(x=1, y=1, width=2, length=1)]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                pack.validate(dict(raw, **change))

    def test_unresolved_warps_are_retained_not_walls(self):
        raw = pack.load(pack.ROOT / 'data/games/frlg/maps/runtime/VermilionCity.json')
        # The generator links every FRLG source warp by name, so make one unresolved.
        del raw['warps'][0]['to_map'], raw['warps'][0]['to_point']
        unresolved = [warp for warp in raw['warps'] if 'to_map' not in warp]
        self.assertTrue(unresolved)
        self.assertTrue(all(warp in pack.effective_map(raw)['warps'] for warp in unresolved))

    def test_consumer_export_is_byte_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, '-m', 'pokesim.maps.runtime_map_pack',
                            '--export-game', 'bdsp', '--out', directory], check=True, stdout=subprocess.PIPE)
            sources = pack.ROOT / 'data/games/bdsp/maps/runtime'
            files = list(sources.glob('*.json'))
            self.assertEqual(len(files), 22)
            self.assertEqual(len(list(Path(directory).glob('*.json'))), 22)
            for source in files:
                self.assertEqual(source.read_bytes(), (Path(directory) / source.name).read_bytes())
            self.assertTrue((Path(directory) / 'OreburghMineB1F.json').exists())


if __name__ == '__main__':
    unittest.main()

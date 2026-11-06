"""Actual pickup catalog, provenance, fixed inventory intent and guarded enrichment."""

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from . import item_identity as identity
from .local_routing import Context, LocalMap
from .runtime_map_coordinates import compact_map
from .runtime_map_pack import ROOT, audit, load, validate
from pokesim.grid.geometry import Tile


class ItemIdentityTest(unittest.TestCase):
    def test_catalog_pin_digest_and_all_existing_item_ball_records(self):
        inputs = json.loads(identity.INPUTS.read_text())
        catalog = json.loads(identity.CATALOG.read_text())
        self.assertEqual(catalog['inputs_sha256'], identity.digest(json.dumps(inputs, sort_keys=True).encode()))
        counts = {'frlg': [0, 0], 'bdsp': [0, 0]}
        for game, pack in audit()['games'].items():
            for entry in pack['maps']:
                data = load(ROOT / entry['file'])
                original = copy.deepcopy(data)
                enriched = identity.enrich_map(data, game)
                self.assertEqual(data, original)
                self.assertEqual(enriched['tiles'], data['tiles'])
                validate(enriched)
                compact = compact_map(enriched)
                validate(compact)
                counts[game][0] += len(compact.get('items', []))
                counts[game][1] += len(compact.get('interactables', []))
                if any(o['kind'] == 'item' for o in data.get('objects', [])):
                    provenance = enriched['source']['item_identities']
                    self.assertEqual(provenance['catalog_sha256'], identity.digest(identity.CATALOG.read_bytes()))
                    self.assertRegex(provenance['revision'], r'^[a-f0-9]{40}$')
                    for record in enriched['objects']:
                        if record['kind'] == 'item':
                            self.assertIs(type(record['source_event']), int)
                            self.assertIn('hide_flag', record)
        self.assertEqual(counts, {'frlg': [30, 3], 'bdsp': [15, 0]})

    def test_mine_escape_rope_and_potion_have_real_identities_and_collection_flags(self):
        data = identity.enrich_map(load(ROOT / 'data/games/bdsp/maps/runtime/OreburghMine.json'), 'bdsp')
        items = {r['name']: r for r in data['objects'] if r['kind'] == 'item'}
        self.assertEqual((items['item_3']['item'], items['item_3']['quantity']), ('escape_rope', 1))
        self.assertEqual((items['item_4']['item'], items['item_4']['quantity']), ('potion', 1))
        self.assertEqual(items['item_3']['source_event'], 3)
        self.assertEqual(items['item_3']['hide_flag'], 'flag 993')
        self.assertIn('not verified against BDSP', data['source']['item_identities']['verification'])
        self.assertIn(Tile(4, 28), LocalMap(data, 'bdsp').occupied)
        after = LocalMap(data, 'bdsp', Context(flags=frozenset({'flag 993'})))
        self.assertNotIn(Tile(4, 28), after.occupied)

    def test_forest_pickups_and_starter_balls_are_distinct(self):
        forest = identity.enrich_map(load(ROOT / 'data/games/frlg/maps/runtime/ViridianForest.json'), 'frlg')
        items = compact_map(forest)['items']
        self.assertEqual([r['item'] for r in items], ['poke_ball', 'antidote', 'potion', 'potion'])
        self.assertEqual(len({r['source_event'] for r in items}), 4)
        lab = identity.enrich_map(load(ROOT / 'data/games/frlg/maps/runtime/PalletTown_ProfessorOaksLab.json'), 'frlg')
        compact = compact_map(lab)
        self.assertNotIn('items', compact)
        self.assertEqual([o['interaction']['species'] for o in compact['interactables']],
                         ['bulbasaur', 'squirtle', 'charmander'])
        self.assertTrue(all('item' not in o and 'quantity' not in o for o in compact['interactables']))

    def test_unknown_source_and_conflicting_references_do_not_invent_rewards(self):
        unknown = dict(name='Unknown', source={}, objects=[dict(name='ball', kind='item', x=0, y=0)])
        enriched = identity.enrich_map(unknown, 'frlg')['objects'][0]
        self.assertEqual(enriched['pickup']['status'], 'unresolved')
        self.assertNotIn('item', enriched)
        self.assertNotIn('quantity', enriched)
        changed_map = load(ROOT / 'data/games/bdsp/maps/runtime/OreburghMine.json')
        changed_map['tiles'][0] = '.' + changed_map['tiles'][0][1:]
        with self.assertRaisesRegex(ValueError, 'map-content mismatch'):
            identity.enrich_map(changed_map, 'bdsp')
        catalog = json.loads(identity.CATALOG.read_text())
        entry = catalog['maps']['bdsp']['OreburghMine']
        objects = load(ROOT / 'data/games/bdsp/maps/runtime/OreburghMine.json')['objects']
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            identity.enrich_objects(objects, 'bdsp', 'OreburghMine', '0' * 64)
        with self.assertRaisesRegex(ValueError, 'source revision mismatch'):
            identity.enrich_objects(objects, 'bdsp', 'OreburghMine', entry['events_sha256'], source_revision='0' * 40)
        objects[1]['source_event'] = 999
        with self.assertRaisesRegex(ValueError, 'source event changed'):
            identity.enrich_objects(objects, 'bdsp', 'OreburghMine', entry['events_sha256'])

    def test_cached_inputs_must_match_both_reviewed_hashes(self):
        raw = b'known source'
        info = dict(sha256=identity.digest(raw),
                    git_blob=hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest())
        inputs = dict(format='pokesim-item-source-inputs/1', sources={
            'test': dict(repository='pret/test', revision='1' * 40, files={'events.json': info})})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'test/events.json'
            path.parent.mkdir()
            path.write_bytes(raw)
            self.assertEqual(identity.read_inputs(directory, inputs), {'test': {'events.json': raw}})
            path.write_bytes(b'local drift')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                identity.read_inputs(directory, inputs, fetch=True)
            self.assertEqual(path.read_bytes(), b'local drift')


if __name__ == '__main__':
    unittest.main()

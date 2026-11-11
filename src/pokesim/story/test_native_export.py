"""Synthetic capture boundaries; real captures, when present, are checked separately."""

import copy
import json
import unittest

try:
    import jsonschema
except ImportError:
    jsonschema = None

from .native_export import read_native_export
from pokesim.formats.json_schema import ROOT


def synthetic_capture():
    return {
        'format': 'pokesim-native-checkpoint-export/1', 'game': 'frlg',
        'status': 'native-table-export', 'source_revision': '0' * 40,
        'checkpoint': {'id': 'synthetic', 'title': 'Synthetic capture',
                       'events': [{'id': 'answer', 'kind': 'answer', 'yes': False}]},
        'state_basis': 'native-table-bookkeeping',
        'unbound': ['runtime_configuration', 'map_pins', 'executor_bindings',
                    'entry_evidence', 'effective_save_retry_policy'],
        'native_fields': {'menu': 'before_pokedex', 'supplies': {
            'potions': 0, 'antidotes': 0, 'parlyz_heals': 0,
            'pocket': ['potion', ''], 'status': 'no status', 'hurt': False,
            'hp_red': False, 'hp_fill': 1.0,
            'lead': {'species': 'squirtle', 'moves': [{'move': 'tackle', 'pp': 0}],
                     'moves_through_level': 5, 'moves_read': False, 'level': 0, 'stats': None},
            'protected_slots': [0], 'foes': [], 'trainer': '', 'risk': 'low',
            'foe_out': 0, 'wild_foes': []}}
    }


@unittest.skipUnless(jsonschema, 'install schemas/requirements.txt for authoring schema checks')
class NativeExportTests(unittest.TestCase):
    def test_preserves_bookkeeping_false_zero_and_unknown_stats(self):
        source = synthetic_capture()
        row = source['checkpoint']
        source['checkpoint'] = {'events': row['events'], 'title': row['title'], 'id': row['id']}
        original = copy.deepcopy(source)
        result = read_native_export(source, '0' * 40)
        self.assertEqual(result, source)
        self.assertEqual(json.dumps(result), json.dumps(source))
        result['native_fields']['supplies']['pocket'].append('new')
        self.assertEqual(source, original)

    def test_rejects_extensions_missing_fields_revision_and_claimed_evidence(self):
        mutations = [
            ('unknown game', lambda v: v.update(game='bdsp')),
            ('unknown native field', lambda v: v['native_fields'].update(handoff='assumed')),
            ('missing native field', lambda v: v['native_fields']['supplies'].pop('foe_out')),
            ('claimed observation', lambda v: v.update(state_basis='observed')),
            ('claimed bound', lambda v: v.update(unbound=[])),
            ('boolean PP', lambda v: v['native_fields']['supplies']['lead']['moves'][0].update(pp=False)),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                value = synthetic_capture()
                mutate(value)
                with self.assertRaises(ValueError):
                    read_native_export(value)
        with self.assertRaisesRegex(ValueError, 'source revision'):
            read_native_export(synthetic_capture(), '1' * 40)

    def test_still_rejects_duplicate_event_ids_after_schema_validation(self):
        value = synthetic_capture()
        value['checkpoint']['events'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            read_native_export(value)

    def test_actual_parcel_capture_from_clean_native_ci(self):
        path = ROOT / 'data/story/native/frlg-parcel-02.01.json'
        source = json.loads(path.read_text())
        result = read_native_export(source, 'b170b7d2103e887ded825c37fdbdc19fd654fca8')
        self.assertEqual(result, source)
        row = result['checkpoint']
        self.assertEqual(row['id'], '02.01')
        self.assertEqual(row['start'], {
            'map': 'PalletTown_ProfessorOaksLab', 'certainty': 'tile',
            'where': {'kind': 'tiles', 'tiles': [[7, 8]], 'facing': 'south'}})
        self.assertEqual([(e['id'], e['kind']) for e in row['events']], [
            ('below_mart_door', 'route'), ('mart_door', 'step'), ('parcel_from_clerk', 'scene')])
        route, door, scene = row['events']
        self.assertEqual(route['target']['where']['tiles'], [[36, 20]])
        self.assertEqual(route['target']['map'], 'ViridianCity')
        self.assertEqual(door.get('direction', 'north'), 'north')
        self.assertEqual(scene['declared_after']['map'], 'ViridianCity_Mart')
        self.assertEqual(scene['declared_after']['where']['tiles'], [[4, 3]])
        self.assertEqual(result['native_fields']['menu'], 'before_pokedex')
        # Native bookkeeping keeps an unread summary level (zero) and no stats;
        # moves_through_level is not an observed current level.
        lead = result['native_fields']['supplies']['lead']
        self.assertEqual(lead['level'], 0)
        self.assertEqual(lead['moves_through_level'], 5)
        self.assertIsNone(lead['stats'])
        self.assertIn('entry_evidence', result['unbound'])

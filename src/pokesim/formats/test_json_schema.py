"""Check published documents and schema/reader agreement at the wire boundary."""

import copy
import json
import unittest

try:
    import jsonschema
except ImportError:
    jsonschema = None

from .json_schema import ROOT, SCHEMAS, published, validator
from pokesim.maps.runtime_map_schema import validate as validate_map
from pokesim.story.authored_checkpoint import read_authored_checkpoint
from pokesim.story.checkpoint_wire import read_checkpoint

# Copied byte for byte from dayfine/Arduino-Source #314 (frlg/story-json) at
# 3dcf3e8a231fce9935de5c60729272fa5347f52e, StoryData/frlg-00.*.plan.json.
FRLG_AUTHORED = ROOT / 'data/story/frlg-authored'


@unittest.skipUnless(jsonschema, 'install schemas/requirements.txt for schema tests')
class JsonSchemaTests(unittest.TestCase):
    def test_action_assertions_require_opt_in_and_exact_typed_lists(self):
        original = json.loads((ROOT / 'data/story/parcel-pilot/cases.json').read_text())
        check = validator('story-replay-cases')
        changes = [
            lambda c: c['expectation'].pop('actions'),
            lambda c: c['input'].update(check_actions=False),
            lambda c: c['input'].update(check_actions=1),
            lambda c: c['expectation']['actions'][0].update(tiles=True),
            lambda c: c['expectation']['actions'][0].update(extra='ignored'),
            lambda c: c['expectation']['actions'][0].update(kind='press'),
        ]
        for change in changes:
            with self.subTest(change=changes.index(change)):
                value = copy.deepcopy(original)
                change(value['cases'][0])
                self.assertFalse(check.is_valid(value))

    def test_schemas_are_valid_and_published_data_passes(self):
        for path in SCHEMAS.glob('*.schema.json'):
            validator(path.name[:-12])
        for name, path in published():
            with self.subTest(path=path):
                value = json.loads(path.read_text())
                validator(name).validate(value)
                if name == 'runtime-map-v2':
                    validate_map(value)

    def test_story_vectors_and_canonical_records(self):
        schema = json.loads((SCHEMAS / 'story-checkpoint.schema.json').read_text())
        cases = json.loads((ROOT / 'data/story/wire-conformance.json').read_text())['cases']
        for row in cases:
            record = row['input']['record']
            selected = schema if record == 'checkpoint' else {
                '$schema': schema['$schema'], '$defs': schema['$defs'], '$ref': '#/$defs/' + record}
            check = jsonschema.Draft202012Validator(selected)
            with self.subTest(name=row['input']['name']):
                if 'canonical' in row['expectation']:
                    check.validate(row['input']['value'])
                    check.validate(row['expectation']['canonical'])
                elif record != 'checkpoint' or 'duplicate' not in row['input']['name']:
                    self.assertFalse(check.is_valid(row['input']['value']))

    def test_map_pair_types_and_pickup_defaults(self):
        source = json.loads((ROOT / 'data/games/bdsp/maps/runtime/OreburghMine.json').read_text())
        check = validator('runtime-map-v2')
        variants = [
            ('short pair', lambda m: m['npcs'][0].update(coord=[1])),
            ('boolean coordinate', lambda m: m['npcs'][0].update(coord=[True, 1])),
            ('legacy alias', lambda m: m['npcs'][0].update(x=1)),
            ('missing pickup identity', lambda m: m['items'][0].pop('source_event')),
            ('zero quantity', lambda m: m['items'][0].update(quantity=0)),
            ('redundant kind', lambda m: m['npcs'][0].update(kind='npc')),
        ]
        for name, mutate in variants:
            with self.subTest(name=name):
                value = copy.deepcopy(source)
                mutate(value)
                self.assertFalse(check.is_valid(value))
        self.assertNotIn('quantity', source['items'][0])
        check.validate(source)
        self.assertNotIn('quantity', source['items'][0])

    def test_unidentified_pickup_metadata_is_allowed_but_cannot_conflict_with_identity(self):
        data = json.loads((ROOT / 'data/games/bdsp/maps/runtime/OreburghMine.json').read_text())
        item = data['items'][0]
        item.pop('item')
        item['name'] = 'unresolved_source_event'
        item['pickup'] = {'status': 'unresolved', 'reason': 'no pinned identity catalog'}
        check = validator('runtime-map-v2')
        check.validate(data)
        item['item'] = 'potion'
        self.assertFalse(check.is_valid(data))

    def test_battle_input_and_report_boundaries(self):
        data = json.loads((ROOT / 'data/games/frlg/battles/cases.json').read_text())
        check = validator('frlg-battle-cases')
        for level in (True, 0, 101):
            value = copy.deepcopy(data)
            value['cases'][0]['player']['level'] = level
            self.assertFalse(check.is_valid(value))
        report = {'format': 'pokesim-frlg-report/1', 'seed': 1, 'turn_limit': 100,
                  'results': [{'id': 'synthetic', 'battles': 20, 'wins': 18,
                               'win_probability': .9, 'outcomes': {'win': 18, 'loss': 2}}]}
        check = validator('frlg-battle-report')
        check.validate(report)
        report['results'][0]['win_probability'] = 1.1
        self.assertFalse(check.is_valid(report))

    def test_semantic_validation_is_still_required(self):
        value = {'id': 'example', 'title': 'Synthetic', 'events': [
            {'id': 'same', 'kind': 'talk'}, {'id': 'same', 'kind': 'talk'}]}
        validator('story-checkpoint').validate(value)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            read_checkpoint(value)

    def test_frlg_authored_plans_pass_schema_and_reader(self):
        check = validator('authored-checkpoint')
        paths = sorted(FRLG_AUTHORED.glob('*.plan.json'))
        self.assertEqual(len(paths), 35)
        for path in paths + [ROOT / 'data/story/parcel-pilot/frlg-parcel-02.01.plan.json']:
            with self.subTest(path=path.name):
                value = json.loads(path.read_text())
                check.validate(value)
                read_authored_checkpoint(value)

    def test_frlg_authored_fields_stay_strict(self):
        source = json.loads((FRLG_AUTHORED / 'frlg-00.28.plan.json').read_text())
        check = validator('authored-checkpoint')
        variants = [
            ('events and sections', lambda v: v['checkpoint'].update(events=[])),
            ('neither events nor sections', lambda v: v['checkpoint'].pop('sections')),
            ('no sections', lambda v: v['checkpoint'].update(sections=[])),
            ('empty section', lambda v: v['checkpoint']['sections'][0].update(events=[])),
            ('unknown section field', lambda v: v['checkpoint']['sections'][0].update(mystery=1)),
            ('empty section id', lambda v: v['checkpoint']['sections'][0].update(id='')),
            ('note not a string', lambda v: v['checkpoint'].update(notes=[1])),
            ('once_per_save not boolean', lambda v: v['checkpoint']['sections'][0]['events'][0].update(once_per_save=1)),
            ('unknown execution field', lambda v: v['execution'].update(mystery=1)),
            ('unknown handoff', lambda v: v['execution'].update(handoff='trade')),
            ('live_start not boolean', lambda v: v['execution'].update(live_start='yes')),
            ('unknown lead', lambda v: v['execution'].update(supplies={'lead': 'new_game'})),
            ('unknown supply', lambda v: v['execution'].update(supplies={'repels': 1})),
            ('supply beyond int', lambda v: v['execution'].update(supplies={'potions': 2147483648})),
            ('menu missing', lambda v: v['execution'].pop('menu')),
        ]
        check.validate(source)
        read_authored_checkpoint(source)
        for name, mutate in variants:
            with self.subTest(name=name):
                value = copy.deepcopy(source)
                mutate(value)
                self.assertFalse(check.is_valid(value))
                with self.assertRaises((ValueError, KeyError, TypeError)):
                    read_authored_checkpoint(value)

    def test_sections_still_need_unique_ids_in_code(self):
        value = {'id': 'x', 'title': 'X', 'sections': [
            {'id': 's', 'title': 'S', 'events': [{'id': 'a', 'kind': 'talk'}]},
            {'id': 't', 'title': 'T', 'events': [{'id': 'a', 'kind': 'talk'}]}]}
        validator('story-checkpoint').validate(value)
        with self.assertRaisesRegex(ValueError, 'duplicate story event'):
            read_checkpoint(value)
        value['sections'][1].update(id='s', events=[{'id': 'b', 'kind': 'talk'}])
        with self.assertRaisesRegex(ValueError, 'duplicate story section'):
            read_checkpoint(value)

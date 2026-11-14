"""The shared story cases, which Arduino-Source's native reader also reads."""
import json
from pathlib import Path
import unittest
from .checkpoint_wire import (read_action_specs, read_declared_pose, read_grid_pose, read_story_checkpoint,
                              read_story_step)

ROOT = Path(__file__).resolve().parents[3]


class CheckpointWireTest(unittest.TestCase):
    def test_shared_native_vectors(self):
        data = json.loads((ROOT / 'data/story/wire-conformance.json').read_text())
        self.assertEqual(data['format'], 'pokesim-story-wire-cases/2')
        actions = read_action_specs(data['actions'])
        readers = dict(pose=read_grid_pose, declared=read_declared_pose,
                       step=lambda value: read_story_step(value, actions),
                       checkpoint=lambda value: read_story_checkpoint(value, actions))
        for case in data['cases']:
            value, expected = case['input'], case['expectation']
            with self.subTest(name=value['name']):
                if expected.get('rejected'):
                    with self.assertRaises(ValueError):
                        readers[value['record']](value['value'])
                else:
                    actual = readers[value['record']](value['value'])
                    self.assertEqual(actual, expected['read'])
                    self.assertEqual(readers[value['record']](actual), actual)

    def test_game_actions_need_their_spec(self):
        step = {'id': 'buy', 'kind': 'game_action', 'action': 'mart', 'args': {'map': 'M', 'budget': 1}}
        with self.assertRaisesRegex(ValueError, 'unknown action'):
            read_story_step(step)

    def test_fallback_is_read_as_its_type(self):
        spec = [{'kind': 'game_action', 'name': 'x', 'args': [{'key': 'n', 'type': 'integer', 'fallback': True}]}]
        with self.assertRaises(ValueError):
            read_action_specs(spec)

    def test_required_arg_cannot_have_a_fallback(self):
        spec = [{'kind': 'game_action', 'name': 'x',
                 'args': [{'key': 'n', 'type': 'integer', 'required': True, 'fallback': 1}]}]
        with self.assertRaisesRegex(ValueError, 'required argument cannot have a fallback'):
            read_action_specs(spec)

    def test_invalid_records_raise_field_level_value_errors(self):
        cases = (
            ('pose map', read_grid_pose, {}, 'missing field: map'),
            ('declared place', read_declared_pose, {'place': 1}, 'place: expected string'),
            ('action args', read_action_specs, [{'kind': 'game_action', 'name': 'x'}], 'missing field: args'),
            ('step id', read_story_step, {'kind': 'talk'}, 'missing field: id'),
            ('checkpoint events', read_story_checkpoint, {'id': 'x', 'title': 'X'}, 'missing field: events'),
            ('item quantity', read_story_step,
             {'id': 'shop', 'kind': 'shop', 'args': {'items': [{'item': 'potion'}]}},
             'argument items: missing field: quantity'),
            ('verification hash', read_story_checkpoint,
             {'id': 'x', 'title': 'X', 'events': [], 'metadata': {'verified': {}}},
             'missing field: steps_hash'),
        )
        for name, reader, value, message in cases:
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, message):
                reader(value)


if __name__ == '__main__':
    unittest.main()

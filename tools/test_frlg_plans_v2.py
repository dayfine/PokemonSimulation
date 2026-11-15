"""Tests for the one-off FRLG plan converter.

    python3 -I -m unittest discover -s tools -t tools
"""

import unittest

from frlg_plans_v2 import convert_plan, convert_step

POSE = {'certainty': 'tile', 'map': 'CeruleanCity_Mart', 'where': {'kind': 'tiles', 'tiles': [[4, 3]], 'facing': 'west'}}
V2_POSE = {'map': 'CeruleanCity_Mart', 'tiles': [[4, 3]], 'facing': 'west'}
NURSE = {'certainty': 'tile', 'map': 'CeruleanCity_PokemonCenter_1F',
         'where': {'kind': 'tiles', 'tiles': [[7, 4]], 'facing': 'north'}}

STEP_CASES = [
    {
        'name': 'a run route: the variant is the action, the target an arg',
        'input': {'id': 'a', 'kind': 'route', 'variant': 'run', 'target': POSE, 'why': 'w'},
        'expectation': {'id': 'a', 'kind': 'route', 'action': 'run', 'args': {'target': V2_POSE}, 'why': 'w'},
    },
    {
        'name': 'a step without a direction faces north, as the older reader read it',
        'input': {'id': 'a', 'kind': 'step'},
        'expectation': {'id': 'a', 'kind': 'step', 'args': {'direction': 'north'}},
    },
    {
        'name': 'flags at their defaults are left out',
        'input': {'id': 'a', 'kind': 'answer', 'yes': True},
        'expectation': {'id': 'a', 'kind': 'answer'},
    },
    {
        'name': 'a flag off its default is an arg',
        'input': {'id': 'a', 'kind': 'battle', 'may_lose': True},
        'expectation': {'id': 'a', 'kind': 'battle', 'args': {'may_lose': True}},
    },
    {
        'name': "a Mart's words: the map, budget and floor, then what it buys",
        'input': {'id': 'a', 'kind': 'game_action', 'once_per_save': True,
                  'variant': 'mart CeruleanCity_Mart budget=1500 floor=1500 potion=3 awakening=2'},
        'expectation': {'id': 'a', 'kind': 'game_action', 'action': 'mart', 'once_per_save': True, 'args': {
            'map': 'CeruleanCity_Mart', 'budget': 1500, 'floor': 1500,
            'items': [{'item': 'potion', 'quantity': 3}, {'item': 'awakening', 'quantity': 2}]}},
    },
    {
        'name': "a GRIND's target is its nurse",
        'input': {'id': 'a', 'kind': 'game_action', 'target': NURSE,
                  'variant': 'grind slot=1 level=28 pace=west beat=TRAINER_X chance=50'},
        'expectation': {'id': 'a', 'kind': 'game_action', 'action': 'grind', 'args': {
            'slot': 1, 'level': 28, 'pace': 'west', 'beat': 'TRAINER_X', 'chance': 50,
            'nurse': {'map': 'CeruleanCity_PokemonCenter_1F', 'tiles': [[7, 4]], 'facing': 'north'}}},
    },
    {
        'name': "a PC's bare word is a flag",
        'input': {'id': 'a', 'kind': 'game_action', 'variant': 'pc deposit slot=2 box=1 if_present'},
        'expectation': {'id': 'a', 'kind': 'game_action', 'action': 'pc', 'args': {
            'do': 'deposit', 'slot': 2, 'box': 1, 'if_present': True}},
    },
    {
        'name': "a cut tree's direction is an arg",
        'input': {'id': 'a', 'kind': 'game_action', 'variant': 'cut_tree', 'direction': 'east'},
        'expectation': {'id': 'a', 'kind': 'game_action', 'action': 'cut_tree', 'args': {'direction': 'east'}},
    },
    {
        'name': 'a TM: the item and the move, then key=value',
        'input': {'id': 'a', 'kind': 'game_action', 'variant': 'teach tm03 water-pulse slot=1 forget=tail-whip'},
        'expectation': {'id': 'a', 'kind': 'game_action', 'action': 'teach', 'args': {
            'item': 'tm03', 'move': 'water-pulse', 'slot': 1, 'forget': 'tail-whip'}},
    },
]

REJECTED_STEP_CASES = [
    {'name': 'an unknown bare word', 'input': {'id': 'a', 'kind': 'game_action', 'variant': 'pc deposit slot=2 box=1 maybe'}},
    {'name': 'a target on an action without a pose arg',
     'input': {'id': 'a', 'kind': 'game_action', 'variant': 'pc deposit slot=2 box=1', 'target': NURSE}},
    {'name': 'a missing positional word', 'input': {'id': 'a', 'kind': 'game_action', 'variant': 'teach tm03 slot=1'}},
    {'name': 'a pose that is not one tile', 'input': {'id': 'a', 'kind': 'route', 'target': dict(POSE, certainty='set')}},
    {'name': "a field the kind doesn't take", 'input': {'id': 'a', 'kind': 'talk', 'legs': []}},
]


class ConvertStepTest(unittest.TestCase):
    def test_steps(self):
        for case in STEP_CASES:
            with self.subTest(case['name']):
                self.assertEqual(convert_step(case['input']), case['expectation'])

    def test_rejected_steps(self):
        for case in REJECTED_STEP_CASES:
            with self.subTest(case['name']):
                with self.assertRaises(ValueError):
                    convert_step(case['input'])


class ConvertPlanTest(unittest.TestCase):
    def test_sections_flatten_and_notes_move_to_execution(self):
        plan = {'format': 'pokesim-authored-checkpoint/1', 'game': 'frlg', 'execution': {'menu': 'full'}, 'checkpoint': {
            'id': '00.99', 'title': 'T', 'notes': ['about the checkpoint'], 'start': POSE, 'sections': [
                {'id': 's1', 'title': 'S1', 'notes': ['about s1'], 'events': [
                    {'id': 'talk1', 'kind': 'talk', 'notes': ['about talk1']},
                    {'id': 'talk2', 'kind': 'talk', 'notes': ['about talk2']}]},
                {'id': 's2', 'title': 'S2', 'events': [{'id': 'heal', 'kind': 'heal'}]}]}}
        self.assertEqual(convert_plan(plan), {
            'format': 'pokesim-authored-checkpoint/1', 'game': 'frlg',
            'checkpoint': {'id': '00.99', 'title': 'T', 'start': V2_POSE, 'events': [
                {'id': 'talk1', 'kind': 'talk'}, {'id': 'talk2', 'kind': 'talk'}, {'id': 'heal', 'kind': 'heal'}]},
            'execution': {'menu': 'full', 'notes': {
                'checkpoint': ['about the checkpoint'], 'talk1': ['about s1', 'about talk1'], 'talk2': ['about talk2']}}})

    def test_a_step_the_frlg_actions_reject_fails_the_plan(self):
        plan = {'format': 'pokesim-authored-checkpoint/1', 'game': 'frlg', 'execution': {'menu': 'full'}, 'checkpoint': {
            'id': '00.99', 'title': 'T', 'events': [{'id': 'a', 'kind': 'game_action', 'variant': 'grind slot=1 level=5'}]}}
        with self.assertRaisesRegex(ValueError, 'nurse'):
            convert_plan(plan)


if __name__ == '__main__':
    unittest.main()

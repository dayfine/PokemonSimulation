"""Current #226 mine checkpoint, pinned maps and explicit observation boundaries."""

import copy
import json
import unittest

from pokesim.maps.runtime_map_pack import ROOT
from pokesim.story.authored_checkpoint import read_authored_checkpoint
from pokesim.story.checkpoint_replay import run
from pokesim.story.replay_binding import load_binding
from pokesim.story.replay_cases import read_cases, check_case, render_cases

FOLDER = ROOT / 'data/story/bdsp-mine-pilot'


class BDSPStoryReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = read_cases(FOLDER / 'cases.json')

    def binding(self):
        return load_binding(FOLDER / 'binding.json')

    def test_all_shared_scenarios(self):
        binding = self.binding()
        for case in self.cases:
            with self.subTest(case=case['id']):
                check_case(case, run(binding, case['input']))

    def test_success_runs_every_authored_event_and_keeps_all_native_alternatives(self):
        binding = self.binding()
        report = run(binding, self.cases[0]['input'])
        self.assertEqual(15, len(report['completed_events']))
        self.assertEqual([e['id'] for e in binding.checkpoint['events']], report['completed_events'])
        bounds = next(t for t in report['trace'] if t['phase'] == 'wall_bounds')
        self.assertEqual((37, 38), (bounds['fewest'], bounds['most']))
        self.assertIsNone(report['native_source_revision'])
        self.assertFalse(report['save_performed'])

    def test_both_exit_tiles_relocalize_at_the_same_wall(self):
        for y, tiles in ((59, 38), (58, 37)):
            with self.subTest(exit_y=y):
                scenario = copy.deepcopy(self.cases[0]['input'])
                scenario['signals']['out_of_the_mine']['pose']['tile'] = [46, y]
                report = run(self.binding(), scenario)
                self.assertEqual('model_complete', report['status'])
                action = next(a for a in report['actions'] if a['event'] == 'north_to_the_centers_wall')
                self.assertEqual(tiles, action['tiles'])
                step = next(t for t in report['trace'] if t['event'] == 'north_to_the_centers_wall' and t['phase'] == 'completed')
                self.assertEqual([46, 21], step['pose']['tile'])

    def test_interruption_retains_requested_leg_and_two_uncredited_tiles(self):
        case = next(c for c in self.cases if c['id'] == 'interrupted-before-roark')
        report = run(self.binding(), case['input'])
        self.assertEqual([5], [a['tiles'] for a in report['actions']
                             if a['event'] == 'to_roarks_corner' and a.get('direction') == 'south' and a.get('tiles') == 5])
        self.assertEqual([[15, 12], [15, 13]], [p['tile'] for p in report['candidates']])
        self.assertTrue(all(p['facing'] is None for p in report['candidates']))
        self.assertNotIn('roark', report['completed_events'])

    def test_source_corridor_is_traversed_before_the_door_observation(self):
        report = run(self.binding(), self.cases[0]['input'])
        reached = {t['event']: t for t in report['trace'] if t['phase'] == 'doorway_reached'}
        self.assertEqual([12, 21], reached['into_the_coal_room']['tile'])
        self.assertGreater(reached['into_the_coal_room']['walked'], 1)
        self.assertEqual([12, 1], reached['out_of_the_mine']['tile'])

    def test_shortened_leg_cannot_be_rescued_by_declared_after(self):
        binding = self.binding()
        event = next(e for e in binding.checkpoint['events'] if e['id'] == 'below_roark')
        event['legs'][0]['tiles'] = 1
        report = run(binding, self.cases[0]['input'])
        self.assertEqual('declared_arrival_disagrees_with_model', report['failure'])
        self.assertNotIn('roark', report['completed_events'])

    def test_talk_requires_adjacency_not_just_a_requested_dialogue(self):
        binding = self.binding()
        actor = next(o for o in binding.adapter.world.views['OreburghMine'].data['objects'] if o['name'] == 'roark')
        actor['x'] -= 1  # Synthetic actor diagnostic; map source/terrain remains unchanged.
        report = run(binding, self.cases[0]['input'])
        self.assertEqual('not_adjacent_to_dialogue_target', report['failure'])

    def test_invalid_observation_type_does_not_pass_as_true(self):
        scenario = copy.deepcopy(self.cases[0]['input'])
        scenario['signals']['into_the_mine']['result']['transition'] = 1
        with self.assertRaises(ValueError):
            run(self.binding(), scenario)

    def test_clearance_actor_and_bound_profiles_are_strict(self):
        binding = self.binding()
        scenario = copy.deepcopy(self.cases[0]['input'])
        scenario['signals']['above_the_mine']['clear_npcs'] = ['unknown']
        with self.assertRaises(ValueError):
            run(binding, scenario)
        for change in (lambda e: e.update(variant='one_short_ok'),
                       lambda e: e['legs'][0].update(tiles=-1)):
            event = copy.deepcopy(binding.checkpoint['events'][4])
            change(event)
            with self.assertRaises(ValueError):
                binding.adapter.validate_event(event)

    def test_unreached_encounter_injection_cannot_silently_pass(self):
        scenario = copy.deepcopy(next(c['input'] for c in self.cases if c['id'] == 'interrupted-before-roark'))
        scenario['signals']['to_roarks_corner']['encounter']['direction'] = 'north'
        with self.assertRaisesRegex(ValueError, 'not reached'):
            run(self.binding(), scenario)

    def test_game_extensions_do_not_leak_between_games(self):
        plan = json.loads((FOLDER / 'bdsp-mine-01.03.plan.json').read_text())
        for change in (lambda p: p['execution'].update(menu='full'),
                       lambda p: p['execution'].update(saves_in=''),
                       lambda p: p['execution'].update(on_failure='guess')):
            altered = copy.deepcopy(plan)
            change(altered)
            with self.assertRaises(ValueError):
                read_authored_checkpoint(altered)

    def test_review_document_is_generated_without_running_the_simulation(self):
        self.assertEqual((FOLDER / 'CASES.md').read_text(), render_cases(self.cases))

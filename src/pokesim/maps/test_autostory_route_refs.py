"""Reviewed native route contracts, not a parser or replay of C++ source."""

import unittest

from .test_route_goldens import cases


class AutoStoryReferenceTest(unittest.TestCase):
    def test_pallet_checkpoint_targets_oaks_trigger_not_the_lab(self):
        case = next(case for case in cases() if case['id'] == 'frlg-pallet-town')
        self.assertEqual(case['start'], [6, 8])
        self.assertEqual(case['goal'], [12, 2])
        self.assertEqual(case['goal_facing'], 'north')
        self.assertEqual(case['source']['checkpoint'], '00.03')
        self.assertEqual(case['source']['step'], 'below_oaks_trigger')

    def test_fan_club_arrives_on_mat_and_talks_from_west(self):
        case = next(case for case in cases() if case['id'] == 'frlg-fan-club')
        self.assertEqual(case['start'], [5, 10])
        self.assertEqual(case['goal'], [4, 4])
        self.assertEqual(case['goal_facing'], 'east')
        self.assertEqual(case['source']['checkpoint'], '00.26')
        self.assertEqual(case['source']['step'], 'beside_chairman')

    def test_route202_uses_story_save_and_goal_region(self):
        case = next(case for case in cases() if case['id'] == 'bdsp-route202-story')
        self.assertEqual(case['start'], [30, 24])
        self.assertEqual(case['goal_region'], 'jubilife_exit')
        self.assertEqual(case['source']['checkpoint'], '00.04d')
        self.assertEqual(case['source']['step'], 'north_to_jubilife')


if __name__ == '__main__':
    unittest.main()

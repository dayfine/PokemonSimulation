"""plan.json's item budget: per-fight caps add up to the bag, and reserves are exactly the later fights' caps."""

import unittest

from pokesim.cli.frlg_league_chain import BAG_NOW
from pokesim.games.frlg.league import planned

# Every one of these is spent somewhere: the caps use the whole bag.
WHOLE_BAG = ('fullrestore', 'xspecial', 'xspeed', 'maxelixir')


class PlanBudgetTest(unittest.TestCase):
    def setUp(self):
        self.plan = planned.load_plan()

    def total(self, name):
        return sum(planned.caps(self.plan, f).get(name, 0) for f in planned.FIGHTS)

    def test_caps_use_the_whole_bag(self):
        for name in WHOLE_BAG:
            self.assertEqual(self.total(name), BAG_NOW[name], name)

    def test_caps_fit_in_the_bag(self):
        names = {n for f in planned.FIGHTS for n in planned.caps(self.plan, f)}
        for name in names:
            self.assertLessEqual(self.total(name), BAG_NOW.get(name, 0), name)

    def test_reserves_are_the_later_caps(self):
        want = planned.reserves_from_caps(self.plan)
        for fight in planned.FIGHTS:
            self.assertEqual(self.plan['fights'][fight]['reserve']['items'], want[fight], fight)

    def test_setup_goals_fit_the_x_item_caps(self):
        for fight in planned.FIGHTS:
            need = planned.setup_count(self.plan['fights'][fight]['foes'])
            for name, stages in need.items():
                cap = planned.caps(self.plan, fight).get(name, 0)
                # X Speed at Bruno: a goal of +1 may take up to its cap (Rock Tomb lowers Speed).
                self.assertLessEqual(stages, cap, (fight, name))


if __name__ == '__main__':
    unittest.main()

"""League retry budget: a fight's Full Restore budget k, and the X items an allocation consumes."""

import unittest

from pokesim.cli import frlg_league_retry as retry
from pokesim.games.frlg.league import planned
from pokesim.games.frlg.league.chain import MOVE_PP


def carry(hp, **bag):
    return {'hp': hp, 'status': '', 'pp': dict(MOVE_PP), 'bag': dict(bag)}


class BudgetTest(unittest.TestCase):
    def test_top_up_spends_a_full_restore_only_within_the_budget(self):
        base = planned.load_plan()
        none = carry(40, fullrestore=retry.FR_POOL)
        planned.between(none, 171, retry.run_plan(base, 'lance', k=0), 'lance', MOVE_PP)
        self.assertEqual((none['hp'], none['bag']['fullrestore']), (40, retry.FR_POOL))
        one = carry(40, fullrestore=retry.FR_POOL)
        planned.between(one, 171, retry.run_plan(base, 'lance', k=1), 'lance', MOVE_PP)
        self.assertEqual((one['hp'], one['bag']['fullrestore']), (171, retry.FR_POOL - 1))

    def test_more_setup_and_long_champion_setup_exceed_x_special(self):
        use = retry.x_use(['more_setup', 'plan', 'plan', 'plan'], 'long')
        self.assertGreater(use['xspecial'], retry.BAG_NOW['xspecial'])
        use = retry.x_use(['more_setup', 'plan', 'plan', 'plan'], 'plan')
        self.assertLessEqual(use['xspecial'], retry.BAG_NOW['xspecial'])


if __name__ == '__main__':
    unittest.main()

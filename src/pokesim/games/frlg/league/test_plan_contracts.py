"""plan.json's entry / exit contracts add up: the bag covers Lorelei's entry, each fight's entry less what it may
still spend covers its exit, each exit less the next top-up covers the next entry, and the items sum to the bag."""

import copy
import math
import unittest

from pokesim.cli.frlg_league_chain import BAG_NOW
from pokesim.games.frlg.league import planned
from pokesim.games.frlg.league.chain import MOVE_PP, ours_at
from pokesim.games.frlg.league.contracts import ITEMS, binom_cdf, contract

MAX_HP = ours_at(54)['hp']
PP_TOPUP = ('elixir', 'maxelixir')


class PlanContractTest(unittest.TestCase):
    def setUp(self):
        self.plan = planned.load_plan()

    def pairs(self):
        return zip(planned.FIGHTS, planned.FIGHTS[1:])

    def test_the_bag_meets_lorelei_entry(self):
        entry = contract(self.plan, 'lorelei')['entry']
        for name in ITEMS:
            self.assertGreaterEqual(BAG_NOW[name], entry['items'][name], name)
        for move, pp in entry['pp'].items():
            self.assertLessEqual(pp, MOVE_PP[move.upper()], move)

    def test_entry_less_what_the_fight_may_spend_meets_its_exit(self):
        # The caps include the top-up, so in the fight itself it may spend caps - top-up.
        for fight in planned.FIGHTS:
            c = contract(self.plan, fight)
            caps = planned.caps(self.plan, fight)
            for name in ITEMS:
                left = c['entry']['items'][name] - (caps.get(name, 0) - c['topup'].get(name, 0))
                self.assertGreaterEqual(left, c['exit']['items'][name], (fight, name))

    def test_exit_less_the_next_topup_meets_the_next_entry(self):
        for prev, fight in self.pairs():
            x, c = contract(self.plan, prev)['exit'], contract(self.plan, fight)
            for name in ITEMS:
                self.assertGreaterEqual(x['items'][name] - c['topup'].get(name, 0), c['entry']['items'][name],
                                        (prev, fight, name))
            if not any(c['topup'].get(name) for name in PP_TOPUP):
                # No PP item before this fight: its PP is what the last fight left (Blizzard held as a reserve).
                self.assertGreaterEqual(x['pp'].get('blizzard', 0), c['entry']['pp']['blizzard'], (prev, fight))
                self.assertGreaterEqual(x['surf']['min'], c['entry']['pp']['surf'], (prev, fight))

    def test_items_sum_to_the_bag(self):
        last = contract(self.plan, planned.FIGHTS[-1])['exit']['items']
        for name in ITEMS:
            spent = sum(planned.caps(self.plan, f).get(name, 0) for f in planned.FIGHTS)
            self.assertEqual(spent + last[name], BAG_NOW[name], name)

    def test_the_topup_spends_no_more_than_its_contract(self):
        # Every HP, with and without a status, PP drained or full, from the previous fight's exit bag.
        for prev, fight in self.pairs():
            bag = dict(contract(self.plan, prev)['exit']['items'])
            bag.update({k: BAG_NOW[k] for k in ('fullheal', 'parlyzheal', 'antidote')})
            topup = contract(self.plan, fight)['topup']
            for hp in range(1, MAX_HP + 1):
                for status in ('', 'par', 'slp'):
                    for pp in (0, None):
                        carry = {'hp': hp, 'status': status, 'bag': copy.deepcopy(bag),
                                 'pp': {k: (v if pp is None else pp) for k, v in MOVE_PP.items()}}
                        used = planned.between(carry, MAX_HP, self.plan, fight, MOVE_PP)
                        for name in ITEMS:
                            self.assertLessEqual(used.get(name, 0), topup.get(name, 0), (fight, hp, status, name))
                        # One heal: Super Potions or a Full Restore, never both.
                        self.assertFalse(used.get('superpotion') and used.get('fullrestore'), (fight, hp, status))

    def test_pass_figures_follow_the_binomial(self):
        for fight in planned.FIGHTS:
            c = contract(self.plan, fight)['pass']
            p, k, n = c['expected_pass'], c['min_pass']['k'], c['min_pass']['of']
            if k:
                self.assertLess(binom_cdf(k - 1, n, p), 0.05, fight)
            self.assertGreaterEqual(binom_cdf(k, n, p), 0.05, fight)
            self.assertEqual(c['reset_budget'], math.ceil(3 / p), fight)


if __name__ == '__main__':
    unittest.main()

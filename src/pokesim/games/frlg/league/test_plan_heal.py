"""Per-foe plan keys: the `heal` block and the attack `sequence`."""

import unittest

from pokesim.games.frlg.league import planned


def state(hp, bag, foe_index=4):
    return {'own': {'hp': hp, 'max_hp': 171, 'moves': [
                {'id': 'bite', 'pp': 25, 'disabled': False}, {'id': 'strength', 'pp': 15, 'disabled': False}]},
            'bag': dict(bag), 'foe': {'party_index': foe_index}}


def goals(reserve=None):
    plan = {'fights': {'bruno': {'reserve': {'items': dict(reserve or {})}}}}
    return {'_league_plan': plan, '_fight': 'bruno'}


class HealBlockTest(unittest.TestCase):
    RULE = {'heal': {'below': 80, 'heal_at_least': 100}}

    def test_no_heal_at_or_above_the_threshold(self):
        self.assertIsNone(planned.foe_heal(state(80, {'fullrestore': 2}), goals(), self.RULE))

    def test_super_potion_too_small_so_full_restore(self):
        self.assertEqual(planned.foe_heal(state(60, {'superpotion': 3, 'fullrestore': 2}), goals(), self.RULE),
                         'fullrestore')

    def test_super_potion_enough_when_heal_at_least_50(self):
        rule = {'heal': {'below': 80, 'heal_at_least': 50}}
        self.assertEqual(planned.foe_heal(state(60, {'superpotion': 3, 'fullrestore': 2}), goals(), rule),
                         'superpotion')

    def test_full_restore_budget_holds(self):
        self.assertIsNone(planned.foe_heal(state(60, {'fullrestore': 2}), goals({'fullrestore': 2}), self.RULE))


class SequenceTest(unittest.TestCase):
    def test_nth_attack_uses_the_nth_move_then_falls_back(self):
        plan_foe = {'sequence': ['strength', 'bite'], 'moves': ['bite']}
        g = goals()
        s = state(171, {})
        self.assertEqual(planned.sequence_move(s, g, plan_foe)[1]['id'], 'strength')
        g['_memo'] = {('attacks', 4): 1}
        self.assertEqual(planned.sequence_move(s, g, plan_foe)[1]['id'], 'bite')
        g['_memo'] = {('attacks', 4): 2}
        self.assertIsNone(planned.sequence_move(s, g, plan_foe))


if __name__ == '__main__':
    unittest.main()

"""Regression cases for the planned League policy: the console failures of 2026-11-16.

Each case checks the planned policy's choice; where the old policy (autostory_new, the program's
greedy per-turn rows) made the console's mistake, the case also pins that (the red half).
"""

import unittest

from pokesim.games.frlg.battle.test_battle import HAS_ENGINE

BAG = {'fullrestore': 8, 'xspecial': 15, 'xspeed': 5, 'xaccuracy': 3, 'guardspec': 2, 'maxelixir': 1,
       'elixir': 1, 'superpotion': 6, 'fullheal': 2, 'parlyzheal': 2, 'antidote': 1}
FULL_PP = {'BITE': 25, 'STRENGTH': 15, 'SURF': 15, 'BLIZZARD': 5}


@unittest.skipUnless(HAS_ENGINE, "Install engines/frlg-showdown dependencies for battle integration checks")
class PlannedPolicyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from pokesim.cli.frlg_league_chain import league_cases
        from pokesim.games.frlg.battle.engine import Engine
        from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
        from pokesim.games.frlg.league import autostory, chain, planned, specs
        cls.autostory, cls.chain, cls.planned = autostory, chain, planned
        cls.cases, cls.pret = league_cases()
        cls.ai = NPCTrainerAI(cls.pret)
        cls.plan = planned.build(specs.BASE, BAG)
        cls.engine = Engine().__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.engine.__exit__(None, None, None)

    def start(self, fight, slot, hp=None, pp=None, bag=None, boosts=None, foe_boosts=None, foe_hp=None):
        carry = {'hp': hp, 'status': '', 'pp': dict(FULL_PP, **(pp or {})), 'bag': dict(bag if bag is not None else BAG)}
        scenario = self.chain.fight_scenario(self.cases[fight], self.pret, carry, self.chain.ours_at(54), 54)
        party = scenario['trainer']['party']
        others = [p for i, p in enumerate(party) if i != slot]
        scenario['trainer']['party'] = [party[slot]] + others  # the foe leads; the rest stay alive
        if boosts:
            scenario['player']['boosts'] = boosts
        if foe_boosts:
            scenario['trainer']['party'][0]['boosts'] = foe_boosts
        state = self.engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
        if foe_hp is not None:
            state['foe']['hp'] = foe_hp
            state['party'][0]['hp'] = foe_hp
        items = [i.lower().replace('_', '') for i in scenario['trainer']['items']]
        goals = {'_fight': fight, '_league_plan': self.plan, '_trainer_items': items}
        return state, goals, scenario

    def choose(self, state, goals, streak=0):
        return self.planned.choose(state, goals, streak)

    def move_id(self, state, action):
        return state['own']['moves'][action['slot']]['id'] if action.get('kind') == 'move' else action.get('item')

    def old(self, state, fight, scenario):
        policy = self.autostory.POLICIES['autostory_new']
        goals = {'_fight': fight, '_plan': self.autostory.plan(BAG, True), '_start_bag': dict(BAG)}
        items = [i.lower().replace('_', '') for i in scenario['trainer']['items']]
        return self.move_id(state, policy(state, self.ai, scenario['trainer']['ai'], items, goals))

    # 1. Blizzard PP spent on Gyarados and the Dragonairs before Dragonite.
    def test_1_blizzard_is_reserved_before_lance_and_not_spent_on_gyarados(self):
        done = {'spa': 3, 'spe': 6, 'accuracy': 2}  # the old rows' setup is complete: it attacks
        state, goals, scenario = self.start('agatha', 1, boosts=done)  # Golbat: Blizzard is the best hit
        self.assertEqual(self.old(state, 'agatha', scenario), 'blizzard')
        _, action = self.choose(state, goals)
        self.assertNotEqual(self.move_id(state, action), 'blizzard')
        state, goals, scenario = self.start('lance', 0, boosts=done)  # Gyarados
        self.assertEqual(self.old(state, 'lance', scenario), 'blizzard')
        _, action = self.choose(state, goals)
        self.assertNotEqual(self.move_id(state, action), 'blizzard')

    # 2. X Accuracy against Dragonite with Blizzard at 0 PP.
    def test_2_setup_goal_needs_its_moves_pp(self):
        state, goals, _ = self.start('lance', 0, pp={'BLIZZARD': 0}, bag=dict(BAG, elixir=0, maxelixir=0))
        why, action = self.choose(state, goals)
        self.assertNotIn(action.get('item'), ('xaccuracy', 'xspecial'))
        state, goals, _ = self.start('lance', 0)
        why, action = self.choose(state, goals)
        self.assertEqual((why, action.get('item')), ('plan:setup', 'xspecial'))

    # 3. Surf into Dragonite's resistance. In Gen 3 Bite is special: Surf (95, STAB, 1/2) and Bite (60, 1x)
    # land within a few points (Lv54: 22-27 vs 22-26), not 25% apart. The plan takes Bite to keep Surf's
    # 15 PP for the Champion; the old rows took the strongest (Surf).
    def test_3_dragonite_without_blizzard_takes_bite(self):
        state, goals, scenario = self.start('lance', 4, pp={'BLIZZARD': 0}, bag=dict(BAG, elixir=0, maxelixir=0),
                                            boosts={'spa': 3, 'spe': 6, 'accuracy': 2})
        bite = next(m for m in state['own']['moves'] if m['id'] == 'bite')
        surf = next(m for m in state['own']['moves'] if m['id'] == 'surf')
        self.assertLess(abs(sum(bite['damage']) - sum(surf['damage'])), 0.1 * sum(surf['damage']))
        self.assertEqual(self.old(state, 'lance', scenario), 'surf')
        _, action = self.choose(state, goals)
        self.assertEqual(self.move_id(state, action), 'bite')

    # 4. Strength "finisher" under 25%: the trainer's Full Restore lands first.
    def test_4_no_finisher_into_a_trainer_full_restore(self):
        state, goals, scenario = self.start('lorelei', 4, foe_hp=26, boosts={'spa': 3})  # Lapras 12%
        self.assertEqual(self.old(state, 'lorelei', scenario), 'strength')
        self.assertEqual(self.planned.foe_hp_at_our_move(state, goals), state['foe']['max_hp'])
        self.assertEqual(self.planned.danger(state, goals)['normal_max'], 0)  # it heals instead of attacking
        why, action = self.choose(state, goals)
        self.assertNotEqual(why, 'sure_ko')

    def test_4_pret_trainer_item_slots(self):
        from pokesim.games.frlg.battle.npc_actions import trainer_item_slots
        state, goals, _ = self.start('lorelei', 0)
        items = goals['_trainer_items']
        self.assertEqual(trainer_item_slots(state, items), ['fullrestore'])  # 5 alive: slot 0 only
        state['trainer_items_used'] = {'fullrestore': 1}
        self.assertEqual(trainer_item_slots(state, items), [])
        state['party'][1]['hp'] = 0  # 4 alive: slot 1 opens
        self.assertEqual(trainer_item_slots(state, items), ['fullrestore'])

    # 5. Chained Super Potions against Dragon Rage / Hyper Beam.
    def test_5_no_super_potion_that_does_not_outpace_the_foe(self):
        state, goals, _ = self.start('lance', 1, hp=50)  # Dragonair: Hyper Beam 45-54, Dragon Rage 40
        why, action = self.choose(state, goals)
        self.assertEqual(why, 'ko_heal')
        self.assertNotEqual(action['item'], 'superpotion')
        why, action = self.choose(state, goals, streak=2)
        self.assertEqual(action, {'kind': 'item', 'item': 'fullrestore'})

    # 6. Full Restore against the second Onix with Machamp's threat row.
    def test_6_ko_risk_uses_the_current_foe(self):
        state, goals, _ = self.start('bruno', 3, hp=60, boosts={'spa': 2, 'spe': 1})
        d = self.planned.danger(state, goals)['normal_max']
        self.assertLess(d, 60)
        why, action = self.choose(state, goals)
        self.assertEqual(action['kind'], 'move')

    # 7. Our Speed after Rock Tomb.
    def test_7_speed_stages_decide_who_moves_first(self):
        state, _, _ = self.start('bruno', 1)  # Hitmonchan, 101 Speed
        surf = next(m for m in state['own']['moves'] if m['id'] == 'surf')
        self.assertTrue(self.planned.we_move_first(state, surf))
        state, _, _ = self.start('bruno', 1, boosts={'spe': -1})
        self.assertFalse(self.planned.we_move_first(state, surf))

    # 8. "We move first and the hit KOs" with the foe at +3 evasion.
    def test_8_evasion_is_no_sure_ko(self):
        state, goals, _ = self.start('agatha', 0, foe_boosts={'evasion': 3}, foe_hp=40, boosts={'spa': 2})
        surf = next(m for m in state['own']['moves'] if m['id'] == 'surf')
        self.assertLess(surf['accuracy'], 1)
        why, _ = self.choose(state, goals)
        self.assertNotEqual(why, 'sure_ko')

    # 9. Gyarados's Hyper Beam at 101 HP.
    def test_9_gyarados_hyper_beam_is_in_the_risk(self):
        state, goals, _ = self.start('lance', 0, hp=101)
        beam = next(m for m in state['foe']['moves'] if m['id'] == 'hyperbeam')
        self.assertEqual(self.planned.danger(state, goals)['normal_max'], max(beam['damage']))
        self.assertLess(max(beam['damage']), 101)  # no KO without a critical hit (68-80 at Lv54)
        self.assertGreaterEqual(max(beam['critical']), 101)

    # User rule 2026-11-16: kill order around the trainer heal.
    def test_kill_order_keeps_the_foe_out_of_heal_range(self):
        state, goals, _ = self.start('bruno', 4, foe_hp=79)  # Machamp 79/183: Surf leaves 4-16
        surf = next(m for m in state['own']['moves'] if m['id'] == 'surf')
        self.assertTrue(any(0 < 79 - r < 183 // 4 for r in surf['damage']))
        why, action = self.choose(state, goals)
        self.assertEqual(why, 'kill_order')
        opener = state['own']['moves'][action['slot']]
        self.assertGreaterEqual(79 - max(opener['damage']), 183 // 4)

    # User rule 2026-11-16: a PP item stays unspent until after Lance.
    def test_max_elixir_is_held_until_the_champion(self):
        bag = dict(BAG, elixir=0)
        state, goals, _ = self.start('lance', 4, pp={'BLIZZARD': 0, 'BITE': 0, 'SURF': 0}, bag=bag)
        why, action = self.choose(state, goals)
        self.assertNotEqual(action.get('item'), 'maxelixir')
        carry = {'hp': 171, 'status': '', 'pp': dict(FULL_PP, BLIZZARD=0, SURF=7), 'bag': dict(bag)}
        self.planned.between(carry, 171, self.plan, 'lance', FULL_PP)
        self.assertEqual(carry['bag']['maxelixir'], 1)
        self.planned.between(carry, 171, self.plan, 'champion', FULL_PP)
        self.assertEqual((carry['bag']['maxelixir'], carry['pp']['BLIZZARD']), (0, 5))

    # Console Champion loss 2026-11-16: entry 89/171, Surf 7, Blizzard 0, Max Elixir used before it;
    # Venusaur took Strength. With the Max Elixir working, Venusaur takes Blizzard.
    def test_champion_venusaur_takes_blizzard(self):
        carry = {'hp': 89, 'status': '', 'pp': dict(FULL_PP, BLIZZARD=0, SURF=7), 'bag': dict(BAG)}
        used = self.planned.between(carry, 171, self.plan, 'champion', FULL_PP)
        self.assertEqual(carry['pp']['BLIZZARD'], 5)
        self.assertEqual(carry['hp'], 171)
        state, goals, _ = self.start('champion', 5, pp=carry['pp'])
        _, action = self.choose(state, goals)
        self.assertEqual(self.move_id(state, action), 'blizzard')
        self.assertTrue(used)


if __name__ == '__main__':
    unittest.main()

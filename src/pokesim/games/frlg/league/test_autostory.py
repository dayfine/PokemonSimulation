"""AutoStory League policy port: the foe's KO-risk input (D)."""

import unittest

from pokesim.games.frlg.battle.test_battle import HAS_ENGINE


@unittest.skipUnless(HAS_ENGINE, "Install engines/frlg-showdown dependencies for battle integration checks")
class ChampionVenusaurTest(unittest.TestCase):
    """Venusaur (Lv63, Solar Beam, no sun) against our Lv54 Blastoise at full HP (171)."""

    @classmethod
    def setUpClass(cls):
        from pokesim.cli.frlg_league_chain import league_cases
        from pokesim.games.frlg.battle.engine import Engine
        from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
        from pokesim.games.frlg.league import autostory, chain
        cls.autostory = autostory
        cases, pret = league_cases()
        cls.ai = NPCTrainerAI(pret)
        carry = {'hp': None, 'status': '', 'pp': dict(chain.MOVE_PP), 'bag': {'xspecial': 4}}
        scenario = chain.fight_scenario(cases['champion'], pret, carry, chain.ours_at(54), 54)
        scenario['trainer']['party'] = [p for p in scenario['trainer']['party'] if p['species'] == 'VENUSAUR']
        cls.flags = scenario['trainer']['ai']
        cls.engine = Engine().__enter__()
        cls.full = cls.engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
        # Venusaur picks Solar Beam (slot 0); we spend the turn on an X Special.
        cls.charging = cls.engine.request(command='step', own={'kind': 'item', 'item': 'xspecial'},
                                          foe={'kind': 'move', 'slot': 0})

    @classmethod
    def tearDownClass(cls):
        cls.engine.__exit__(None, None, None)

    def danger(self, state):
        goals = {'_fight': 'champion'}
        return self.autostory.danger(state, self.ai, self.flags, goals)

    def test_charge_turn_is_no_ko_risk_from_full_hp(self):
        own = self.full['own']
        self.assertEqual(own['hp'], own['max_hp'])
        self.assertLess(self.danger(self.full)['normal_max'], own['hp'])

    def test_a_charged_solar_beam_is_a_ko_risk(self):
        self.assertEqual(self.charging['foe']['locked_move'], 'solarbeam')
        self.assertGreaterEqual(self.danger(self.charging)['normal_max'], self.charging['own']['max_hp'])

    def test_full_hp_against_a_charge_move_sets_up(self):
        policy = self.autostory.POLICIES['autostory_new']
        plan = self.autostory.plan({'xspecial': 4}, True)
        goals = {'_fight': 'champion', '_plan': plan, '_start_bag': {'xspecial': 4}}
        choice = policy(self.full, self.ai, self.flags, [], goals)
        self.assertEqual(choice, {'kind': 'item', 'item': 'xspecial'})


if __name__ == '__main__':
    unittest.main()

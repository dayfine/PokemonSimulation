"""PokeGuy's League chain: his out-of-battle healing and the held-item override."""

import unittest

from pokesim.games.frlg.league import chain


def carry(hp, status='', pp=None, **bag):
    return {'hp': hp, 'status': status, 'pp': dict(pp or chain.MOVE_PP), 'bag': dict(bag)}


class PokeguyBetweenTest(unittest.TestCase):
    """state-history.json: 130/162 into Bruno and 45/165 into Agatha untouched; a Full Restore to full
    before Lance and the Champion with his Super Potions unused; his Elixir before the Champion."""

    def test_no_top_up_before_agatha(self):
        c = carry(45, fullrestore=12, superpotion=4)
        self.assertEqual(chain.pokeguy_between(c, 165, 'agatha'), {})
        self.assertEqual(c['hp'], 45)

    def test_full_restore_before_lance(self):
        c = carry(48, fullrestore=12, superpotion=4)
        self.assertEqual(chain.pokeguy_between(c, 168, 'lance'), {'fullrestore': 1})
        self.assertEqual((c['hp'], c['bag']['superpotion']), (168, 4))

    def test_elixir_before_champion(self):
        c = carry(37, pp={'BITE': 18, 'SURF': 3, 'BLIZZARD': 0, 'STRENGTH': 15}, fullrestore=10, elixir=1)
        self.assertEqual(chain.pokeguy_between(c, 171, 'champion'), {'fullrestore': 1, 'elixir': 1})
        self.assertEqual(c['pp'], {'BITE': 25, 'SURF': 13, 'BLIZZARD': 5, 'STRENGTH': 15})

    def test_status_cured_with_its_own_cure(self):
        c = carry(100, status='par', parlyzheal=1, fullrestore=5)
        self.assertEqual(chain.pokeguy_between(c, 162, 'bruno'), {'parlyzheal': 1})
        self.assertEqual((c['status'], c['hp']), ('', 100))


class HeldItemTest(unittest.TestCase):
    """The cases carry PokeGuy's Black Glasses; our console Blastoise holds nothing."""

    @classmethod
    def setUpClass(cls):
        from pokesim.cli.frlg_league_chain import league_cases
        cls.cases, cls.pret = league_cases()

    def scenario(self, held_item):
        return chain.fight_scenario(self.cases['lorelei'], self.pret, carry(None), chain.ours_at(54), 54,
                                    held_item=held_item)

    def test_case_keeps_his_black_glasses(self):
        self.assertEqual(self.scenario(None)['player']['held_item'], 'BLACK_GLASSES')

    def test_empty_string_holds_nothing(self):
        self.assertEqual(self.scenario('')['player']['held_item'], '')


if __name__ == '__main__':
    unittest.main()

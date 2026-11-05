"""Keep preparation comparisons isolated and coherent with live progression."""

import copy
import json
import unittest

from pokesim.cli.frlg_preparation import DATA, preparation_cases
from pokesim.games.frlg.battle.run import trainer_cases
from pokesim.games.frlg.battle.schema import validate_cases
from pokesim.games.frlg.progression.stats import summary_stats


class PreparationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda name: json.loads((DATA / (name + '.json')).read_text())
        cls.reference, cls.pret = read('reference'), read('battle-reference')
        cls.originals = trainer_cases(read('events'), cls.reference, read('moves'),
                                     read('state-history'), cls.pret)['cases']

    def test_full_hp_preserves_fast_case_and_pp_and_potion_accounting(self):
        before = copy.deepcopy(self.originals)
        cases = preparation_cases(self.originals, self.reference)
        self.assertEqual(before, self.originals)
        validate_cases(cases, self.pret)
        rows = {c['id']: c for c in cases}
        fast = rows['brock/recorded']
        healthy = rows['brock/full-hp']
        self.assertEqual((fast['player']['hp'], healthy['player']['hp']), (11, 33))
        expected = copy.deepcopy(fast)
        expected['id'], expected['preparation'] = healthy['id'], healthy['preparation']
        expected['player']['hp'] = 33
        self.assertEqual(expected, healthy)
        self.assertEqual(rows['brock/pre-potion']['player']['hp'], 31)
        self.assertNotIn('potion', rows['brock/pre-potion']['bag'])
        self.assertEqual(rows['brock/carry-potion']['bag']['potion'], 1)
        self.assertEqual(rows['brock/carry-potion']['player']['hp'], 11)
        rested = rows['ssanne-rival/full-rest']['player']
        self.assertEqual(rested['hp'], rested['stats']['hp'])
        self.assertTrue(all(m['pp'] == self.reference['move_pp'][m['name']] for m in rested['moves']))

    def test_dig_and_speed_alternatives_preserve_other_inputs(self):
        cases = preparation_cases(self.originals, self.reference)
        for case in cases:
            variant = case['preparation']['variant']
            if variant in ('dig', 'dig-speed'):
                names = {m['name'] for m in case['player']['moves']}
                self.assertTrue({'DIG', 'BITE', 'MEGA_KICK'} <= names)
                self.assertNotIn('WATER_GUN', names)
            if variant not in ('speed', 'dig-speed'):
                continue
            original = next(c for c in self.originals if c['id'] == case['preparation']['fight'])
            player, data = case['player'], case['progression']
            stats = summary_stats(self.reference['species'][player['species']]['base_stats'],
                                  player['level'], data['ivs'], data['evs'], data['nature'])
            self.assertEqual(player['stats'], stats)
            self.assertEqual(data['exp'], original['progression']['exp'])
            self.assertGreater(data['evs']['spe'], original['progression']['evs']['spe'])
            self.assertIn('diagnostic', case['preparation'])


if __name__ == '__main__':
    unittest.main()

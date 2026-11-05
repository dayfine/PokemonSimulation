"""Reject stale entry contracts and keep prepared rankings separate from diagnostics."""

import copy
import json
import unittest

from pokesim.cli.frlg_conditions import DATA, REPO, resolve_conditions, ranking
from pokesim.games.frlg.battle.run import trainer_cases
from pokesim.games.frlg.progression.ledger import fingerprint


class ConditionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = lambda name: json.loads((DATA / (name + '.json')).read_text())
        cls.pret, cls.reference, cls.plan = read('battle-reference'), read('reference'), read('battle-preparation')
        cls.inputs = trainer_cases(read('events'), cls.reference, read('moves'), read('state-history'), cls.pret)
        cls.baseline = json.loads((REPO / 'docs/battles/pokeguy-trainers.json').read_text())
        cls.prep = json.loads((REPO / 'docs/battles/pokeguy-preparation.json').read_text())

    def resolve(self, plan=None):
        return resolve_conditions(self.inputs, self.reference, self.pret,
                                  self.baseline, self.prep, plan or self.plan)

    def test_two_contracts_cover_every_fight_without_changing_other_preconditions(self):
        before = fingerprint(self.inputs)
        report = self.resolve()
        self.assertEqual(fingerprint(self.inputs), before)
        self.assertEqual(len(report['fights']), 69)
        self.assertEqual(report['family_size'], 112)
        self.assertEqual(sum(bool(r['requirement']) for r in report['fights']), 6)
        self.assertEqual(sum(r['strategy']['tier'] == 'C' for r in report['fights']), 12)
        for row in report['fights']:
            a, b = row['recorded'], row['prepared']
            if not row['requirement']:
                self.assertEqual(a, b)
                self.assertEqual(row['results']['recorded'], row['results']['prepared'])
                continue
            expected = copy.deepcopy(a)
            p = expected['player']
            p['hp'], p['status'] = p['stats']['hp'], ''
            for m in p['moves']:
                m['pp'] = self.reference['move_pp'][m['name']]
            self.assertEqual(expected, b)

    def test_unmeasured_healing_and_stale_measurements_cannot_enter_rankings(self):
        for change in ('unmeasured', 'stale-pp', 'stale-bag'):
            plan = copy.deepcopy(self.plan)
            if change == 'unmeasured':
                plan['requirements']['koga'] = copy.deepcopy(plan['requirements']['brock'])
            elif change == 'stale-pp':
                plan['supplemental_rest_results']['results'][0]['moves'][0]['pp'] -= 1
            else:
                plan['supplemental_rest_results']['input_sha256_by_fight']['brock'] = 'wrong'
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.resolve(plan)

    def test_prepared_ranking_keeps_real_speed_and_pending_setup_conditions(self):
        report = self.resolve()
        top = ranking(report['fights'], 'prepared')
        self.assertEqual(top[0]['id'], 'surge')
        self.assertEqual(top[0]['prepared']['player']['stats']['spe'], 47)
        self.assertAlmostEqual(top[0]['results']['prepared']['probability'], 1147 / 2040)
        self.assertNotIn('brock', [r['id'] for r in top])
        koga = next(r for r in report['fights'] if r['id'] == 'koga')
        self.assertEqual(koga['prepared']['player']['hp'], 34)
        self.assertTrue(koga['pending_full_hp_test'])
        self.assertEqual(koga['strategy']['tier'], 'C')


if __name__ == '__main__':
    unittest.main()

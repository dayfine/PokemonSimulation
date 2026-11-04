"""Check selective result reuse and the original/fresh confidence split."""

import copy
import json
import unittest

from pokesim.games.frlg.battle.comparison import compare_strategies
from pokesim.games.frlg.battle.engine import REPO
from pokesim.games.frlg.battle.sampling import AdaptiveSampling, confidence_sequence
from pokesim.games.frlg.battle.test_run import CASES
from pokesim.games.frlg.progression.ledger import fingerprint

BASELINE = json.loads((REPO / 'docs/battles/pokeguy-trainers.json').read_text())


def fresh_fixture():
    case = copy.deepcopy(next(c for c in CASES if c['id'] == 'bruno'))
    case.update(enable_complex_planning=True, planning_goals={'spa': 2})
    return {'seed': 4, 'policy': 'C:test', 'implementation_sha256': {},
        'pret_snapshot_sha256': BASELINE['pret_snapshot_sha256'],
        'run_inputs': BASELINE['run_inputs'], 'sampling': AdaptiveSampling(confidence=.975).describe(12),
        'results': [{'id': 'bruno', 'battles': 100, 'maximum_battles': 3000, 'wins': 95,
            'win_probability': .95, 'outcomes': {'win': 95, 'loss': 5}, 'mean_turns': 8,
            'mean_items_used': {'xspecial': 2}, 'losses_by_foe': {'onix': 5}, 'inputs': case,
            'confidence_sequence': {'bounds': confidence_sequence(95, 100, .025 / 12), 'stop_reason': 'budget_exhausted'},
            'examples': {'win': {'seed': {'master': 4, 'trial': 0, 'engine': [1, 2, 3, 4]}}}}]}


class StrategyComparisonTest(unittest.TestCase):
    def test_reuse_keeps_point_estimates_and_rebudgets_the_whole_original_family(self):
        before = fingerprint(BASELINE)
        result = compare_strategies(BASELINE, fresh_fixture())
        self.assertEqual(fingerprint(BASELINE), before)
        self.assertEqual(len(result['retained_case_ids']), 68)
        self.assertEqual(result['confidence']['original_family_size'], 69)
        self.assertAlmostEqual(result['confidence']['original_alpha_per_case'], .025 / 69)
        self.assertAlmostEqual(result['confidence']['updated_alpha_per_case'], .025 / 12)
        self.assertEqual(result['top_ten'][0]['id'], 'route22-rival')
        self.assertEqual(result['top_ten'][0]['win_probability'],
                         next(r for r in BASELINE['results'] if r['id'] == 'route22-rival')['win_probability'])
        self.assertEqual(result['changes'][0]['comparison'], 'improved')

    def test_refuses_reused_validation_seed_changed_inputs_and_excess_error_budget(self):
        for field, value in [('seed', 1), ('pret_snapshot_sha256', 'changed'),
                             ('sampling', AdaptiveSampling().describe(1)),
                             ('run_inputs', {'source_sha256': {}})]:
            data = fresh_fixture(); data[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                compare_strategies(BASELINE, data)

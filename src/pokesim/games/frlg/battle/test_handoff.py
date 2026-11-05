"""Verify portable entry previews include reserves and use the right variant."""

import json
import unittest

from pokesim.cli.frlg_conditions import DATA, REPO, resolve_conditions
from pokesim.games.frlg.battle.handoff import opening_contracts
from pokesim.games.frlg.battle.benchmark import scenario_for, trial
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.battle.run import trainer_cases
from pokesim.games.frlg.battle.test_battle import HAS_ENGINE


@unittest.skipUnless(HAS_ENGINE, 'Install pinned Node dependencies')
class HandoffTest(unittest.TestCase):
    def test_all_openings_use_exact_entry_variants_and_include_the_full_opponent_party(self):
        read = lambda name: json.loads((DATA / (name + '.json')).read_text())
        reference, pret, plan = read('reference'), read('battle-reference'), read('battle-preparation')
        inputs = trainer_cases(read('events'), reference, read('moves'), read('state-history'), pret)
        baseline = json.loads((REPO / 'docs/battles/pokeguy-trainers.json').read_text())
        preparation = json.loads((REPO / 'docs/battles/pokeguy-preparation.json').read_text())
        report = resolve_conditions(inputs, reference, pret, baseline, preparation, plan)
        previews = opening_contracts(report, pret)
        self.assertEqual(len(previews), 69)
        for row in report['fights']:
            for variant in ('recorded', 'prepared'):
                case, preview = row[variant], previews[row['id']][variant]
                with self.subTest(fight=row['id'], variant=variant):
                    self.assertEqual(preview['own']['hp'], case['player']['hp'])
                    self.assertEqual(preview['own']['level'], case['player']['level'])
                    self.assertEqual([m['pp'] for m in preview['own']['moves']],
                                     [m['pp'] for m in case['player']['moves']])
                    self.assertEqual(len(preview['opponents']), len(pret['trainers'][case['trainer']]['party']))
                    self.assertTrue(all(m['ability'] and m['max_hp'] == m['hp'] for m in preview['opponents']))
                    action = preview['action']
                    if action['kind'] == 'move':
                        self.assertGreater(case['player']['moves'][action['slot']]['pp'], 0)
                    else:
                        self.assertEqual(action['kind'], 'item')
                        self.assertGreater(case['bag'].get(action['item'], 0), 0)
        surge = previews['surge']['prepared']
        self.assertEqual(next(m for m in surge['opponents'] if m['species'] == 'raichu')['speed'], 53)
        self.assertEqual(previews['brock']['recorded']['own']['hp'], 11)
        self.assertEqual(previews['brock']['prepared']['own']['hp'], 33)
        # Check the separate preview path against the actual trial driver,
        # including NPC revealed-move knowledge and C opt-in/goals.
        with Engine() as engine:
            for fight in ('cerulean-rival', 'koga', 'bruno'):
                row = next(r for r in report['fights'] if r['id'] == fight)
                scenario = scenario_for(row['prepared'], pret)
                scenario['enable_complex_planning'] = row['strategy']['tier'] == 'C'
                scenario['planning_goals'] = row['strategy'].get('planning_goals', {})
                played = trial(engine, scenario, NPCTrainerAI(pret), 4, 0, 300)
                self.assertEqual(previews[fight]['prepared']['action'], played['decisions'][0]['own'])


if __name__ == '__main__':
    unittest.main()

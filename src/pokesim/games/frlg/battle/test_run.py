"""Cross-check live battle progression against the independent Python ledger."""

import copy
import json
import os
from pathlib import Path
import unittest

from pokesim.games.frlg.battle.benchmark import scenario_for, trial
from pokesim.games.frlg.battle.engine import Engine, REPO
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI, move_id
from pokesim.games.frlg.battle.pret import import_checkout
from pokesim.games.frlg.battle.run import trainer_cases
from pokesim.games.frlg.battle.schema import validate_cases
from pokesim.games.frlg.battle.policy import player_action
from pokesim.games.frlg.battle.test_battle import HAS_ENGINE
from pokesim.games.frlg.progression.experience import defeat_exp, level_at
from pokesim.games.frlg.progression.stats import gain_evs, summary_stats

DATA = REPO / 'data/runs/pokeguy-leafgreen-15934'
read = lambda name: json.loads((DATA / (name + '.json')).read_text())
REFERENCE, PRET = read('reference'), read('battle-reference')
INPUTS = trainer_cases(read('events'), REFERENCE, read('moves'), read('state-history'), PRET)
CASES = INPUTS['cases']


class RunInputsTest(unittest.TestCase):
    def test_invalid_live_progression_is_rejected_before_trials(self):
        for key, value in (('exp', 0), ('evs', {s: 100 for s in ('hp', 'atk', 'def', 'spe', 'spa', 'spd')}),
                           ('ivs', {s: 32 for s in ('hp', 'atk', 'def', 'spe', 'spa', 'spd')}),
                           ('badges', ['earth']), ('species', {})):
            case = copy.deepcopy(CASES[0])
            case['progression'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_cases([case], PRET)

    def test_all_trainers_have_reconciled_inputs_and_matching_parties(self):
        self.assertEqual(len(CASES), 69)
        self.assertEqual(INPUTS['checks_passed'], 38)
        validate_cases(CASES, PRET)
        for case in CASES:
            expected = REFERENCE['trainers'][case['trainer']]['party']
            imported = PRET['trainers'][case['trainer']]['party']
            self.assertEqual([(m['species'], m['level']) for m in expected],
                             [(m['species'], m['level']) for m in imported])
        self.assertTrue(CASES[0]['tutorial'])
        self.assertFalse(any(c['tutorial'] for c in CASES[1:]))
        champion = CASES[-1]
        self.assertEqual(champion['player']['hp'], 171)
        self.assertEqual(champion['bag']['fullrestore'], 9)
        self.assertEqual(champion['player']['held_item'], 'BLACK_GLASSES')
        self.assertNotIn('pokeball', champion['bag'])
        self.assertTrue(any(m.get('held_item') for t in PRET['trainers'].values() for m in t['party']))

    @unittest.skipUnless(os.environ.get('POKEFIRERED_DIR'), 'Set POKEFIRERED_DIR for source reproducibility')
    def test_complete_battle_import_is_reproducible(self):
        actual = import_checkout(Path(os.environ['POKEFIRERED_DIR']), REFERENCE['trainers'], REFERENCE['move_pp'])
        self.assertEqual(actual, PRET)


@unittest.skipUnless(HAS_ENGINE, 'Install pinned Node dependencies')
class LiveProgressionTest(unittest.TestCase):
    def test_level_up_learns_a_move_before_replacement_and_preserves_hp_delta_and_stages(self):
        case = copy.deepcopy(CASES[0])
        data = case['progression']
        data['exp'] = data['thresholds'][7] - 1
        case['player']['level'] = 6
        case['player']['stats'] = summary_stats(REFERENCE['species']['SQUIRTLE']['base_stats'],
            6, data['ivs'], data['evs'], data['nature'])
        case['player']['hp'] = case['player']['stats']['hp'] - 5
        case['player']['boosts'] = {'accuracy': 1}
        case['badges'] = data['badges'] = ['boulder']
        scenario = scenario_for(case, PRET)
        scenario['trainer']['party'] = [{'species': s, 'level': 1, 'hp': 1, 'moves': ['Splash']}
                                        for s in ('RATTATA', 'PIDGEY')]
        with Engine() as engine:
            engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
            state = engine.request(command='step', own={'kind': 'move', 'slot': 0}, foe={'kind': 'move', 'slot': 0})
            self.assertTrue(state['needs_switch'])
            self.assertEqual(state['own']['level'], 7)
            self.assertEqual(state['own']['hp'], state['own']['max_hp'] - 5)
            self.assertEqual(state['own']['boosts']['accuracy'], 1)
            self.assertEqual(state['own']['moves'][-1]['id'], 'bubble')
            self.assertEqual(state['own']['moves'][-1]['pp'], REFERENCE['move_pp']['BUBBLE'])
            raw = state['progression']['awards'][0]['raw_stats']
            self.assertEqual(state['own']['stats']['atk'], raw['atk'] * 110 // 100)
            state = engine.request(command='step', own={'kind': 'pass'}, foe={'kind': 'switch', 'slot': 1})
            state = engine.request(command='step', own={'kind': 'move', 'slot': 2}, foe={'kind': 'move', 'slot': 0})
            self.assertEqual(state['winner'], 'Player')
            self.assertEqual(state['own']['moves'][-1]['pp'], REFERENCE['move_pp']['BUBBLE'] - 1)

    def test_safe_finishing_attack_precedes_unnecessary_healing(self):
        case = copy.deepcopy(next(c for c in CASES if c['id'] == 'misty'))
        case['player']['hp'] = 3
        case['player']['stats']['spe'] = 999
        scenario = scenario_for(case, PRET)
        scenario['trainer']['party'] = scenario['trainer']['party'][:1]
        scenario['trainer']['party'][0]['hp'] = 1
        scenario['trainer']['items'] = []
        scenario['trainer']['bag'] = {}
        with Engine() as engine:
            state = engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
            action = player_action(state, NPCTrainerAI(PRET), [], [])
            self.assertEqual(action['kind'], 'move')

    def test_every_route_matchup_executes_and_live_awards_match_python(self):
        ai = NPCTrainerAI(PRET)
        with Engine() as engine:
            for case in CASES:
                with self.subTest(event=case['id']):
                    played = trial(engine, scenario_for(case, PRET), ai, 1, 0, 300)
                    exp = case['progression']['exp']
                    evs = copy.deepcopy(case['progression']['evs'])
                    level = case['player']['level']
                    for award in played['progression']['awards']:
                        foe = PRET['trainers'][case['trainer']]['party'][award['party_index']]
                        source = REFERENCE['species'][foe['species']]
                        gained = defeat_exp(source['exp_yield'], foe['level'], trainer=True)
                        exp += gained
                        evs = gain_evs(evs, source['ev_yield'], REFERENCE['ev_limits'])
                        next_level = level_at(exp, case['progression']['thresholds'])
                        self.assertEqual(award['exp'], gained)
                        self.assertEqual(award['total_exp'], exp)
                        self.assertEqual(award['evs'], evs)
                        self.assertEqual(award['level_before'], level)
                        self.assertEqual(award['level_after'], next_level)
                        if next_level > level:
                            expected = summary_stats(REFERENCE['species'][case['player']['species']]['base_stats'],
                                next_level, case['player']['ivs'], evs, case['progression']['nature'])
                            self.assertEqual(award['raw_stats'], expected)
                        level = next_level
                    if played['outcome'] == 'win':
                        self.assertEqual(len(played['progression']['awards']), len(PRET['trainers'][case['trainer']]['party']))

"""Verify opt-in layering, setup commitments and unchanged A/B replay traces."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from pokesim.games.frlg.battle.benchmark import scenario_for, trial
from pokesim.games.frlg.battle.engine import Engine, REPO
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.battle.policy import player_action
from pokesim.games.frlg.battle.player_strategy import attacks, planning
from pokesim.games.frlg.battle.run import configure_strategies
from pokesim.games.frlg.battle.schema import validate_cases
from pokesim.games.frlg.battle.test_battle import HAS_ENGINE
from pokesim.games.frlg.battle.test_run import CASES, PRET
from pokesim.games.frlg.progression.ledger import fingerprint

DATA = REPO / 'data/runs/pokeguy-leafgreen-15934'
CONFIG = json.loads((DATA / 'strategies.json').read_text())
CONFIGURED = configure_strategies(CASES, CONFIG)


class StrategyConfigurationTest(unittest.TestCase):
    def test_exactly_twelve_opt_in_and_default_is_recovery(self):
        validate_cases(CONFIGURED, PRET)
        self.assertEqual(sum(c['enable_complex_planning'] for c in CONFIGURED), 12)
        self.assertEqual(sum(not c['enable_complex_planning'] for c in CONFIGURED), 57)
        self.assertTrue(all('enable_complex_planning' not in c for c in CASES))
        altered = copy.deepcopy(CONFIG)
        altered['fights']['typo'] = {'enable_complex_planning': True}
        with self.assertRaises(ValueError):
            configure_strategies(CASES, altered)

    def test_planning_requires_explicit_boolean_and_valid_goals(self):
        for update in ({'enable_complex_planning': 1},
                       {'planning_goals': {'spa': 2}},
                       {'enable_complex_planning': True, 'planning_goals': {'spa': 7}},
                       {'enable_complex_planning': True, 'planning_goals': {'target_torrent': 1}}):
            case = copy.deepcopy(CASES[0]); case.update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate_cases([case], PRET)


@unittest.skipUnless(HAS_ENGINE, 'Install pinned battle engine')
class StrategyLayersTest(unittest.TestCase):
    def setUp(self):
        self.ai = NPCTrainerAI(PRET)
        self.context = Engine()
        self.engine = self.context.__enter__()
        self.addCleanup(self.context.__exit__, None, None, None)

    def scenario(self, name):
        return scenario_for(next(c for c in CONFIGURED if c['id'] == name), PRET)

    def start(self, scenario, seed=None):
        return self.engine.request(command='start', scenario=scenario, seed=seed or [1, 2, 3, 4])

    def choose_c(self, state, scenario):
        return player_action(state, self.ai, scenario['trainer']['ai'], scenario['trainer']['items'],
            enable_complex_planning=True, planning_goals=scenario['planning_goals'])

    def test_b_is_default_even_with_exp_and_x_items(self):
        state = self.start(self.scenario('bruno'))
        with patch('pokesim.games.frlg.battle.player_strategy.planning.choose_action', side_effect=AssertionError('C called')):
            self.assertEqual(player_action(state, self.ai, [], [])['kind'], 'move')

    def test_b_adds_healing_to_a_without_adding_setup(self):
        scenario = self.scenario('bruno')
        scenario['player']['hp'] = 50
        scenario['trainer']['party'] = scenario['trainer']['party'][-1:]
        state = self.start(scenario)
        self.assertEqual(attacks.choose_action(state)['kind'], 'move')
        self.assertEqual(player_action(state, self.ai, scenario['trainer']['ai'], []),
                         {'kind': 'item', 'item': 'fullrestore'})

    def test_bruno_setup_is_committed_and_torrent_is_not_healed_away(self):
        scenario = self.scenario('bruno')
        state = self.start(scenario, [5, 6, 7, 8])
        # Force the observed NPC move sequence; these are real engine turns.
        for item, slot in [('xspecial', 1), ('xspecial', 0), ('xspeed', 0)]:
            action = self.choose_c(state, scenario)
            self.assertEqual(action, {'kind': 'item', 'item': item})
            state = self.engine.request(command='step', own=action, foe={'kind': 'move', 'slot': slot})
        self.assertTrue(planning.torrent_active(state['own']))
        self.assertEqual(self.choose_c(state, scenario), {'kind': 'move', 'slot': 1})
        state = self.engine.request(command='step', own={'kind': 'move', 'slot': 1}, foe={'kind': 'move', 'slot': 0})
        state = self.engine.request(command='step', own={'kind': 'pass'}, foe={'kind': 'switch', 'slot': 4})
        self.assertGreaterEqual(min(state['own']['moves'][1]['damage']), state['foe']['hp'])
        self.assertEqual(self.choose_c(state, scenario), {'kind': 'move', 'slot': 1})

    def test_setup_guard_precedes_boosts_against_smokescreen(self):
        scenario = self.scenario('koga')
        state = self.start(scenario)
        self.assertEqual(self.choose_c(state, scenario), {'kind': 'item', 'item': 'guardspec'})

    def test_torrent_activation_does_not_restart_on_later_opponents(self):
        scenario = self.scenario('bruno')
        scenario['player']['boosts'] = {'spa': 4}
        state = self.start(scenario)
        self.assertFalse(planning.needs_torrent_setup(state, scenario['planning_goals']))
        state['own']['boosts']['spa'] = 2
        state['foe']['party_index'] = 1
        self.assertFalse(planning.needs_torrent_setup(state, scenario['planning_goals']))

    def test_all_57_unmodified_fights_preserve_published_example_traces(self):
        frozen = json.loads((DATA / 'recovery-baseline-replays.json').read_text())
        self.assertEqual(frozen['baseline_summary_sha256'], __import__('hashlib').sha256(
            (REPO / 'docs/battles/pokeguy-trainers.json').read_bytes()).hexdigest())
        by_id = {c['id']: c for c in CONFIGURED}
        checked = set()
        for entry in frozen['checks']:
            with self.subTest(case=entry['case'], outcome=entry['outcome']):
                case = by_id[entry['case']]
                self.assertFalse(case['enable_complex_planning'])
                played = trial(self.engine, scenario_for(case, PRET), self.ai,
                    entry['master_seed'], entry['trial'], 300)
                self.assertEqual(fingerprint(played), entry['trace_sha256'])
                checked.add(case['id'])
        self.assertEqual(len(checked), 57)

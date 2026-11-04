"""FRLG source, policy, and real-engine benchmark regression checks."""

import copy
import json
import os
from pathlib import Path
import random
import shutil
import unittest

from pokesim.battle.npc_ai import NPCTrainerAI
from pokesim.battle.benchmark import evaluate, scenario_for, wilson
from pokesim.battle.engine import BRIDGE, Engine
from pokesim.battle.policy import player_action, trainer_item, replacement
from pokesim.battle.pret import compile_scripts, import_checkout
from pokesim.battle.schema import validate_cases
from pokesim.cli.battle import DATA

PRET = json.loads((DATA / "pret.json").read_text())
CASES = json.loads((DATA / "cases.json").read_text())["cases"]
HAS_ENGINE = bool(shutil.which("node") and (BRIDGE / "node_modules" / "pokemon-showdown").is_dir())
if os.environ.get("POKESIM_REQUIRE_BATTLE") and not HAS_ENGINE:
    raise RuntimeError("Battle integration tests required: install the pinned Node dependencies")


class BattleDataTest(unittest.TestCase):
    """Keep the imported parties and experimental inputs explicit and reproducible."""

    def test_source_party_fields(self):
        misty = PRET["trainers"]["TRAINER_LEADER_MISTY"]
        self.assertEqual([m["level"] for m in misty["party"]], [18, 21])
        self.assertEqual(misty["items"], ["SUPER_POTION"])
        self.assertEqual(misty["party"][1]["nature"], "Naughty")
        rival = PRET["trainers"]["TRAINER_RIVAL_SS_ANNE_BULBASAUR"]
        self.assertEqual(rival["party"][-1]["moves"], ["LEECH_SEED", "VINE_WHIP", "POISON_POWDER", "SLEEP_POWDER"])
        self.assertEqual(rival["party"][-1]["pret_iv"], 100)
        self.assertEqual(rival["party"][-1]["iv"], 12)
        self.assertEqual(rival["party"][-1]["nature"], "Serious")

    def test_cases_validate_and_record_assumptions(self):
        validate_cases(CASES, PRET)
        self.assertEqual(len(CASES), 4)
        for case in CASES:
            self.assertTrue(case["input_notes"])
            self.assertRegex(case["source"], r"/blob/[a-f0-9]{40}/")
        self.assertEqual(CASES[-1]["player"]["stats"], {"hp": 83, "atk": 44, "def": 59, "spa": 51, "spd": 64, "spe": 49})

    def test_invalid_experiments_fail_before_launch(self):
        for update in ({"level": 0}, {"stats": {"hp": 60}}, {"moves": ["SURF"]}, {"hp": 10000}):
            cases = copy.deepcopy(CASES[:1])
            cases[0]["player"].update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate_cases(cases, PRET)
        with self.assertRaises(ValueError):
            evaluate(CASES, PRET, battles=0)

    def test_initial_stat_stages_validate_all_seven_without_changing_summary_stats(self):
        cases = copy.deepcopy(CASES[:1])
        original = copy.deepcopy(cases[0]["player"]["stats"])
        cases[0]["player"]["boosts"] = {"atk": -6, "def": 6, "spa": -2,
            "spd": 2, "spe": 1, "accuracy": -1, "evasion": 3}
        validate_cases(cases, PRET)
        self.assertEqual(cases[0]["player"]["stats"], original)
        for boosts in ({"hp": 1}, {"attack": 1}, {"atk": 7}, {"def": -7},
                       {"spe": 1.5}, {"accuracy": True}, []):
            cases[0]["player"]["boosts"] = boosts
            with self.subTest(boosts=boosts), self.assertRaises(ValueError):
                validate_cases(cases, PRET)

    def test_badges_and_bag_are_not_silently_duplicated(self):
        cases = copy.deepcopy(CASES[:1])
        cases[0]["badges"] = ["boulder", "boulder"]
        with self.assertRaises(ValueError):
            validate_cases(cases, PRET)
        cases[0]["badges"] = []
        cases[0]["bag"] = {"potion": -1}
        with self.assertRaises(ValueError):
            validate_cases(cases, PRET)

    def test_wilson_endpoints_are_not_false_certainty(self):
        self.assertGreater(wilson(0, 100)[1], 0)
        self.assertLess(wilson(100, 100)[0], 1)
        self.assertAlmostEqual(wilson(50, 100)[0], 0.40383, places=4)
        self.assertAlmostEqual(wilson(50, 100)[1], 0.59617, places=4)

    def test_source_compiler_prunes_unreachable_effects(self):
        text = """
AI_CheckBadMove::
 if_effect EFFECT_SLEEP, Sleep
 if_effect EFFECT_EXPLOSION, Unsupported
 end
AI_CheckViability::
 end
AI_TryToFaint::
 end
Sleep::
 score -10
 end
Unsupported::
 unsupported_opcode
 end
"""
        script = compile_scripts(text, {"EFFECT_SLEEP"})
        self.assertNotIn("Unsupported", script["labels"])
        self.assertNotIn(["unsupported_opcode"], script["instructions"])
        self.assertIn(["score", "-10"], script["instructions"])

    @unittest.skipUnless(os.environ.get("POKEFIRERED_DIR"), "Set POKEFIRERED_DIR to check the pinned source snapshot")
    def test_reimport_real_pret_snapshot(self):
        self.assertEqual(import_checkout(Path(os.environ["POKEFIRERED_DIR"]).expanduser()), PRET)


@unittest.skipUnless(HAS_ENGINE, "Install engines/showdown dependencies for battle integration checks")
class BattleIntegrationTest(unittest.TestCase):
    """Exercise policies against actual Showdown state, including replacements."""

    def setUp(self):
        self.ai = NPCTrainerAI(PRET)
        self.context = Engine()
        self.engine = self.context.__enter__()
        self.addCleanup(self.context.__exit__, None, None, None)

    def start(self, case):
        return self.engine.request(command="start", scenario=scenario_for(case, PRET), seed=[1, 2, 3, 4])

    def test_same_trial_seeds_reproduce_whole_report(self):
        first = evaluate(CASES, PRET, battles=2, seed=42)
        second = evaluate(CASES, PRET, battles=2, seed=42)
        self.assertEqual(first, second)
        for result in first["results"]:
            self.assertEqual(sum(result["outcomes"].values()), 2)
            self.assertTrue(result["examples"])
            for sample in result["examples"].values():
                self.assertTrue(sample["decisions"])
                self.assertFalse(any(line.startswith("|t:|") for line in sample["log"]))

    def test_raichu_uses_double_team_at_full_hp_but_not_at_max_evasion(self):
        case = copy.deepcopy(CASES[-1])
        scenario = scenario_for(case, PRET)
        scenario["trainer"]["party"] = scenario["trainer"]["party"][-1:]
        state = self.engine.request(command="start", scenario=scenario, seed=[1, 2, 3, 4])
        flags = scenario["trainer"]["ai"]
        rng = random.Random(7)
        choices = [self.ai.choose_move(state, flags, rng)["slot"] for _ in range(1000)]
        self.assertGreater(choices.count(2), 650)
        state["foe"]["boosts"]["evasion"] = 6
        choices = [self.ai.choose_move(state, flags, rng)["slot"] for _ in range(1000)]
        self.assertEqual(choices.count(2), 0)

    def test_trainer_healing_thresholds_and_one_use(self):
        state = self.start(CASES[0])
        state["foe"]["hp"] = 1
        self.assertEqual(trainer_item(state, ["superpotion"]), {"kind": "item", "item": "superpotion"})
        state["trainer_bag"]["superpotion"] = 0
        self.assertIsNone(trainer_item(state, ["superpotion"]))

    def test_low_hp_potion_cannot_outheal_seeded_vine_whip(self):
        state = self.start(CASES[1])
        # Isolate the console's failure: no Awakening and each enemy turn
        # costs more than the Potion's 20 HP while asleep and seeded.
        scenario = scenario_for(CASES[1], PRET)
        scenario["trainer"]["party"] = scenario["trainer"]["party"][-1:]
        state = self.engine.request(command="start", scenario=scenario, seed=[1, 2, 3, 4])
        state["own"].update(hp=13, status="slp", volatiles=["leechseed"])
        state["bag"] = {"potion": 15}
        for move in state["foe"]["moves"]:
            move["damage"] = [20]
            move["critical"] = [40]
        self.assertEqual(player_action(state, self.ai, scenario["trainer"]["ai"], [] )["kind"], "move")

    def test_full_heal_is_gated_by_remaining_party(self):
        state = self.start(CASES[-1])
        state["foe"]["status"] = "par"
        items = ["superpotion", "fullheal"]
        self.assertIsNone(trainer_item(state, items))
        state["party"][1]["hp"] = 0
        self.assertEqual(trainer_item(state, items), {"kind": "item", "item": "fullheal"})

    def test_compulsory_replacement_does_not_cost_a_player_attack(self):
        case = copy.deepcopy(CASES[1])
        case["player"]["level"] = 100
        case["player"]["stats"] = {"hp": 500, "atk": 500, "def": 500, "spa": 500, "spd": 500, "spe": 500}
        state = self.start(case)
        state = self.engine.request(command="step", own={"kind": "move", "slot": 0}, foe={"kind": "move", "slot": 0})
        self.assertTrue(state["needs_switch"])
        action = replacement(state)
        # Against a solo Water lead, the type-first pass finds Bulbasaur.
        self.assertEqual(state["party"][action["slot"]]["species"], "bulbasaur")
        pp = state["own"]["moves"][0]["pp"]
        turn = state["turn"]
        state = self.engine.request(command="step", own={"kind": "pass"}, foe=action)
        self.assertEqual(state["own"]["moves"][0]["pp"], pp)
        self.assertEqual(state["turn"], turn + 1)
        self.assertEqual(state["foe"]["species"], "bulbasaur")


if __name__ == "__main__":
    unittest.main()

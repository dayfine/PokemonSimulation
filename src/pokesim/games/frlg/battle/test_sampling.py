"""Sequential coverage, stopping boundaries, and real benchmark integration."""

from collections import defaultdict
import copy
import math
import unittest
from unittest.mock import patch
import json
from pathlib import Path

from pokesim.games.frlg.battle import benchmark
from pokesim.games.frlg.battle.benchmark import evaluate
from pokesim.games.frlg.battle.sampling import AdaptiveSampling, confidence_sequence
from pokesim.games.frlg.battle.test_battle import CASES, PRET, HAS_ENGINE


class ConfidenceSequenceTest(unittest.TestCase):
    """Check the mixture inversion without relying on a fixed-sample interval."""

    def test_empty_counts_closed_form_edges_and_symmetry(self):
        self.assertEqual(confidence_sequence(0, 0), [0, 1])
        self.assertAlmostEqual(confidence_sequence(1, 1)[0], 0.025)
        self.assertAlmostEqual(confidence_sequence(2, 2)[0], math.sqrt(0.375 * 0.05))
        left, right = confidence_sequence(3, 10)
        mirrored = confidence_sequence(7, 10)
        self.assertAlmostEqual(left, 1 - mirrored[1])
        self.assertAlmostEqual(right, 1 - mirrored[0])
        self.assertEqual(confidence_sequence(10, 10)[1], 1)
        self.assertEqual(confidence_sequence(0, 10)[0], 0)

    def test_exact_probability_of_any_exclusion_through_30_looks(self):
        # Sum probabilities of every Bernoulli path, absorbing a path at its
        # FIRST exclusion. This checks repeated looks, not only terminal coverage.
        for probability in (0.05, 0.25, 0.5, 0.75, 0.95):
            live, excluded = {0: 1.0}, 0.0
            for trials in range(1, 31):
                following = defaultdict(float)
                for wins, mass in live.items():
                    for increment, chance in ((0, 1 - probability), (1, probability)):
                        successes = wins + increment
                        bounds = confidence_sequence(successes, trials)
                        weight = mass * chance
                        if bounds[0] <= probability <= bounds[1]:
                            following[successes] += weight
                        else:
                            excluded += weight
                live = following
            self.assertLessEqual(excluded, 0.05 + 1e-12)
            self.assertAlmostEqual(excluded + sum(live.values()), 1.0)

    def test_stops_easy_69_case_family_at_100_and_does_not_claim_certainty(self):
        plan = AdaptiveSampling()
        stopped = None
        for trials in range(1, 2001):
            checked = plan.check(trials, trials, 2000, 69)
            if checked and checked["stop_reason"]:
                stopped = (trials, checked)
                break
        self.assertEqual(stopped[0], 100)
        self.assertGreater(stopped[1]["bounds"][0], 0.90)
        self.assertLess(stopped[1]["bounds"][0], 0.95)
        self.assertEqual(stopped[1]["stop_reason"], "interval_width")
        self.assertIsNone(plan.check(19, 19, 2000, 69))

    def test_budget_is_reported_without_claiming_precision(self):
        plan = AdaptiveSampling(width=0.01)
        checked = plan.check(10, 20, 20, 1)
        self.assertFalse(checked["precision_reached"])
        self.assertEqual(checked["stop_reason"], "budget_exhausted")
        # A failure after a streak changes the estimate and interval.
        self.assertGreater(confidence_sequence(20, 21)[1] - confidence_sequence(20, 21)[0], 0.1)

    def test_invalid_counts_and_sampling_plans(self):
        for args in ((2, 1), (-1, 20), (True, 10), (1, 0), (1, 2, 0)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                confidence_sequence(*args)
        for kwargs in ({"width": 0}, {"confidence": 1}, {"minimum": 0}, {"batch": 1.5}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                AdaptiveSampling(**kwargs)


class RunInputAuditTest(unittest.TestCase):
    """Keep source checkpoints explicitly partial until inventory is reconciled."""

    def test_purchases_are_sourced_and_partial_bags_do_not_imply_zero(self):
        root = Path(__file__).resolve().parents[5]
        data = root / "data/runs/pokeguy-leafgreen-15934"
        book = json.loads((data / "inventory-audit.json").read_text())
        route = json.loads((data / "events.json").read_text())
        ids = {event["id"] for event in route["events"]}
        self.assertEqual(len(book["purchases"]), 5)
        self.assertEqual(book["purchases"][1]["items"]["SUPER_POTION"], 5)
        self.assertIsNone(book["purchases"][-1]["items"]["FULL_RESTORE"])
        for purchase in book["purchases"]:
            self.assertTrue(purchase["evidence"])
            self.assertLessEqual(purchase["video_start"], purchase["video_end"])
        for check in book["partial_battle_checkpoints"]:
            self.assertIn(check["event"], ids)
            self.assertFalse(check["complete_scenario"])
            self.assertTrue(check["evidence"])
            self.assertLessEqual(check["hp"], check["max_hp"])
        self.assertTrue(all(issue["evidence"] for issue in book["unresolved"]))


@unittest.skipUnless(HAS_ENGINE, "Install the FRLG Showdown dependencies")
class AdaptiveBenchmarkTest(unittest.TestCase):
    """Exercise actual engine trials and protect normalization after stopping."""

    def test_real_easy_battle_stops_early_and_preserves_per_trial_means(self):
        case = copy.deepcopy(CASES[0])
        case["player"].update(level=100, moves=["BITE"],
            stats={"hp": 500, "atk": 500, "def": 500, "spa": 500, "spd": 500, "spe": 500})
        plan = AdaptiveSampling(width=0.5, minimum=10, batch=10)
        with patch.object(benchmark, "trial", wraps=benchmark.trial) as played:
            report = evaluate([case], PRET, battles=200, seed=42, sampling=plan)
        result = report["results"][0]
        self.assertEqual(result["wins"], result["battles"])
        self.assertLess(result["battles"], 200)
        self.assertEqual(result["confidence_sequence"]["stop_reason"], "interval_width")
        samples = played.call_args_list
        self.assertEqual(len(samples), result["battles"])
        self.assertGreater(result["mean_hp_remaining"], 400)
        self.assertNotIn("wilson_95", result)
        again = evaluate([case], PRET, battles=200, seed=42, sampling=plan)
        self.assertEqual(report, again)

    def test_maximum_budget_and_family_allocation(self):
        report = evaluate(CASES[:2], PRET, battles=2, sampling=AdaptiveSampling(width=0.01, minimum=1, batch=1))
        self.assertAlmostEqual(report["sampling"]["alpha_per_case"], 0.025)
        for result in report["results"]:
            self.assertEqual(result["battles"], 2)
            self.assertEqual(result["confidence_sequence"]["stop_reason"], "budget_exhausted")
        with self.assertRaisesRegex(ValueError, "Minimum trials"):
            evaluate(CASES[:1], PRET, battles=2, sampling=AdaptiveSampling())


if __name__ == "__main__":
    unittest.main()

"""Source-backed EXP arithmetic and full-run audit checks, without a battle engine."""

import contextlib
import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from pokesim.cli.frlg_progression import DATA, main
from pokesim.games.frlg.progression.experience import defeat_exp, level_at, medium_slow_thresholds, rare_candy
from pokesim.games.frlg.progression.ledger import audit, compare, markdown_report
from pokesim.games.frlg.progression.pret import import_reference

ROUTE = json.loads((DATA / "events.json").read_text())
REFERENCE = json.loads((DATA / "reference.json").read_text())


class ExperienceTest(unittest.TestCase):
    """Check integer boundaries against explicit early-run examples."""

    def test_award_rounding_and_modifier_order(self):
        self.assertEqual(defeat_exp(64, 5, trainer=True), 67)
        self.assertEqual(defeat_exp(57, 3), 24)  # Rattata
        self.assertEqual(defeat_exp(55, 2), 15)  # Pidgey
        self.assertEqual(defeat_exp(86, 10, trainer=True), 183)  # Liam's Geodude
        self.assertEqual(defeat_exp(64, 5, participants=2, trainer=True), 33)
        self.assertEqual(defeat_exp(64, 5, lucky_egg=True, trainer=True, traded=True), 150)
        self.assertEqual(defeat_exp(1, 1, participants=6), 1)
        for args in ((0, 5), (256, 5), (64, 0), (64, 101), (64.0, 5)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                defeat_exp(*args)

    def test_medium_slow_boundaries_and_multiple_level_award(self):
        curve = medium_slow_thresholds()
        self.assertEqual([curve[n] for n in (1, 5, 11, 100)], [1, 135, 742, 1059860])
        self.assertEqual(level_at(741, curve), 10)
        self.assertEqual(level_at(742, curve), 11)
        # Observed EXP after wild wins, Sammy, and Liam's Geodude.
        self.assertEqual(level_at(135 + 67 + 24 + 15 + 99 + 183, curve), 9)
        self.assertEqual(level_at(135 + 67 + 24 + 15 + 99 + 183 + 219, curve), 11)
        self.assertEqual(level_at(9999999, curve), 100)

    def test_candy_discards_progress_and_synchronizes_routes(self):
        curve = medium_slow_thresholds()
        self.assertEqual(rare_candy(curve[18] + 1, curve), curve[19])
        self.assertEqual(rare_candy(curve[19] - 1, curve), curve[19])
        self.assertEqual(rare_candy(curve[100], curve), curve[100])


class RouteAuditTest(unittest.TestCase):
    """Preserve independent observations and explain the flee-all counterfactual."""

    def test_full_route_matches_notes_with_documented_wild_wins(self):
        run = audit(ROUTE, REFERENCE, "observed_wild_wins")
        self.assertEqual((run["trainer_battles"], run["trainer_foes"], run["rare_candies"]), (69, 199, 7))
        self.assertEqual((run["matching_levels"], run["level_checks"], run["exp_checks"]), (126, 126, 33))
        self.assertEqual(run["level_checks_by_basis"]["explicit_level_in_notes"], {"checks": 69, "matches": 69})
        self.assertEqual((run["level_mismatches"], run["exp_mismatches"]), ([], []))
        self.assertEqual((run["final_level"], run["final_exp"]), (57, 181418))

    def test_flee_route_diverges_early_then_candy_restores_same_exp(self):
        flee, control = compare(ROUTE, REFERENCE)["runs"]
        self.assertEqual((flee["matching_levels"], flee["level_checks"]), (112, 126))
        left = {e["event"]: e for e in flee["timeline"]}
        right = {e["event"]: e for e in control["timeline"]}
        self.assertEqual((left["brock"]["exp_after"], left["brock"]["level_after"]), (1247, 12))
        self.assertEqual((right["brock"]["exp_after"], right["brock"]["level_after"]), (1286, 13))
        self.assertEqual(left["cerulean-candy1"]["exp_after"], right["cerulean-candy1"]["exp_after"])
        self.assertTrue(all(a["exp_after"] == b["exp_after"] for a, b in
            zip(flee["timeline"], control["timeline"]) if a["video_start"] >= 1381))
        self.assertEqual(left["route1-rattata-capture"]["exp_gained"], 0)
        marowak = next(e for e in flee["timeline"] if e["kind"] == "scripted_battle" and e["defeats"])
        self.assertEqual(marowak["exp_gained"], 531)

    def test_observations_do_not_drive_predictions(self):
        changed = copy.deepcopy(ROUTE)
        for event in changed["events"]:
            for reading in event.get("observations", []):
                reading["level"] = 100
        actual = audit(changed, REFERENCE)
        baseline = audit(ROUTE, REFERENCE)
        self.assertEqual([e["exp_after"] for e in actual["timeline"]],
                         [e["exp_after"] for e in baseline["timeline"]])
        self.assertEqual(actual["matching_levels"], 0)

    def test_complete_parties_required_but_defeat_order_can_differ(self):
        changed = copy.deepcopy(ROUTE)
        changed["events"][0]["observed_party"].append({"species": "BULBASAUR", "level": 5})
        with self.assertRaisesRegex(ValueError, "Trainer party differs"):
            audit(changed, REFERENCE)
        run = audit(ROUTE, REFERENCE, "observed_wild_wins")
        grunt = next(e for e in run["timeline"] if e["event"] == "silph-boardroom-grunt")
        self.assertEqual([m["calculated_exp"] for m in grunt["defeats"]], [595, 849, 699])
        self.assertEqual([m["level_after"] for m in grunt["defeats"]], [45, 46, 46])

    def test_generated_report_and_cli(self):
        report = compare(ROUTE, REFERENCE)
        saved = DATA.parents[2] / "docs" / "progression" / "pokeguy-exp.md"
        self.assertEqual(saved.read_text(), markdown_report(report))
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["--out", directory]), 0)
            output = Path(directory)
            self.assertEqual(json.loads((output / "report.json").read_text()), report)
            self.assertEqual((output / "report.md").read_text(), markdown_report(report))

    @unittest.skipUnless(os.environ.get("POKEFIRERED_DIR"), "Set POKEFIRERED_DIR for source integration")
    def test_snapshot_reproduces_from_pinned_pret(self):
        actual = import_reference(Path(os.environ["POKEFIRERED_DIR"]), ROUTE)
        self.assertEqual(actual, REFERENCE)
        self.assertIn("BULBASAUR", actual["species"])


if __name__ == "__main__":
    unittest.main()

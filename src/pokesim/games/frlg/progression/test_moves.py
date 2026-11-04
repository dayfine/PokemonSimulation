"""Move reconstruction checks against pret level-up offers and video menus."""

import copy
import json
import unittest

from pokesim.cli.frlg_progression import DATA
from pokesim.games.frlg.progression.moves import reconstruct_moves, moves_markdown

ROUTE = json.loads((DATA / "events.json").read_text())
REFERENCE = json.loads((DATA / "reference.json").read_text())
HISTORY = json.loads((DATA / "moves.json").read_text())


class MoveHistoryTest(unittest.TestCase):
    """Move membership must follow recorded decisions, including refusals."""

    def setUp(self):
        self.report = reconstruct_moves(ROUTE, REFERENCE, HISTORY)
        self.battles = {b["event"]: b for b in self.report["battles"]}

    def test_complete_route_and_six_recorded_menu_checks(self):
        self.assertEqual(sum(b["kind"] == "trainer_battle" for b in self.report["battles"]), 69)
        self.assertEqual(sum(c["action"] == "learn" for c in self.report["changes"]), 9)
        self.assertEqual(sum(c["action"] == "decline" for c in self.report["changes"]), 4)
        self.assertEqual(len(self.report["menu_checks"]), 6)
        saved = DATA.parents[2] / "docs/progression/pokeguy-moves.md"
        self.assertEqual(saved.read_text(), moves_markdown(self.report))

    def test_mid_battle_learning_does_not_apply_to_earlier_foes(self):
        pidgey = self.battles["route1-pidgey-defeated"]
        self.assertNotIn("BUBBLE", pidgey["moves_before"])
        self.assertIn("BUBBLE", pidgey["moves_after"])
        liam = self.battles["pewter-liam"]
        self.assertNotIn("WITHDRAW", liam["foes"][1]["moves_before"])
        self.assertIn("WITHDRAW", liam["moves_after"])
        brock = self.battles["brock"]
        self.assertIn("TAIL_WHIP", brock["moves_before"])
        self.assertNotIn("WATER_GUN", brock["foes"][1]["moves_before"])
        self.assertIn("WATER_GUN", brock["moves_after"])
        self.assertNotIn("TAIL_WHIP", brock["moves_after"])

    def test_tm_hm_timing_and_endgame_moves(self):
        self.assertEqual(set(self.battles["misty"]["moves_before"]),
                         {"TACKLE", "WATER_GUN", "BITE", "MEGA_KICK"})
        self.assertIn("WATER_PULSE", self.battles["cerulean-rival"]["moves_before"])
        self.assertNotIn("SURF", self.battles["tower-rocket3"]["moves_after"])
        self.assertIn("SURF", self.battles["fuchsia-kirk"]["moves_before"])
        self.assertNotIn("BLIZZARD", self.battles["celadon-tamia"]["moves_after"])
        self.assertIn("BLIZZARD", self.battles["celadon-lori"]["moves_before"])
        self.assertIn("WATER_PULSE", self.battles["route22-rival"]["moves_after"])
        final = {"SURF", "STRENGTH", "BITE", "BLIZZARD"}
        for key in ("lorelei", "bruno", "agatha", "lance", "champion"):
            self.assertEqual(set(self.battles[key]["moves_before"]), final)
            self.assertEqual(set(self.battles[key]["moves_after"]), final)

    def test_missing_decline_is_detected_from_species_learnset(self):
        changed = copy.deepcopy(HISTORY)
        changed["decisions"] = [c for c in changed["decisions"] if c["id"] != "decline-rapid-spin"]
        with self.assertRaisesRegex(ValueError, "Missing level-up move decision"):
            reconstruct_moves(ROUTE, REFERENCE, changed)

    def test_wrong_level_replacement_capacity_and_menu_disagreement_fail(self):
        for name, field, value, error in (
                ("learn-bite", "level", 18, "not offered"),
                ("tutor-mega-kick", "replaces", "BUBBLE_BEAM", "not known"),
                ("tutor-mega-kick", "replaces", None, "fifth move")):
            changed = copy.deepcopy(HISTORY)
            next(c for c in changed["decisions"] if c["id"] == name)[field] = value
            with self.subTest(name=name, field=field), self.assertRaisesRegex(ValueError, error):
                reconstruct_moves(ROUTE, REFERENCE, changed)
        changed = copy.deepcopy(HISTORY)
        changed["menu_checks"][0]["moves"] = ["WATER_PULSE"]
        with self.assertRaisesRegex(ValueError, "Moves disagree"):
            reconstruct_moves(ROUTE, REFERENCE, changed)


if __name__ == "__main__":
    unittest.main()

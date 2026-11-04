"""Conservation and checkpoint checks for the recorded FRLG player states."""

import copy
import json
import unittest

from pokesim.cli.frlg_progression import DATA
from pokesim.games.frlg.progression.states import reconstruct_states, states_markdown
from pokesim.games.frlg.progression.stats import ORDER, gain_evs, summary_stats

load = lambda name: json.loads((DATA / name).read_text())
ROUTE, REFERENCE, MOVES, HISTORY = [load(n) for n in ("events.json", "reference.json", "moves.json", "state-history.json")]


class StatModelTest(unittest.TestCase):
    """Check cartridge arithmetic and caps independently of observed HP resets."""

    def test_known_level22_stats_and_ivs_are_not_badge_or_stage_boosted(self):
        stats = summary_stats(REFERENCE["species"]["WARTORTLE"]["base_stats"], 22,
            HISTORY["profile"]["ivs"], {"hp":5,"atk":0,"def":11,"spa":3,"spd":0,"spe":16},
            REFERENCE["natures"]["Mild"])
        self.assertEqual(stats, {"hp":64,"atk":38,"def":39,"spa":44,"spd":44,"spe":37})

    def test_evs_are_full_yield_and_caps_follow_cartridge_stat_order(self):
        limits = REFERENCE["ev_limits"]
        self.assertEqual(limits, {"per_stat":255,"total":510})
        zero = dict.fromkeys(ORDER, 0)
        gains = dict(zero, spa=3)
        self.assertEqual(gain_evs(zero, gains, limits)["spa"], 3)
        capped = gain_evs(dict(zero, hp=254), dict(zero, hp=3), limits)
        self.assertEqual(capped["hp"], 255)
        total = gain_evs({**zero, "hp":252, "atk":252, "def":4}, dict.fromkeys(ORDER,3), limits)
        self.assertEqual(total["hp"], 254)
        self.assertEqual(sum(total.values()), 510)


class StartingStateTest(unittest.TestCase):
    """Recorded outcomes supply carry-forward HP; inventory and PP must balance."""

    def setUp(self):
        self.report = reconstruct_states(ROUTE, REFERENCE, MOVES, HISTORY)
        self.battles = {b["event"]: b for b in self.report["battles"]}

    def test_every_encounter_and_all_source_checks_reproduce(self):
        self.assertEqual(len(self.battles), 78)
        self.assertEqual(sum(b["kind"] == "trainer_battle" for b in self.battles.values()), 69)
        self.assertEqual(len(self.report["checks_passed"]), 38)
        self.assertFalse(self.report["simulation_ready"])
        self.assertEqual((DATA.parents[2]/"docs/progression/pokeguy-states.md").read_text(), states_markdown(self.report))
        self.assertEqual(self.report, reconstruct_states(ROUTE, REFERENCE, MOVES, HISTORY))

    def test_real_starting_hp_and_bags_replace_full_hp_fixture_assumptions(self):
        for key, expected in {"misty":(20,54,59),"cerulean-rival":(21,32,61),
                              "ssanne-rival":(27,37,76),"surge":(28,79,79)}.items():
            state = self.battles[key]["starting_state"]
            self.assertEqual((state["level"], state["hp"], state["max_hp"]), expected)
        self.assertEqual(self.battles["misty"]["starting_state"]["battle_bag"]["POTION"], 7)
        self.assertEqual(self.battles["ssanne-rival"]["starting_state"]["battle_bag"]["SUPER_POTION"], 5)

    def test_mid_battle_leveling_does_not_apply_new_evs_to_older_stats(self):
        state = self.battles["lance"]["starting_state"]
        self.assertGreater(state["evs_earned"]["spa"], state["evs_applied_to_stats"]["spa"])
        self.assertEqual(state["stats"]["spa"], 130)
        incorrectly_refreshed = summary_stats(REFERENCE["species"]["BLASTOISE"]["base_stats"], 54,
            HISTORY["profile"]["ivs"], state["evs_earned"], REFERENCE["natures"]["Mild"])
        self.assertGreater(incorrectly_refreshed["spa"], 130)
        self.assertEqual(self.battles["hideout-giovanni"]["starting_state"]["hp"], 38)

    def test_pp_and_items_reconcile_late_video_counts(self):
        route22 = self.battles["route22-rival"]["starting_state"]
        self.assertEqual({m:route22["pp"][m] for m in ("SURF","BITE","BLIZZARD")}, {"SURF":4,"BITE":23,"BLIZZARD":3})
        self.assertEqual(self.battles["agatha"]["starting_state"]["inventory"]["X_SPEED"], 3)
        champion = self.battles["champion"]["starting_state"]
        self.assertEqual(champion["pp"], {"SURF":13,"STRENGTH":15,"BITE":25,"BLIZZARD":5})
        self.assertNotIn("ELIXIR", champion["inventory"])
        self.assertEqual(champion["inventory"]["FULL_RESTORE"], 9)
        end = self.report["final_state"]
        self.assertEqual(end["inventory"]["FULL_RESTORE"], 8)
        self.assertEqual(end["evs_earned"], {"hp":31,"atk":65,"def":60,"spa":57,"spd":18,"spe":77})

    def test_badges_held_item_status_and_alternative_iv_remain_explicit(self):
        self.assertEqual(self.battles["surge"]["starting_state"]["stats"]["atk"], 47)
        self.assertEqual(self.battles["surge"]["starting_state"]["badges"], ["boulder","cascade"])
        self.assertEqual(self.battles["tower-rival"]["starting_state"]["held_item"], "BLACK_GLASSES")
        self.assertEqual(self.battles["hideout-right-guard"]["ending_state"]["status"], "par")
        self.assertEqual(self.battles["hideout-giovanni"]["starting_state"]["status"], "")
        self.assertEqual(len(self.report["final_state"]["badges"]), 8)
        self.assertTrue(any(b["starting_state"]["stats"] != b["starting_state"]["alternate_attack_iv_stats"] for b in self.battles.values()))

    def test_missing_acquisition_or_extra_cast_cannot_silently_reset_to_a_reading(self):
        changed = copy.deepcopy(HISTORY)
        changed["before_events"] = [a for a in changed["before_events"] if not
            (a["kind"] == "acquire" and a.get("items",{}).get("POTION") == 9)]
        with self.assertRaisesRegex(ValueError, "inventory"):
            reconstruct_states(ROUTE, REFERENCE, MOVES, changed)
        changed = copy.deepcopy(HISTORY)
        changed["battles"]["mtmoon-miguel"]["move_uses"]["WATER_GUN"] = 6
        with self.assertRaisesRegex(ValueError, "mismatch"):
            reconstruct_states(ROUTE, REFERENCE, MOVES, changed)
        changed = copy.deepcopy(HISTORY)
        changed["battles"]["rocktunnel-martha"]["move_uses"]["MEGA_KICK"] = 6
        with self.assertRaisesRegex(ValueError, "PP"):
            reconstruct_states(ROUTE, REFERENCE, MOVES, changed)


if __name__ == "__main__":
    unittest.main()

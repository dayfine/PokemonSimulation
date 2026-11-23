import json
import os
from pathlib import Path
import random
import unittest

from pokesim.games.frlg.progression import grind
from pokesim.games.frlg.progression.grind_pret import import_grind_data

POKEFIRERED = os.environ.get("POKEFIRERED_DIR", "")


class GrindTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.party = grind.load(), grind.load_party()

    def test_saved_mimien_stats_match_pret_formula_with_save_nature(self):
        mon = self.party["MR_MIME"]  # no EVs yet, so summary stats are current
        battler = grind.Battler(self.data, "MR_MIME", mon["level"], mon["ivs"],
                                self.data["natures"][mon["nature_index"]], evs=mon["evs"])
        self.assertEqual(battler.stats, mon["stats"])

    def test_wild_moveset_skips_duplicate_learnset_entries(self):
        # Haunter learns Spite at 1 and 8; the oldest distinct move drops out.
        learnset = self.data["species"]["HAUNTER"]["learnset"]
        self.assertEqual(grind.initial_moves(learnset, 20), ["LICK", "SPITE", "CURSE", "NIGHT_SHADE"])

    def test_switch_trick_grinder_never_takes_a_hit(self):
        rng = random.Random(7)
        table = self.data["spots"]["victory-road"][1]
        for _ in range(300):
            grinder = grind.party_battler(self.data, self.party["MR_MIME"])
            sweeper = grind.party_battler(self.data, self.party["BLASTOISE"])
            outcome, shared = grind.fight(self.data, grinder, sweeper, grind.wild_foe(self.data, table, rng), rng)
            self.assertEqual(grinder.hp, grinder.stats["hp"])
            self.assertTrue(shared)

    def test_chding_from_mg03_needs_no_grind_and_mimien_reaches_recycle(self):
        rows = grind.summarize(self.data, self.party, "tower-mimien-solo", runs=2, seed=1)
        self.assertTrue(rows["FARFETCHD"]["already_done"])
        self.assertEqual(rows["MR_MIME"]["completed_runs"], 2)


@unittest.skipUnless(POKEFIRERED and os.path.isdir(POKEFIRERED), "set POKEFIRERED_DIR to a pokefirered checkout")
class GrindPretTest(unittest.TestCase):
    def test_checked_in_grind_data_regenerates_from_pret(self):
        regenerated = json.loads(json.dumps(import_grind_data(Path(POKEFIRERED))))
        self.assertEqual(regenerated, grind.load())


if __name__ == "__main__":
    unittest.main()

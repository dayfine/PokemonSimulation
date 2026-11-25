import json
import os
from pathlib import Path
import unittest

from pokesim._test_paths import GAMES
from pokesim.games.frlg.progression.level_up_pret import evolution, import_level_up_data, select_version

DATA = Path(GAMES) / "frlg/progression/level-up-pret.json"
POKEFIRERED = os.environ.get("POKEFIRERED_DIR", "")


class SelectVersionTest(unittest.TestCase):
    TEXT = "a\n#if defined(FIRERED)\nfr\n#elif defined(LEAFGREEN)\nlg\n#endif\nb"

    def test_keeps_only_the_arm_for_the_version(self):
        self.assertEqual(select_version(self.TEXT, "FIRERED"), "a\nfr\nb")
        self.assertEqual(select_version(self.TEXT, "LEAFGREEN"), "a\nlg\nb")

    def test_else_arm_and_unsupported_conditionals(self):
        text = "#if defined(FIRERED)\nfr\n#else\nother\n#endif"
        self.assertEqual(select_version(text, "LEAFGREEN"), "other")
        with self.assertRaises(ValueError):
            select_version("#ifdef BUGFIX\nx\n#endif", "FIRERED")


class EvolutionTest(unittest.TestCase):
    def test_parameter_is_named_by_method(self):
        self.assertEqual(evolution("EVO_LEVEL", "21", "GLOOM"), {"method": "LEVEL", "level": 21, "species": "GLOOM"})
        self.assertEqual(evolution("EVO_TRADE_ITEM", "ITEM_KINGS_ROCK", "POLITOED"),
                         {"method": "TRADE_ITEM", "item": "KINGS_ROCK", "species": "POLITOED"})
        self.assertEqual(evolution("EVO_FRIENDSHIP", "0", "CROBAT"), {"method": "FRIENDSHIP", "species": "CROBAT"})
        with self.assertRaises(ValueError):
            evolution("EVO_MOVE", "MOVE_ROLLOUT", "X")


class CheckedInLevelUpDataTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.species = cls.data["species"]

    def test_early_route_evolutions(self):
        for name, level, into in (("RATTATA", 20, "RATICATE"), ("PIDGEY", 18, "PIDGEOTTO"), ("ODDISH", 21, "GLOOM")):
            with self.subTest(name=name):
                self.assertEqual(self.species[name]["evolutions"], [{"method": "LEVEL", "level": level, "species": into}])
        self.assertEqual([e["item"] for e in self.species["GLOOM"]["evolutions"]], ["LEAF_STONE", "SUN_STONE"])
        self.assertEqual(self.species["BLASTOISE"]["evolutions"], [])

    def test_learnsets_and_hm_moves(self):
        self.assertEqual([m for m in self.species["BLASTOISE"]["learnset"] if m[0] > 62], [[68, "HYDRO_PUMP"]])
        self.assertEqual(self.data["hm_moves"],
                         ["CUT", "FLY", "SURF", "STRENGTH", "FLASH", "ROCK_SMASH", "WATERFALL", "DIVE"])
        self.assertEqual(len(self.species), 411)  # every pointer-table species except NONE

    def test_firered_arm_of_version_conditionals(self):
        self.assertEqual(self.data["version"], "FIRERED")
        self.assertEqual(self.species["DUGTRIO"]["learnset"][:3], [[1, "TRI_ATTACK"], [1, "SCRATCH"], [1, "SAND_ATTACK"]])
        self.assertIn([15, "TAUNT"], self.species["DEOXYS"]["learnset"])


@unittest.skipUnless(POKEFIRERED and os.path.isdir(POKEFIRERED), "set POKEFIRERED_DIR to a pokefirered checkout")
class LevelUpPretTest(unittest.TestCase):
    def test_checked_in_level_up_data_regenerates_from_pret(self):
        self.assertEqual(import_level_up_data(Path(POKEFIRERED)), json.loads(DATA.read_text()))

    def test_leafgreen_takes_its_own_deoxys(self):
        deoxys = import_level_up_data(Path(POKEFIRERED), "LEAFGREEN")["species"]["DEOXYS"]["learnset"]
        self.assertIn([15, "KNOCK_OFF"], deoxys)


if __name__ == "__main__":
    unittest.main()

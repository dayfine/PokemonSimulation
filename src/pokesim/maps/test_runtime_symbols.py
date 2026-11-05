"""Runtime and legacy numeric glyphs must never share decoding rules."""

import unittest

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.model import Behavior
from pokesim.grid.maps.textgrid import parse
from .runtime_symbols import CLOSED_SIDES, GLYPHS, cell_for
from .runtime_map_schema import validate


class RuntimeSymbolsTest(unittest.TestCase):
    def test_runtime_digit_is_stationary_but_legacy_digit_is_forced(self):
        self.assertEqual(cell_for('8').behavior, Behavior.NONE)
        self.assertEqual(CLOSED_SIDES['8'], Direction.NORTH)
        self.assertEqual(parse('8', name='legacy').grid.at(Tile(0, 0)).behavior, Behavior.FORCED_NORTH)

    def test_validation_accepts_every_canonical_symbol(self):
        for glyph in GLYPHS:
            with self.subTest(glyph=glyph):
                validate(dict(name='M', source=dict(decomp_file='x', revision='x', date='x'), tiles=[glyph]))
        self.assertTrue(cell_for('w').blocked)
        self.assertTrue(cell_for('S').blocked)
        self.assertEqual(cell_for(' ', 3).behavior, Behavior.UNKNOWN)
        self.assertEqual(cell_for('~', 3).elevation, 3)


if __name__ == '__main__':
    unittest.main()

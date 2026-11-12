"""Behavioral regressions for the reviewed #226 map deltas; no console or network."""

import unittest

from pokesim.grid.geometry import Direction as D, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Blocked, Moved, Warp, WorldState, world_step
from .local_routing import Context, LocalMap
from .runtime_map_pack import ROOT, effective_map, load
from .runtime_world import RuntimeWorld
from .transition_state import clip_plan, Pose


def map_data(name):
    return load(ROOT / 'data/games/bdsp/maps/runtime' / (name + '.json'))


def state(name, x, y):
    return WorldState(Place(name, Tile(x, y)), 0)


class BDSPMapReconciliationTest(unittest.TestCase):
    def test_mine_hall_warps_interrupt_before_entering_row_21(self):
        world = RuntimeWorld([LocalMap(map_data('OreburghMineB1F'), 'bdsp'),
                              LocalMap(map_data('OreburghMine'), 'bdsp')])
        # Diamond events narc_0196 has three B2F warps; #226 expects this boundary.
        # No BDSP arrival contract is manufactured from the destination's name.
        for x in (11, 12, 13):
            with self.subTest(column=x):
                self.assertIsInstance(world_step(world, state('OreburghMineB1F', x, 20), D.SOUTH), Warp)
        self.assertIsNone(clip_plan(world, [Pose(state('OreburghMineB1F', 12, 20), D.SOUTH)], D.SOUTH, 8))

    def test_moms_post_heal_call_allows_approach_but_intercepts_exit_mat(self):
        raw = map_data('PlayerHouse1F')
        active = LocalMap(raw, 'bdsp', Context(variables={
            'VAR_PLAYER_HOUSE_STATE': 0, 'CONSOLE_MOMS_CALL': 0}))
        # #226 00.04: around_mom -> (6,9), then SOUTH onto the mat triggers the call.
        self.assertIsInstance(world_step(active, state('PlayerHouse1F', 6, 8), D.SOUTH), Moved)
        self.assertIsInstance(world_step(active, state('PlayerHouse1F', 6, 9), D.SOUTH), Blocked)
        spent = LocalMap(raw, 'bdsp', Context(variables={
            'VAR_PLAYER_HOUSE_STATE': 0, 'CONSOLE_MOMS_CALL': 1}))
        self.assertIsInstance(world_step(spent, state('PlayerHouse1F', 6, 9), D.SOUTH), Warp)

    def test_route201_pre_recovery_tree_edits_remain_held(self):
        raw = map_data('Route201')
        # #226 attributes 20 extra walls to r6, before shared recovery (#229).
        # No anchored capture was found: do not turn a drifted walk into terrain.
        reported = [(x, y) for y in (9, 10, 11, 12) for x in (36, 37, 38, 39)]
        reported += [(x, 12) for x in (32, 33, 34, 35)]
        corrected = effective_map(raw)
        for x, y in reported:
            with self.subTest(tile=(x, y)):
                self.assertEqual(raw['tiles'][y][x], '.')
                self.assertEqual(corrected['tiles'][y][x], '.')
        # Source sign is (13,17); the old pack overrides it. Record this known
        # discrepancy until target-game sign/collision can be reconciled together.
        self.assertEqual(raw['tiles'][17][13], 'S')

    def test_unverified_mine_corridor_edits_do_not_replace_decomp(self):
        raw = map_data('OreburghMine')
        # Independently decoded narc_0314 at Diamond b623abef; these seven WIP
        # replacements have no per-tile target-game evidence. Do not fit a route.
        facts = [(16, 9, '.'), (17, 9, '.'), (15, 10, '#'), (13, 11, '#'),
                 (14, 11, '#'), (15, 11, '.'), (16, 12, '#')]
        for x, y, glyph in facts:
            with self.subTest(tile=(x, y)):
                self.assertEqual(raw['tiles'][y][x], glyph)

    def test_president_spawn_is_not_replaced_by_an_unverified_scene_pose(self):
        raw = map_data('JubilifeCity')
        president = next(obj for obj in raw['objects'] if obj['name'] == 'poketch_president')
        self.assertEqual([president['x'], president['y']], [46, 35])
        self.assertEqual(raw['points']['poketch_president'], [46, 35])
        # This is spawn data, not proof of his current position after the scene.

    def test_floaroma_old_couple_columns_match_console_measurement(self):
        raw = map_data('FloaromaTown')
        # Console B, oldprobe/westedge (2026-11-08): from under the old man,
        # D-pad taps west moved 3 tiles, then bumped the west edge (x 0). The
        # old woman stands east of him. r251a's (2, 25)/(3, 25) was one column west.
        couple = {'old_man': [3, 25], 'old_woman': [4, 25]}
        npcs = {obj['name']: [obj['x'], obj['y']] for obj in raw['objects'] if obj['name'] in couple}
        self.assertEqual(npcs, couple)
        for name, coord in couple.items():
            self.assertEqual(raw['points'][name], coord)
        floaroma = LocalMap(raw, 'bdsp')
        for x in range(0, 7):
            with self.subTest(column=x):
                step = world_step(floaroma, state('FloaromaTown', x, 26), D.NORTH)
                self.assertIsInstance(step, Blocked if x in (3, 4) else Moved)
        here = state('FloaromaTown', 3, 26)
        for _ in range(3):
            step = world_step(floaroma, here, D.WEST)
            self.assertIsInstance(step, Moved)
            here = step.state
        self.assertEqual(here, state('FloaromaTown', 0, 26))
        self.assertNotIsInstance(world_step(floaroma, here, D.WEST), Moved)

    def test_jubilife_clowns_keep_their_wander_boxes_and_story_flag(self):
        raw = map_data('JubilifeCity')
        # lab-B 2026-11-11 21:00 (00.05b mart_clown): the Mart clown was found
        # off his spawn row, so the story's sims must see both clowns move.
        # Diamond hides them behind flag 531 outside the Poketch campaign.
        clowns = {obj['name']: obj for obj in raw['objects'] if obj['name'].startswith('clown_')}
        self.assertEqual(clowns['clown_mart']['wander'], {'x0': 54, 'y0': 32, 'x1': 56, 'y1': 34})
        self.assertEqual(clowns['clown_poketch_company']['wander'], {'x0': 14, 'y0': 17, 'x1': 16, 'y1': 19})
        for name in ('clown_mart', 'clown_poketch_company'):
            self.assertEqual(clowns[name]['hide_flag'], 'flag 531')
        self.assertNotIn('wander', clowns['clown_tv_station'])
        shown = LocalMap(raw, 'bdsp')
        hidden = LocalMap(raw, 'bdsp', Context(flags=frozenset({'flag 531'})))
        self.assertIn(Tile(56, 34), shown.occupied)
        self.assertNotIn(Tile(56, 34), hidden.occupied)


if __name__ == '__main__':
    unittest.main()

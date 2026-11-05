"""Runtime metadata must affect the shared search, not disappear in conversion."""

import copy
import unittest

from pokesim.grid.geometry import Direction, Tile
from pokesim.grid.maps.model import Behavior
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Blocked, BlockReason, Edge, Moved, Warp, WorldState, world_step
from .local_routing import Context, LocalMap
from .route_drawing import ascii_route, route_image
from .runtime_map_pack import ROOT, load


N, E, S, W = Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST


def fixture(rows=None, **fields):
    return dict(name='M', source=dict(decomp_file='fixture', revision='fixed', date='test'),
                tiles=rows or ['...'], **fields)


def state(x, y=0, elevation=0):
    return WorldState(Place('M', Tile(x, y)), elevation)


class LocalRoutingTest(unittest.TestCase):
    def test_closed_sides_block_entry_and_exit_without_forced_movement(self):
        for glyph, closed in [('8', N), ('2', S), ('4', W), ('6', E)]:
            with self.subTest(glyph=glyph):
                view = LocalMap(fixture(['...', '.' + glyph + '.', '...']), 'frlg')
                center = Tile(1, 1)
                outside = center.step(closed)
                self.assertEqual(world_step(view, state(1, 1), closed), Blocked(BlockReason.WALL))
                self.assertEqual(world_step(view, state(*outside), closed.opposite), Blocked(BlockReason.WALL))
                approach = center.step(closed.opposite)
                moved = world_step(view, state(*approach), closed)
                self.assertIsInstance(moved, Moved)
                self.assertEqual(moved.state.place.tile, center)

    def test_shared_shortest_path_respects_closed_sides(self):
        view = LocalMap(fixture(['...', '.4.', '...']), 'frlg')
        path = view.route(Tile(0, 1), Tile(2, 1))
        self.assertEqual(len(path.moves), 4)
        self.assertNotEqual(path.moves[0].to.place.tile, Tile(1, 1))

    def test_terrain_patches_are_applied_before_search_and_keep_raw(self):
        data = fixture(['...', '...', '...'], patches=[dict(x=1, y=1, glyph='#', measured_by='run')])
        before = copy.deepcopy(data)
        view = LocalMap(data, 'bdsp')
        path = view.route(Tile(0, 1), Tile(2, 1))
        self.assertNotIn(Place('M', Tile(1, 1)), path.places())
        self.assertEqual(data, before)
        self.assertEqual(view.raw, before)

    def test_directional_warp_activates_on_press_from_mat(self):
        view = LocalMap(fixture(['.D.'], warps=[dict(x=1, y=0, enter='walk_south')]), 'frlg')
        moved = world_step(view, state(0), E)
        self.assertIsInstance(moved, Moved)
        self.assertEqual(moved.state.place.tile, Tile(1, 0))
        self.assertEqual(world_step(view, state(1), S), Warp(Tile(1, 0)))
        self.assertIsNotNone(view.route(Tile(0, 0), Tile(2, 0)))
        view = LocalMap(fixture(warps=[dict(x=1, y=0, enter='walk_east')]), 'frlg')
        self.assertIsNone(view.route(Tile(0, 0), Tile(2, 0)))

    def test_all_other_warps_end_local_route_even_with_named_destination(self):
        for mode in ('walk_into', 'step_on', 'cave_entrance'):
            with self.subTest(mode=mode):
                view = LocalMap(fixture(warps=[dict(x=1, y=0, enter=mode,
                               to_map='Elsewhere', to_point='exit')]), 'bdsp')
                self.assertIsNone(view.route(Tile(0, 0), Tile(2, 0)))
                self.assertIsInstance(world_step(view, state(0), E), Warp)
                with self.assertRaisesRegex(ValueError, 'transition'):
                    view.route(Tile(0, 0), Tile(1, 0))

    def test_unknown_edges_are_not_wall_stops(self):
        view = LocalMap(fixture(['.']), 'bdsp')
        self.assertIsInstance(world_step(view, state(0), E), Edge)
        self.assertEqual(world_step(view, state(-1), E), Blocked(BlockReason.UNKNOWN))

    def test_frlg_elevation_and_bridge_start(self):
        view = LocalMap(fixture(elevation=['334']), 'frlg')
        self.assertIsNone(view.route(Tile(0, 0), Tile(2, 0)))
        view = LocalMap(fixture(elevation=['304']), 'frlg')
        self.assertEqual(view.route(Tile(0, 0), Tile(2, 0)).end.elevation, 4)
        view = LocalMap(fixture(elevation=['3f3']), 'frlg')
        self.assertEqual(view.route(Tile(0, 0), Tile(2, 0)).moves[0].to.elevation, 3)
        with self.assertRaisesRegex(ValueError, 'bridge start'):
            view.route(Tile(1, 0), Tile(2, 0))
        self.assertIsNotNone(view.route(Tile(1, 0), Tile(2, 0), elevation=3))
        with self.assertRaisesRegex(ValueError, 'disagrees'):
            view.route(Tile(0, 0), Tile(0, 0), elevation=4)

    def test_wander_boxes_and_hidden_flags(self):
        obj = dict(name='npc', kind='npc', x=2, y=0, hide_flag='HIDE',
                   wander=dict(x0=1, y0=0, x1=3, y1=0))
        view = LocalMap(fixture(['.....'], objects=[obj]), 'bdsp')
        self.assertIsNone(view.route(Tile(0, 0), Tile(4, 0)))
        view = LocalMap(fixture(['.....'], objects=[obj]), 'bdsp', Context(flags=frozenset({'HIDE'})))
        self.assertIsNotNone(view.route(Tile(0, 0), Tile(4, 0)))

    def test_unknown_or_active_scene_blocks_and_disarmed_scene_allows(self):
        data = fixture(coord_events=[dict(name='scene', x=1, y=0, width=1, length=1, var='STATE', value=0)])
        for context in (Context(), Context(variables={'STATE': 0})):
            self.assertIsNone(LocalMap(data, 'bdsp', context).route(Tile(0, 0), Tile(2, 0)))
        self.assertIsNotNone(LocalMap(data, 'bdsp', Context(variables={'STATE': 1})).route(Tile(0, 0), Tile(2, 0)))

    def test_baked_map_state_requires_acknowledgement(self):
        with self.assertRaisesRegex(ValueError, 'acknowledgement'):
            LocalMap(fixture(), 'frlg', preconditions=['barriers already open'])
        view = LocalMap(fixture(), 'frlg', Context(acknowledge_map_state=True), ['barriers already open'])
        self.assertEqual(view.preconditions, ['barriers already open'])

    def test_goal_region_reaches_nearest_stable_member_not_first_point(self):
        view = LocalMap(fixture(points={'exit.1': [2, 0], 'exit.2': [1, 0]}), 'bdsp')
        path = view.route_region(Tile(0, 0), 'exit')
        self.assertEqual(path.end.place.tile, Tile(1, 0))
        self.assertEqual(len(path.moves), 1)
        with self.assertRaisesRegex(ValueError, 'region'):
            view.route_region(Tile(0, 0), 'missing')

    def test_closed_side_encounter_region_has_grass_cost(self):
        view = LocalMap(fixture(['.8.'], regions={'wild': [[1, 0]]}), 'frlg')
        self.assertEqual(view.map_file.grid.at(Tile(1, 0)).behavior, Behavior.TALL_GRASS)
        self.assertEqual(view.route(Tile(0, 0), Tile(2, 0)).cost, 7)

    def test_ledge_cannot_land_in_unknown_ground_or_transition(self):
        for end in (' ', 'D'):
            view = LocalMap(fixture(['.', 'v', end]), 'frlg')
            self.assertIsInstance(world_step(view, state(0), S), Blocked)

    def test_draw_computed_route(self):
        view = LocalMap(fixture(['.8.']), 'frlg')
        path = view.route(Tile(0, 0), Tile(2, 0))
        self.assertEqual(ascii_route(view, path), '@*X\n')
        image = route_image(view, path)
        self.assertEqual((image.width, image.height), (48, 16))
        self.assertEqual(image.get(24, 0), (0, 0, 0, 255))

    def test_real_map_points_are_preserved_in_their_runtime_crop(self):
        raw = load(ROOT / 'data/games/bdsp/maps/runtime/Route201.json')
        view = LocalMap(raw, 'bdsp')
        for name, tile in raw['points'].items():
            self.assertEqual(view.point(name), Tile(*tile))
        self.assertEqual(view.data['tiles'][18][8], '#')


if __name__ == '__main__':
    unittest.main()

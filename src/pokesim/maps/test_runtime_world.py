"""Cross-map contracts on unchanged, checked-in runtime packs."""
import json
import unittest

from pokesim.grid.geometry import Direction as D, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import Blocked, Edge, Moved, Warp, Warped, WorldState, world_step
from pokesim.grid.routing.shortest import shortest_path
from .local_routing import Context, LocalMap
from .runtime_map_pack import ROOT
from .runtime_world import ArrivalContract, RuntimeWorld


def view(game, name, flags=(), **variables):
    data = json.loads((ROOT / 'data/games' / game / 'maps/runtime' / (name + '.json')).read_text())
    return LocalMap(data, game, Context(frozenset(flags), variables=variables))


def state(name, x, y, level=0):
    return WorldState(Place(name, Tile(x, y)), level)


class RuntimeWorldTests(unittest.TestCase):
    def test_forest_north_gate_arrives_on_mat_not_one_tile_south(self):
        # cp0007 m6f / r15; native OverworldSim test_forest_north_gate.
        world = RuntimeWorld([view('frlg', 'ViridianForest'), view('frlg', 'Route2_ViridianForest_NorthEntrance')])
        result = world_step(world, state('ViridianForest', 5, 10, 3), D.NORTH)
        self.assertIsInstance(result, Warped)
        self.assertEqual(result.state.place, Place('Route2_ViridianForest_NorthEntrance', Tile(7, 10)))
        self.assertEqual(result.facing, D.NORTH)
        route = shortest_path(world, state('ViridianForest', 5, 20, 3), Place('Route2_ViridianForest_NorthEntrance', Tile(7, 9)))
        self.assertIsNotNone(route)
        self.assertEqual(sum(m.kind.value == 'warp' for m in route.moves), 1)

    def test_route2_gate_entry_then_forest_arrival_and_exit_mat(self):
        world = RuntimeWorld([view('frlg', n) for n in ['Route2', 'ViridianForest', 'Route2_ViridianForest_SouthEntrance']])
        first = world_step(world, state('Route2', 5, 52, 3), D.NORTH)
        self.assertEqual(first.state.place, Place('Route2_ViridianForest_SouthEntrance', Tile(7, 10)))
        second = world_step(world, state('Route2_ViridianForest_SouthEntrance', 7, 2, 3), D.NORTH)
        self.assertEqual(second.state.place, Place('ViridianForest', Tile(29, 62)))
        # Entering the mat does not warp; pressing south FROM it does.
        onto = world_step(world, state('ViridianForest', 29, 61, 3), D.SOUTH)
        self.assertIsInstance(onto, Moved)
        out = world_step(world, onto.state, D.SOUTH)
        self.assertEqual(out.state.place, Place('Route2_ViridianForest_SouthEntrance', Tile(7, 2)))
        self.assertEqual(out.facing, D.SOUTH)

    def test_cerulean_connection_uses_local_offset_not_global_crop(self):
        world = RuntimeWorld([view('frlg', 'CeruleanCity', flags=['FLAG_HIDE_CERULEAN_RIVAL']), view('frlg', 'Route24')])
        result = world_step(world, state('CeruleanCity', 22, 0, 3), D.NORTH)
        self.assertIsInstance(result, Moved)
        self.assertEqual(result.state.place, Place('Route24', Tile(10, 39)))
        back = world_step(world, result.state, D.SOUTH)
        self.assertEqual(back.state.place, Place('CeruleanCity', Tile(22, 0)))

    def test_unloaded_edges_and_warps_remain_unresolved(self):
        world = RuntimeWorld([view('frlg', 'CeruleanCity')])
        self.assertIsInstance(world_step(world, state('CeruleanCity', 22, 0, 3), D.NORTH), Edge)
        self.assertIsInstance(world_step(world, state('CeruleanCity', 22, 20, 3), D.NORTH), Warp)

    def test_bdsp_mine_pending_correction_is_not_silently_imported(self):
        world = RuntimeWorld([view('bdsp', 'OreburghMineB1F'), view('bdsp', 'OreburghMine')])
        # #226's row-21 door correction is NOT in the publishing pin.
        self.assertIsInstance(world_step(world, state('OreburghMineB1F', 12, 20), D.SOUTH), Moved)
        self.assertIsInstance(world_step(world, state('OreburghMineB1F', 12, 21), D.SOUTH), Warp)

    def test_bdsp_house_arrival_does_not_infer_link_from_crop_overlap(self):
        world = RuntimeWorld([view('bdsp', 'PlayerHouse1F', VAR_PLAYER_HOUSE_STATE=0, CONSOLE_MOMS_CALL=1), view('bdsp', 'TwinleafTown')])
        out = world_step(world, state('PlayerHouse1F', 6, 9), D.SOUTH)
        # BDSP has no arrival-facing contract in this pack: fail closed.
        self.assertIsInstance(out, Warp)

    def test_frlg_door_entry_and_automatic_south_walkout(self):
        world = RuntimeWorld([view('frlg', 'PalletTown'), view('frlg', 'PalletTown_PlayersHouse_1F')])
        inside = world_step(world, state('PalletTown', 6, 8, 3), D.NORTH)
        self.assertEqual(inside.state.place, Place('PalletTown_PlayersHouse_1F', Tile(4, 8)))
        self.assertEqual(inside.facing, D.NORTH)
        outside = world_step(world, inside.state, D.SOUTH)
        self.assertEqual(outside.state.place, Place('PalletTown', Tile(6, 8)))
        self.assertEqual(outside.facing, D.SOUTH)

    def test_mtmoon_step_on_ladder_can_be_left_after_arrival(self):
        world = RuntimeWorld([view('frlg', 'MtMoon_1F'), view('frlg', 'MtMoon_B1F')])
        result = world_step(world, state('MtMoon_1F', 5, 7, 3), D.NORTH)
        self.assertIsInstance(result, Warped)
        self.assertEqual(result.state.place, Place('MtMoon_B1F', Tile(3, 3)))
        self.assertEqual(result.facing, D.NORTH)
        world.validate_state(result.state)
        departure = world_step(world, result.state, D.SOUTH)
        self.assertIsInstance(departure, Moved)
        self.assertEqual(departure.state.place, Place('MtMoon_B1F', Tile(3, 4)))

    def test_bdsp_reviewed_arrival_contract_for_existing_house_link(self):
        maps = [view('bdsp', 'PlayerHouse1F', VAR_PLAYER_HOUSE_STATE=0, CONSOLE_MOMS_CALL=1),
                view('bdsp', 'TwinleafTown')]
        source = Place('PlayerHouse1F', Tile(6, 10))
        dest = Place('TwinleafTown', Tile(20, 22))
        contract = ArrivalContract(source, dest, D.SOUTH, D.SOUTH, 'native #226 table 00.01 out_of_the_house')
        result = world_step(RuntimeWorld(maps, [contract]), state('PlayerHouse1F', 6, 9), D.SOUTH)
        self.assertEqual(result, Warped(state('TwinleafTown', 20, 22), D.SOUTH))
        for invalid in [ArrivalContract(source, dest, D.SOUTH, D.SOUTH, ''),
                        ArrivalContract(Place('PlayerHouse1F', Tile(5, 10)), dest, D.SOUTH, D.SOUTH, 'unlinked')]:
            with self.assertRaises(ValueError):
                RuntimeWorld(maps, [invalid])

    def test_duplicate_or_mixed_game_world_rejected(self):
        with self.assertRaises(ValueError):
            RuntimeWorld([view('frlg', 'Route2'), view('bdsp', 'Route202')])
        with self.assertRaises(ValueError):
            RuntimeWorld([view('frlg', 'Route2'), view('frlg', 'Route2')])


if __name__ == '__main__':
    unittest.main()

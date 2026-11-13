# Imported from dayfine/Arduino-Source@51c0ce6128e5981da56b370a770874b96a1e129f
# Original path: devtools/maps/tests/test_frlg_maps.py
import unittest

from pokesim.grid.geometry import Tile
from pokesim.maps import frlg_decomp_map_builder as frlg_maps
from pokesim.maps.local_routing import LocalMap
from pokesim.maps.runtime_map_pack import ROOT, load

TILES = ['.....'] * 5


def event(**fields):
    obj = {'graphics_id': 'OBJ_EVENT_GFX_BUG_CATCHER', 'x': 2, 'y': 2, 'movement_type': 'MOVEMENT_TYPE_FACE_RIGHT',
           'movement_range_x': 1, 'movement_range_y': 1, 'trainer_type': 'TRAINER_TYPE_NORMAL',
           'trainer_sight_or_berry_tree_id': '3', 'flag': '0'}
    obj.update(fields)
    return obj


class TrainerTest(unittest.TestCase):
    def test_facing_trainer_looks_ahead(self):
        data = frlg_maps.map_object(event(), TILES)
        self.assertEqual(data['facing'], 'east')
        self.assertEqual(data['trainer'], {'sight': 3})

    def test_wandering_trainer_looks_both_ways(self):
        data = frlg_maps.map_object(event(movement_type='MOVEMENT_TYPE_WANDER_UP_AND_DOWN'), TILES)
        self.assertNotIn('facing', data)
        self.assertEqual(data['trainer'], {'sight': 3, 'looks': ['north', 'south']})
        self.assertEqual(data['wander'], {'x0': 2, 'y0': 1, 'x1': 2, 'y1': 3})

    def test_trainer_looking_around_looks_every_way(self):
        data = frlg_maps.map_object(event(movement_type='MOVEMENT_TYPE_LOOK_AROUND'), TILES)
        self.assertEqual(data['trainer']['looks'], frlg_maps.ALL_LOOKS)

    def test_others_are_no_trainers(self):
        for fields in ({'trainer_type': 'TRAINER_TYPE_NONE'}, {'trainer_sight_or_berry_tree_id': '0'}):
            data = frlg_maps.map_object(event(**fields), TILES)
            self.assertNotIn('trainer', data)
            self.assertNotIn('facing', data)


class DoorScriptTest(unittest.TestCase):
    SCRIPTS = (
        'EventScript_Close5FDoor1:: @ comment\n'
        '\tsetmetatile 7, 8, METATILE_SilphCo_VerticalBarrier_TopLeft, 1\n'
        '\tsetmetatile 7, 9, METATILE_SilphCo_Floor_ShadeFull, 0\n'
        '\treturn\n'
        '\nSilphCo_5F_OnLoad::\n'
        '\tcall_if_unset FLAG_SILPH_5F_DOOR_1, EventScript_Close5FDoor1\n'
        '\tend\n')

    def test_only_impassable_tiles_close(self):
        blocks = frlg_maps.script_blocks(self.SCRIPTS)
        self.assertEqual(frlg_maps.impassable_tiles(blocks['EventScript_Close5FDoor1']), [(7, 8)])

    def test_on_load_names_the_flag_and_closing_script(self):
        blocks = frlg_maps.script_blocks(self.SCRIPTS)
        self.assertEqual(blocks['SilphCo_5F_OnLoad'][0].strip(),
                         'call_if_unset FLAG_SILPH_5F_DOOR_1, EventScript_Close5FDoor1')
        self.assertTrue(frlg_maps.CALL_IF_UNSET.match(blocks['SilphCo_5F_OnLoad'][0]))

    def test_a_door_is_a_gate_of_its_walkable_closed_tiles(self):
        #   The top row of a barrier is wall in the blockdata too: it is not part of the gate.
        open_tiles = ['........', '.#......', '........']
        doors = [('FLAG_SILPH_5F_DOOR_1', 'EventScript_Close5FDoor1', [(1, 1), (2, 1), (3, 1)])]
        self.assertEqual(frlg_maps.door_gates(doors, open_tiles), {'door_1': {
            'tiles': [[2, 1], [3, 1]], 'open_glyph': '.', 'new_game': 'closed',
            'opens_by': 'card_key_face_a', 'flag': 'FLAG_SILPH_5F_DOOR_1'}})
        self.assertEqual(frlg_maps.set_tiles(open_tiles, [(2, 1), (3, 1)], 'G')[1], '.#GG....')

    def test_other_maps_have_no_doors(self):
        self.assertEqual(frlg_maps.closed_doors(None, 'Route1'), [])


class MansionSwitchTest(unittest.TestCase):
    #   A 2F-like floor: a barrier at x=1..2 (closed at reset, open when pressed)
    #   and floor at x=5 (open at reset, a barrier when pressed). The statue's
    #   eyes are drawn by both scripts and change nothing.
    SCRIPTS = (
        'PokemonMansion_EventScript_PressSwitch_2F::\n'
        '\tsetmetatile 1, 0, METATILE_PokemonMansion_Floor, 0\n'
        '\tsetmetatile 2, 0, METATILE_PokemonMansion_Floor, 0\n'
        '\tsetmetatile 5, 0, METATILE_PokemonMansion_Barrier_Vertical_Mid, 1\n'
        '\tsetmetatile 3, 0, METATILE_PokemonMansion_Statue_RedEyes, 0\n'
        '\treturn\n'
        '\nPokemonMansion_EventScript_ResetSwitch_2F::\n'
        '\tsetmetatile 1, 0, METATILE_PokemonMansion_Barrier_Vertical_Mid, 1\n'
        '\tsetmetatile 2, 0, METATILE_PokemonMansion_Barrier_Vertical_Mid, 1\n'
        '\tsetmetatile 5, 0, METATILE_PokemonMansion_Floor, 0\n'
        '\tsetmetatile 3, 0, METATILE_PokemonMansion_Statue_BlackEyes, 0\n'
        '\treturn\n')

    def test_gates_are_the_connected_tiles_the_press_changes(self):
        gates = frlg_maps.mansion_gates(self.SCRIPTS, 'PokemonMansion_2F', ['.##.~~'])
        self.assertEqual(gates, {
            'barrier_1': {'tiles': [[1, 0], [2, 0]], 'open_glyph': '~', 'new_game': 'closed',
                          'switch': 'mansion', 'open_when': 'on'},
            'barrier_2': {'tiles': [[5, 0]], 'open_glyph': '~', 'new_game': 'open',
                          'switch': 'mansion', 'open_when': 'off'}})

    def test_blockdata_must_be_the_reset_state(self):
        with self.assertRaisesRegex(ValueError, 'reset state'):
            frlg_maps.mansion_gates(self.SCRIPTS, 'PokemonMansion_2F', ['.~~.~~'])

    def test_statues_are_pressed_from_the_tile_they_are_faced_from(self):
        source = {'bg_events': [
            {'x': 2, 'y': 16, 'script': 'PokemonMansion_2F_EventScript_Statue', 'player_facing_dir': 'BG_EVENT_PLAYER_FACING_NORTH'},
            {'x': 3, 'y': 3, 'script': 'Other_EventScript_Sign', 'player_facing_dir': 'BG_EVENT_PLAYER_FACING_ANY'}]}
        statues = frlg_maps.mansion_switches(source)['mansion']
        self.assertEqual(statues['statues'], [{'coord': [2, 16], 'face_from': [2, 17], 'facing': 'north'}])
        self.assertEqual((statues['flag'], statues['floors'][0]), ('FLAG_POKEMON_MANSION_SWITCH_STATE', 'PokemonMansion_1F'))


class VictoryRoadSwitchTest(unittest.TestCase):
    #   A floor with one barrier at x=2 (top at y=0, bottom at y=1) and a button at x=0.
    SCRIPTS = (
        'VictoryRoad_2F_OnLoad::\n'
        '\tcall_if_ne VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1, 100, VictoryRoad_2F_EventScript_SetRockBarrier1\n'
        '\tend\n'
        '\nVictoryRoad_2F_EventScript_SetRockBarrier1::\n'
        '\tsetmetatile 2, 0, METATILE_Cave_RockBarrier_Top, 1\n'
        '\tsetmetatile 2, 1, METATILE_Cave_RockBarrier_Bottom, 1\n'
        '\treturn\n'
        '\nVictoryRoad_2F_EventScript_FloorSwitch1::\n'
        '\tlockall\n'
        '\tgoto_if_eq VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1, 100, VictoryRoad_2F_EventScript_FloorSwitch1AlreadyPressed\n'
        '\tsetmetatile 2, 0, METATILE_Cave_Floor_Ledge_Top, 0\n'
        '\tsetmetatile 2, 1, METATILE_Cave_Floor_Ledge_Bottom, 0\n'
        '\tsetvar VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1, 100\n'
        '\treleaseall\n'
        '\tend\n')
    SOURCE = {'coord_events': [{'x': 0, 'y': 1, 'script': 'VictoryRoad_2F_EventScript_FloorSwitch1'}]}

    def test_barrier_tiles_are_gates_per_metatile_and_the_button_is_a_switch(self):
        gates, switches = frlg_maps.victory_road_gates(self.SCRIPTS, self.SOURCE, 'VictoryRoad_2F', ['..8', 'B.~'])
        self.assertEqual(gates, {
            'barrier_1_top': {'tiles': [[2, 0]], 'open_glyph': '8', 'new_game': 'closed', 'switch': 'floor_switch_1', 'open_when': 'on'},
            'barrier_1_bottom': {'tiles': [[2, 1]], 'open_glyph': '~', 'new_game': 'closed', 'switch': 'floor_switch_1', 'open_when': 'on'}})
        self.assertEqual(switches, {'floor_switch_1': {
            'flag': 'VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1', 'set_value': 100, 'toggle': False, 'floors': ['VictoryRoad_2F'],
            'pressed_by': 'strength_boulder', 'buttons': [{'coord': [0, 1]}]}})

    def test_the_event_must_be_on_a_strength_button(self):
        with self.assertRaisesRegex(ValueError, 'not a Strength button'):
            frlg_maps.victory_road_gates(self.SCRIPTS, self.SOURCE, 'VictoryRoad_2F', ['..8', '..~'])

    def test_the_switch_must_open_what_onload_closes(self):
        scripts = self.SCRIPTS.replace('2, 1, METATILE_Cave_Floor_Ledge_Bottom', '3, 1, METATILE_Cave_Floor_Ledge_Bottom')
        with self.assertRaisesRegex(ValueError, 'closes'):
            frlg_maps.victory_road_gates(scripts, self.SOURCE, 'VictoryRoad_2F', ['..8', 'B.~'])


class EncounterTest(unittest.TestCase):
    #   MtMoon_1F's cave floor: behavior MB_CAVE (0x08), encounter type LAND.
    CAVE_FLOOR = 0x08 | (frlg_maps.TILE_ENCOUNTER_LAND << frlg_maps.ENCOUNTER_TYPE_SHIFT)

    def test_cave_floor_has_wild_encounters(self):
        self.assertEqual(frlg_maps.encounter_glyph('.', self.CAVE_FLOOR), '~')

    def test_floor_without_encounters_stays_open(self):
        self.assertEqual(frlg_maps.encounter_glyph('.', 0x08), '.')

    def test_walls_stay_walls(self):
        self.assertEqual(frlg_maps.encounter_glyph('#', self.CAVE_FLOOR), '#')

    #   MtMoon_B2F's floor closed on the north: MB_IMPASSABLE_NORTH (0x32),
    #   encounter type LAND, as wild as the cave floor around it.
    CLOSED_NORTH = 0x32 | (frlg_maps.TILE_ENCOUNTER_LAND << frlg_maps.ENCOUNTER_TYPE_SHIFT)

    def test_closed_side_floor_has_wild_encounters(self):
        for glyph in '8264':
            self.assertTrue(frlg_maps.wild_edge(glyph, self.CLOSED_NORTH))

    def test_closed_side_floor_without_encounters_is_not_wild(self):
        self.assertFalse(frlg_maps.wild_edge('8', 0x32))

    def test_other_tiles_are_no_wild_edges(self):
        for glyph in '.~#':
            self.assertFalse(frlg_maps.wild_edge(glyph, self.CAVE_FLOOR))


class FloorAndWarpTest(unittest.TestCase):
    def test_cosmetic_floors_are_open_without_unhandled_mark(self):
        for behavior in ('MB_NORMAL', 'MB_CAVE', 'MB_ROCK_STAIRS',
                         'MB_SAND', 'MB_SAND_CAVE', 'MB_MOUNTAIN_TOP', 'MB_ICE'):
            with self.subTest(behavior=behavior):
                unhandled = {}
                glyph, entry = frlg_maps.tile_glyph(behavior, 0, unhandled, False)
                self.assertEqual(glyph, '.')
                self.assertIsNone(entry)
                self.assertEqual(unhandled, {})

    def test_tall_grass_is_terrain_glyph(self):
        unhandled = {}
        glyph, entry = frlg_maps.tile_glyph('MB_TALL_GRASS', 0, unhandled, False)
        self.assertEqual(glyph, '~')
        self.assertIsNone(entry)
        self.assertEqual(unhandled, {})

    def test_interactive_terrain_glyphs(self):
        expected = {
            'MB_SPIN_UP': ('u', None),
            'MB_SPIN_DOWN': ('d', None),
            'MB_SPIN_LEFT': ('l', None),
            'MB_SPIN_RIGHT': ('r', None),
            'MB_STOP_SPINNING': ('o', None),
            'MB_FALL_WARP': ('H', 'step_on'),
            'MB_STRENGTH_BUTTON': ('B', None),
        }
        for behavior, (exp_glyph, exp_entry) in expected.items():
            with self.subTest(behavior=behavior):
                unhandled = {}
                glyph, entry = frlg_maps.tile_glyph(behavior, 0, unhandled, False)
                self.assertEqual(glyph, exp_glyph)
                self.assertEqual(entry, exp_entry)
                self.assertEqual(unhandled, {})

    def test_regular_warp_is_step_on(self):
        unhandled = {}
        glyph, entry = frlg_maps.tile_glyph('MB_REGULAR_WARP', 0, unhandled, False)
        self.assertEqual(glyph, '.')
        self.assertEqual(entry, 'step_on')
        self.assertEqual(unhandled, {})


class FakeDecomp:
    def __init__(self, files):
        self.files = files

    def read(self, rel):
        return self.files[rel]


class TilesetTest(unittest.TestCase):
    #   gTileset_SSAnne's folder is ss_anne, which the symbol doesn't say.
    METATILES = (b'const u32 gMetatileAttributes_SS[] = INCBIN_U32("data/tilesets/secondary/ss/metatile_attributes.bin");\n'
                 b'const u32 gMetatileAttributes_SSAnne[] = INCBIN_U32("data/tilesets/secondary/ss_anne/metatile_attributes.bin");\n')

    def test_attributes_from_the_file_metatiles_h_names(self):
        decomp = FakeDecomp({
            'src/data/tilesets/metatiles.h': self.METATILES,
            'data/tilesets/secondary/ss_anne/metatile_attributes.bin': bytes([1, 0, 0, 0, 0x22, 0, 0, 1]),
        })
        self.assertEqual(frlg_maps.tileset_attributes(decomp, 'gTileset_SSAnne'), [1, 0x01000022])


if __name__ == '__main__':
    unittest.main()


class FullCatalogTest(unittest.TestCase):
    def test_follows_declared_groups_and_ignores_metadata_lists(self):
        import json
        class Source:
            def read(self, path):
                self_path = 'data/maps/map_groups.json'
                if path != self_path:
                    raise AssertionError(path)
                return json.dumps({'group_order': ['group_b', 'group_a'],
                    'group_a': ['MapA', 'MapB'], 'group_b': ['MapC', 'MapA'],
                    'connections_include_order': ['NotAnAdditionalMap']}).encode()
        self.assertEqual(frlg_maps.all_map_names(Source()), ['MapA', 'MapB', 'MapC'])

    def test_invalid_or_missing_groups_fail(self):
        import json
        for data in ({}, {'group_order': ['missing']},
                     {'group_order': ['a'], 'a': ['../map']}):
            with self.subTest(data=data):
                class Source:
                    def read(self, path):
                        return json.dumps(data).encode()
                with self.assertRaises(ValueError):
                    frlg_maps.all_map_names(Source())


class DynamicWarpTest(unittest.TestCase):
    def test_dynamic_elevator_destination_remains_unresolved(self):
        event = {'x': 1, 'y': 2, 'dest_map': 'MAP_DYNAMIC', 'dest_warp_id': 'WARP_ID_DYNAMIC'}
        result = frlg_maps.warp(event, {}, {}, {})
        self.assertEqual(result, {'x': 1, 'y': 2, 'enter': 'walk_into',
            'unresolved': 'dynamic_destination',
            'source_destination': {'map': 'MAP_DYNAMIC', 'warp': 'WARP_ID_DYNAMIC'}})
        self.assertEqual(frlg_maps.arrivals({'Elevator': {'warp_events': [event]}}, {}), {'Elevator': set()})

    def test_unknown_symbol_is_not_guessed_or_truncated(self):
        for value in ('UNSUPPORTED_WARP', -1, 1.5, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    frlg_maps.static_warp_id({'dest_warp_id': value})


class CandidateTerrainTest(unittest.TestCase):
    def test_full_catalog_blocks_unhandled_effects_without_changing_legacy_output(self):
        import struct
        from unittest.mock import patch
        class Source:
            def read(self, path):
                if path != 'map.bin':
                    raise AssertionError(path)
                return struct.pack('<HH', 0, 1)
        layout = {'width': 2, 'height': 1, 'blockdata_filepath': 'map.bin',
                  'primary_tileset': 'a', 'secondary_tileset': 'b'}
        behaviors = {0: 'MB_NORMAL', 1: 'MB_CRACKED_ICE'}
        with patch.object(frlg_maps, 'tileset_attributes', return_value=[1, 0]):
            unresolved = {}
            candidate = frlg_maps.grid(Source(), layout, behaviors, {}, unresolved=unresolved)
            legacy = frlg_maps.grid(Source(), layout, behaviors, {})
        self.assertEqual(candidate[0], [' .'])
        self.assertEqual(legacy[0], ['..'])
        self.assertEqual(unresolved, {'MB_CRACKED_ICE': [[0, 0]]})

    def test_base_keeps_closed_source_gym_barriers_in_every_mode(self):
        from unittest.mock import patch
        sources = {'VermilionCity_Gym': {'id': 'GYM', 'layout': 'L'}}
        class Source:
            commit = frlg_maps.COMMIT
        def grid(*args):
            return ['#' * 10] * 10, ['3' * 10] * 10, {}, []
        with patch.object(frlg_maps, 'grid', side_effect=grid):
            candidate = frlg_maps.map_json(Source(), 'VermilionCity_Gym', sources,
                {'L': {}}, {}, {'GYM': 'VermilionCity_Gym'}, {}, candidate=True)
            legacy = frlg_maps.map_json(Source(), 'VermilionCity_Gym', sources,
                {'L': {}}, {}, {'GYM': 'VermilionCity_Gym'}, {})
        # The opened beams are a story_state overlay operation, not generator output.
        self.assertEqual(candidate['tiles'][6][4], '#')
        self.assertEqual(legacy['tiles'][6][4], '#')
        self.assertNotIn('unapplied_story_patch', candidate['source'])


class CandidateWaterTest(unittest.TestCase):
    def test_water_collision_is_preserved_as_water_not_a_generic_wall(self):
        import struct
        from unittest.mock import patch
        class Source:
            def read(self, path):
                return struct.pack('<H', 1 << 10)
        layout = {'width': 1, 'height': 1, 'blockdata_filepath': 'map.bin',
                  'primary_tileset': 'a', 'secondary_tileset': 'b'}
        with patch.object(frlg_maps, 'tileset_attributes', return_value=[1]):
            candidate = frlg_maps.grid(Source(), layout, {1: 'MB_POND_WATER'}, {}, unresolved={})
            legacy = frlg_maps.grid(Source(), layout, {1: 'MB_POND_WATER'}, {})
        self.assertEqual(candidate[0], ['w'])
        self.assertEqual(legacy[0], ['#'])


class ElevationElisionTest(unittest.TestCase):
    def test_only_default_ground_may_be_omitted(self):
        cases = [
            (['..#'], ['331'], True),  # Wall height cannot affect a walking leg.
            (['...'], ['333'], True),
            (['...'], ['303'], False),  # Zero accepts arrivals at any elevation.
            (['...'], ['343'], False),  # A level change blocks ordinary walking.
            (['...'], ['3f3'], False),  # Bridge preserves the player's level.
            (['.w.'], ['303'], False),  # Water is not a dispensable wall in pure ground_only.
        ]
        for tiles, levels, expected in cases:
            with self.subTest(tiles=tiles, elevation=levels):
                self.assertEqual(frlg_maps.ground_only(tiles, levels), expected)

    def test_elevation_omission_reason(self):
        # 1. Pure ground
        self.assertIn('all walkable tiles are ground level',
                      frlg_maps.elevation_omission_reason(['..#'], ['331']))
        # 2. Water keeps its grid: a missing grid reads as ground, and water's own
        #    level is what stops a walking player (Arduino's FRLG walker).
        self.assertIsNone(frlg_maps.elevation_omission_reason(['.w.'], ['313']))
        self.assertIsNone(frlg_maps.elevation_omission_reason(['.w.'], ['313'], [{'coord': [0, 0]}], {}))
        # A map entered only by its connections has nothing to search from.
        self.assertIsNone(frlg_maps.elevation_omission_reason(['.#.'], ['330'], [], {}))
        self.assertIn('all reachable land is ground level',
                      frlg_maps.elevation_omission_reason(['.#.'], ['330'], [{'coord': [0, 0]}], {}))
        # 3. Multi-level bridge cannot be omitted
        self.assertIsNone(frlg_maps.elevation_omission_reason(['.w.'], ['3f3']))
        self.assertIsNone(frlg_maps.elevation_omission_reason(['...'], ['343']))
        # 4. Reachable ground with blocked non-3 tile
        tiles = ['###', '#.#', '###', '...']
        levels = ['000', '000', '000', '333']
        warps = [{'coord': [1, 3]}]
        points = {'p': [1, 3]}
        self.assertIn('all reachable land is ground level',
                      frlg_maps.elevation_omission_reason(tiles, levels, warps, points))


class ItemTest(unittest.TestCase):
    def test_hidden_items_are_data_with_their_flag(self):
        source = {'bg_events': [
            {'type': 'sign', 'x': 1, 'y': 1},
            {'type': 'hidden_item', 'x': 3, 'y': 2, 'item': 'ITEM_RARE_CANDY', 'flag': 'FLAG_HIDDEN_ITEM_X',
             'quantity': 1, 'underfoot': False},
            {'type': 'hidden_item', 'x': 9, 'y': 9, 'item': 'ITEM_ETHER', 'flag': 'FLAG_OFF_MAP', 'quantity': 1},
        ]}
        self.assertEqual(frlg_maps.hidden_items(source, TILES), [
            {'coord': [3, 2], 'item': 'rare_candy', 'quantity': 1, 'flag': 'FLAG_HIDDEN_ITEM_X', 'source_bg_event': 1}])

    def test_uncatalogued_item_balls_resolve_from_their_scripts(self):
        expected = {'PokemonTower_5F': {(6, 16): 'nugget', (11, 9): 'cleanse_tag'},
                    'PokemonTower_6F': {(5, 15): 'rare_candy', (15, 15): 'x_accuracy'}}
        for name, items in expected.items():
            data = load(ROOT / 'data/games/frlg/maps/runtime' / (name + '.json'))
            balls = {(o['x'], o['y']): o for o in data['objects'] if o['kind'] == 'item'}
            self.assertEqual({coord: o['item'] for coord, o in balls.items()}, items)
            self.assertEqual(data['source']['item_identities']['scripts'], 'data/scripts/item_ball_scripts.inc')
            world = LocalMap(data, 'frlg')
            for coord in items:
                self.assertIn(Tile(*coord), world.occupied)
        tower = load(ROOT / 'data/games/frlg/maps/runtime/PokemonTower_5F.json')
        for hidden in tower['hidden_items']:
            self.assertNotIn(Tile(*hidden['coord']), LocalMap(tower, 'frlg').occupied)

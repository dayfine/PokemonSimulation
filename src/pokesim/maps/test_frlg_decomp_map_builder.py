# Imported from dayfine/Arduino-Source@51c0ce6128e5981da56b370a770874b96a1e129f
# Original path: devtools/maps/tests/test_frlg_maps.py
import unittest

from pokesim.maps import frlg_decomp_map_builder as frlg_maps

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
        behaviors = {0: 'MB_NORMAL', 1: 'MB_SPIN_UP'}
        with patch.object(frlg_maps, 'tileset_attributes', return_value=[1, 0]):
            unresolved = {}
            candidate = frlg_maps.grid(Source(), layout, behaviors, {}, unresolved=unresolved)
            legacy = frlg_maps.grid(Source(), layout, behaviors, {})
        self.assertEqual(candidate[0], [' .'])
        self.assertEqual(legacy[0], ['..'])
        self.assertEqual(unresolved, {'MB_SPIN_UP': [[0, 0]]})

    def test_candidate_keeps_closed_source_gym_barriers(self):
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
        self.assertEqual(candidate['tiles'][6][4], '#')
        self.assertEqual(legacy['tiles'][6][4], '.')
        self.assertIn('unapplied_story_patch', candidate['source'])


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
            (['.w.'], ['303'], False),  # Water is not a dispensable wall.
        ]
        for tiles, levels, expected in cases:
            with self.subTest(tiles=tiles, elevation=levels):
                self.assertEqual(frlg_maps.ground_only(tiles, levels), expected)

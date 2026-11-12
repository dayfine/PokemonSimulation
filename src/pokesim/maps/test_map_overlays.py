"""Overlays over generated base maps: resolution, story-state gating, audit and the published pack."""

import copy
import json
import unittest

try:
    import jsonschema
except ImportError:
    jsonschema = None

from . import map_overlays as overlays
from .map_overlays import COMPLETE, NEW_GAME, StoryState


SOURCE = {'decomp_file': 'x', 'revision': 'x', 'date': 'x'}


def base_map(**extra):
    data = {'format': 'pokesim-runtime-map/2', 'name': 'Test', 'source': dict(SOURCE),
            'tiles': ['...', '.#.', '...'],
            'points': {'warp_0': [0, 0]},
            'npcs': [{'name': 'man', 'coord': [2, 2]}],
            'warps': [{'coord': [0, 0], 'enter': 'walk_into'}],
            'connections': [{'side': 'north', 'to_map': 'Other', 'offset': 0}]}
    data.update(extra)
    return data


def op(op_name, why='console_measured', status='candidate', **fields):
    result = {'op': op_name, 'why': why, 'evidence': {'run': 'test'}, 'status': status}
    result.update(fields)
    return result


def overlay(*operations):
    return {'format': overlays.FORMAT, 'map': 'Test', 'operations': list(operations)}


GATE = op('tile', why='story_state', coords=[[1, 1]], glyph='.',
          when={'flag': 'FLAG_GATE_OPEN', 'after_checkpoint': '00.23'})


class ResolveTest(unittest.TestCase):
    def test_no_overlay_is_the_base(self):
        data, applied = overlays.resolve(base_map(), None)
        self.assertEqual(data['tiles'], base_map()['tiles'])
        self.assertEqual(applied, [])

    def test_resolution_copies_and_keeps_the_base(self):
        base = base_map()
        before = copy.deepcopy(base)
        data, applied = overlays.resolve(base, overlay(GATE))
        self.assertEqual(base, before)
        self.assertEqual(data['tiles'][1], '...')
        self.assertEqual(applied[0][1], ["tile (1, 1) '#' -> '.'"])

    def test_story_state_applies_after_its_flag_or_checkpoint(self):
        cases = [(NEW_GAME, '#'), (COMPLETE, '.'),
                 (StoryState(checkpoint='00.22'), '#'), (StoryState(checkpoint='00.23'), '#'),
                 (StoryState(checkpoint='00.23b'), '.'), (StoryState(checkpoint='00.24'), '.'),
                 (StoryState(checkpoint='01.00'), '.'),
                 (StoryState(checkpoint='00.05', flags=frozenset({'FLAG_GATE_OPEN'})), '.'),
                 (StoryState(flags=frozenset({'FLAG_OTHER'})), '#')]
        for state, glyph in cases:
            with self.subTest(state=state):
                self.assertEqual(overlays.resolve(base_map(), overlay(GATE), state)[0]['tiles'][1][1], glyph)

    def test_operations_without_when_always_apply(self):
        wall = op('tile', coords=[[0, 2]], glyph='#')
        self.assertEqual(overlays.resolve(base_map(), overlay(wall), NEW_GAME)[0]['tiles'][2], '#..')

    def test_operations_apply_in_order(self):
        first = op('tile', coords=[[0, 2]], glyph='#')
        second = op('tile', coords=[[0, 2]], glyph='w')
        self.assertEqual(overlays.resolve(base_map(), overlay(first, second))[0]['tiles'][2], 'w..')

    def test_points_links_and_objects(self):
        data, applied = overlays.resolve(base_map(), overlay(
            op('point', name='sign', coord=[2, 0]),
            op('point', name='warp_0', remove=True),
            op('link', kind='warp', index=0, to_map='Other', to_point='warp_3'),
            op('link', kind='connection', action='remove', side='north', to_map='Other', offset=0),
            op('link', kind='connection', action='add', side='south', to_map='Else', offset=2),
            op('object', action='move', name='man', at=[2, 2], to=[2, 1]),
            op('object', action='add', object={'name': 'girl', 'kind': 'npc', 'coord': [0, 2]}),
            op('object', action='remove', name='girl', at=[0, 2])))
        self.assertEqual(data['points'], {'sign': [2, 0]})
        self.assertEqual((data['warps'][0]['to_map'], data['warps'][0]['to_point']), ('Other', 'warp_3'))
        self.assertEqual(data['connections'], [{'side': 'south', 'to_map': 'Else', 'offset': 2}])
        self.assertEqual([(o['name'], o['x'], o['y']) for o in data['objects']], [('man', 2, 1)])
        self.assertEqual(len(applied), 8)

    def test_stale_or_impossible_operations_fail(self):
        for bad in (op('tile', coords=[[0, 0]], glyph='.'),        # changes nothing
                    op('tile', coords=[[3, 0]], glyph='#'),        # off the map
                    op('point', name='warp_0', coord=[0, 0]),
                    op('point', name='nowhere', remove=True),
                    op('link', kind='warp', index=4, to_map='Other', to_point='warp_0'),
                    op('link', kind='connection', action='add', side='north', to_map='Other', offset=0),
                    op('object', action='remove', name='man', at=[0, 0]),
                    op('trigger', action='add')):
            with self.subTest(op=bad), self.assertRaises(ValueError):
                overlays.resolve(base_map(), overlay(bad))

    def test_invalid_overlays_fail(self):
        for change in (lambda o: o.update(format='other'),
                       lambda o: o.update(map='Elsewhere'),
                       lambda o: o.update(operations=[]),
                       lambda o: o['operations'][0].update(why='because'),
                       lambda o: o['operations'][0].update(status='approved'),
                       lambda o: o['operations'][0].pop('evidence'),
                       lambda o: o['operations'][0].pop('when'),
                       lambda o: o['operations'][0].update(why='console_measured'),
                       lambda o: o['operations'][0].update(when={'after_checkpoint': 'soon'}),
                       lambda o: o['operations'][0].update(why='generator_gap', when=None)):
            data = overlay(copy.deepcopy(GATE))
            change(data)
            if data['operations'] and data['operations'][0].get('when', 0) is None:
                del data['operations'][0]['when']
            with self.subTest(data=data), self.assertRaises(ValueError):
                overlays.resolve(base_map(), data)

    def test_generator_gap_names_its_fix(self):
        gap = op('tile', why='generator_gap', coords=[[0, 2]], glyph='#')
        with self.assertRaisesRegex(ValueError, 'generator fix'):
            overlays.resolve(base_map(), overlay(gap))
        gap['evidence']['generator_fix'] = 'emit water behind collision as w'
        self.assertEqual(overlays.resolve(base_map(), overlay(gap))[0]['tiles'][2], '#..')

    def test_checkpoint_order(self):
        keys = [overlays.checkpoint_key(c) for c in ('00.05', '00.12', '00.12b', '00.13', '01.00')]
        self.assertEqual(keys, sorted(keys))
        with self.assertRaises(ValueError):
            overlays.checkpoint_key('00.x5')


def gate_map():
    return base_map(
        tiles=['....', '.GG.', '.G..', '...G'],
        gates={'door': {'tiles': [[1, 1], [2, 1], [1, 2]], 'open_glyph': '.', 'new_game': 'closed',
                        'opens_by': 'card_key_face_a', 'flag': 'FLAG_DOOR'},
               'bars': {'tiles': [[3, 3]], 'open_glyph': '~', 'new_game': 'open',
                        'switch': 'lever', 'open_when': 'off'}},
        switches={'lever': {'flag': 'FLAG_LEVER', 'toggle': True, 'floors': ['Test'],
                            'statues': [{'coord': [0, 0], 'face_from': [0, 1], 'facing': 'north'}]}})


def gate_op(gate, state, flag):
    return op('gate', why='story_state', gate=gate, state=state, when={'flag': flag})


class GateTest(unittest.TestCase):
    def test_gates_are_settled_to_their_new_game_state(self):
        data, _ = overlays.resolve(gate_map(), None)
        self.assertEqual(data['tiles'], ['....', '.##.', '.#..', '...~'])

    def test_a_gate_operation_flips_its_tiles_once_its_flag_is_set(self):
        file = overlay(gate_op('door', 'open', 'FLAG_DOOR'), gate_op('bars', 'closed', 'FLAG_LEVER'))
        door = overlays.resolve(gate_map(), file, StoryState(flags=frozenset({'FLAG_DOOR'})))[0]
        self.assertEqual(door['tiles'], ['....', '....', '....', '...~'])
        lever = overlays.resolve(gate_map(), file, StoryState(flags=frozenset({'FLAG_LEVER'})))[0]
        self.assertEqual(lever['tiles'], ['....', '.##.', '.#..', '...#'])
        self.assertEqual(overlays.resolve(gate_map(), file, NEW_GAME)[0]['tiles'][3], '...~')

    def test_unsettled_resolution_keeps_the_gate_glyph(self):
        file = overlay(gate_op('door', 'open', 'FLAG_DOOR'))
        data, applied = overlays.resolve(gate_map(), file, COMPLETE, settle=False)
        self.assertEqual(data['tiles'], gate_map()['tiles'])
        self.assertEqual(applied, [])

    def test_an_operation_must_agree_with_the_gate_table(self):
        wrong = [gate_op('door', 'closed', 'FLAG_DOOR'), gate_op('door', 'open', 'FLAG_OTHER'),
                 gate_op('bars', 'open', 'FLAG_LEVER'), gate_op('missing', 'open', 'FLAG_DOOR')]
        for operation in wrong:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                overlays.resolve(gate_map(), overlay(operation))

    def test_the_gate_tables_are_validated(self):
        from .runtime_map_schema import validate
        validate(gate_map())
        mutations = [
            lambda d: d['tiles'].__setitem__(0, 'G...'),                        # G in no gate
            lambda d: d['gates']['door'].update(new_game='open'),               # flag gate starts closed
            lambda d: d['gates']['bars'].update(open_when='on'),                # switch starts off
            lambda d: d['gates']['bars'].update(switch='nope'),
            lambda d: d['gates']['bars']['tiles'].append([1, 1]),               # tile in two gates
            lambda d: d['switches']['lever']['statues'][0].update(facing='south'),
            lambda d: d['switches']['lever'].update(floors=['Other']),
        ]
        for mutate in mutations:
            data = copy.deepcopy(gate_map())
            mutate(data)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                validate(data)


class PublishedPackTest(unittest.TestCase):
    def test_runtime_files_are_base_plus_overlays(self):
        self.assertEqual(overlays.check(), 156)

    def test_vermilion_gym_beams_open_after_the_switches(self):
        beams = [(x, y) for y in (6, 7) for x in (4, 5, 6)]
        closed = overlays.effective_map('VermilionCity_Gym', NEW_GAME)
        during = overlays.effective_map('VermilionCity_Gym', StoryState(checkpoint='00.23'))
        after = overlays.effective_map('VermilionCity_Gym', StoryState(checkpoint='00.24'))
        flagged = overlays.effective_map('VermilionCity_Gym',
                                         StoryState(flags=frozenset({'FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES'})))
        runtime = json.loads(overlays.path_of('frlg', 'runtime', 'VermilionCity_Gym').read_text())
        for x, y in beams:
            self.assertEqual(closed['tiles'][y][x], '#')
            self.assertEqual(during['tiles'][y][x], '#')
            self.assertEqual(after['tiles'][y][x], '.')
            self.assertEqual(flagged['tiles'][y][x], '.')
            self.assertEqual(runtime['tiles'][y][x], '.')
        self.assertEqual(runtime['source']['overlay'], {
            'file': 'data/games/frlg/maps/overlays/VermilionCity_Gym.json', 'story_state': 'complete'})

    def test_silph_card_key_doors_are_gates_closed_until_opened(self):
        #   (gate, flag, tiles that open); the base and runtime files show `G`,
        #   the effective map is a wall until the flag is set, then open floor.
        doors = {
            'SilphCo_5F': [('door_1', 'FLAG_SILPH_5F_DOOR_1', [(7, 9), (8, 9), (7, 10), (8, 10)]),
                           ('door_2', 'FLAG_SILPH_5F_DOOR_2', [(7, 18), (8, 18), (7, 19), (8, 19)]),
                           ('door_3', 'FLAG_SILPH_5F_DOOR_3', [(18, 13), (19, 13), (18, 14), (19, 14)])],
            'SilphCo_11F': [('door', 'FLAG_SILPH_11F_DOOR', [(5, 16), (6, 16), (5, 17), (6, 17)])],
        }
        for name, floor in doors.items():
            base = json.loads(overlays.path_of('frlg', 'base', name).read_text())
            runtime = json.loads(overlays.path_of('frlg', 'runtime', name).read_text())
            for gate_id, flag, tiles in floor:
                with self.subTest(map=name, gate=gate_id):
                    gate = base['gates'][gate_id]
                    self.assertEqual(sorted(map(tuple, gate['tiles'])), sorted(tiles))
                    self.assertEqual((gate['flag'], gate['opens_by'], gate['new_game']),
                                     (flag, 'card_key_face_a', 'closed'))
                    closed = overlays.effective_map(name, NEW_GAME)
                    opened = overlays.effective_map(name, StoryState(flags=frozenset({flag})))
                    for x, y in tiles:
                        self.assertEqual(base['tiles'][y][x], 'G')
                        self.assertEqual(runtime['tiles'][y][x], 'G')
                        self.assertEqual(closed['tiles'][y][x], '#')
                        self.assertEqual(opened['tiles'][y][x], '.')
            self.assertEqual(runtime['gates'], base['gates'])

    def test_every_silph_gate_has_one_flag_operation(self):
        count = 0
        for floor in range(2, 12):
            name = f'SilphCo_{floor}F'
            gates = json.loads(overlays.path_of('frlg', 'base', name).read_text())['gates']
            operations = overlays.read_overlay(name)['operations']
            count += len(operations)
            self.assertEqual(sorted(o['gate'] for o in operations), sorted(gates))
            for operation in operations:
                self.assertEqual(operation['op'], 'gate')
                self.assertEqual(operation['when']['flag'], gates[operation['gate']]['flag'])
                self.assertRegex(operation['when']['flag'], r'FLAG_SILPH_\d+F_DOOR(_\d)?\Z')
        self.assertEqual(count, 20)

    def test_maps_without_overlays_publish_base_bytes(self):
        for name in ('VermilionCity', 'SSAnne_Exterior', 'Route1'):
            with self.subTest(map=name):
                self.assertFalse(overlays.path_of('frlg', 'overlays', name).exists())
                self.assertEqual(overlays.path_of('frlg', 'runtime', name).read_bytes(),
                                 overlays.path_of('frlg', 'base', name).read_bytes())

    def test_water_is_water_not_wall(self):
        # The v1 pack drew water behind collision as walls; the base keeps it water.
        for name in ('VermilionCity', 'SSAnne_Exterior'):
            data = overlays.effective_map(name)
            self.assertTrue(any('w' in row for row in data['tiles']))
            self.assertIn('elevation', data)

    def test_audit_groups_by_why(self):
        text = overlays.audit('VermilionCity_Gym')
        self.assertIn('story_state: 1 operation(s)', text)
        self.assertIn('when flag=FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES, after_checkpoint=00.23', text)
        self.assertEqual(text.count("'#' -> '.'"), 6)
        self.assertIn('no overlay', overlays.audit('Route1'))

    def test_manifest_lists_base_and_overlay_hashes(self):
        manifest = json.loads(overlays.MANIFEST.read_text())
        entries = {e['name']: e for e in manifest['games']['frlg']['maps']}
        self.assertEqual(entries['VermilionCity_Gym']['overlay']['file'],
                         'data/games/frlg/maps/overlays/VermilionCity_Gym.json')
        self.assertEqual(sum('overlay' in e for e in entries.values()), len(overlays.overlay_names()))
        self.assertTrue(all(e['base']['file'] == f'data/games/frlg/maps/base/{n}.json' for n, e in entries.items()))


@unittest.skipUnless(jsonschema, 'install schemas/requirements.txt for schema tests')
class OverlaySchemaTest(unittest.TestCase):
    def test_schema_matches_the_reader(self):
        from pokesim.formats.json_schema import validator
        check = validator('map-overlay')
        good = overlay(GATE, op('point', name='sign', coord=[2, 0]),
                       op('link', kind='connection', action='add', side='south', to_map='Else', offset=2),
                       op('object', action='move', name='man', at=[2, 2], to=[2, 1]))
        self.assertEqual(list(check.iter_errors(good)), [])
        for change in (lambda o: o['operations'][0].pop('when'),
                       lambda o: o['operations'][1].update(when={'flag': 'FLAG_X'}),
                       lambda o: o['operations'][0].update(why='because'),
                       lambda o: o['operations'][0].update(glyph='?'),
                       lambda o: o['operations'][1].update(why='generator_gap'),
                       lambda o: o.update(extra=1)):
            data = copy.deepcopy(good)
            change(data)
            with self.subTest(data=data):
                self.assertTrue(list(check.iter_errors(data)))
                with self.assertRaises(ValueError):
                    overlays.check_overlay(data)


if __name__ == '__main__':
    unittest.main()

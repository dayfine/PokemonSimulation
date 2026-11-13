"""V2 publication preserves the reviewed v1 data and historical replay outcomes."""

import json
import hashlib
import unittest

from . import bdsp_native_recovery_replay as bdsp, frlg_native_recovery_replay as frlg
from .conformance import read_pack, run_case
from .local_routing import Context, LocalMap
from .runtime_map_coordinates import COMPACT, compact_map, legacy_map
from .runtime_map_format import map_text
from .runtime_map_pack import ROOT, audit
from .runtime_world import RuntimeWorld

# Canonical value digests survive branch deletion and squash merges of #55.
BASELINE = ROOT / 'data/maps/v2-value-baseline.json'

# Reviewed value corrections published after the v1 baseline, as
# {(game, map): {name: (v1 coord, current coord)}} for points and NPCs.
# Each is undone before digesting so every other value still matches v1.
# Floaroma's old couple: console oldprobe/westedge, 2026-11-08 (one column east).
CORRECTIONS = {
    ('bdsp', 'FloaromaTown'): {'old_man': ([2, 25], [3, 25]), 'old_woman': ([3, 25], [4, 25])},
}


def undo_corrections(game, data):
    for name, (before, after) in CORRECTIONS.get((game, data['name']), {}).items():
        assert data['points'][name] == after, (name, data['points'][name])
        data['points'][name] = before
        npc = next(obj for obj in data['objects'] if obj['name'] == name)
        assert [npc['x'], npc['y']] == after, (name, npc)
        npc['x'], npc['y'] = before


# Wanderers shown despite a story flag, published after the v1 baseline with
# their wander box and the flag: the Jubilife clowns (lab-B 2026-11-11, 00.05b
# mart_clown). Both fields are undone before digesting.
ADDED_WANDER = {('bdsp', 'JubilifeCity'): {'clown_mart', 'clown_poketch_company'}}


def undo_story_flags_and_wander(game, data):
    for obj in data.get('objects', []):
        if obj['name'] in ADDED_WANDER.get((game, data['name']), set()):
            del obj['wander'], obj['hide_flag']


# Links to maps published after the v1 baseline, as {(game, map): (points,
# warp destinations by tile, connections)}. The v1 pack left these out because
# their destinations weren't in it; the generator writes them once they are.
# They are removed before digesting so every other value still matches v1.
# Route 10's Rock Tunnel entrances and its south edge to Lavender Town.
ADDED_LINKS = {
    ('frlg', 'Route10'): (['warp_0', 'warp_1'], [(8, 19), (8, 57)], ['LavenderTown']),
}


# People published after the v1 baseline, as {(game, map): names}: Route 203's
# youngster at the Oreburgh Gate, whom v1 left out as a wanderer; he stopped
# AutoStory 01.02 on lab-B (2026-11-12). Removed before digesting.
ADDED_PEOPLE = {('bdsp', 'Route203'): {'youngster_0'}}


def undo_added_people(game, data):
    names = ADDED_PEOPLE.get((game, data['name']), set())
    data['objects'] = [o for o in data.get('objects', []) if o['name'] not in names]


# Object movement published after the v1 baseline: every FRLG object's
# `movement` (pret movement_type and range), and the box of each person who
# walks on their own without wandering (walk sequences and back-and-forth
# walkers: Route21_North's swimmer Spencer, 12.03). Both are undone before digesting.
def undo_movement(game, data):
    if game != 'frlg':
        return
    for obj in data.get('objects', []):
        movement = obj.pop('movement', None)
        if movement and not movement['type'].startswith('MOVEMENT_TYPE_WANDER_'):
            obj.pop('wander', None)


def undo_added_links(game, data):
    if (game, data['name']) not in ADDED_LINKS:
        return
    points, warps, connections = ADDED_LINKS[(game, data['name'])]
    for name in points:
        del data['points'][name]
    for warp in data['warps']:
        if (warp['x'], warp['y']) in warps:
            del warp['to_map'], warp['to_point']
    data['connections'] = [c for c in data['connections'] if c['to_map'] not in connections]


# What each approved FRLG map gained when it became generated base + overlays
# (docs/maps/OVERLAYS.md step 1): every source warp and connection linked, their
# arrival points, object provenance and pickup identities, elevation grids left
# out where every walkable tile is ground, water drawn as water, and hidden items
# (data only). Nothing
# else may differ from the reviewed pack, so undoing exactly this must
# reproduce the v1 digests.
FRLG_BASE_DELTA = ROOT / 'src/pokesim/maps/testdata/frlg-v1-to-base-delta.json'
DELTA_KEYS = {'points_added', 'warps_linked', 'connections_added', 'object_fields_added',
              'source_fields_added', 'elevation_omitted', 'water_was_wall', 'hidden_items_added'}


def undo_base_delta(game, data, deltas):
    delta = deltas.get(data['name'], {}) if game == 'frlg' else {}
    assert set(delta) <= DELTA_KEYS, set(delta) - DELTA_KEYS
    if delta.get('hidden_items_added'):
        del data['hidden_items']
    for name in delta.get('points_added', []):
        del data['points'][name]
    for index in delta.get('warps_linked', []):
        del data['warps'][index]['to_map'], data['warps'][index]['to_point']
    if 'connections_added' in delta:
        data['connections'] = [c for c in data['connections'] if c not in delta['connections_added']]
    for obj in data.get('objects', []):
        for field in delta.get('object_fields_added', []):
            obj.pop(field, None)
    for field in delta.get('source_fields_added', []):
        del data['source'][field]
    if 'elevation_omitted' in delta:
        assert 'elevation' not in data and 'elevation_omitted' in delta['source_fields_added']
        data['elevation'] = delta['elevation_omitted']
    for y, row in delta.get('water_was_wall', {}).items():
        now = data['tiles'][int(y)]
        assert all(a == b or (a, b) == ('#', 'w') for a, b in zip(row, now)), y
        data['tiles'][int(y)] = row


def current_world(game, names, context):
    return RuntimeWorld([LocalMap(json.loads((ROOT / 'data/games' / game / 'maps/runtime'
                        / (name + '.json')).read_text()), game,
                        Context(flags=frozenset(context['flags']), variables=context['variables']))
                         for name in names])


class PublicationTest(unittest.TestCase):
    def test_all_published_values_match_reviewed_v1_baseline_and_stable_formatter(self):
        manifest = audit()
        self.assertEqual(manifest['runtime_format'], COMPACT)
        baseline = json.loads(BASELINE.read_text())
        deltas = json.loads(FRLG_BASE_DELTA.read_text())['maps']
        self.assertEqual(set(baseline['games']), set(manifest['games']))
        count = 0
        for game, pack in manifest['games'].items():
            # The v1 baseline covers the approved legacy pack. FRLG maps added as candidates
            # stay generator bytes (frlg_decomp_map_builder --check), also after promotion.
            reviewed = [e for e in pack['maps']
                        if 'status' not in e or e.get('verified', {}).get('basis') == 'approved-runtime-pack']
            self.assertEqual(set(baseline['games'][game]), {e['name'] for e in reviewed})
            for entry in reviewed:
                with self.subTest(game=game, map=entry['name']):
                    raw = (ROOT / entry['file']).read_text()
                    data = json.loads(raw)
                    self.assertEqual(data['format'], COMPACT)
                    baseline_data = legacy_map(data)
                    if game == 'bdsp' and 'item_identities' in baseline_data['source']:
                        # The reviewed publication adds pickup identity/collection
                        # metadata only. All other values still match the v1 baseline.
                        del baseline_data['source']['item_identities']
                        for item in baseline_data.get('objects', []):
                            if item.get('kind') != 'item':
                                continue
                            for field in ('item', 'quantity', 'source_event', 'hide_flag'):
                                item.pop(field, None)
                    undo_base_delta(game, baseline_data, deltas)
                    undo_corrections(game, baseline_data)
                    undo_story_flags_and_wander(game, baseline_data)
                    undo_added_links(game, baseline_data)
                    undo_added_people(game, baseline_data)
                    undo_movement(game, baseline_data)
                    digest = hashlib.sha256(json.dumps(compact_map(baseline_data), sort_keys=True).encode()).hexdigest()
                    self.assertEqual(digest, baseline['games'][game][entry['name']])
                    if game != 'frlg':  # FRLG runtime files are base + overlays in the contract format.
                        self.assertEqual(raw, map_text(data))
                    count += 1
        self.assertEqual(count, 79)

    def test_current_pack_matches_shared_transition_expectations(self):
        for case in read_pack()['cases']:
            value = case['input']
            with self.subTest(case=value['id']):
                self.assertEqual(case['expectation'], run_case(value,
                    current_world(value['game'], value['maps'], value)))

    def test_current_pack_matches_captured_native_recovery_results(self):
        # These are Python replays on new data, not fresh native captures.
        for game, name, module, replay in (('frlg', 'ViridianForest', frlg, frlg.check_case),
                                          ('bdsp', 'Route202', bdsp, bdsp.replay_case)):
            bundle = module.read_bundle()
            historical = module.check_bundle(bundle)
            world = current_world(game, [name], bundle['context'])
            with self.subTest(game=game):
                self.assertEqual([replay(case, world) for case in bundle['cases']], historical)

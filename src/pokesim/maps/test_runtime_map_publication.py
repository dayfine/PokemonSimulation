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
        self.assertEqual(set(baseline['games']), set(manifest['games']))
        count = 0
        for game, pack in manifest['games'].items():
            self.assertEqual(set(baseline['games'][game]), {e['name'] for e in pack['maps']})
            for entry in pack['maps']:
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
                    undo_corrections(game, baseline_data)
                    digest = hashlib.sha256(json.dumps(compact_map(baseline_data), sort_keys=True).encode()).hexdigest()
                    self.assertEqual(digest, baseline['games'][game][entry['name']])
                    self.assertEqual(raw, map_text(data))
                    count += 1
        self.assertEqual(count, 75)

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

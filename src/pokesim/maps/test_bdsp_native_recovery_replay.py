"""Check real native planner facts, independently of its recovery algorithm."""
import copy
import json
from pathlib import Path
import tempfile
import subprocess
import unittest

from .bdsp_native_recovery_replay import (EXPORTER, NATIVE_MAP, capture, check_bundle,
                                          parse_plans, read_bundle, replay_case, verify_native_source)
from .runtime_map_pack import ROOT
from .conformance import make_world


class NativeReplayTests(unittest.TestCase):
    def test_parse_actual_recovery_plan(self):
        # Actual route_plan_line output from the native GridSim/walker export.
        line = ('[Route] native-recovery: plan from Route202 (26, 5), Route202 (27, 5), Route202 (28, 5):\n'
                '    east 4 (to wall) to Route202 (30, 5)\n'
                '    west 2 (open) to Route202 (28, 5)')
        plans = parse_plans([line])
        self.assertEqual([(26, 5), (27, 5), (28, 5)], plans[0]['from'])
        self.assertEqual(dict(direction='east', tiles=4, kind='to wall', after=[(30, 5)]), plans[0]['legs'][0])
        self.assertEqual(dict(direction='west', tiles=2, kind='open', after=[(28, 5)]), plans[0]['legs'][1])

    def test_all_captured_native_cases(self):
        bundle = read_bundle()
        results = check_bundle(bundle)
        self.assertEqual(7, len(results))
        by_id = {r['id']: r for r in results}
        self.assertEqual([(26, 5), (27, 5), (28, 5)], by_id['last-tap-before']['candidate_tiles'])
        self.assertEqual(4, by_id['last-wall-retry-succeeds']['wall_attempts'])
        self.assertFalse(by_id['last-wall-retry-succeeds']['native_failure'])
        self.assertIn('recovery budget', by_id['interrupted-wall-budget']['native_failure'])
        self.assertEqual(0, by_id['reported-unknown-origin']['wall_attempts'])
        self.assertIn('queue_drain', results[0]['unchecked'])

    def test_corrupted_native_facts_do_not_pass(self):
        original = next(c for c in read_bundle()['cases'] if c['id'] == 'last-tap-before')
        pack = read_bundle()
        world = make_world(pack, dict(game='bdsp', maps=['Route202'], **pack['context']))
        changes = [
            lambda c: c['calls'][1]['after'].update(tile=[28, 5]),  # Credit is two; actual motion was one.
            lambda c: c['physical'].update(facing='east'),
            lambda c: c['calls'][0].update(queued=True),
            lambda c: c['calls'][0].update(kind='unknown_input'),
            lambda c: c['input'].update(move_speed='walk'),
            lambda c: c['notes'].pop(),  # No actual arrival record.
            lambda c: c['notes'].__setitem__(next(i for i, n in enumerate(c['notes']) if '(walked).' in n),
                next(n for n in c['notes'] if '(walked).' in n).replace('(walked)', '(assumed)')),
            lambda c: c['notes'].__setitem__(next(i for i, n in enumerate(c['notes']) if '; planning again.' in n),
                next(n for n in c['notes'] if '; planning again.' in n).replace('Route202 (26, 5)', 'Route202 (29, 5)')),
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                case = copy.deepcopy(original)
                change(case)
                with self.assertRaises(ValueError):
                    replay_case(case, world)

    def test_unknown_origin_cannot_claim_arrival(self):
        pack = read_bundle()
        case = copy.deepcopy(next(c for c in pack['cases'] if c['id'] == 'reported-unknown-origin'))
        case['declared'] = [case['input']['goal']]
        with self.assertRaisesRegex(ValueError, 'must not return'):
            replay_case(case, make_world(pack, dict(game='bdsp', maps=['Route202'], **pack['context'])))

    def test_wrong_map_bytes_fail_before_replay(self):
        pack = read_bundle()
        pack['maps'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'map hash mismatch'):
            check_bundle(pack)

    def test_partial_or_duplicate_capture_is_rejected(self):
        pack = read_bundle()
        for cases in (pack['cases'][:-1], pack['cases'] + [pack['cases'][0]]):
            with self.subTest(count=len(cases)), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'trace.json'
                bad = dict(pack, cases=cases)
                path.write_text(json.dumps(bad))
                with self.assertRaisesRegex(ValueError, 'case inventory'):
                    read_bundle(path)

    def test_capture_checks_git_bytes_and_refuses_dirty_native_tree(self):
        # Synthetic Git transport repos; the seven trace payloads remain actual native exports.
        def git(root, *args):
            return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE).decode().strip()

        def commit(root):
            git(root, 'add', '-A')
            git(root, '-c', 'user.name=Trace transport', '-c', 'user.email=trace@example.test', 'commit', '-qm', 'transport fixture')
            return git(root, 'rev-parse', 'HEAD')

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            native, source = root / 'native', root / 'source'
            for repo in (native, source):
                repo.mkdir()
                git(repo, 'init', '-q')
            git(source, 'remote', 'add', 'origin', 'https://github.com/dayfine/PokemonSimulation.git')
            relative = 'data/games/bdsp/maps/runtime/Route202.json'
            for target in (source / relative, native / NATIVE_MAP):
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            exporter = native / EXPORTER
            exporter.parent.mkdir(parents=True, exist_ok=True)
            exporter.write_text('// Synthetic transport fixture, not an executable exporter.\n')
            native_revision = commit(native)
            source_revision = commit(source)
            git(source, 'update-ref', 'refs/remotes/origin/main', source_revision)
            stdout = root / 'stdout.txt'
            stdout.write_text(''.join('POKESIM_NATIVE_REPLAY ' + json.dumps(c) + '\n' for c in read_bundle()['cases']))
            output = root / 'capture.json'
            captured = capture(stdout, native, source, output)
            self.assertEqual(native_revision, captured['native_revision'])
            self.assertEqual(source_revision, captured['map_revision'])
            verify_native_source(captured, native)
            captured['native_exporter']['sha256'] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'exporter checksum'):
                verify_native_source(captured, native)
            before = output.read_bytes()
            exporter.write_text('// Local change must not inherit the old source pin.\n')
            with self.assertRaisesRegex(ValueError, 'clean committed worktree'):
                capture(stdout, native, source, output)
            self.assertEqual(before, output.read_bytes())

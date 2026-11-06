"""Check captured native Forest decisions, including deliberately unsafe controls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from .conformance import make_world
from .frlg_native_recovery_replay import BUNDLE, check_bundle, check_case, read_bundle
from .frlg_native_recovery_text import canonical, read_text, write_text
from .native_recovery_capture import diagnostic_source, format_trace


class ForestNativeReplayTests(unittest.TestCase):
    def test_actual_native_cases_and_controls(self):
        results = {r['id']: r for r in check_bundle(read_bundle())}
        self.assertEqual(6, len(results))
        for shortfall in ('one', 'two'):
            repaired = results['forest-' + shortfall + '-short']
            self.assertEqual('arrived', repaired['status'])
            self.assertTrue(repaired['inserted'])
            self.assertEqual([[7, 28], [8, 28], [9, 28]], repaired['possible_tiles'])
            self.assertEqual(4, repaired['call_count'])
            reused = results['next-wall-' + shortfall + '-short']
            self.assertFalse(reused['inserted'])
            self.assertTrue(reused['next_hold_converges'])
            self.assertEqual(2, reused['call_count'])
        wrong = results['trust-one-short-control']
        self.assertEqual('mislocalized-control', wrong['status'])
        self.assertEqual([8, 33], wrong['physical']['tile'])
        stopped = results['trust-two-short-control']
        self.assertEqual('stopped-control', stopped['status'])
        self.assertEqual(2, stopped['signs'])
        self.assertIn('native_candidate_storage', stopped['unchecked'])

    def test_corrupted_recovery_facts_fail(self):
        bundle = read_bundle()
        world = make_world(bundle, dict(game='frlg', maps=['ViridianForest'], **bundle['context']))
        original = bundle['cases'][0]
        changes = [
            lambda c: c['calls'][1]['after'].update(tile=[4, 28]),
            lambda c: c['calls'][1].update(facing_input='east'),
            lambda c: c['calls'].pop(1),
            lambda c: c['input'].update(shortfall=3),
            lambda c: c['physical'].update(facing='west'),
            lambda c: c['notes'].__setitem__(next(i for i, n in enumerate(c['notes']) if '(walked)' in n),
                next(n for n in c['notes'] if '(walked)' in n).replace('(walked)', '(assumed)')),
            lambda c: c['notes'].pop(next(i for i, n in enumerate(c['notes']) if n.startswith('Route: position check:'))),  # Native shortfall policy diagnostic.
        ]
        for index, change in enumerate(changes):
            with self.subTest(index=index):
                case = copy.deepcopy(original)
                change(case)
                with self.assertRaises(ValueError):
                    check_case(case, world)

    def test_wrong_map_bytes_fail(self):
        bundle = read_bundle()
        bundle['maps'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'map hash mismatch'):
            check_bundle(bundle)

    def test_case_inventory_is_explicit(self):
        bundle = read_bundle()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bundle.json'
            for cases in (bundle['cases'][:-1], bundle['cases'] + [bundle['cases'][0]]):
                path.write_text(json.dumps(dict(bundle, cases=cases)))
                with self.assertRaisesRegex(ValueError, 'case inventory'):
                    read_bundle(path)

    def fixture(self, root):
        bundle = read_bundle(BUNDLE.parent / 'diagnostics/frlg-forest.raw.json')
        path = Path(root) / 'forest.trace'
        write_text(bundle, path, format_trace(bundle))
        return path, bundle

    def test_readable_roundtrip_preserves_checked_native_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, raw = self.fixture(tmp)
            readable = read_bundle(path)
            self.assertEqual(canonical(raw), canonical(readable))
            self.assertEqual(check_bundle(raw), check_bundle(readable))
            self.assertLess(len(path.read_text().splitlines()), 220)
            self.assertIn('signs_read = 0', path.read_text())

    def test_editing_readable_or_raw_facts_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            original = path.read_text()
            path.write_text(original.replace('physical = (7,33) south', 'physical = (8,33) south', 1))
            with self.assertRaisesRegex(ValueError, 'differs from raw'):
                read_text(path)
            path.write_text(original)
            raw, _ = diagnostic_source(path)
            raw.write_bytes(raw.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                read_text(path)

    def test_no_defaults_unknown_fields_or_silent_zeros(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            original = path.read_text()
            for changed in (original.replace('signs_read = 0\n', '', 1),
                            '[DEFAULT]\nsigns_read = 0\n\n' + original,
                            original.replace('shortfall = 1', 'shortfall = 1\nextra = 0', 1)):
                with self.subTest(changed=changed[:50]):
                    path.write_text(changed)
                    with self.assertRaises(ValueError):
                        read_text(path)

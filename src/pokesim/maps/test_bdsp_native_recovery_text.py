"""Readable captures retain the same checked facts and diagnostic provenance."""
import json
from pathlib import Path
import tempfile
import unittest

from .bdsp_native_recovery_replay import BUNDLE, check_bundle, format_trace, read_bundle
from .bdsp_native_recovery_text import canonical, diagnostic_source, read_text, write_text


class ReadableTraceTests(unittest.TestCase):
    def fixture(self, root):
        raw = BUNDLE.parent / 'diagnostics/bdsp-route202.raw.json'
        bundle = read_bundle(raw)
        path = Path(root) / 'capture.trace'
        write_text(bundle, path, format_trace(bundle))
        return path, bundle

    def test_roundtrip_preserves_all_replay_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, raw = self.fixture(tmp)
            readable = read_bundle(path)
            self.assertEqual(json.dumps(canonical(raw), sort_keys=True), json.dumps(canonical(readable), sort_keys=True))
            self.assertEqual(sorted(check_bundle(raw), key=lambda c: c['id']),
                             sorted(check_bundle(readable), key=lambda c: c['id']))
            text = path.read_text()
            self.assertLess(len(text.splitlines()), 200)
            for explicit in ('elevation = 0', 'credited=0', 'queued=false', 'declared = (28,5) ?'):
                self.assertIn(explicit, text)

    def test_changed_readable_fact_must_match_native_diagnostic(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            path.write_text(path.read_text().replace('physical = (28,5) west', 'physical = (27,5) west', 1))
            with self.assertRaisesRegex(ValueError, 'differs from raw'):
                read_text(path)

    def test_raw_diagnostic_bytes_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            raw, _ = diagnostic_source(path)
            raw.write_bytes(raw.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                read_text(path)

    def test_implicit_defaults_and_missing_zeros_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            original = path.read_text()
            for changed in (original.replace('elevation = 0\n', '', 1),
                            '[DEFAULT]\nelevation = 0\n\n' + original):
                with self.subTest(text=changed[:30]):
                    path.write_text(changed)
                    with self.assertRaises(ValueError):
                        read_text(path)

    def test_unknown_fields_and_untyped_booleans_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            original = path.read_text()
            for changed in (original.replace('queued=false', 'queued=false surprise=0', 1),
                            original.replace('queued=false', 'queued=0', 1),
                            original.replace('turn east 50ms', 'teleport east 50ms', 1)):
                with self.subTest(change=changed[:30]):
                    path.write_text(changed)
                    with self.assertRaises(ValueError):
                        read_text(path)

    def test_duplicate_sections_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, _ = self.fixture(tmp)
            path.write_text(path.read_text() + '\n[context]\nmap = Route202\n')
            with self.assertRaises(ValueError):
                read_text(path)

    def test_raw_false_does_not_equal_zero(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            path, bundle = self.fixture(tmp)
            raw, old_checksum = diagnostic_source(path)
            call = next(c for case in bundle['cases'] for c in case['calls']
                        if 'report' in c and c['report']['credited_chunks'] == 0)
            call['report']['credited_chunks'] = False
            raw.write_text(format_trace(bundle))
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()
            path.write_text(path.read_text().replace(old_checksum, digest))
            with self.assertRaisesRegex(ValueError, 'differs from raw'):
                read_text(path)

"""Fixture adoption is immutable, explicit for previews, and drift-safe."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from . import conformance_sync as sync
from .conformance import PACK
from .consumer_source import GitSource
from .runtime_map_pack import ROOT


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.publisher = self.root / 'publisher'
        self.publisher.mkdir()
        self.consumer = self.root / 'consumer'
        self.git('init', '-q')
        self.git('remote', 'add', 'origin', 'https://github.com/dayfine/PokemonSimulation.git')
        pack = json.loads(PACK.read_text())
        for entry in pack['maps']:
            relative = 'data/games/{game}/maps/runtime/{name}.json'.format(**entry)
            path = self.publisher / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / relative).read_bytes())
        self.maps = self.commit()
        self.git('update-ref', 'refs/remotes/origin/main', self.maps)
        pack['map_revision'] = self.maps
        path = self.publisher / sync.SOURCE
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(pack))
        self.revision = self.commit()
        self.source = GitSource(self.publisher)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.publisher), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git('add', '-A')
        self.git('-c', 'user.name=Fixtures', '-c', 'user.email=fixtures@example.test', 'commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def test_preview_requires_opt_in_and_preserves_approved_map_check(self):
        with self.assertRaisesRegex(ValueError, 'not on cached origin/main'):
            sync.update(self.consumer, self.source, self.revision)
        sync.update(self.consumer, self.source, self.revision, preview=True)
        with self.assertRaisesRegex(ValueError, 'explicit --preview'):
            sync.check(self.consumer, self.source)
        sync.check(self.consumer, self.source, preview=True)
        self.git('update-ref', 'refs/remotes/origin/main', self.revision)
        # Promotion requires an explicit update; no silently approved preview.
        promoted = sync.update(self.consumer, self.source, self.revision)
        self.assertEqual('main-approved', promoted['status'])
        sync.check(self.consumer, self.source)

    def test_drift_is_not_overwritten(self):
        sync.update(self.consumer, self.source, self.revision, preview=True)
        target = self.consumer / sync.DEST / 'cases.json'
        target.write_bytes(target.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'drift'):
            sync.update(self.consumer, self.source, self.revision, preview=True)
        self.assertTrue(target.read_bytes().endswith(b'\n'))

    def test_unapproved_map_revision_rejected_even_in_preview(self):
        path = self.publisher / sync.SOURCE
        pack = json.loads(path.read_text())
        pack['map_revision'] = self.revision
        path.write_text(json.dumps(pack))
        with self.assertRaisesRegex(ValueError, 'not on cached origin/main'):
            sync.update(self.consumer, self.source, self.commit(), preview=True)

"""Pinned resource preparation uses the existing export/approval transaction."""

import json
import shutil

from . import consumer_sync as sync
from .consumer_source import lock_entry
from .test_consumer_sync import PublisherFixture


class ResourceTest(PublisherFixture):
    def resource(self, game='bdsp', name='A.json'):
        return self.consumer / sync.RESOURCES.destinations[game] / name

    def adopt(self, games=('bdsp',)):
        return sync.update(self.consumer, self.source, games, self.base, sync.RESOURCES)

    def test_resources_have_exact_maps_pinned_license_and_provenance(self):
        lock = self.adopt(('bdsp', 'frlg'))
        self.assertEqual(sync.check(self.consumer, self.source, sync.RESOURCES), lock)
        self.assertFalse((self.consumer / sync.LOCK).exists())
        self.assertEqual(self.resource(name='LICENSE.txt').read_text(), 'MIT fixture license\n')
        provenance = json.loads(self.resource(name='PROVENANCE.txt').read_bytes())
        self.assertEqual(provenance['revision'], self.base)
        self.assertEqual(set(provenance['maps']), {'A.json', 'B.json'})
        self.assertEqual(provenance['manifest_sha256'], lock['games']['bdsp']['manifest_sha256'])
        for game in ('bdsp', 'frlg'):
            for name in ('A', 'B'):
                self.assertEqual(json.loads(self.resource(game, name + '.json').read_bytes()), self.maps[game][name])

    def test_fresh_prepare_preserves_existing_independent_pins(self):
        self.adopt(('bdsp', 'frlg'))
        self.maps['bdsp']['A']['tiles'] = ['##', '..']
        revision = self.publish()
        sync.update(self.consumer, self.source, ['bdsp'], revision, sync.RESOURCES)
        path = self.consumer / sync.RESOURCES.lock
        before = path.read_bytes()
        for game in ('bdsp', 'frlg'):
            shutil.rmtree(self.resource(game).parent)
        sync.prepare(self.consumer, self.source)
        lock = sync.check(self.consumer, self.source, sync.RESOURCES)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(lock['games']['bdsp']['revision'], revision)
        self.assertEqual(lock['games']['frlg']['revision'], self.base)

    def test_prepare_refuses_drift_partial_exports_and_extra_files(self):
        self.adopt()
        before = (self.consumer / sync.RESOURCES.lock).read_bytes()
        for filename in ('A.json', 'LICENSE.txt', 'PROVENANCE.txt'):
            path = self.resource(name=filename)
            original = path.read_bytes()
            path.write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'modified ' + filename):
                sync.prepare(self.consumer, self.source)
            self.assertEqual(path.read_bytes(), original + b'changed')
            path.write_bytes(original)
        self.resource('bdsp', 'B.json').unlink()
        with self.assertRaisesRegex(ValueError, 'missing B.json'):
            sync.prepare(self.consumer, self.source)
        self.assertEqual((self.consumer / sync.RESOURCES.lock).read_bytes(), before)

    def test_prepare_requires_locked_approved_packs_and_cannot_repin(self):
        with self.assertRaisesRegex(ValueError, 'missing consumer lock'):
            sync.prepare(self.consumer, self.source)
        self.adopt()
        revision = self.publish(approved=False)
        path = self.consumer / sync.RESOURCES.lock
        lock = json.loads(path.read_bytes())
        lock['games']['bdsp'] = dict(lock_entry(self.source, self.base), revision=revision)
        path.write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError, 'not on cached origin/main'):
            sync.prepare(self.consumer, self.source)

    def test_symlink_resource_path_and_unlocked_game_fail(self):
        self.adopt()
        self.resource('frlg').parent.mkdir()
        with self.assertRaisesRegex(ValueError, 'unlocked consumer map directory'):
            sync.prepare(self.consumer, self.source)
        self.resource('frlg').parent.rmdir()
        original = self.resource().read_bytes()
        self.resource().unlink()
        target = self.root / 'elsewhere.json'
        target.write_bytes(original)
        self.resource().symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'unexpected consumer map entry'):
            sync.check(self.consumer, self.source, sync.RESOURCES)

    def test_cmake_configure_uses_prepared_resources_and_fails_on_drift(self):
        import subprocess
        from .runtime_map_pack import ROOT
        self.adopt()
        project = self.root / 'cmake project with spaces'
        project.mkdir()
        helper = ROOT / 'integrations/arduino-source/resource-maps.cmake'
        (project / 'CMakeLists.txt').write_text(
            'cmake_minimum_required(VERSION 3.20)\nproject(ResourceCheck NONE)\n'
            'include("' + helper.as_posix() + '")\n'
            'pa_pokesim_map_directory(MAPS bdsp "' + self.consumer.as_posix()
            + '" "' + self.publisher.as_posix() + '")\n'
            'file(WRITE "${CMAKE_BINARY_DIR}/maps.txt" "${MAPS}")\n')
        def configure():
            return subprocess.run(['cmake', '-S', str(project), '-B', str(project / 'build')],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        result = configure()
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual((project / 'build/maps.txt').read_text(), self.resource().parent.as_posix())
        self.resource().write_bytes(self.resource().read_bytes() + b'\n')
        before = self.snapshot()
        result = configure()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'modified A.json', result.stderr)
        self.assertEqual(self.snapshot(), before)  # Configure never repairs or repins.

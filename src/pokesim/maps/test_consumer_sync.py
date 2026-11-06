"""Exercise the consumer boundary with actual Git history and temporary exports."""

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

from . import consumer_sync as sync
from .runtime_map_coordinates import compact_map
from .consumer_source import GitSource, MANIFEST, lock_entry, published_pack, sha256


class ConsumerTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.publisher = self.root / 'publisher'
        self.publisher.mkdir()
        self.consumer = self.root / 'consumer'
        self.consumer.mkdir()
        self.git('init', '-q')
        self.git('remote', 'add', 'origin', 'https://github.com/dayfine/PokemonSimulation.git')
        self.maps = {}
        for game in ('bdsp', 'frlg'):
            self.maps[game] = {name: dict(name=name, source=dict(decomp_file='fixture', revision='fixed', date='test'),
                tiles=['..', '..'], points={'door': [0, 0]},
                objects=[dict(name='npc', kind='npc', x=1, y=1)]) for name in ('A', 'B')}
        self.base = self.publish()
        self.source = GitSource(self.publisher)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.publisher), *args], stderr=subprocess.PIPE).decode().strip()

    def commit(self, approved=True):
        self.git('add', '-A')
        self.git('-c', 'user.name=Map test', '-c', 'user.email=maps@example.test',
                 'commit', '--allow-empty', '-qm', 'map fixture')
        revision = self.git('rev-parse', 'HEAD')
        if approved:
            self.git('update-ref', 'refs/remotes/origin/main', revision)
        return revision

    def publish(self, change_manifest=None, approved=True):
        manifest = dict(format='pokesim-map-pack/1', runtime_format='pokesim-runtime-map/1', games={})
        for game, maps in self.maps.items():
            directory = self.publisher / f'data/games/{game}/maps/runtime'
            directory.mkdir(parents=True, exist_ok=True)
            for path in directory.glob('*.json'):
                path.unlink()
            entries = []
            for name, data in maps.items():
                path = directory / (name + '.json')
                raw = (json.dumps(data) + '\n').encode()
                path.write_bytes(raw)
                entries.append(dict(name=name, file=path.relative_to(self.publisher).as_posix(),
                                    sha256=sha256(raw), source=data['source']))
            manifest['games'][game] = dict(maps=entries)
        if change_manifest:
            change_manifest(manifest)
        path = self.publisher / MANIFEST
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(manifest) + '\n')
        return self.commit(approved)

    def initialize(self, games=('bdsp',)):
        return sync.update(self.consumer, self.source, games, self.base)

    def map_path(self, name='A', game='bdsp'):
        return self.consumer / sync.DESTINATIONS[game] / (name + '.json')

    def snapshot(self):
        return {p.relative_to(self.consumer).as_posix(): p.read_bytes()
                for p in self.consumer.rglob('*') if p.is_file()}

    def rewrite_lock(self, change):
        path = self.consumer / sync.LOCK
        lock = json.loads(path.read_text())
        change(lock)
        path.write_text(json.dumps(lock))

    def test_initialize_check_and_independent_game_update(self):
        self.initialize(('bdsp', 'frlg'))
        old_frlg = self.map_path(game='frlg').read_bytes()
        del self.maps['bdsp']['A']
        self.maps['bdsp']['C'] = dict(self.maps['bdsp']['B'], name='C')
        revision = self.publish()
        sync.update(self.consumer, self.source, ['bdsp'], revision)
        lock = sync.check(self.consumer, self.source)
        self.assertEqual(lock['games']['bdsp']['revision'], revision)
        self.assertEqual(lock['games']['frlg']['revision'], self.base)
        self.assertFalse(self.map_path().exists())
        self.assertTrue(self.map_path('C').exists())
        self.assertEqual(self.map_path(game='frlg').read_bytes(), old_frlg)

    def test_changed_points_objects_triggers_and_metadata_are_drift(self):
        self.initialize()
        path = self.map_path()
        original = path.read_bytes()
        changes = [dict(tiles=['#.', '..']), dict(points={'door': [1, 0]}),
                   dict(objects=[]), dict(patches=[dict(x=0, y=0, glyph='#', measured_by='test')]),
                   dict(coord_events=[dict(x=0, y=0, width=1, length=1, var='x', value=0)]),
                   dict(source=dict(decomp_file='changed', revision='fixed', date='test'))]
        for change in changes:
            with self.subTest(change=change):
                data = json.loads(original)
                data.update(change)
                path.write_text(json.dumps(data))
                before = self.snapshot()
                with self.assertRaisesRegex(ValueError, 'modified A.json'):
                    sync.check(self.consumer, self.source)
                self.assertEqual(self.snapshot(), before)
        path.write_bytes(original)
        sync.check(self.consumer, self.source)

    def test_missing_and_extra_inventory(self):
        self.initialize()
        self.map_path().unlink()
        self.map_path('Unexpected').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'missing A.json\nbdsp: extra Unexpected.json'):
            sync.check(self.consumer, self.source)

    def test_local_manifest_and_rehashed_lock_cannot_approve_edits(self):
        self.initialize()
        self.map_path().write_text('{}')
        forged = self.consumer / MANIFEST
        forged.parent.mkdir(parents=True)
        forged.write_text('{"games": {"bdsp": {"maps": []}}}')
        self.rewrite_lock(lambda lock: lock['games']['bdsp'].update(manifest_sha256=sha256(forged.read_bytes())))
        with self.assertRaisesRegex(ValueError, 'published manifest hash mismatch'):
            sync.check(self.consumer, self.source)

    def test_checkout_edits_in_source_do_not_change_published_git_objects(self):
        self.initialize()
        (self.publisher / MANIFEST).write_text('broken local manifest')
        (self.publisher / 'data/games/bdsp/maps/runtime/A.json').write_text('broken local map')
        sync.check(self.consumer, self.source)

    def test_unknown_repo_mutable_revision_and_unmerged_commit_rejected(self):
        self.initialize()
        original = (self.consumer / sync.LOCK).read_bytes()
        for change, message in [
            (lambda lock: lock.update(repository='other/repo'), 'repository'),
            (lambda lock: lock['games']['bdsp'].update(revision='main'), 'full lowercase'),
        ]:
            with self.subTest(message=message):
                (self.consumer / sync.LOCK).write_bytes(original)
                self.rewrite_lock(change)
                with self.assertRaisesRegex(ValueError, message):
                    sync.check(self.consumer, self.source)
        candidate = self.publish(approved=False)
        with self.assertRaisesRegex(ValueError, 'not on cached origin/main'):
            lock_entry(self.source, candidate)

    def test_published_hash_schema_duplicate_name_and_path_errors(self):
        for change in ('hash', 'format', 'duplicate', 'path', 'empty'):
            with self.subTest(change=change):
                def edit(manifest):
                    entries = manifest['games']['bdsp']['maps']
                    if change == 'hash': entries[0]['sha256'] = '0' * 64
                    if change == 'format': manifest['runtime_format'] = 'unsupported/99'
                    if change == 'duplicate': entries.append(copy.deepcopy(entries[0]))
                    if change == 'path': entries[0]['file'] = '../elsewhere.json'
                    if change == 'empty': entries.clear()
                revision = self.publish(edit)
                with self.assertRaises(ValueError):
                    published_pack(self.source, 'bdsp', lock_entry(self.source, revision))

    def test_v2_map_cannot_hide_under_a_legacy_manifest(self):
        self.maps['bdsp']['A'] = compact_map(self.maps['bdsp']['A'])
        revision = self.publish()
        with self.assertRaisesRegex(ValueError, 'map/manifest runtime format mismatch'):
            published_pack(self.source, 'bdsp', lock_entry(self.source, revision))

    def test_approved_v2_pack_updates_and_preserves_independent_v1_pin(self):
        self.initialize(('bdsp', 'frlg'))
        old_frlg = self.map_path(game='frlg').read_bytes()
        self.maps['bdsp'] = {name: compact_map(data) for name, data in self.maps['bdsp'].items()}
        # Only the selected game becomes v2 at this publisher revision.
        self.maps['frlg'] = {name: compact_map(data) for name, data in self.maps['frlg'].items()}
        revision = self.publish(lambda m: m.update(runtime_format='pokesim-runtime-map/2'))
        sync.update(self.consumer, self.source, ['bdsp'], revision)
        lock = sync.check(self.consumer, self.source)
        self.assertEqual(lock['games']['bdsp']['revision'], revision)
        self.assertEqual(lock['games']['frlg']['revision'], self.base)
        self.assertEqual(self.map_path(game='frlg').read_bytes(), old_frlg)
        self.assertEqual(json.loads(self.map_path().read_bytes()), self.maps['bdsp']['A'])
        self.map_path().write_bytes(self.map_path().read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'modified A.json'):
            sync.check(self.consumer, self.source)

    def test_v1_map_cannot_hide_under_a_v2_manifest(self):
        revision = self.publish(lambda m: m.update(runtime_format='pokesim-runtime-map/2'))
        with self.assertRaisesRegex(ValueError, 'map/manifest runtime format mismatch'):
            published_pack(self.source, 'bdsp', lock_entry(self.source, revision))

    def test_extra_published_file_not_in_manifest_is_rejected(self):
        (self.publisher / 'data/games/bdsp/maps/runtime/Extra.json').write_text('{}')
        revision = self.commit()
        with self.assertRaisesRegex(ValueError, 'published inventory'):
            published_pack(self.source, 'bdsp', lock_entry(self.source, revision))

    def test_new_game_cannot_be_hidden_by_removing_lock_entry(self):
        self.initialize(('bdsp', 'frlg'))
        self.rewrite_lock(lambda lock: lock['games'].pop('frlg'))
        with self.assertRaisesRegex(ValueError, 'unlocked consumer map directory: frlg'):
            sync.check(self.consumer, self.source)

    def test_retired_builder_reappearing_fails(self):
        self.initialize()
        path = self.consumer / sync.RETIRED['bdsp'][0]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('# duplicate builder')
        with self.assertRaisesRegex(ValueError, 'retired map authoring module'):
            sync.check(self.consumer, self.source)

    def test_symlink_never_follows_or_replaces_external_map(self):
        self.initialize()
        external = self.root / 'external.json'
        external.write_text('do not touch')
        self.map_path().unlink()
        self.map_path().symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'unexpected consumer map entry'):
            sync.update(self.consumer, self.source, ['bdsp'], self.base)
        self.assertEqual(external.read_text(), 'do not touch')

    def test_update_refuses_local_edits_without_changing_any_files(self):
        self.initialize()
        self.map_path().write_text('pending local correction')
        before = self.snapshot()
        revision = self.publish()
        with self.assertRaisesRegex(ValueError, 'modified A.json'):
            sync.update(self.consumer, self.source, ['bdsp'], revision)
        self.assertEqual(self.snapshot(), before)

    def test_first_adoption_refuses_existing_unreviewed_maps(self):
        self.map_path().parent.mkdir(parents=True)
        self.map_path().write_text('pending local correction')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'review local differences first'):
            self.initialize()
        self.assertEqual(self.snapshot(), before)

    def test_failed_second_directory_swap_rolls_back_maps_and_lock(self):
        self.initialize(('bdsp', 'frlg'))
        before = self.snapshot()
        self.maps['bdsp']['A']['tiles'] = ['#.', '..']
        self.maps['frlg']['A']['tiles'] = ['.#', '..']
        revision = self.publish()
        rename = Path.rename
        destination = self.map_path(game='frlg').parent.resolve()
        def fail_second(path, target):
            if path.name == 'new' and target == destination:
                raise OSError('simulated disk error')
            return rename(path, target)
        with mock.patch.object(Path, 'rename', fail_second), self.assertRaisesRegex(OSError, 'disk error'):
            sync.update(self.consumer, self.source, ['bdsp', 'frlg'], revision)
        self.assertEqual(self.snapshot(), before)
        sync.check(self.consumer, self.source)

    def test_duplicate_lock_keys_are_rejected(self):
        self.initialize()
        path = self.consumer / sync.LOCK
        path.write_text('{"games": {}, "games": {}}')
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            sync.check(self.consumer, self.source)

    def test_cli_refreshes_by_default_and_offline_failure_is_read_only(self):
        self.initialize()
        args = ['check', '--consumer', str(self.consumer), '--source', str(self.publisher)]
        with mock.patch.object(GitSource, 'refresh') as refresh, redirect_stdout(io.StringIO()):
            sync.main(args)
            refresh.assert_called_once_with()
        self.map_path().write_text('local edit')
        before = self.snapshot()
        errors = io.StringIO()
        with mock.patch.object(GitSource, 'refresh') as refresh, redirect_stderr(errors):
            with self.assertRaises(SystemExit) as result:
                sync.main(args + ['--offline'])
            self.assertEqual(result.exception.code, 1)
            refresh.assert_not_called()
        self.assertIn('modified A.json', errors.getvalue())
        self.assertEqual(self.snapshot(), before)


if __name__ == '__main__':
    unittest.main()

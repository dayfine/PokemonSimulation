"""Historical replay maps remain exact across publication changes and shallow clones."""

import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest

from .pinned_runtime_map import read_pinned_map


class PinnedMapTest(unittest.TestCase):
    def test_current_and_historical_bytes_are_verified_without_changing_the_worktree(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'data/games/bdsp/maps/runtime/Test.json'
            path.parent.mkdir(parents=True)
            original = b'{"historical": true}\n'
            path.write_bytes(original)
            digest = hashlib.sha256(original).hexdigest()
            def git(*args):
                return subprocess.check_output(['git', '-C', folder, *args], stderr=subprocess.PIPE).decode().strip()
            git('init', '-q')
            git('add', '.')
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'pin')
            revision = git('rev-parse', 'HEAD')
            self.assertEqual(read_pinned_map(revision, 'bdsp', 'Test', digest, root), original)
            current = b'{"new_publication": true}\n'
            path.write_bytes(current)
            self.assertEqual(read_pinned_map(revision, 'bdsp', 'Test', digest, root), original)
            self.assertEqual(path.read_bytes(), current)
            with self.assertRaisesRegex(ValueError, 'map hash mismatch at historical pin'):
                read_pinned_map(revision, 'bdsp', 'Test', '0' * 64, root)
            with self.assertRaisesRegex(ValueError, 'provide local Git history'):
                read_pinned_map('0' * 40, 'bdsp', 'Test', digest, root)
            with self.assertRaisesRegex(ValueError, 'invalid historical map pin'):
                read_pinned_map('HEAD', 'bdsp', 'Test', digest, root)

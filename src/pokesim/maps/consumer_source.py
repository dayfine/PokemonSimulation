"""Read a published map pack from immutable Git objects, never checkout files."""

import hashlib
import json
from pathlib import Path
import re
import subprocess

from .runtime_map_schema import validate
from .runtime_map_coordinates import COMPACT, LEGACY


REPOSITORY = 'dayfine/PokemonSimulation'
MANIFEST = 'data/maps/runtime-manifest.json'
SHA = re.compile(r'[0-9a-f]{40}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
NAME = re.compile(r'[A-Za-z0-9_]+\Z')
GAMES = ('bdsp', 'frlg')


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


class GitSource:
    """A trusted cache of the publishing repository, with an approved main tip.

    CLI callers refresh by default. Offline use explicitly trusts the cache's
    origin/main ref; it cannot establish freshness or remote authenticity.
    """

    def __init__(self, root):
        self.root = Path(root).resolve()
        origin = self.git('remote', 'get-url', 'origin').decode().strip()
        if origin not in (f'https://github.com/{REPOSITORY}.git',
                          f'https://github.com/{REPOSITORY}',
                          f'git@github.com:{REPOSITORY}.git'):
            raise ValueError('source origin must be ' + REPOSITORY)

    def git(self, *args):
        result = subprocess.run(['git', '-C', str(self.root), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode:
            raise ValueError('source git: ' + result.stderr.decode(errors='replace').strip())
        return result.stdout

    def refresh(self):
        if self.git('rev-parse', '--is-shallow-repository').strip() == b'true':
            raise ValueError('source cache is shallow; fetch full history before verifying ancestry')
        self.git('fetch', '--no-tags', 'origin', '+refs/heads/main:refs/remotes/origin/main')

    def approved(self, revision):
        if not isinstance(revision, str) or not SHA.fullmatch(revision):
            raise ValueError('revision must be a full lowercase commit SHA')
        if self.git('cat-file', '-t', revision).strip() != b'commit':
            raise ValueError('revision is not a commit')
        try:
            self.git('merge-base', '--is-ancestor', revision, 'refs/remotes/origin/main')
        except ValueError:
            raise ValueError('revision is not on cached origin/main (or ancestry is unavailable): ' + revision)

    def files(self, revision, directory):
        """Map relative paths to blob IDs; reject symlinks and non-file entries."""
        entries = self.git('ls-tree', '-rz', revision, '--', directory).split(b'\0')
        result = {}
        for entry in entries:
            if not entry:
                continue
            metadata, path = entry.split(b'\t', 1)
            mode, kind, oid = metadata.decode().split()
            if mode != '100644' or kind != 'blob':
                raise ValueError('source must contain regular files: ' + path.decode())
            result[path.decode()] = oid
        return result

    def read(self, revision, path):
        entries = self.files(revision, path)
        if path not in entries or len(entries) != 1:
            raise ValueError('missing source file: ' + path)
        return self.git('cat-file', 'blob', entries[path])


def lock_entry(source, revision):
    source.approved(revision)
    return dict(revision=revision, manifest_path=MANIFEST,
                manifest_sha256=sha256(source.read(revision, MANIFEST)))


def published_pack(source, game, pin):
    """Return verified filename -> bytes for the selected, approved game pack."""
    if game not in GAMES:
        raise ValueError('unknown game: ' + game)
    if not isinstance(pin, dict) or set(pin) != {'revision', 'manifest_path', 'manifest_sha256'}:
        raise ValueError('invalid pin fields: ' + game)
    if pin['manifest_path'] != MANIFEST or not isinstance(pin['manifest_sha256'], str) or not DIGEST.fullmatch(pin['manifest_sha256']):
        raise ValueError('invalid manifest path/hash: ' + game)
    revision = pin['revision']
    source.approved(revision)
    raw = source.read(revision, MANIFEST)
    if sha256(raw) != pin['manifest_sha256']:
        raise ValueError('published manifest hash mismatch: ' + game)
    manifest = read_json(raw)
    if not isinstance(manifest, dict) or manifest.get('format') != 'pokesim-map-pack/1' or manifest.get('runtime_format') not in (LEGACY, COMPACT):
        raise ValueError('unsupported map manifest/runtime format')
    if not isinstance(manifest.get('games'), dict) or game not in manifest['games']:
        raise ValueError('game not published: ' + game)
    directory = f'data/games/{game}/maps/runtime'
    entries = manifest['games'][game]['maps']
    if not isinstance(entries, list) or not entries:
        raise ValueError('empty or invalid published pack: ' + game)
    files = source.files(revision, directory)
    result = {}
    expected_paths = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('invalid published map entry')
        name = entry.get('name')
        if not isinstance(name, str) or not NAME.fullmatch(name) or name + '.json' in result:
            raise ValueError('invalid/duplicate published map name: ' + repr(name))
        path = f'{directory}/{name}.json'
        if entry.get('file') != path:
            raise ValueError('unexpected published path: ' + repr(entry.get('file')))
        expected_paths.add(path)
        if path not in files:
            raise ValueError('missing published map: ' + path)
        content = source.git('cat-file', 'blob', files[path])
        if sha256(content) != entry.get('sha256'):
            raise ValueError('published map hash mismatch: ' + path)
        data = validate(read_json(content))
        if data.get('format', LEGACY) != manifest['runtime_format']:
            raise ValueError('map/manifest runtime format mismatch: ' + path)
        if data['name'] != name or data['source'] != entry.get('source'):
            raise ValueError('published map identity/source mismatch: ' + path)
        result[name + '.json'] = content
    if set(files) != expected_paths:
        raise ValueError('published inventory differs from manifest: ' + game)
    return result

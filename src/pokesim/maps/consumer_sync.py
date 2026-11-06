r"""Check or update Arduino's pinned map exports. Check never modifies files.

From the PokemonSimulation root, initialize an empty trial consumer directory:

    PYTHONPATH=src python3 -m pokesim.maps.consumer_sync update \
        --source . --consumer /tmp/pokesim-consumer --game bdsp --game frlg \
        --revision d139398d48ee831da540b901e6700c6ba5dbb32c
    PYTHONPATH=src python3 -m pokesim.maps.consumer_sync check \
        --source . --consumer /tmp/pokesim-consumer

Resource staging (prepare reads an existing approved resource lock):
    PYTHONPATH=src python3 -m pokesim.maps.consumer_sync prepare \
        --layout resources --source . --consumer /path/to/Arduino-Source --offline

Use --offline only with a trusted cache. See integrations/arduino-source/README.md.
"""

import argparse
from contextlib import ExitStack
from dataclasses import dataclass
import json
from pathlib import Path
import shutil
import tempfile

from .consumer_source import GAMES, REPOSITORY, GitSource, lock_entry, published_pack, read_json, sha256


LOCK = 'devtools/maps/map-packs.lock.json'
DESTINATIONS = {
    'bdsp': 'SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Maps',
    'frlg': 'SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/Maps',
}
RETIRED = {
    'bdsp': ('devtools/maps/bdsp_maps.py', 'devtools/maps/decomp.py'),
    'frlg': ('devtools/maps/frlg_maps.py',),
}


@dataclass(frozen=True)
class ExportLayout:
    """Fixed consumer paths and lock identity; paths never come from lock data."""
    lock: str
    format: str
    destinations: dict
    retired: dict
    resources: bool = False


EMBEDDED = ExportLayout(LOCK, 'pokesim-map-lock/1', DESTINATIONS, RETIRED)
RESOURCES = ExportLayout('devtools/maps/map-resources.lock.json', 'pokesim-map-resource-lock/1',
    {game: 'Packages/Resources/Pokemon/Maps/' + game for game in GAMES},
    {game: () for game in GAMES}, resources=True)


def export_pack(source, game, pin, layout):
    """Verified map bytes, plus pinned license/provenance for resource exports."""
    files = published_pack(source, game, pin)
    if layout.resources:
        provenance = dict(format='pokesim-map-resource/1', repository=REPOSITORY, game=game,
                          **pin, maps={name: sha256(raw)
                                       for name, raw in sorted(files.items())})
        files['LICENSE.txt'] = source.read(pin['revision'], 'LICENSE')
        files['PROVENANCE.txt'] = (json.dumps(provenance, indent=2) + '\n').encode()
    return files


def safe_path(root, relative):
    root = Path(root).resolve()
    path = root
    for part in Path(relative).parts:
        if part in ('..', '.') or Path(part).is_absolute():
            raise ValueError('invalid consumer path: ' + relative)
        path = path / part
        if path.is_symlink():
            raise ValueError('symlink in consumer path: ' + relative)
    return path


def read_lock(root, layout=EMBEDDED):
    path = safe_path(root, layout.lock)
    if not path.is_file():
        raise ValueError('missing consumer lock: ' + layout.lock)
    lock = read_json(path.read_bytes())
    if not isinstance(lock, dict) or set(lock) != {'format', 'repository', 'games'}:
        raise ValueError('invalid lock fields')
    if lock['format'] != layout.format or lock['repository'] != REPOSITORY:
        raise ValueError('unsupported lock format/repository')
    if not isinstance(lock['games'], dict) or not lock['games'] or not set(lock['games']) <= set(GAMES):
        raise ValueError('invalid/empty lock games')
    return lock


def inventory(root, game, layout=EMBEDDED):
    directory = safe_path(root, layout.destinations[game])
    if not directory.exists():
        return {}
    if not directory.is_dir():
        raise ValueError('map destination is not a directory: ' + str(directory))
    result = {}
    for path in sorted(directory.iterdir()):
        if path.is_symlink() or not path.is_file() or (path.suffix != '.json' and not (layout.resources and path.name in ('LICENSE.txt', 'PROVENANCE.txt'))):
            raise ValueError('unexpected consumer map entry: ' + str(path))
        result[path.name] = path.read_bytes()
    return result


def differences(root, game, expected, layout=EMBEDDED):
    actual = inventory(root, game, layout)
    result = []
    result += [f'{game}: missing {name}' for name in sorted(set(expected) - set(actual))]
    result += [f'{game}: extra {name}' for name in sorted(set(actual) - set(expected))]
    result += [f'{game}: modified {name}' for name in sorted(set(actual) & set(expected))
               if actual[name] != expected[name]]
    return result


def ownership_errors(root, games, layout=EMBEDDED):
    return ['retired map authoring module: ' + path
            for game in games for path in layout.retired[game] if safe_path(root, path).exists()]


def check(root, source, layout=EMBEDDED):
    lock = read_lock(root, layout)
    errors = ownership_errors(root, lock['games'], layout)
    for game in GAMES:
        if game not in lock['games']:
            if safe_path(root, layout.destinations[game]).exists():
                errors.append('unlocked consumer map directory: ' + game)
            continue
        pin = lock['games'][game]
        expected = export_pack(source, game, pin, layout)
        errors.extend(differences(root, game, expected, layout))
    if errors:
        raise ValueError('\n'.join(errors))
    return lock


def replace_exports(root, packs, lock, layout=EMBEDDED):
    """Stage complete directories, swap them, then atomically replace the lock.

    Roll back swapped directories on an ordinary I/O failure. A process kill
    between swaps still fails integrity under the old lock; no false success.
    """
    with ExitStack() as stack:
        staged = []
        for game, files in packs.items():
            destination = safe_path(root, layout.destinations[game])
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = Path(stack.enter_context(tempfile.TemporaryDirectory(
                prefix='.pokesim-maps-', dir=str(destination.parent))))
            new = temporary / 'new'
            new.mkdir()
            for name, raw in files.items():
                (new / name).write_bytes(raw)
            staged.append((destination, new, temporary / 'old'))
        lock_path = safe_path(root, layout.lock)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(stack.enter_context(tempfile.TemporaryDirectory(
            prefix='.pokesim-lock-', dir=str(lock_path.parent))))
        new_lock = temporary / 'lock.json'
        new_lock.write_bytes((json.dumps(lock, indent=2) + '\n').encode('utf-8'))
        swapped = []
        try:
            for destination, new, old in staged:
                if destination.exists():
                    destination.rename(old)
                swapped.append((destination, old))
                new.rename(destination)
            new_lock.replace(lock_path)
        except OSError:
            for destination, old in reversed(swapped):
                if destination.exists():
                    shutil.rmtree(destination)
                if old.exists():
                    old.rename(destination)
            raise


def update(root, source, games, revision, layout=EMBEDDED):
    """Update clean locked exports; initialize only empty or matching copies.

    Unrecorded map edits and retired generators are never silently removed.
    Source validation completes before changing consumer files.
    """
    if not games or not set(games) <= set(GAMES) or len(set(games)) != len(games):
        raise ValueError('select each known game once')
    lock_path = safe_path(root, layout.lock)
    if lock_path.exists():
        lock = check(root, source, layout)
    else:
        lock = dict(format=layout.format, repository=REPOSITORY, games={})
    pin = lock_entry(source, revision)
    packs = {game: export_pack(source, game, pin, layout) for game in games}
    errors = ownership_errors(root, games, layout)
    for game in GAMES:
        if game not in games and game not in lock['games'] and safe_path(root, layout.destinations[game]).exists():
            errors.append('unlocked consumer map directory: ' + game)
        if game in games and game not in lock['games'] and inventory(root, game, layout):
            errors.extend(differences(root, game, packs[game], layout))
    if errors:
        raise ValueError('cannot adopt/update; review local differences first:\n' + '\n'.join(errors))
    for game in games:
        lock['games'][game] = dict(pin)
    replace_exports(root, packs, lock, layout)
    return lock


def prepare(root, source):
    """Materialize an existing resource lock; refuse partial or modified exports."""
    lock = read_lock(root, RESOURCES)
    packs = {game: export_pack(source, game, pin, RESOURCES) for game, pin in lock['games'].items()}
    errors = []
    for game in GAMES:
        if game in packs:
            if inventory(root, game, RESOURCES):
                errors.extend(differences(root, game, packs[game], RESOURCES))
        elif safe_path(root, RESOURCES.destinations[game]).exists():
            errors.append('unlocked consumer map directory: ' + game)
    if errors:
        raise ValueError('cannot prepare; review local differences first:\n' + '\n'.join(errors))
    replace_exports(root, packs, lock, RESOURCES)
    return lock


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=('check', 'update', 'compare', 'prepare'))
    parser.add_argument('--layout', choices=('embedded', 'resources'), default='embedded')
    parser.add_argument('--consumer', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True, help='PokemonSimulation Git checkout/cache')
    parser.add_argument('--offline', action='store_true', help='trust cached origin/main; do not fetch')
    parser.add_argument('--game', action='append', choices=GAMES)
    parser.add_argument('--revision', help='full publishing commit, reachable from source origin/main')
    args = parser.parse_args(argv)
    layout = RESOURCES if args.layout == 'resources' else EMBEDDED
    if args.command == 'prepare' and layout != RESOURCES:
        parser.error('prepare requires --layout resources')
    if args.command in ('check', 'prepare') and (args.game or args.revision):
        parser.error('check reads all games/revisions from the lock')
    if args.command not in ('check', 'prepare') and (not args.game or not args.revision):
        parser.error('update/compare require --game and --revision')
    try:
        source = GitSource(args.source)
        if not args.offline:
            source.refresh()
        if args.command == 'check':
            lock = check(args.consumer, source, layout)
        elif args.command == 'prepare':
            lock = prepare(args.consumer, source)
        elif args.command == 'update':
            lock = update(args.consumer, source, args.game, args.revision, layout)
        else:
            pin = lock_entry(source, args.revision)
            errors = ownership_errors(args.consumer, args.game, layout)
            for game in args.game:
                errors.extend(differences(args.consumer, game, export_pack(source, game, pin, layout), layout))
            if errors:
                raise ValueError('\n'.join(errors))
            lock = dict(games={game: pin for game in args.game})
        for game, pin in lock['games'].items():
            print(f'{game}: verified {pin["revision"]} manifest {pin["manifest_sha256"]}')
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

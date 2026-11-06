r"""Compare checked-in simulation maps with an immutable Arduino map snapshot.

    PYTHONPATH=src python3 -m pokesim.maps.map_parity \
        --arduino-source /path/to/Arduino-Source --game bdsp \
        --revision 01e6659116f520b51c35ee956aa6a222dfa864f8

Read-only: reports byte drift separately from decoded JSON drift. It never
imports corrections, changes a pin or treats a semantic match as integrity proof.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from .consumer_source import read_json
from .runtime_map_coordinates import legacy_map
from .runtime_map_pack import ROOT


DIRECTORIES = {
    'bdsp': 'SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Maps',
    'frlg': 'SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/Maps',
}


def _git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError(result.stderr.decode(errors='replace').strip())
    return result.stdout


def read_map_tree(root, revision, directory):
    """Read regular JSON blobs at one full commit SHA without touching its worktree."""
    if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('revision must be a full lowercase commit SHA')
    if _git(root, 'cat-file', '-t', revision).strip() != b'commit':
        raise ValueError('revision must identify a commit')
    entries = _git(root, 'ls-tree', '-rz', revision, '--', directory).split(b'\0')
    maps = {}
    for entry in entries:
        if not entry:
            continue
        metadata, path = entry.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        relative = Path(path.decode()).relative_to(directory)
        if mode != '100644' or kind != 'blob' or len(relative.parts) != 1 or relative.suffix != '.json':
            raise ValueError('expected regular map JSON: ' + path.decode())
        maps[relative.name] = _git(root, 'cat-file', 'blob', oid)
    if not maps:
        raise ValueError('no map JSON at ' + revision + ':' + directory)
    return maps


def compare_maps(expected, actual):
    """Compare filename->bytes maps; identify formatting versus field/terrain drift."""
    result = []
    for name in sorted(set(expected) | set(actual)):
        if name not in actual:
            result.append(dict(name=name, status='missing'))
            continue
        if name not in expected:
            result.append(dict(name=name, status='extra'))
            continue
        before, after = expected[name], actual[name]
        if before == after:
            continue
        left, right = legacy_map(read_json(before)), legacy_map(read_json(after))
        fields = sorted(key for key in set(left) | set(right)
                        if key not in left or key not in right or left[key] != right[key])
        row = dict(name=name, status='content-drift' if fields else 'format-only', fields=fields,
                   simulation_sha256=hashlib.sha256(before).hexdigest(),
                   arduino_sha256=hashlib.sha256(after).hexdigest())
        if 'tiles' in fields:
            old, new = left.get('tiles', []), right.get('tiles', [])
            row['changed_tile_rows'] = [i for i in range(max(len(old), len(new)))
                                        if i >= len(old) or i >= len(new) or old[i] != new[i]]
        result.append(row)
    return dict(simulation_maps=len(expected), arduino_maps=len(actual),
                identical_bytes=sum(expected[n] == actual[n] for n in set(expected) & set(actual)),
                differences=result)


def report(arduino_source, game, revision, simulation_root=ROOT):
    expected = {p.name: p.read_bytes() for p in
                (Path(simulation_root) / 'data/games' / game / 'maps/runtime').glob('*.json')}
    if not expected:
        raise ValueError('no simulation maps for ' + game)
    actual = read_map_tree(arduino_source, revision, DIRECTORIES[game])
    return dict(game=game, arduino_revision=revision,
                simulation_revision=_git(simulation_root, 'rev-parse', 'HEAD').decode().strip(),
                **compare_maps(expected, actual))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--arduino-source', required=True, type=Path)
    parser.add_argument('--game', required=True, choices=tuple(DIRECTORIES))
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    print(json.dumps(report(args.arduino_source, args.game, args.revision), indent=2))


if __name__ == '__main__':
    main()

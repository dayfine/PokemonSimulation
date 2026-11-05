r"""Lossless runtime maps, correction application and audited pack export.

This is not the pokenav-map/1 loader. In particular, 8/2/4/6 mean closed
tile sides here, not forced movement. Unknown JSON fields are preserved.

From the repository root (export requires an empty destination):

    PYTHONPATH=src python3 -m pokesim.maps.runtime_map_pack
    PYTHONPATH=src python3 -m pokesim.maps.runtime_map_pack \
        --export-game frlg --out /tmp/frlg-map-export
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil

from .runtime_map_schema import validate


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'data/maps/runtime-manifest.json'


def load(path):
    """Read and validate raw JSON; all fields survive a round trip."""
    return validate(json.loads(Path(path).read_text()))


def effective_map(data):
    """Apply recorded patches in order to a copy; keep raw source unmodified.

    Story flags and dynamic NPC occupancy are not evaluated by this loader.
    """
    validate(data)
    result = copy.deepcopy(data)
    rows = [list(row) for row in data['tiles']]
    for patch in data.get('patches', []):
        rows[patch['y']][patch['x']] = patch['glyph']
    result['tiles'] = [''.join(row) for row in rows]
    return result


def audit(manifest_path=MANIFEST):
    """Verify bytes, map identities, pack inventory and resolved graph edges."""
    manifest = json.loads(Path(manifest_path).read_text())
    for game, pack in manifest['games'].items():
        maps = {}
        for entry in pack['maps']:
            path = ROOT / entry['file']
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('checksum mismatch: ' + entry['file'])
            data = load(path)
            if data['name'] != entry['name'] or data['source'] != entry['source']:
                raise ValueError('manifest identity/source mismatch: ' + entry['file'])
            maps[entry['name']] = data
        actual = {p.stem for p in (ROOT / 'data/games' / game / 'maps/runtime').glob('*.json')}
        if actual != set(maps):
            raise ValueError('pack inventory mismatch: ' + game)
        for name, data in maps.items():
            for warp in data.get('warps', []):
                if 'to_map' in warp:
                    if warp['to_map'] not in maps or warp['to_point'] not in maps[warp['to_map']].get('points', {}):
                        raise ValueError('unresolved named warp: ' + name + ' -> ' + repr(warp))
            for connection in data.get('connections', []):
                if connection['to_map'] not in maps:
                    raise ValueError('unresolved connection: ' + name)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--export-game', choices=('frlg', 'bdsp'))
    parser.add_argument('--out', type=Path, help='empty destination directory for byte-identical JSON')
    args = parser.parse_args()
    if bool(args.export_game) != bool(args.out):
        parser.error('--export-game and --out must be supplied together')
    manifest = audit()
    if args.out:
        if args.out.exists() and any(args.out.iterdir()):
            parser.error('--out must be empty (no stale consumer maps)')
        args.out.mkdir(parents=True, exist_ok=True)
        for entry in manifest['games'][args.export_game]['maps']:
            shutil.copyfile(ROOT / entry['file'], args.out / (entry['name'] + '.json'))
    print('Validated ' + ', '.join(f'{game}: {len(pack["maps"])} maps'
                                  for game, pack in manifest['games'].items()))


if __name__ == '__main__':
    main()

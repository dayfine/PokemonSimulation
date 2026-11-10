r"""The single FRLG map set: one file per map, status recorded in the manifest.

Every FRLG map lives in data/games/frlg/maps/runtime/ and has one manifest
entry in data/maps/runtime-manifest.json with a ``status``:

- ``candidate``: generated from pret/pokefirered, unreviewed.
- ``verified``: reviewed content. ``verified`` records the basis: either an
  ``approved-runtime-pack`` (approved before per-map console records), or a
  ``console-run`` with the run, date and checkpoint that walked it.

Either way the bytes are derived: ``maps/base/<Map>.json`` is the generator's
(``frlg_decomp_map_builder --check``), ``maps/overlays/<Map>.json`` holds the
authored operations, and the runtime file is base + overlays
(``map_overlays check``). Each entry references its base and overlay with hashes.

Promotion edits only the manifest, so map bytes and hashes stay unchanged.
From the repository root:

    PYTHONPATH=src python3 -m pokesim.maps.frlg_map_set check
    PYTHONPATH=src python3 -m pokesim.maps.frlg_map_set sync-candidates
    PYTHONPATH=src python3 -m pokesim.maps.frlg_map_set promote Route11 \
        --run <run record> --date 2026-11-10 --checkpoint 00.14 \
        --consumer-revision <Arduino-Source commit>

See data/games/frlg/maps/README.md for the workflow.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re

from .map_overlays import pack_refs
from .runtime_map_coordinates import legacy_map
from .runtime_map_schema import validate


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'data/maps/runtime-manifest.json'
DIRECTORY = 'data/games/frlg/maps/runtime'
SCOPE = ROOT / 'data/games/frlg/maps/pokeguy-map-scope.json'
STATUSES = ('candidate', 'verified')
PACK_BASIS = 'approved-runtime-pack'
RUN_BASIS = 'console-run'
DATE = re.compile(r'\d{4}-\d\d-\d\d\Z')
SHA = re.compile(r'[0-9a-f]{40}\Z')


def read_manifest(path=MANIFEST):
    return json.loads(Path(path).read_text())


def write_manifest(manifest, path=MANIFEST):
    Path(path).write_text(json.dumps(manifest, indent=2) + '\n')


def check_verified(name, record):
    """Raise ValueError unless a verified record names its evidence."""
    if not isinstance(record, dict):
        raise ValueError(name + ': verified map needs a verified record')
    basis = record.get('basis')
    if basis == PACK_BASIS:
        if set(record) != {'basis', 'pack_revision', 'note'} or not SHA.fullmatch(record['pack_revision']):
            raise ValueError(name + ': approved-runtime-pack needs pack_revision and note')
    elif basis == RUN_BASIS:
        if set(record) - {'consumer_revision'} != {'basis', 'run', 'date', 'checkpoint'}:
            raise ValueError(name + ': console-run needs run, date and checkpoint')
        if not record['run'] or not record['checkpoint'] or not DATE.fullmatch(record['date']):
            raise ValueError(name + ': console-run needs a non-empty run/checkpoint and a YYYY-MM-DD date')
        if 'consumer_revision' in record and not SHA.fullmatch(record['consumer_revision']):
            raise ValueError(name + ': consumer_revision must be a full commit SHA')
    else:
        raise ValueError(name + ': unknown verified basis ' + repr(basis))


def statuses(manifest):
    """Map name -> status for FRLG; raise ValueError on missing/invalid records."""
    result = {}
    for entry in manifest['games']['frlg']['maps']:
        name, status = entry['name'], entry.get('status')
        if status not in STATUSES:
            raise ValueError(name + ': status must be one of ' + ', '.join(STATUSES))
        if status == 'verified':
            check_verified(name, entry.get('verified'))
        elif 'verified' in entry:
            raise ValueError(name + ': a candidate has no verified record')
        if entry['file'] != f'{DIRECTORY}/{name}.json':
            raise ValueError(name + ': map file must be ' + f'{DIRECTORY}/{name}.json')
        result[name] = status
    return result


def read_excluded(names, scope=SCOPE):
    """Scope-excluded map -> reason; the catalog is the set plus every exclusion."""
    from .frlg_map_scope import read_scope
    declaration = json.loads(Path(scope).read_text())
    catalog = set(names) | {n for group in declaration['excluded'] for n in group['maps']}
    return read_scope(scope, catalog, declaration['source_revision'])


def link_gaps(maps, status, excluded):
    """Classify every named link that does not resolve inside the set.

    ``boundary``: the destination is scope-excluded and not in the set (a dead
    end, never a successful transition; a scripted Center or elevator keeps its
    name). ``pending_relink``: a candidate links into a verified map that does
    not define the return point. Since verified maps are generated bases too,
    there are none; the category stays to report a regression.
    Anything else is an error. Returns (boundary, pending_relink, errors).
    """
    boundary, pending, errors = [], [], []
    for name, data in sorted(maps.items()):
        links = [(w['to_map'], w['to_point']) for w in data.get('warps', []) if 'to_map' in w]
        links += [(c['to_map'], None) for c in data.get('connections', [])]
        for target, point in links:
            if target not in maps:
                (boundary if target in excluded else errors).append((name, target, point))
            elif point is not None and point not in maps[target].get('points', {}):
                pending_case = status.get(name) == 'candidate' and status.get(target) == 'verified'
                (pending if pending_case else errors).append((name, target, point))
    return boundary, pending, errors


def candidate_entry(name, raw, root=ROOT):
    data = legacy_map(json.loads(raw))
    validate(data)
    return dict(name=name, file=f'{DIRECTORY}/{name}.json', sha256=hashlib.sha256(raw).hexdigest(),
                source=data['source'], target_game='frlg', source_game='firered', source_revision_resolved=True,
                verification='decomp-only',
                coordinate_frame={'kind': 'local tiles', 'origin': [0, 0], 'width': len(data['tiles'][0]),
                                  'height': len(data['tiles']), 'origin_space': 'map layout'},
                terrain_corrections=[], generation_overrides={'opened_tiles': []}, preconditions=[],
                status='candidate', **pack_refs(name, 'frlg', root))


def sync_candidates(manifest, root=ROOT):
    """Add/refresh candidate entries from the files; never touch verified entries.

    A file without an entry becomes a candidate. Returns the changed names.
    """
    pack = manifest['games']['frlg']['maps']
    entries = {e['name']: e for e in pack}
    files = {p.stem: p.read_bytes() for p in (Path(root) / DIRECTORY).glob('*.json')}
    missing = sorted(set(entries) - set(files))
    if missing:
        raise ValueError('manifest entries without a map file: ' + ' '.join(missing))
    changed = []
    for name, raw in sorted(files.items()):
        entry = entries.get(name)
        if entry is not None and entry.get('status') != 'candidate':
            continue
        fresh = candidate_entry(name, raw, root)
        if entry != fresh:
            changed.append(name)
            if entry is None:
                pack.append(fresh)
            else:
                pack[pack.index(entry)] = fresh
    pack.sort(key=lambda e: e['name'])
    return changed


def promote(manifest, name, run, date, checkpoint, consumer_revision=None):
    """Record a console pass; the map bytes and hash stay unchanged."""
    entry = next((e for e in manifest['games']['frlg']['maps'] if e['name'] == name), None)
    if entry is None:
        raise ValueError('no FRLG map named ' + name)
    if entry['status'] != 'candidate':
        raise ValueError(name + ' is already ' + entry['status'])
    record = dict(basis=RUN_BASIS, run=run, date=date, checkpoint=checkpoint)
    if consumer_revision:
        record['consumer_revision'] = consumer_revision
    check_verified(name, record)
    entry['status'] = 'verified'
    entry['verified'] = record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check', help='validate statuses (the pack audit covers bytes and links)')
    sub.add_parser('sync-candidates', help='write candidate manifest entries from the map files')
    up = sub.add_parser('promote', help='mark a candidate verified after a console pass')
    up.add_argument('name')
    up.add_argument('--run', required=True, help='run record (path or id) of the console pass')
    up.add_argument('--date', required=True, help='YYYY-MM-DD')
    up.add_argument('--checkpoint', required=True, help='AutoStory checkpoint that walked the map')
    up.add_argument('--consumer-revision', help='Arduino-Source commit that ran')
    args = parser.parse_args()
    manifest = read_manifest()
    try:
        if args.command == 'sync-candidates':
            changed = sync_candidates(manifest)
            write_manifest(manifest)
            print(f'{len(changed)} candidate entries written')
        elif args.command == 'promote':
            promote(manifest, args.name, args.run, args.date, args.checkpoint, args.consumer_revision)
            write_manifest(manifest)
        counts = {s: 0 for s in STATUSES}
        for status in statuses(manifest).values():
            counts[status] += 1
        print('FRLG maps: ' + ', '.join(f'{n} {s}' for s, n in counts.items()))
    except ValueError as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

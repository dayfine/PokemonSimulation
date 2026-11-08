"""Audit a full FRLG source candidate without publishing or approving it.

    PYTHONPATH=src python3 -m pokesim.maps.frlg_import_audit \
        data/games/frlg/maps/source-candidate --schema \
        --scope data/games/frlg/maps/pokeguy-map-scope.json --out /tmp/frlg-import-audit.json

Generate with frlg_decomp_map_builder --all --scope <inventory> --item-identities.
Unknown mechanics, destinations and pickups stay gaps; valid geometry is not
proof that the complete story can be routed or executed.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from pokesim.formats.contract_format import json_text
from .runtime_map_schema import validate
from .frlg_map_scope import read_scope


def audit(candidate, schema=False, scope=None):
    paths = sorted(Path(candidate).glob('*.json'))
    if not paths:
        raise ValueError('candidate directory has no maps')
    maps = {p.stem: json.loads(p.read_text()) for p in paths}
    excluded = {}
    if scope:
        revision = next(iter(maps.values()))['source']['revision']
        declaration = json.loads(Path(scope).read_text())
        catalog = set(maps) | {n for group in declaration['excluded'] for n in group['maps']}
        excluded = read_scope(scope, catalog, revision)
        if set(maps) != set(catalog) - set(excluded):
            raise ValueError('candidate files do not match the declared map scope')
    if schema:
        from pokesim.formats.json_schema import validator
        check = validator('runtime-map-v2')
    revisions = set()
    behavior_counts, totals, gaps = Counter(), Counter(), []
    for name, data in maps.items():
        validate(data)
        if schema:
            check.validate(data)
        if data['name'] != name or data['source'].get('generation_status') != 'unreviewed-full-catalog-candidate':
            raise ValueError('expected a marked source candidate: ' + name)
        revisions.add(data['source']['revision'])
        unknown = data.get('unresolved_tiles', {})
        if unknown:
            raise ValueError(f'{name}: candidate contains unresolved tiles: {list(unknown)}')
        for y, row in enumerate(data.get('tiles', [])):
            if ' ' in row:
                raise ValueError(f'{name}: candidate contains unmapped space cells at row {y}')
        counts = {
            'scope_boundary_warps': sum(w.get('to_map') in excluded for w in data.get('warps', [])),
            'scope_boundary_connections': sum(e['to_map'] in excluded for e in data.get('connections', [])),
            'unknown_tiles': sum(map(len, unknown.values())),
            'unlinked_warps': sum('to_map' not in w for w in data.get('warps', [])),
            'dynamic_warps': sum(w.get('unresolved') == 'dynamic_destination' for w in data.get('warps', [])),
            'unresolved_pickups': sum('item' not in o for o in data.get('items', [])),
            'identified_pickups': sum('item' in o for o in data.get('items', [])),
            'unapplied_story_patches': int('unapplied_story_patch' in data['source'])}
        totals.update(counts)
        if any(v for k, v in counts.items() if k != 'identified_pickups'):
            gaps.append(dict(map=name, **counts))
        for warp in data.get('warps', []):
            if 'to_map' in warp:
                if warp['to_map'] in excluded:
                    continue
                target = maps.get(warp['to_map'])
                if target is None or warp['to_point'] not in target.get('points', {}):
                    raise ValueError(name + ': missing fixed warp destination ' + repr(warp))
        for edge in data.get('connections', []):
            if edge['to_map'] not in maps and edge['to_map'] not in excluded:
                raise ValueError(name + ': missing connection destination')
    if len(revisions) != 1:
        raise ValueError('candidate mixes source revisions')
    return {'format': 'pokesim-frlg-map-import-audit/1', 'status': 'unreviewed-candidate',
            'source_revision': revisions.pop(), 'map_count': len(maps),
            'excluded_map_count': len(excluded),
            'elevation_grids_retained': sum('elevation' in m for m in maps.values()),
            'elevation_grids_omitted': sum('elevation' not in m for m in maps.values()),
            'schema_checked': schema, 'included_fixed_destinations_checked': True,
            'totals': dict(totals), 'unknown_behaviors': dict(sorted(behavior_counts.items())),
            'maps_with_gaps': gaps}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--schema', action='store_true', help='also use schemas/requirements.txt')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--scope', type=Path, help='explicit excluded-destination inventory')
    args = parser.parse_args()
    result = json_text(audit(args.candidate, args.schema, args.scope))
    if args.out:
        args.out.write_text(result, encoding='utf-8')
    else:
        print(result, end='')


if __name__ == '__main__':
    main()

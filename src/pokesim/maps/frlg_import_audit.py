"""Audit a full FRLG source candidate without publishing or approving it.

    PYTHONPATH=src python3 -m pokesim.maps.frlg_import_audit \
        /tmp/frlg-full-map-candidate --schema --out /tmp/frlg-import-audit.json

Generate the candidate with frlg_decomp_map_builder --all --item-identities.
Unknown mechanics, destinations and pickups stay gaps; valid geometry is not
proof that the complete story can be routed or executed.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

from pokesim.formats.contract_format import json_text
from .runtime_map_schema import validate


def audit(candidate, schema=False):
    paths = sorted(Path(candidate).glob('*.json'))
    if not paths:
        raise ValueError('candidate directory has no maps')
    maps = {p.stem: json.loads(p.read_text()) for p in paths}
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
        for behavior, coords in unknown.items():
            for x, y in coords:
                if data['tiles'][y][x] not in (' ', 'w'):
                    raise ValueError(name + ': unresolved terrain must remain blocked unknown')
            behavior_counts[behavior] += len(coords)
        counts = {
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
                target = maps.get(warp['to_map'])
                if target is None or warp['to_point'] not in target.get('points', {}):
                    raise ValueError(name + ': missing fixed warp destination ' + repr(warp))
        for edge in data.get('connections', []):
            if edge['to_map'] not in maps:
                raise ValueError(name + ': missing connection destination')
    if len(revisions) != 1:
        raise ValueError('candidate mixes source revisions')
    return {'format': 'pokesim-frlg-map-import-audit/1', 'status': 'unreviewed-candidate',
            'source_revision': revisions.pop(), 'map_count': len(maps),
            'schema_checked': schema, 'fixed_destinations_checked': True,
            'totals': dict(totals), 'unknown_behaviors': dict(sorted(behavior_counts.items())),
            'maps_with_gaps': gaps}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--schema', action='store_true', help='also use schemas/requirements.txt')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = json_text(audit(args.candidate, args.schema))
    if args.out:
        args.out.write_text(result, encoding='utf-8')
    else:
        print(result, end='')


if __name__ == '__main__':
    main()

r"""Preview compact runtime-map JSON without changing a pinned source or consumer.

    PYTHONPATH=src python3 -m pokesim.maps.runtime_map_format \
        --input data/games/bdsp/maps/runtime/OreburghMine.json \
        --out /tmp/OreburghMine.coord.json

Use --legacy to generate v1 coordinates from a v2 preview. Native reader adoption
must precede publishing v2 as the active map-pack format.
"""

import argparse
import json
from pathlib import Path

from .consumer_source import read_json
from .runtime_map_coordinates import compact_map, legacy_map
from .runtime_map_schema import validate


EXPANDED = {'tiles', 'elevation', 'points', 'regions', 'objects', 'npcs', 'items', 'signs', 'interactables', 'warps', 'patches', 'coord_events'}


def map_text(data, width=120):
    """Stable JSON: short records and pairs inline, one terrain row per line.

    Keep every field, including zero and false; formatting changes no JSON value.
    """
    def render(value, depth=0, expand=False):
        inline = json.dumps(value, ensure_ascii=False)
        if not isinstance(value, (dict, list)) or not value:
            return inline
        if not expand and depth * 4 + len(inline) <= width:
            return inline
        indent = ' ' * ((depth + 1) * 4)
        if isinstance(value, dict):
            entries = [indent + json.dumps(key) + ': ' + render(item, depth + 1, key in EXPANDED)
                       for key, item in value.items()]
            return '{\n' + ',\n'.join(entries) + '\n' + ' ' * (depth * 4) + '}'
        entries = [indent + render(item, depth + 1) for item in value]
        return '[\n' + ',\n'.join(entries) + '\n' + ' ' * (depth * 4) + ']'
    return render(data, expand=True) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--game', choices=('frlg', 'bdsp'), help='enrich from the pinned item catalog')
    parser.add_argument('--legacy', action='store_true', help='write v1 instead of the v2 preview')
    args = parser.parse_args()
    if args.input.resolve() == args.out.resolve():
        parser.error('preview output must differ from the input; do not overwrite a pinned map')
    data = read_json(args.input.read_bytes())
    validate(data)
    if args.game:
        # Keep the pure coordinate codec independent of source/catalog lookup.
        from .item_identity import enrich_map
        data = enrich_map(legacy_map(data), args.game)
    converted = legacy_map(data) if args.legacy else compact_map(data)
    validate(converted)
    args.out.write_text(map_text(converted), encoding='utf-8')


if __name__ == '__main__':
    main()

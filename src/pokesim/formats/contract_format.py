"""Keep exchange contracts readable with short definitions and arrays inline.

    PYTHONPATH=src python3 -m pokesim.formats.contract_format
    PYTHONPATH=src python3 -m pokesim.formats.contract_format --check
    PYTHONPATH=src python3 -m pokesim.formats.contract_format path/to/data.json

With no paths, formats schemas, shared story cases, native captures and the Parcel pilot.
Explicit paths opt other authored JSON files in. Every field and its order are
retained. Republish hash-pinned data before adopting changed bytes in consumers.
"""

import argparse
import json

from pathlib import Path

from .json_schema import ROOT, SCHEMAS


def json_text(data, width=120):
    """Expand long containers using two-space indentation and a soft width."""
    native_capture = isinstance(data, dict) and data.get("format") == "pokesim-native-checkpoint-export/1"

    def event(value):
        return native_capture and isinstance(value, dict) and "id" in value and "kind" in value

    def render(value, depth=0, prefix=0):
        inline = json.dumps(value, ensure_ascii=False)
        expand = event(value) or (isinstance(value, list) and any(event(item) for item in value))
        if not isinstance(value, (dict, list)) or not value or (not expand and depth * 2 + prefix + len(inline) <= width):
            return inline
        indent = ' ' * ((depth + 1) * 2)
        if isinstance(value, dict):
            entries = []
            for key, item in value.items():
                label = json.dumps(key, ensure_ascii=False) + ': '
                entries.append(indent + label + render(item, depth + 1, len(label)))
            opening, closing = '{', '}'
        else:
            entries = [indent + render(item, depth + 1) for item in value]
            opening, closing = '[', ']'
        return opening + '\n' + ',\n'.join(entries) + '\n' + ' ' * (depth * 2) + closing
    return render(data) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('paths', nargs='*', type=Path, help='JSON files; defaults to schemas and shared story fixtures')
    parser.add_argument('--check', action='store_true', help='report formatting drift without writing')
    args = parser.parse_args()
    changed = []
    paths = args.paths or (sorted(SCHEMAS.glob('*.schema.json'))
        + [ROOT / 'data/story/wire-conformance.json'] + sorted(ROOT.glob('data/story/native/*.json'))
        + sorted(ROOT.glob('data/story/parcel-pilot/*.json')))
    for path in paths:
        original = path.read_text(encoding='utf-8')
        formatted = json_text(json.loads(original))
        if original != formatted:
            changed.append(path.name)
            if not args.check:
                path.write_text(formatted, encoding='utf-8')
    if args.check and changed:
        parser.exit(1, 'Reformat contracts: ' + ', '.join(changed) + '\n')
    print('{} JSON files {}.'.format(len(changed), 'need formatting' if args.check else 'formatted'))


if __name__ == '__main__':
    main()

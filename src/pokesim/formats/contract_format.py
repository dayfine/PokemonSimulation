"""Keep exchange contracts readable with short definitions and arrays inline.

    PYTHONPATH=src python3 -m pokesim.formats.contract_format
    PYTHONPATH=src python3 -m pokesim.formats.contract_format --check

Formats schemas/*.schema.json and data/story/wire-conformance.json. Published game data and resource
hashes are untouched. Every field and its order are retained.
"""

import argparse
import json

from .json_schema import ROOT, SCHEMAS


def json_text(data, width=120):
    """Expand long containers using two-space indentation and a soft width."""
    def render(value, depth=0, prefix=0):
        inline = json.dumps(value, ensure_ascii=False)
        if not isinstance(value, (dict, list)) or not value or depth * 2 + prefix + len(inline) <= width:
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
    parser.add_argument('--check', action='store_true', help='report formatting drift without writing')
    args = parser.parse_args()
    changed = []
    paths = sorted(SCHEMAS.glob('*.schema.json')) + [ROOT / 'data/story/wire-conformance.json']
    for path in paths:
        original = path.read_text(encoding='utf-8')
        formatted = json_text(json.loads(original))
        if original != formatted:
            changed.append(path.name)
            if not args.check:
                path.write_text(formatted, encoding='utf-8')
    if args.check and changed:
        parser.exit(1, 'Reformat contracts: ' + ', '.join(changed) + '\n')
    print('{} contract files {}.'.format(len(changed), 'need formatting' if args.check else 'formatted'))


if __name__ == '__main__':
    main()

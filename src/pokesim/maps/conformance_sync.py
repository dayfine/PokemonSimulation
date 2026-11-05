"""Export/check immutable shared fixture bytes without changing runtime maps.

From the repository root, using a full publishing commit SHA:
    PYTHONPATH=src python3 -m pokesim.maps.conformance_sync update \
        --source . --consumer /path/to/Arduino-Source --revision FULL_SHA
    PYTHONPATH=src python3 -m pokesim.maps.conformance_sync check \
        --source . --consumer /path/to/Arduino-Source

Draft candidates require --preview on BOTH update and check. This never relaxes
approval of the fixture's map_revision. --offline trusts cached origin/main.
"""
import argparse
import json
from pathlib import Path

from .conformance import validate
from .consumer_source import GitSource, REPOSITORY, SHA, read_json, sha256

SOURCE = 'data/navigation/conformance/v1/cases.json'
DEST = Path('SerialPrograms/Source/Pokemon/Navigation/Conformance')


def published(source, revision, preview=False):
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        raise ValueError('fixture revision must be a full immutable SHA')
    if source.git('cat-file', '-t', revision).strip() != b'commit':
        raise ValueError('fixture revision is not a commit')
    if not preview:
        source.approved(revision)
    raw = source.read(revision, SOURCE)
    pack = validate(read_json(raw))
    source.approved(pack['map_revision'])
    for entry in pack['maps']:
        path = 'data/games/{game}/maps/runtime/{name}.json'.format(**entry)
        if sha256(source.read(pack['map_revision'], path)) != entry['sha256']:
            raise ValueError('published fixture/map hash mismatch: ' + path)
    pin = dict(repository=REPOSITORY, revision=revision, path=SOURCE,
               status='candidate-preview' if preview else 'main-approved', sha256=sha256(raw))
    return raw, pin


def check(consumer, source, preview=False):
    folder = Path(consumer) / DEST
    pin = read_json((folder / 'pin.json').read_bytes())
    if not isinstance(pin, dict) or set(pin) != {'repository', 'revision', 'path', 'status', 'sha256'}:
        raise ValueError('invalid conformance pin fields')
    is_preview = pin['status'] == 'candidate-preview'
    if is_preview and not preview:
        raise ValueError('candidate conformance pin requires explicit --preview')
    raw, expected_pin = published(source, pin['revision'], is_preview)
    if pin != expected_pin or (folder / 'cases.json').read_bytes() != raw:
        raise ValueError('conformance pin/fixture drift')
    if {p.name for p in folder.glob('*.json')} != {'cases.json', 'pin.json'}:
        raise ValueError('unexpected conformance resource inventory')
    return pin


def update(consumer, source, revision, preview=False):
    raw, pin = published(source, revision, preview)
    folder = Path(consumer) / DEST
    if folder.exists() and any(folder.iterdir()):
        # Refuse to overwrite unrelated files or a locally modified export.
        # An approved update may promote an intact preview export.
        check(consumer, source, preview=True)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'cases.json').write_bytes(raw)
    (folder / 'pin.json').write_text(json.dumps(pin, indent=2) + '\n')
    return pin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('update', 'check'))
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--consumer', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args()
    source = GitSource(args.source)
    try:
        if not args.offline:
            source.refresh()
        if args.command == 'update':
            if not args.revision:
                parser.error('update requires --revision')
            pin = update(args.consumer, source, args.revision, args.preview)
        else:
            if args.revision:
                parser.error('check uses the checked-in pin; omit --revision')
            pin = check(args.consumer, source, args.preview)
    except (ValueError, OSError, TypeError, KeyError) as error:
        parser.exit(1, str(error) + '\n')
    print('Verified conformance ' + pin['revision'] + ' (' + pin['status'] + ')')


if __name__ == '__main__':
    main()

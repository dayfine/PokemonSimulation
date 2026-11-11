"""Validate published exchange data with JSON Schema 2020-12.

    python3 -m pip install -r schemas/requirements.txt
    PYTHONPATH=src python3 -m pokesim.formats.json_schema --check-published
    PYTHONPATH=src python3 -m pokesim.formats.json_schema runtime-map-v2 map.json

Schema validation is structural. Existing game/map validators still enforce
cross-field, geometric, reference and execution requirements. No schema fetches
or default insertion occur: schemas are loaded from this repository revision.
"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / 'schemas'


def validator(name):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    path = SCHEMAS / (name + '.schema.json')
    if path.parent != SCHEMAS:
        raise ValueError('schema must be a local schema name')
    schema = json.loads(path.read_text())
    Draft202012Validator.check_schema(schema)
    resources = []
    for local in SCHEMAS.glob('*.schema.json'):
        document = json.loads(local.read_text())
        resources.append((document['$id'], Resource.from_contents(document)))
    return Draft202012Validator(schema, registry=Registry().with_resources(resources))


def published():
    """Enumerate current runtime packs and the checked-in FRLG case document."""
    for path in sorted(ROOT.glob('data/games/*/maps/runtime/*.json')):
        yield 'runtime-map-v2', path
    for path in sorted(ROOT.glob('data/games/*/maps/base/*.json')):
        yield 'runtime-map-v2', path
    for path in sorted(ROOT.glob('data/games/*/maps/overlays/*.json')):
        yield 'map-overlay', path
    yield 'frlg-battle-cases', ROOT / 'data/games/frlg/battles/cases.json'
    for path in sorted(ROOT.glob('data/story/native/*.json')):
        yield 'native-checkpoint-export', path
    yield 'authored-checkpoint', ROOT / 'data/story/parcel-pilot/frlg-parcel-02.01.plan.json'
    for path in sorted(ROOT.glob('data/story/frlg-authored/*.plan.json')):
        yield 'authored-checkpoint', path
    yield 'story-replay-binding', ROOT / 'data/story/parcel-pilot/binding.json'
    yield 'story-replay-binding', ROOT / 'data/story/parcel-pilot/authored-binding.json'
    yield 'story-replay-cases', ROOT / 'data/story/parcel-pilot/cases.json'
    yield 'authored-checkpoint', ROOT / 'data/story/bdsp-mine-pilot/bdsp-mine-01.03.plan.json'
    yield 'story-replay-binding', ROOT / 'data/story/bdsp-mine-pilot/binding.json'
    yield 'story-replay-cases', ROOT / 'data/story/bdsp-mine-pilot/cases.json'
    yield 'native-plan-source', ROOT / 'data/story/bdsp-mine-pilot/source.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('schema', nargs='?', choices=[p.name[:-12] for p in SCHEMAS.glob('*.schema.json')])
    parser.add_argument('document', nargs='?', type=Path)
    parser.add_argument('--check-published', action='store_true')
    args = parser.parse_args()
    if args.check_published:
        documents = list(published())
    elif args.schema and args.document:
        documents = [(args.schema, args.document)]
    else:
        parser.error('provide schema and document, or --check-published')
    for name, path in documents:
        errors = list(validator(name).iter_errors(json.loads(path.read_text())))
        if errors:
            error = errors[0]
            parser.exit(1, '{} {}: {}\n'.format(path, error.json_path, error.message))
    print('Validated {} documents.'.format(len(documents)))


if __name__ == '__main__':
    main()

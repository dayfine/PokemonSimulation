r"""Regenerate audited pickup identities and enrich maps from pinned source inputs.

    PYTHONPATH=src python3 -m pokesim.maps.item_identity --cache /path/to/item-sources --check
    PYTHONPATH=src python3 -m pokesim.maps.item_identity --cache /path/to/item-sources --write

Populate the external cache from the exact revisions/files in
data/maps/item-source-inputs.json. Network is opt-in with --fetch; no native checkout is used here.
--write updates the catalog only; published map and native replay pins stay unchanged.
"""

import argparse
import copy
import hashlib
import json
import re
from urllib.request import urlopen
from urllib.parse import quote
from pathlib import Path

from .item_pickup_sources import diamond_events, diamond_pickups, frlg_pickups, frlg_starter, platinum_pickups, unresolved
from .runtime_map_format import map_text
from .runtime_map_coordinates import compact_map

ROOT = Path(__file__).resolve().parents[3]
INPUTS = ROOT / 'data/maps/item-source-inputs.json'
CATALOG = ROOT / 'data/maps/item-identities.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_inputs(cache, inputs, fetch=False):
    """Require every cached source file to match the reviewed pinned input hash."""
    if inputs.get('format') != 'pokesim-item-source-inputs/1':
        raise ValueError('unsupported item-source input format')
    result = {}
    for key, source in inputs['sources'].items():
        if not re.fullmatch(r'[a-z0-9_]+', key):
            raise ValueError('unsafe item source key')
        if not re.fullmatch(r'[0-9a-f]{40}', source['revision']):
            raise ValueError('item source must pin a full commit SHA')
        result[key] = {}
        for path, info in source['files'].items():
            relative = Path(path)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('unsafe item source path')
            destination = Path(cache) / key / relative
            if not destination.exists() and fetch:
                url = 'https://raw.githubusercontent.com/{}/{}/{}'.format(
                    source['repository'], source['revision'], quote(path))
                with urlopen(url, timeout=30) as response:
                    fetched = response.read()
                if digest(fetched) != info['sha256']:
                    raise ValueError('downloaded item source hash mismatch: ' + path)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(fetched)
            raw = destination.read_bytes()
            git_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if digest(raw) != info['sha256'] or git_blob != info['git_blob']:
                raise ValueError('item source hash mismatch: ' + key + '/' + path)
            result[key][path] = raw
    return result


def _json_events(raw, game):
    events = json.loads(raw)['object_events']
    return [dict(index=i, id=e.get('local_id') if game == 'frlg' else e.get('id'),
                 script=e.get('script'), x=e['x'], y=e['y'] if game == 'frlg' else e['z'],
                 hide_flag=e.get('flag') if game == 'frlg' else e.get('hidden_flag'))
            for i, e in enumerate(events)]


def build_catalog(inputs, sources):
    """Resolve source-indexed pickups; unknown script forms stay explicitly unresolved."""
    frlg = frlg_pickups(sources['frlg'][inputs['resolvers']['frlg']['scripts']].decode(),
                       sources['frlg'][inputs['resolvers']['frlg']['macros']].decode())
    diamond = diamond_pickups(sources['diamond'][inputs['resolvers']['diamond']['scripts']],
                             sources['diamond'][inputs['resolvers']['diamond']['constants']].decode())
    platinum = platinum_pickups(sources['platinum'][inputs['resolvers']['platinum']['scripts']].decode())
    result = dict(format='pokesim-item-identities/1',
                  inputs_sha256=digest(json.dumps(inputs, sort_keys=True).encode()),
                  sources={key: {field: value for field, value in source.items() if field != 'files'}
                           for key, source in inputs['sources'].items()}, maps={})
    for game, maps in inputs['maps'].items():
        result['maps'][game] = {}
        for name, spec in maps.items():
            key = spec['source']
            raw = sources[key][spec['events']]
            events = diamond_events(raw) if key == 'diamond' else _json_events(raw, key)
            rows = []
            for location in spec['locations']:
                x, y = location['coord']
                matches = [e for e in events if (e['x'] - spec['origin'][0], e['y'] - spec['origin'][1]) == (x, y)]
                if len(matches) != 1:
                    raise ValueError('ambiguous/missing pickup event: ' + game + '/' + name + repr((x, y)))
                event = matches[0]
                script = event['script']
                if key == 'frlg':
                    identity = frlg.get(script)
                    if identity is None:
                        local_scripts = sources[key].get(spec.get('scripts'), b'').decode()
                        identity = frlg_starter(script, local_scripts)
                else:
                    identity = (diamond if key == 'diamond' else platinum).get(
                        script, unresolved('not a supported fixed ' + key + ' item script'))
                reference = {k: event[k] for k in ('index', 'id', 'script') if event[k] is not None}
                row = dict(coord=[x, y], source_event=reference, **identity)
                if event['hide_flag'] not in (None, '0', 0, ''):
                    row['hide_flag'] = event['hide_flag']
                rows.append(row)
            result['maps'][game][name] = dict(source=key, events=spec['events'], events_sha256=digest(raw),
                                                     map_content_sha256=spec['map_content_sha256'], objects=rows)
    return result


def enrich_objects(objects, game, name, events_sha256, catalog=None, source_revision=None):
    """Attach metadata only to matching pinned events; do not infer a pickup effect."""
    if catalog is None:
        catalog_raw = CATALOG.read_bytes()
        catalog = json.loads(catalog_raw)
    else:
        catalog_raw = map_text(catalog).encode()
    if catalog.get('format') != 'pokesim-item-identities/1':
        raise ValueError('unsupported item identity catalog')
    entry = catalog['maps'].get(game, {}).get(name)
    result = copy.deepcopy(objects)
    items = [o for o in result if o.get('kind') == 'item']
    if not items:
        return result, None
    if entry is None:
        for obj in items:
            obj.update(unresolved('no pinned identity catalog for this map'))
        return result, None
    source = catalog['sources'][entry['source']]
    if source_revision is not None and source_revision != source['revision']:
        raise ValueError('item source revision mismatch: ' + game + '/' + name)
    if events_sha256 != entry['events_sha256']:
        raise ValueError('item event-source hash mismatch: ' + game + '/' + name)
    for obj in items:
        matches = [r for r in entry['objects'] if r['coord'] == [obj['x'], obj['y']]]
        if len(matches) != 1:
            raise ValueError('missing/ambiguous item identity: ' + game + '/' + name)
        row = matches[0]
        if ('source_event' in obj and obj['source_event'] not in
                (row['source_event'], row['source_event']['index'])):
            raise ValueError('item source event changed: ' + game + '/' + name)
        obj.update({k: copy.deepcopy(v) for k, v in row.items() if k not in ('coord', 'source_event')})
        # Full script/local-ID provenance is normalized once in the pinned catalog.
        obj['source_event'] = row['source_event']['index']
    source = catalog['sources'][entry['source']]
    provenance = dict(repository=source['repository'], revision=source['revision'],
                      events=entry['events'], events_sha256=events_sha256,
                      catalog='data/maps/item-identities.json', catalog_sha256=digest(catalog_raw),
                      source_game=source['source_game'], target_game=source['target_game'],
                      target_game_relation=source['target_game_relation'], verification=source['verification'])
    return result, provenance


def _identity_base(data, game):
    """Remove only catalog-owned additions to recover the reviewed map fingerprint.

    Published BDSP item records originally contain only name/position/kind;
    FRLG records already carry collection flags, so retain those there. Unknown
    extensions remain in the fingerprint. Re-enrichment below must reproduce
    every removed value, preventing an altered reward/provenance being repaired.
    """
    result = copy.deepcopy(data)
    result['source'].pop('item_identities', None)
    fields = {'item', 'quantity', 'source_event', 'pickup', 'interaction'}
    if game == 'bdsp':
        fields.add('hide_flag')
    for obj in result.get('objects', []):
        if obj.get('kind') == 'item':
            for key in fields:
                obj.pop(key, None)
    return result


def enrich_map(data, game, catalog=None):
    """Enrich a reviewed map, or verify an already enriched published map."""
    catalog = catalog if catalog is not None else json.loads(CATALOG.read_text())
    published = 'item_identities' in data.get('source', {})
    result = _identity_base(data, game) if published else copy.deepcopy(data)
    if not any(o.get('kind') == 'item' for o in data.get('objects', [])):
        if published:
            raise ValueError('published item metadata without pickups: ' + data['name'])
        return result
    entry = catalog['maps'].get(game, {}).get(data['name'])
    if entry is None:
        if published:
            raise ValueError('published item metadata without pinned catalog: ' + data['name'])
        result['objects'], _ = enrich_objects(result.get('objects', []), game, data['name'], None, catalog)
        return result
    actual_map_hash = digest(json.dumps(compact_map(result), sort_keys=True).encode())
    if actual_map_hash != entry['map_content_sha256']:
        raise ValueError('item catalog map-content mismatch: ' + game + '/' + data['name'])
    result['objects'], provenance = enrich_objects(result.get('objects', []), game, data['name'], entry['events_sha256'], catalog)
    if provenance is not None:
        result['source']['item_identities'] = provenance
    if published and result != data:
        raise ValueError('published item metadata mismatch: ' + game + '/' + data['name'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--cache', required=True, type=Path)
    parser.add_argument('--fetch', action='store_true', help='download missing inputs at their exact pins; never replace cached drift')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--write', action='store_true')
    args = parser.parse_args()
    inputs = json.loads(INPUTS.read_text())
    catalog = build_catalog(inputs, read_inputs(args.cache, inputs, fetch=args.fetch))
    text = map_text(catalog)
    if args.check:
        if CATALOG.read_text() != text:
            parser.error('item catalog differs from pinned sources')
    else:
        CATALOG.write_text(text)
    counts = [o for maps in catalog['maps'].values() for entry in maps.values() for o in entry['objects']]
    print('Resolved {} fixed pickups; {} interactions; {} unresolved'.format(
        sum('item' in o for o in counts), sum('interaction' in o for o in counts), sum('pickup' in o for o in counts)))


if __name__ == '__main__':
    main()

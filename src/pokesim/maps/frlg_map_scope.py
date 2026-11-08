"""Explicit exclusions from a pinned FRLG source catalog, with review reasons."""

import json
from pathlib import Path


def read_scope(path, catalog, revision):
    """Validate exclusions against the full catalog; return map -> reason.

    Unknown names, duplicates and revision/catalog drift require a scope review.
    An excluded destination remains a boundary, never a successful transition.
    """
    data = json.loads(Path(path).read_text())
    if (data.get('format') != 'pokesim-frlg-map-scope/1'
            or data.get('source_revision') != revision
            or data.get('catalog_count') != len(catalog)):
        raise ValueError('map scope revision/catalog mismatch')
    excluded = {}
    for group in data['excluded']:
        if not group['reason'] or not group['basis']:
            raise ValueError('map exclusion requires a reason and basis')
        for name in group['maps']:
            if name not in catalog or name in excluded:
                raise ValueError('unknown or duplicate scope exclusion: ' + name)
            excluded[name] = group['reason']
    return excluded

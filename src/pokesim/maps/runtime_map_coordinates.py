"""Coordinate-array wire format for runtime maps; legacy readers use legacy_map().

Schema-owned coordinates and identified-pickup defaults are normalized. Unknown extensions and zero/false
values survive unchanged. Published maps use format 2; historical v1 pins remain readable.
"""

import copy

LEGACY = 'pokesim-runtime-map/1'
COMPACT = 'pokesim-runtime-map/2'
SECTIONS = ('objects', 'warps', 'patches', 'coord_events')
GROUPS = {'npcs': 'npc', 'items': 'item', 'signs': 'sign', 'interactables': 'item'}


def _pair(value, label):
    if not isinstance(value, list) or len(value) != 2 or any(type(n) is not int for n in value):
        raise ValueError(label + ' must be an array of two integers')
    return value


def _convert_pair(record, old, new, compact, ordered=False):
    """Switch a record between the pair `new` and the fields `old`. Going to
    the fields, `ordered` puts them where the pair was instead of at the end,
    so that a legacy round trip leaves every key where it was."""
    if not isinstance(record, dict):
        raise ValueError('coordinate record must be an object')
    if compact:
        if new in record or any(key not in record for key in old):
            raise ValueError('expected only coordinate fields ' + repr(old))
        value = _pair([record[key] for key in old], new)
        converted = {}
        for key, item in record.items():
            if key == old[0]:
                converted[new] = value
            elif key != old[1]:
                converted[key] = item
        record.clear()
        record.update(converted)
    else:
        if new not in record or any(key in record for key in old):
            raise ValueError('expected only coordinate field ' + new)
        value = _pair(record[new], new)
        if ordered:
            converted = {}
            for key, item in record.items():
                if key == new:
                    converted.update(zip(old, value))
                else:
                    converted[key] = item
            record.clear()
            record.update(converted)
        else:
            del record[new]
            record.update(zip(old, value))


def _records(data, compact, ordered=False):
    for section in SECTIONS:
        records = data.get(section, [])
        if not isinstance(records, list):
            raise ValueError(section + ' must be an array')
        for record in records:
            _convert_pair(record, ('x', 'y'), 'coord', compact, ordered)
            if section == 'objects' and 'wander' in record:
                box = record['wander']
                _convert_pair(box, ('x0', 'y0'), 'min', compact, ordered)
                _convert_pair(box, ('x1', 'y1'), 'max', compact, ordered)
    return data


def _pickup_defaults(record):
    """Expand known pickup defaults; NPCs and non-item interactions are unchanged."""
    if not isinstance(record.get('item'), str) or not record['item']:
        raise ValueError('item must be a nonempty string')
    event = record.get('source_event')
    if 'source_event' in record and (type(event) is not int or not 0 <= event <= 2147483647):
        raise ValueError('source_event must be a nonnegative native integer')
    if 'name' not in record:
        if event is None:
            raise ValueError('unnamed pickup requires source_event')
        record['name'] = 'item_' + str(event)
    quantity = record.setdefault('quantity', 1)
    if type(quantity) is not int or not 0 < quantity <= 9223372036854775807:
        raise ValueError('quantity must be a positive native integer')


def _ungroup(data):
    if 'objects' in data:
        raise ValueError('v2 maps use typed object arrays, not objects')
    records = []
    present = False
    for section, kind in GROUPS.items():
        if section not in data:
            continue
        present = True
        group = data.pop(section)
        if not isinstance(group, list):
            raise ValueError(section + ' must be an array')
        for record in group:
            if not isinstance(record, dict) or 'kind' in record:
                raise ValueError(section + ' entries must be objects without a redundant kind')
            if section == 'interactables':
                if (not isinstance(record.get('interaction'), dict) or not record['interaction'].get('kind')
                        or 'item' in record or 'quantity' in record):
                    raise ValueError('interactables require an interaction, not an item reward')
            elif section == 'items' and 'interaction' in record:
                raise ValueError('non-item interactions belong in interactables')
            if section == 'items' and ('item' in record or 'quantity' in record):
                _pickup_defaults(record)
            records.append(dict(record, kind=kind))
    if present:
        data['objects'] = records
    return data


def _group(data):
    if set(data) & set(GROUPS):
        raise ValueError('v1 maps use objects, not typed object arrays')
    objects = data.pop('objects', [])
    grouped = {section: [] for section in GROUPS}
    sections = {'npc': 'npcs', 'item': 'items', 'sign': 'signs'}
    for record in objects:
        kind = record.pop('kind', None)
        if not isinstance(kind, str) or kind not in sections:
            raise ValueError('unsupported object kind: ' + repr(kind))
        section = 'interactables' if kind == 'item' and 'interaction' in record else sections[kind]
        if section == 'items' and 'item' in record:
            event = record.get('source_event')
            if type(event) is int and 0 <= event <= 2147483647 and record.get('name') == 'item_' + str(event):
                record.pop('name')
            if type(record.get('quantity')) is int and record['quantity'] == 1:
                record.pop('quantity')
        grouped[section].append(record)
    for section, records in grouped.items():
        if records:
            data[section] = records
    return data


def legacy_map(data, ordered=False):
    """Copy a v1/v2 map into the existing Python/native v1 representation.

    Reject conflicting encodings rather than choosing a coordinate silently.
    The wire-format marker is consumed; extensions outside known coordinate fields stay.
    V2 decodes NPCs/items/signs/interactables, retaining order within each group.
    Interactables use the legacy item-sprite kind solely for native compatibility.
    `ordered` keeps x/y (and a wander box's corners) where the coordinate pair
    was in the record; by default they move to the end of it.
    Names need not be unique. Cross-group order is not part of the v2 contract.
    Identified pickups in v2 default quantity to 1 and derive absent names from
    source_event. Geometry/flag validation remains the runtime schema's responsibility.
    """
    if not isinstance(data, dict):
        raise ValueError('map must be an object')
    result = copy.deepcopy(data)
    version = result.pop('format', LEGACY)
    if version == COMPACT:
        return _records(_ungroup(result), compact=False, ordered=ordered)
    if version != LEGACY:
        raise ValueError('unsupported runtime map format: ' + repr(version))
    # Check spelling and grouping without altering the legacy representation.
    _group(_records(copy.deepcopy(result), compact=True))
    return result


def compact_map(data):
    """Copy to typed object arrays and coordinate pairs, preserving record data.

    Empty groups and redundant pickup names/quantity 1 are omitted.
    Record order stays stable within each kind;
    consumers must use explicit names/coordinates rather than cross-kind indices.
    """
    result = _group(_records(legacy_map(data), compact=True))
    return dict(format=COMPACT, **{key: value for key, value in result.items() if key != 'format'})

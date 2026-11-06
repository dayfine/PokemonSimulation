"""Coordinate-array wire format for runtime maps; legacy readers use legacy_map().

Only schema-owned coordinates are converted. Unknown extensions and zero/false
values survive unchanged. Format 2 is staged: existing consumer pins remain v1.
"""

import copy

LEGACY = 'pokesim-runtime-map/1'
COMPACT = 'pokesim-runtime-map/2'
SECTIONS = ('objects', 'warps', 'patches', 'coord_events')
GROUPS = {'npcs': 'npc', 'items': 'item', 'signs': 'sign'}


def _pair(value, label):
    if not isinstance(value, list) or len(value) != 2 or any(type(n) is not int for n in value):
        raise ValueError(label + ' must be an array of two integers')
    return value


def _convert_pair(record, old, new, compact):
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
        value = _pair(record.pop(new), new)
        record.update(zip(old, value))


def _records(data, compact):
    for section in SECTIONS:
        records = data.get(section, [])
        if not isinstance(records, list):
            raise ValueError(section + ' must be an array')
        for record in records:
            _convert_pair(record, ('x', 'y'), 'coord', compact)
            if section == 'objects' and 'wander' in record:
                box = record['wander']
                _convert_pair(box, ('x0', 'y0'), 'min', compact)
                _convert_pair(box, ('x1', 'y1'), 'max', compact)
    return data


def _ungroup(data):
    if 'objects' in data:
        raise ValueError('v2 maps use npcs/items/signs, not objects')
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
            records.append(dict(record, kind=kind))
    if present:
        data['objects'] = records
    return data


def _group(data):
    if set(data) & set(GROUPS):
        raise ValueError('v1 maps use objects, not npcs/items/signs')
    objects = data.pop('objects', [])
    grouped = {kind: [] for kind in GROUPS.values()}
    for record in objects:
        kind = record.pop('kind', None)
        if not isinstance(kind, str) or kind not in grouped:
            raise ValueError('unsupported object kind: ' + repr(kind))
        grouped[kind].append(record)
    for section, kind in GROUPS.items():
        if grouped[kind]:
            data[section] = grouped[kind]
    return data


def legacy_map(data):
    """Copy a v1/v2 map into the existing Python/native v1 representation.

    Reject conflicting encodings rather than choosing a coordinate silently.
    The wire-format marker is consumed; extensions outside known coordinate fields stay.
    V2 groups decode in NPC/item/sign order, retaining order within each kind.
    Names need not be unique. Cross-kind order is not part of the v2 contract.
    Geometry/flag validation remains the runtime schema's responsibility.
    """
    if not isinstance(data, dict):
        raise ValueError('map must be an object')
    result = copy.deepcopy(data)
    version = result.pop('format', LEGACY)
    if version == COMPACT:
        return _records(_ungroup(result), compact=False)
    if version != LEGACY:
        raise ValueError('unsupported runtime map format: ' + repr(version))
    # Check spelling and grouping without altering the legacy representation.
    _group(_records(copy.deepcopy(result), compact=True))
    return result


def compact_map(data):
    """Copy to typed object arrays and coordinate pairs, preserving record data.

    Empty groups are omitted. Record order stays stable within each kind;
    consumers must use explicit names/coordinates rather than cross-kind indices.
    """
    result = _group(_records(legacy_map(data), compact=True))
    return dict(format=COMPACT, **{key: value for key, value in result.items() if key != 'format'})

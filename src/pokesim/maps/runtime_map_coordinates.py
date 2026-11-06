"""Coordinate-array wire format for runtime maps; legacy readers use legacy_map().

Only schema-owned coordinates are converted. Unknown extensions and zero/false
values survive unchanged. Format 2 is staged: existing consumer pins remain v1.
"""

import copy

LEGACY = 'pokesim-runtime-map/1'
COMPACT = 'pokesim-runtime-map/2'
SECTIONS = ('objects', 'warps', 'patches', 'coord_events')


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


def legacy_map(data):
    """Copy a v1/v2 map into the existing Python/native v1 representation.

    Reject conflicting encodings rather than choosing a coordinate silently.
    The wire-format marker is consumed; extensions outside known coordinate fields stay.
    Geometry/flag validation remains the runtime schema's responsibility.
    """
    if not isinstance(data, dict):
        raise ValueError('map must be an object')
    result = copy.deepcopy(data)
    version = result.pop('format', LEGACY)
    if version == COMPACT:
        return _records(result, compact=False)
    if version != LEGACY:
        raise ValueError('unsupported runtime map format: ' + repr(version))
    # Validate the legacy coordinate spelling without altering its representation.
    _records(copy.deepcopy(result), compact=True)
    return result


def compact_map(data):
    """Copy a map to v2: coord=[x,y], wander.min/max=[x,y]; no field elision."""
    result = _records(legacy_map(data), compact=True)
    return dict(format=COMPACT, **{key: value for key, value in result.items() if key != 'format'})

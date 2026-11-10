r"""Map overlays: a generated base plus authored operations (docs/maps/OVERLAYS.md).

Each FRLG map has three published files:

- ``maps/base/<Map>.json``: the generator's output, never edited by hand
  (``frlg_decomp_map_builder --check`` reproduces it byte for byte).
- ``maps/overlays/<Map>.json`` (optional): the ordered operations authored on
  top of the base, each with why, when, evidence and status
  (``schemas/map-overlay.schema.json``).
- ``maps/runtime/<Map>.json``: the effective map at ``RUNTIME_STORY_STATE``,
  pre-resolved for consumers that do not apply overlays yet. It is derived,
  never edited: ``check`` fails if it differs from base + overlays.

From the repository root:

    PYTHONPATH=src python3 -m pokesim.maps.map_overlays audit VermilionCity_Gym
    PYTHONPATH=src python3 -m pokesim.maps.map_overlays audit --all
    PYTHONPATH=src python3 -m pokesim.maps.map_overlays effective VermilionCity_Gym --checkpoint 00.23
    PYTHONPATH=src python3 -m pokesim.maps.map_overlays check
    PYTHONPATH=src python3 -m pokesim.maps.map_overlays write

``write`` regenerates every runtime file from base + overlays and refreshes the
FRLG manifest entries (runtime hash and source, base and overlay references);
statuses are kept.
"""

import argparse
import copy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
import sys

from pokesim.formats.contract_format import json_text as contract_json_text
from .runtime_map_coordinates import compact_map, legacy_map
from .runtime_map_schema import validate
from .runtime_symbols import SYMBOLS


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / 'data/maps/runtime-manifest.json'
FORMAT = 'pokesim-map-overlay/1'
GAMES = ('frlg',)
OPS = ('tile', 'link', 'object', 'trigger', 'point')
WHYS = ('console_measured', 'remake_delta', 'story_state', 'generator_gap')
STATUSES = ('candidate', 'verified')
#   The story state the published runtime files are resolved at: every
#   operation applies, as for a player past every `when`. This matches what
#   the runtime files held before overlays (Vermilion Gym's beams open).
RUNTIME_STORY_STATE = 'complete'
CHECKPOINT = re.compile(r'(\d+)([a-z]*)\Z')


def directory(game, kind):
    return f'data/games/{game}/maps/{kind}'


def path_of(game, kind, name, root=ROOT):
    return Path(root) / directory(game, kind) / (name + '.json')


@dataclass(frozen=True)
class StoryState:
    """Where the story is: the checkpoint about to run (or running) and the
    flags known set. ``complete`` is past every `when`."""
    checkpoint: str = None
    flags: frozenset = field(default_factory=frozenset)
    complete: bool = False


COMPLETE = StoryState(complete=True)
NEW_GAME = StoryState()


def checkpoint_key(checkpoint):
    """Order checkpoint ids such as '00.12', '00.12b', '01.03'."""
    parts = []
    for part in checkpoint.split('.'):
        match = CHECKPOINT.fullmatch(part)
        if not match:
            raise ValueError('invalid checkpoint id: ' + repr(checkpoint))
        parts.append((int(match.group(1)), match.group(2)))
    return tuple(parts)


def applies(operation, state):
    """Whether an operation is in effect at this story state. One without
    `when` always is; one with `when` is once its flag is set or once the
    story is past its checkpoint (the state's checkpoint is later)."""
    when = operation.get('when')
    if when is None or state.complete:
        return True
    if 'flag' in when and when['flag'] in state.flags:
        return True
    return ('after_checkpoint' in when and state.checkpoint is not None
            and checkpoint_key(state.checkpoint) > checkpoint_key(when['after_checkpoint']))


def check_overlay(overlay, name=None):
    """Raise ValueError unless the overlay is structurally valid (the schema
    plus the cross-field rules it cannot say)."""
    if not isinstance(overlay, dict) or set(overlay) != {'format', 'map', 'operations'}:
        raise ValueError('overlay needs exactly format, map and operations')
    if overlay['format'] != FORMAT:
        raise ValueError('unsupported overlay format: ' + repr(overlay['format']))
    if name is not None and overlay['map'] != name:
        raise ValueError(f'overlay for {overlay["map"]} is in the file of {name}')
    if not isinstance(overlay['operations'], list) or not overlay['operations']:
        raise ValueError(overlay['map'] + ': an overlay file has at least one operation')
    for index, op in enumerate(overlay['operations']):
        where = f'{overlay["map"]} operation {index}'
        if op.get('op') not in OPS:
            raise ValueError(where + ': op must be one of ' + ', '.join(OPS))
        if op.get('why') not in WHYS:
            raise ValueError(where + ': why must be one of ' + ', '.join(WHYS))
        if op.get('status') not in STATUSES:
            raise ValueError(where + ': status must be one of ' + ', '.join(STATUSES))
        if not isinstance(op.get('evidence'), dict) or not op['evidence']:
            raise ValueError(where + ': evidence is required')
        when = op.get('when')
        if (op['why'] == 'story_state') != (when is not None):
            raise ValueError(where + ': `when` is required for story_state and only for it')
        if when is not None:
            if not isinstance(when, dict) or not when or set(when) - {'flag', 'after_checkpoint'}:
                raise ValueError(where + ': when needs flag and/or after_checkpoint')
            if 'after_checkpoint' in when:
                checkpoint_key(when['after_checkpoint'])
        if op['op'] == 'tile' and op.get('glyph') not in SYMBOLS:
            raise ValueError(where + ': unknown tile glyph ' + repr(op.get('glyph')))
        if op['why'] == 'generator_gap' and not op['evidence'].get('generator_fix'):
            raise ValueError(where + ': a generator_gap names the generator fix that removes it')
    return overlay


def _coord(value, where):
    if (not isinstance(value, list) or len(value) != 2
            or not all(type(v) is int and v >= 0 for v in value)):
        raise ValueError(where + ': coordinate must be [x, y]')
    return value


def _apply(data, op, where):
    """Apply one operation to a legacy-form map in place; describe its effect.
    An operation that changes nothing is an error: it is stale."""
    kind = op['op']
    effects = []
    if kind == 'tile':
        rows = [list(row) for row in data['tiles']]
        for coord in op['coords']:
            x, y = _coord(coord, where)
            if y >= len(rows) or x >= len(rows[0]):
                raise ValueError(f'{where}: tile ({x}, {y}) is off the map')
            if rows[y][x] == op['glyph']:
                raise ValueError(f'{where}: tile ({x}, {y}) is already {op["glyph"]!r}')
            effects.append(f'tile ({x}, {y}) {rows[y][x]!r} -> {op["glyph"]!r}')
            rows[y][x] = op['glyph']
        data['tiles'] = [''.join(row) for row in rows]
    elif kind == 'point':
        points = data.setdefault('points', {})
        old = points.get(op['name'])
        if op.get('remove'):
            if old is None:
                raise ValueError(f'{where}: no point {op["name"]} to remove')
            del points[op['name']]
            effects.append(f'point {op["name"]} {old} removed')
        else:
            new = _coord(op['coord'], where)
            if old == new:
                raise ValueError(f'{where}: point {op["name"]} is already {new}')
            points[op['name']] = list(new)
            effects.append(f'point {op["name"]} {old} -> {new}')
    elif kind == 'link' and op['kind'] == 'warp':
        warps = data.get('warps', [])
        if not 0 <= op['index'] < len(warps):
            raise ValueError(f'{where}: no warp {op["index"]}')
        warp = warps[op['index']]
        old = (warp.get('to_map'), warp.get('to_point'))
        new = (op.get('to_map'), op.get('to_point'))
        if old == new:
            raise ValueError(f'{where}: warp {op["index"]} already leads to {new}')
        for key, value in zip(('to_map', 'to_point'), new):
            if value is None:
                warp.pop(key, None)
            else:
                warp[key] = value
        effects.append(f'warp {op["index"]} {old} -> {new}')
    elif kind == 'link' and op['kind'] == 'connection':
        connections = data.setdefault('connections', [])
        record = {'side': op['side'], 'to_map': op['to_map'], 'offset': op['offset']}
        if op['action'] == 'add':
            if record in connections:
                raise ValueError(f'{where}: connection {record} already exists')
            connections.append(record)
        else:
            if record not in connections:
                raise ValueError(f'{where}: no connection {record} to remove')
            connections.remove(record)
        effects.append(f'connection {op["action"]} {record}')
    elif kind == 'object':
        objects = data.setdefault('objects', [])
        if op['action'] == 'add':
            record = copy.deepcopy(op['object'])
            x, y = _coord(record.pop('coord'), where)
            record['x'], record['y'] = x, y
            objects.append(record)
            effects.append(f'object {record["name"]} added at ({x}, {y})')
        else:
            x, y = _coord(op['at'], where)
            found = [o for o in objects if o.get('name') == op['name'] and (o['x'], o['y']) == (x, y)]
            if len(found) != 1:
                raise ValueError(f'{where}: expected one {op["name"]} at ({x}, {y}), found {len(found)}')
            if op['action'] == 'remove':
                objects.remove(found[0])
                effects.append(f'object {op["name"]} at ({x}, {y}) removed')
            else:
                to = _coord(op['to'], where)
                found[0]['x'], found[0]['y'] = to
                effects.append(f'object {op["name"]} ({x}, {y}) -> ({to[0]}, {to[1]})')
    else:
        raise ValueError(f'{where}: {kind} operations are not supported by this map format yet')
    return effects


def resolve(base, overlay, state=COMPLETE):
    """The effective map: a copy of `base` (wire or legacy form) with the
    overlay operations that apply at `state`, in order. Returns (map in
    legacy form, [(operation, effects)] of the applied operations)."""
    data = legacy_map(base)
    applied = []
    if overlay is not None:
        check_overlay(overlay, data['name'])
        for index, op in enumerate(overlay['operations']):
            if applies(op, state):
                applied.append((op, _apply(data, op, f'{data["name"]} operation {index}')))
    validate(data)
    return data, applied


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def read_overlay(name, game='frlg', root=ROOT):
    path = path_of(game, 'overlays', name, root)
    return check_overlay(read_json(path), name) if path.exists() else None


def effective_map(name, story_state=COMPLETE, game='frlg', root=ROOT):
    """Base + the overlay operations that apply at `story_state` (legacy form)."""
    return resolve(read_json(path_of(game, 'base', name, root)), read_overlay(name, game, root), story_state)[0]


def runtime_bytes(name, game='frlg', root=ROOT):
    """The published runtime file: the base's bytes when the map has no
    overlay, else the effective map at RUNTIME_STORY_STATE, stamped with it."""
    base_path = path_of(game, 'base', name, root)
    overlay = read_overlay(name, game, root)
    if overlay is None:
        return base_path.read_bytes()
    data, _ = resolve(read_json(base_path), overlay, COMPLETE)
    data['source']['overlay'] = {'file': directory(game, 'overlays') + f'/{name}.json',
                                 'story_state': RUNTIME_STORY_STATE}
    return contract_json_text(compact_map(data)).encode('utf-8')


def names(game='frlg', root=ROOT):
    return sorted(p.stem for p in (Path(root) / directory(game, 'base')).glob('*.json'))


def overlay_names(game='frlg', root=ROOT):
    return sorted(p.stem for p in (Path(root) / directory(game, 'overlays')).glob('*.json'))


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def file_ref(game, kind, name, root=ROOT):
    path = path_of(game, kind, name, root)
    return {'file': f'{directory(game, kind)}/{name}.json', 'sha256': sha256(path.read_bytes())}


def pack_refs(name, game='frlg', root=ROOT):
    """The manifest's base and (if any) overlay references for a map."""
    refs = {'base': file_ref(game, 'base', name, root)}
    if path_of(game, 'overlays', name, root).exists():
        refs['overlay'] = file_ref(game, 'overlays', name, root)
    return refs


def audit(name, game='frlg', root=ROOT):
    """Every difference of the map from its base, grouped by why. Returns text."""
    overlay = read_overlay(name, game, root)
    lines = [f'{name}: base {directory(game, "base")}/{name}.json']
    if overlay is None:
        lines.append('  no overlay: the effective map is the base at every story state')
        return '\n'.join(lines)
    _, applied = resolve(read_json(path_of(game, 'base', name, root)), overlay, COMPLETE)
    for why in WHYS:
        group = [(op, effects) for op, effects in applied if op['why'] == why]
        if not group:
            continue
        lines.append(f'  {why}: {len(group)} operation(s)')
        for op, effects in group:
            when = op.get('when')
            when_text = ' when ' + ', '.join(f'{k}={v}' for k, v in when.items()) if when else ''
            lines.append(f'    {op["op"]} [{op["status"]}]{when_text}')
            lines.extend('      ' + effect for effect in effects)
            lines.append('      evidence: ' + json.dumps(op['evidence'], sort_keys=True))
    return '\n'.join(lines)


def check(game='frlg', root=ROOT, manifest_path=MANIFEST):
    """Raise ValueError unless every overlay applies cleanly, every runtime
    file is base + overlays at RUNTIME_STORY_STATE and the manifest records
    the runtime, base and overlay hashes."""
    errors = []
    base = set(names(game, root))
    runtime = {p.stem for p in (Path(root) / directory(game, 'runtime')).glob('*.json')}
    if base != runtime:
        errors.append('base and runtime inventories differ: ' + ' '.join(sorted(base ^ runtime)))
    stray = set(overlay_names(game, root)) - base
    if stray:
        errors.append('overlays without a base map: ' + ' '.join(sorted(stray)))
    entries = {e['name']: e for e in json.loads(Path(manifest_path).read_text())['games'][game]['maps']}
    for name in sorted(base & runtime):
        try:
            expected = runtime_bytes(name, game, root)
        except ValueError as error:
            errors.append(str(error))
            continue
        if path_of(game, 'runtime', name, root).read_bytes() != expected:
            errors.append(name + ': runtime file is not base + overlays; run map_overlays write')
        entry = entries.get(name)
        if entry is None:
            errors.append(name + ': no manifest entry')
            continue
        if entry.get('sha256') != sha256(expected):
            errors.append(name + ': manifest runtime sha256 is stale')
        refs = pack_refs(name, game, root)
        for key in ('base', 'overlay'):
            if entry.get(key) != refs.get(key):
                errors.append(f'{name}: manifest {key} reference is stale')
    if errors:
        raise ValueError('\n'.join(errors))
    return len(base)


def write(game='frlg', root=ROOT, manifest_path=MANIFEST):
    """Write every runtime file from base + overlays and refresh the manifest
    entries' runtime hash/source and base/overlay references."""
    manifest = json.loads(Path(manifest_path).read_text())
    entries = {e['name']: e for e in manifest['games'][game]['maps']}
    for name in names(game, root):
        raw = runtime_bytes(name, game, root)
        path_of(game, 'runtime', name, root).write_bytes(raw)
        entry = entries.get(name)
        if entry is None:
            continue    # frlg_map_set sync-candidates adds new maps
        entry['sha256'] = sha256(raw)
        entry['source'] = legacy_map(json.loads(raw))['source']
        entry.pop('base', None)
        entry.pop('overlay', None)
        entry.update(pack_refs(name, game, root))
    Path(manifest_path).write_text(json.dumps(manifest, indent=2) + '\n')


def _state(args):
    if args.complete:
        return COMPLETE
    return StoryState(checkpoint=args.checkpoint, flags=frozenset(args.flag or ()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--game', default='frlg', choices=GAMES)
    sub = parser.add_subparsers(dest='command', required=True)
    up = sub.add_parser('audit', help='list a map\'s differences from its base, grouped by why')
    up.add_argument('map', nargs='?')
    up.add_argument('--all', action='store_true', help='every map with an overlay')
    up = sub.add_parser('effective', help='print the effective map at a story state')
    up.add_argument('map')
    up.add_argument('--checkpoint', help='the checkpoint about to run, e.g. 00.24')
    up.add_argument('--flag', action='append', help='a flag known set (repeatable)')
    up.add_argument('--complete', action='store_true', help='past every `when` (the runtime files)')
    sub.add_parser('check', help='check overlays, runtime files and manifest references')
    sub.add_parser('write', help='write runtime files and manifest references from base + overlays')
    args = parser.parse_args(argv)
    try:
        if args.command == 'audit':
            if args.all == bool(args.map):
                parser.error('give a map or --all')
            for name in (overlay_names(args.game) if args.all else [args.map]):
                print(audit(name, args.game))
        elif args.command == 'effective':
            data = effective_map(args.map, _state(args), args.game)
            sys.stdout.write(contract_json_text(compact_map(data)))
        elif args.command == 'check':
            count = check(args.game)
            print(f'{count} {args.game} runtime maps are base + overlays at story state {RUNTIME_STORY_STATE}; '
                  f'{len(overlay_names(args.game))} overlay file(s)')
        else:
            write(args.game)
    except (ValueError, FileNotFoundError) as error:
        parser.exit(1, str(error) + '\n')


if __name__ == '__main__':
    main()

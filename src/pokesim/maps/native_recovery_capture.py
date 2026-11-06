"""Shared literal encoding and integrity checks for native replay captures.

Game adapters retain their own report and policy semantics. These helpers do
not decide movement, localization or recovery.
"""
import configparser
import hashlib
import json
from pathlib import Path
import re
from .consumer_source import read_json
from pokesim.grid.movement import Hop, Moved, world_step
from .transition_state import Pose


def same(actual, expected, label):
    if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
        raise ValueError(label + ': expected ' + repr(expected) + ', got ' + repr(actual))


def native_git(root, *args):
    import subprocess
    result = subprocess.run(['git', '-C', str(root), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError('native git: ' + result.stderr.decode(errors='replace'))
    return result.stdout


def format_trace(value, width=100):
    """Indent objects; keep scalar arrays inline when the full line fits."""
    def render(item, depth, column):
        inline = json.dumps(item)
        if not isinstance(item, (dict, list)) or not item:
            return inline
        if isinstance(item, list) and all(not isinstance(v, (dict, list)) for v in item):
            if column + len(inline) <= width:
                return inline
        pad = '  ' * (depth + 1)
        if isinstance(item, dict):
            lines = []
            for key, child in item.items():
                prefix = pad + json.dumps(key) + ': '
                lines.append(prefix + render(child, depth + 1, len(prefix)))
            opening, closing = '{', '}'
        else:
            lines = [pad + render(child, depth + 1, len(pad)) for child in item]
            opening, closing = '[', ']'
        return opening + '\n' + ',\n'.join(lines) + '\n' + '  ' * depth + closing

    return render(value, 0, 0) + '\n'


def keys(value, expected):
    if set(value) != set(expected.split()):
        raise ValueError('missing or unknown text-trace fields: ' + repr(set(value)))


def boolean(value):
    if value not in ('true', 'false'):
        raise ValueError('expected true or false')
    return value == 'true'


def pose_text(pose):
    return '({},{}) {}'.format(*pose['tile'], pose['facing'] or '?')


def parse_pose(text, context):
    match = re.fullmatch(r'\((\d+),(\d+)\) (north|south|east|west|\?)', text)
    if not match:
        raise ValueError('invalid pose: ' + text)
    return dict(map=context['map'], tile=[int(match[1]), int(match[2])],
                facing=None if match[3] == '?' else match[3], elevation=int(context['elevation']))


def milliseconds(text):
    if not re.fullmatch(r'\d+ms', text):
        raise ValueError('expected milliseconds: ' + text)
    return int(text[:-2])


def assignments(tokens):
    pairs = [token.split('=', 1) for token in tokens]
    if any(len(p) != 2 for p in pairs) or len({p[0] for p in pairs}) != len(pairs):
        raise ValueError('invalid/duplicate call fields')
    return dict(pairs)


def diagnostic_source(path):
    """Locate the explicit diagnostic and its checksum beside a readable trace."""
    path = Path(path)
    source = configparser.ConfigParser(interpolation=None, delimiters=('=',), empty_lines_in_values=False)
    source.read_string(path.read_text())
    relative = Path(source['source']['diagnostic'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('diagnostic must be inside the trace directory')
    return path.parent / relative, source['source']['diagnostic_sha256']


def write_checked_text(bundle, path, raw_text, encoder, decoder, projection):
    path = Path(path)
    relative = Path('diagnostics') / (path.stem + '.raw.json')
    raw = raw_text.encode()
    text = encoder(bundle, relative.as_posix(), hashlib.sha256(raw).hexdigest())
    same(projection(decoder(text)), projection(bundle), 'readable encoding preserves replay facts')
    (path.parent / relative).parent.mkdir(parents=True, exist_ok=True)
    (path.parent / relative).write_bytes(raw)
    path.write_text(text)


def read_checked_text(path, decoder, projection):
    bundle = decoder(Path(path).read_text())
    diagnostic, checksum = diagnostic_source(path)
    raw = diagnostic.read_bytes()
    if hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError('raw diagnostic checksum mismatch')
    if json.dumps(projection(bundle), sort_keys=True) != json.dumps(projection(read_json(raw)), sort_keys=True):
        raise ValueError('readable trace differs from raw diagnostic replay facts')
    return bundle


def advance(world, pose, direction, count):
    for _ in range(count):
        moved = world_step(world, pose.state, direction)
        if not isinstance(moved, Moved) or isinstance(moved, Hop):
            raise ValueError('native replay profile requires ordinary same-map steps')
        pose = Pose(moved.state, direction)
    return pose


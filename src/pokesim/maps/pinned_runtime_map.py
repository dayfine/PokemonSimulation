"""Load exact historical replay bytes without fetching or changing a consumer pin.

Current bytes are accepted only on an exact hash match. Otherwise the fixture's
immutable Git revision is read locally. Shallow clones need that history supplied
explicitly; no mutable fallback or network lookup is attempted.
"""

import hashlib
from pathlib import Path
import subprocess

from .consumer_source import DIGEST, NAME, SHA
from .runtime_map_pack import ROOT


def read_pinned_map(revision, game, name, digest, root=ROOT):
    """Read and hash-check the fixture's map, or fail with its missing pin named."""
    if (not isinstance(revision, str) or not SHA.fullmatch(revision)
            or game not in ('frlg', 'bdsp') or not NAME.fullmatch(name)
            or not DIGEST.fullmatch(digest)):
        raise ValueError('invalid historical map pin')
    path = 'data/games/{}/maps/runtime/{}.json'.format(game, name)
    current = Path(root) / path
    raw = current.read_bytes() if current.is_file() else b''
    if hashlib.sha256(raw).hexdigest() == digest:
        return raw
    result = subprocess.run(['git', '-C', str(root), 'show', revision + ':' + path],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise ValueError('map hash mismatch or missing historical map: ' + name
                         + '; provide local Git history for ' + revision)
    if hashlib.sha256(result.stdout).hexdigest() != digest:
        raise ValueError('map hash mismatch at historical pin: ' + name)
    return result.stdout

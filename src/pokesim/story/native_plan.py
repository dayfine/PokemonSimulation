"""Replay an authoritative Arduino plan from a pinned local Git checkout.

Example (fetch the Arduino repository separately; this command never fetches):
    PYTHONPATH=src python3 -m pokesim.story.native_plan \
      data/story/bdsp-mine-pilot/source.json --checkout ../Arduino-Source

The checked-in pilot plan is a frozen test snapshot. Explicit native input
replaces its binding pin only in a temporary profile, without editing fixtures.
"""

import argparse
import hashlib
import re
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

from pokesim.formats.contract_format import json_text
from pokesim.maps.consumer_source import read_json
from pokesim.maps.runtime_map_pack import ROOT
from .checkpoint_replay import run
from .replay_binding import load_binding
from .replay_cases import read_cases, check_case
from .replay_handlers import exact

REPOSITORY = 'dayfine/Arduino-Source'


def read_pinned_plan(pin_path, checkout):
    """Read committed bytes, not mutable worktree contents, and verify identity/hash."""
    pin = read_json(Path(pin_path).read_bytes())
    exact(pin, 'format repository revision file sha256')
    if pin['format'] != 'pokesim-native-plan-source/1' or pin['repository'] != REPOSITORY:
        raise ValueError('unsupported native plan source')
    if not re.fullmatch(r'[0-9a-f]{40}', pin['revision']) or not re.fullmatch(r'[0-9a-f]{64}', pin['sha256']):
        raise ValueError('native plan needs full immutable revision and SHA-256')
    path = PurePosixPath(pin['file'])
    if path.is_absolute() or '..' in path.parts or not path.parts or ':' in pin['file']:
        raise ValueError('native plan file must be a repository-relative path')
    def git(*args):
        result = subprocess.run(['git', '-C', str(checkout), *args], capture_output=True)
        if result.returncode:
            raise ValueError('native plan Git lookup failed; fetch the pinned revision separately')
        return result.stdout
    origin = git('remote', 'get-url', 'origin').decode().strip()
    if origin not in ('https://github.com/' + REPOSITORY, 'https://github.com/' + REPOSITORY + '.git',
                       'git@github.com:' + REPOSITORY + '.git'):
        raise ValueError('checkout is not the pinned Arduino repository')
    raw = git('show', pin['revision'] + ':' + pin['file'])
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('native plan hash mismatch')
    return raw


def replay_plan(raw, profile_path, cases_path, root=ROOT):
    """Replay explicit authoritative bytes; independent scenario expectations still apply."""
    root = Path(root).resolve()
    profile = read_json(Path(profile_path).read_bytes())
    if 'plan' not in profile or 'capture' in profile:
        raise ValueError('native plan replay requires an authored binding')
    with tempfile.TemporaryDirectory(prefix='.native-story-', dir=root) as temporary:
        stage = Path(temporary)
        (stage / 'plan.json').write_bytes(raw)
        profile['plan'] = {'file': str((stage / 'plan.json').relative_to(root)),
                           'sha256': hashlib.sha256(raw).hexdigest()}
        (stage / 'binding.json').write_text(json_text(profile))
        binding = load_binding(stage / 'binding.json', root)
        return [check_case(case, run(binding, case['input'])) for case in read_cases(cases_path)]


def main(argv=None):
    """Load the source pin beside a pilot binding/cases and report semantic results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--checkout', required=True, type=Path)
    args = parser.parse_args(argv)
    folder = args.source.parent
    raw = read_pinned_plan(args.source, args.checkout)
    for result in replay_plan(raw, folder / 'binding.json', folder / 'cases.json'):
        print('{}: outcomes {}; actions {}'.format(result['id'], result['outcomes'], result['actions']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""Validate/import an evaluated native checkpoint capture; never execute it.

    python3 -m pip install -r schemas/requirements.txt
    PYTHONPATH=src python3 -m pokesim.story.native_export frlg-parcel.native.json \
        --expected-revision COMMIT_SHA --out /tmp/frlg-parcel.capture.json

This authoring tool uses the local JSON Schema registry and the common semantic
reader. Unknown game fields fail; bookkeeping does not become entry evidence.
"""

import argparse
import copy
import json
from pathlib import Path

from pokesim.formats.contract_format import json_text
from pokesim.formats.json_schema import validator
from .checkpoint_wire import read_checkpoint


def read_native_export(value, expected_revision=None):
    """Validate the current FRLG extension and preserve all supplied fields.

    Runtime settings, data pins, policy binding and observations stay unbound.
    The optional revision comes from independent build/run metadata, not a
    revision guessed from the fixture. Source identity alone is not provenance
    authentication; canonical captures come from clean native CI artifacts.
    """
    from jsonschema import ValidationError
    try:
        validator('native-checkpoint-export').validate(value)
    except ValidationError as error:
        raise ValueError('{}: {}'.format(error.json_path, error.message)) from error
    if expected_revision is not None and value['source_revision'] != expected_revision:
        raise ValueError('native capture source revision does not match expected build')
    result = copy.deepcopy(value)
    result['checkpoint'] = read_checkpoint(value['checkpoint'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--expected-revision')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    try:
        value = read_native_export(json.loads(args.capture.read_text()), args.expected_revision)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, str(error) + '\n')
    formatted = json_text(value)
    if args.out:
        args.out.write_text(formatted, encoding='utf-8')
    else:
        print(formatted, end='')


if __name__ == '__main__':
    main()

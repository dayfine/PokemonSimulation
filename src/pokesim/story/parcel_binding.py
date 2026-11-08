"""Bind the captured Parcel row to a deliberately limited offline profile.

The profile is a simulation diagnostic, not the native runtime configuration.
It never supplies missing native save/retry options or observed party state.
"""

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

from pokesim.maps.consumer_source import read_json
from pokesim.maps.local_routing import LocalMap
from pokesim.maps.pinned_runtime_map import read_pinned_map
from pokesim.maps.runtime_map_pack import ROOT
from pokesim.maps.runtime_world import RuntimeWorld
from pokesim.grid.routing.shortest import Costs
from .checkpoint_wire import read_checkpoint

PROFILE = ROOT / 'data/story/parcel-pilot/binding.json'
CAPABILITIES = {'route': 'frlg-runtime-route/1', 'step': 'frlg-runtime-step/1',
                'scene': 'scripted-parcel-scene/1'}
OFFLINE_POLICY = {'basis': 'synthetic-offline-policy', 'entry': 'scripted-observation',
                  'attempts': 1, 'failure': 'stop', 'save': 'never'}


def exact(value, keys):
    """Reject unknown or missing fields at the pilot binding boundary."""
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError('expected exactly: ' + keys)
    return value


def positive(value):
    """A finite positive press count, not a boolean or unbounded budget."""
    if type(value) is not int or not 1 <= value <= 4096:
        raise ValueError('press budget must be an integer in 1..4096')
    return value


@dataclass
class ParcelBinding:
    """Validated capture, model and explicit simulation-only execution options."""
    capture: dict
    checkpoint: dict
    world: RuntimeWorld
    costs: Costs
    max_route_presses: int
    profile_sha256: str


def load_binding(path=PROFILE, root=ROOT):
    """Preflight every binding/hash before any replay action; never fetch data."""
    raw = Path(path).read_bytes()
    config = exact(read_json(raw), 'format capture map_revision maps capabilities costs max_route_presses policy')
    if (config['format'] != 'pokesim-frlg-parcel-pilot/1' or config['policy'] != OFFLINE_POLICY
            or type(config['policy'].get('attempts')) is not int):
        raise ValueError('unsupported offline profile/policy; native options remain unbound')
    pin = exact(config['capture'], 'file sha256 source_revision')
    source = Path(root).resolve()
    capture_path = (source / pin['file']).resolve()
    if source not in capture_path.parents:
        raise ValueError('capture must be inside the source repository')
    capture_raw = capture_path.read_bytes()
    if hashlib.sha256(capture_raw).hexdigest() != pin['sha256']:
        raise ValueError('capture hash mismatch')
    capture = read_json(capture_raw)
    if (capture['format'] != 'pokesim-native-checkpoint-export/1'
            or capture['game'] != 'frlg' or capture['source_revision'] != pin['source_revision']
            or capture['state_basis'] != 'native-table-bookkeeping'):
        raise ValueError('unsupported capture identity/state basis')
    checkpoint = read_checkpoint(capture['checkpoint'])
    if checkpoint['id'] != '00.05' or [e['kind'] for e in checkpoint['events']] != ['route', 'step', 'scene']:
        raise ValueError('profile supports only the Parcel route/step/scene row')
    allowed = {'route': {'id', 'kind', 'why', 'target'},
               'step': {'id', 'kind', 'why', 'direction'},
               'scene': {'id', 'kind', 'why', 'declared_after'}}
    for event in checkpoint['events']:
        if set(event) - allowed[event['kind']]:
            raise ValueError('unsupported event options in the Parcel profile')
    expected = {e['id']: CAPABILITIES[e['kind']] for e in checkpoint['events']}
    if config['capabilities'] != expected:
        raise ValueError('unknown, missing or mismatched event capability')
    costs = exact(config['costs'], 'tile turn grass warp')
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in costs.values()) or costs['tile'] <= 0:
        raise ValueError('route costs must be finite nonnegative numbers with positive tile cost')
    budget = positive(config['max_route_presses'])
    if not isinstance(config['maps'], dict) or not config['maps']:
        raise ValueError('map pins required')
    maps = [LocalMap(read_json(read_pinned_map(config['map_revision'], 'frlg', name, digest, root)), 'frlg')
            for name, digest in config['maps'].items()]
    world = RuntimeWorld(maps)
    poses = [checkpoint['start'], checkpoint['events'][0]['target'], checkpoint['events'][2]['declared_after']]
    for pose in poses:
        if pose['map'] not in world.views:
            raise ValueError('checkpoint references an unbound map')
    return ParcelBinding(capture, checkpoint, world, Costs(**costs), budget, hashlib.sha256(raw).hexdigest())

"""Bind captured checkpoints to versioned offline game/action capabilities.

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
from .replay_handlers import exact, resolve_action
from pokesim.games.frlg.story_replay import FRLGReplay

PROFILE = ROOT / 'data/story/parcel-pilot/binding.json'
OFFLINE_POLICY = {'basis': 'synthetic-offline-policy', 'entry': 'scripted-observation',
                  'attempts': 1, 'failure': 'stop', 'save': 'never'}


def positive(value):
    """A finite positive route move count, not a boolean or unbounded budget."""
    if type(value) is not int or not 1 <= value <= 4096:
        raise ValueError('route move budget must be an integer in 1..4096')
    return value


@dataclass
class ReplayBinding:
    """Validated capture, model and explicit simulation-only execution options."""
    capture: dict
    checkpoint: dict
    adapter: object
    actions: dict
    profile_sha256: str


def load_binding(path=PROFILE, root=ROOT):
    """Preflight every binding/hash before any replay action; never fetch data."""
    raw = Path(path).read_bytes()
    config = read_json(raw)
    authored = 'plan' in config
    source_key = 'plan' if authored else 'capture'
    exact(config, 'format {} map_revision maps capabilities costs max_route_moves policy'.format(source_key))
    if (config['format'] != 'pokesim-story-replay-binding/1' or config['policy'] != OFFLINE_POLICY
            or type(config['policy'].get('attempts')) is not int):
        raise ValueError('unsupported offline profile/policy; native options remain unbound')
    pin = exact(config[source_key], 'file sha256' if authored else 'file sha256 source_revision')
    source = Path(root).resolve()
    capture_path = (source / pin['file']).resolve()
    if source not in capture_path.parents:
        raise ValueError('capture must be inside the source repository')
    capture_raw = capture_path.read_bytes()
    if hashlib.sha256(capture_raw).hexdigest() != pin['sha256']:
        raise ValueError('capture hash mismatch')
    capture = read_json(capture_raw)
    if authored:
        from .authored_checkpoint import read_authored_checkpoint
        plan = read_authored_checkpoint(capture)
        # Internal report provenance, not an invented native export or observation.
        capture = dict(plan, source_revision=None, authored_plan_sha256=pin['sha256'],
                       unbound=['entry_evidence', 'effective_save_retry_policy'])
    elif (capture['format'] != 'pokesim-native-checkpoint-export/1'
            or capture['game'] != 'frlg' or capture['source_revision'] != pin['source_revision']
            or capture['state_basis'] != 'native-table-bookkeeping'):
        raise ValueError('unsupported capture identity/state basis')
    checkpoint = read_checkpoint(capture['checkpoint'])
    if not checkpoint['events'] or 'start' not in checkpoint:
        raise ValueError('replay currently requires a nonempty checkpoint with a starting pose')
    allowed = {'route': {'id', 'kind', 'why', 'target'},
               'step': {'id', 'kind', 'why', 'direction'},
               'scene': {'id', 'kind', 'why', 'declared_after'}}
    for event in checkpoint['events']:
        if event['kind'] not in allowed or set(event) - allowed[event['kind']]:
            raise ValueError('unsupported event kind/options in spatial replay')
        required = {'route': 'target', 'scene': 'declared_after'}.get(event['kind'])
        if required and required not in event:
            raise ValueError('event is missing ' + required)
    if not isinstance(config['capabilities'], dict) or set(config['capabilities']) != {e['id'] for e in checkpoint['events']}:
        raise ValueError('missing or extra event capability')
    costs = exact(config['costs'], 'tile turn grass warp')
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in costs.values()) or costs['tile'] <= 0:
        raise ValueError('route costs must be finite nonnegative numbers with positive tile cost')
    budget = positive(config['max_route_moves'])
    if not isinstance(config['maps'], dict) or not config['maps']:
        raise ValueError('map pins required')
    maps = [LocalMap(read_json(read_pinned_map(config['map_revision'], 'frlg', name, digest, root)), 'frlg')
            for name, digest in config['maps'].items()]
    world = RuntimeWorld(maps)
    adapter = FRLGReplay(world, Costs(**costs), budget)
    poses = [checkpoint['start']] + [e[k] for e in checkpoint['events'] for k in ('target', 'declared_after') if k in e]
    for pose in poses:
        if pose['map'] not in world.views:
            raise ValueError('checkpoint references an unbound map')
        adapter.authored_pose(pose)
    actions = {e['id']: resolve_action(e['kind'], config['capabilities'][e['id']], adapter) for e in checkpoint['events']}
    return ReplayBinding(capture, checkpoint, adapter, actions, hashlib.sha256(raw).hexdigest())

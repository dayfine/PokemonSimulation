"""Resolve versioned action capabilities; scripted scene effects are bound data."""

from dataclasses import dataclass
from typing import Callable


def exact(value, keys):
    """Reject unknown or missing fields at replay boundaries."""
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError('expected exactly: ' + keys)
    return value


@dataclass
class BoundAction:
    """One validated game action with its own signal checker and executor."""
    capability: str
    parameters: dict
    preflight: Callable
    execute: Callable


def resolve_action(kind, spec, adapter):
    """Reject unknown capabilities/kind combinations before executing any event."""
    exact(spec, 'capability parameters')
    capability, parameters = spec['capability'], spec['parameters']
    methods = adapter.handlers()
    if capability in methods:
        supported_kind, preflight, execute = methods[capability]
        if kind != supported_kind or parameters != {}:
            raise ValueError('mismatched kind or unsupported movement parameters')
        return BoundAction(capability, parameters, preflight, execute)
    if capability != 'scripted-scene/1' or kind != 'scene':
        raise ValueError('unknown or mismatched event capability')
    exact(parameters, 'require_received')
    required = parameters['require_received']
    if (not isinstance(required, dict) or any(not isinstance(k, str) or not k
            or type(v) is not int or v <= 0 for k, v in required.items())):
        raise ValueError('scene receipt requirements must have named positive quantities')

    def preflight(event, signal):
        if signal is None:
            return
        exact(signal, 'kind basis screen pose received')
        if signal['kind'] != 'scene-observation' or signal['basis'] != 'scripted':
            raise ValueError('scene observation must be explicitly scripted')
        received = signal['received']
        if (not isinstance(received, dict) or set(received) - set(required)
                or any(type(v) is not int or v <= 0 for v in received.values())):
            raise ValueError('unsupported receipt item/quantity')
        adapter.validate_pose(signal['pose'])

    def execute(state, event, signal):
        state.action(event['id'], 'scene', capability=capability)
        # Authored arrival is checked against separately supplied evidence.
        if (not signal or signal['screen'] != 'overworld'
                or signal['pose'] != adapter.authored_pose(event['declared_after'])
                or signal['received'] != required):
            state.pose, state.basis = None, 'unknown-after-scene'
            return 'scene_evidence_missing_or_mismatched'
        state.pose, state.basis = dict(signal['pose']), 'scripted-observation'
        for item, count in signal['received'].items():
            state.received[item] = state.received.get(item, 0) + count
        state.record(event['id'], 'observation', received=dict(signal['received']))
        return None

    return BoundAction(capability, parameters, preflight, execute)

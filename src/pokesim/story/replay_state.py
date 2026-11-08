"""Shared execution state and requested actions for offline checkpoint replay."""

from dataclasses import dataclass, field


@dataclass
class ReplayState:
    """Keep model/observation basis alongside pose, effects and ordered actions."""
    pose: object
    basis: str = 'scripted-observation'
    received: dict = field(default_factory=dict)
    candidates: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    actions: list = field(default_factory=list)

    def record(self, event, phase, **details):
        """Record state independently of case expectations."""
        self.trace.append(dict(event=event, phase=phase, pose=self.pose, basis=self.basis, **details))

    def action(self, event, kind, **details):
        """Record actual requests, coalescing consecutive identical modeled presses.

        Counts are input presses, not confirmed tile displacement. Interrupted
        presses are separate records; scene requests do not describe buttons.
        """
        row = dict(event=event, kind=kind, **details)
        if kind == 'press':
            if self.actions and {k: v for k, v in self.actions[-1].items() if k != 'count'} == row:
                self.actions[-1]['count'] += 1
                return
            row['count'] = 1
        self.actions.append(row)

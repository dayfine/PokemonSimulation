"""Shared execution state and requested actions for offline checkpoint replay."""

from dataclasses import dataclass, field


@dataclass
class ReplayState:
    """Keep model/observation basis alongside pose, effects and ordered actions."""
    pose: object
    basis: str = 'scripted-observation'
    received: dict = field(default_factory=dict)
    candidates: list = field(default_factory=list)
    # Native author-declared fallback, kept separate from physical pose uncertainty.
    declared_belief: list = field(default_factory=list)
    trace: list = field(default_factory=list)
    actions: list = field(default_factory=list)

    def record(self, event, phase, **details):
        """Record state independently of case expectations."""
        self.trace.append(dict(event=event, phase=phase, pose=self.pose, basis=self.basis, **details))

    def action(self, event, kind, **details):
        """Record a requested semantic leg before execution, not its completion.

        Distance is intent: an interrupted walk retains its requested tiles.
        Confirmed/model displacement and uncertainty belong to state/trace.
        """
        self.actions.append(dict(event=event, kind=kind, **details))

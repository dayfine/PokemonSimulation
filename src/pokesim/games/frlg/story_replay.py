"""FRLG capabilities for the shared runtime-world movement adapter."""

from pokesim.story.spatial_replay import RuntimeSpatialReplay


class FRLGReplay(RuntimeSpatialReplay):
    """Bind FRLG action names to shared movement with FRLG runtime rules."""
    def handlers(self):
        return {'frlg-runtime-route/1': ('route', self.route_signal, self.route),
                'frlg-runtime-step/1': ('step', self.step_signal, self.step)}

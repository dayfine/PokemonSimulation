"""Observed-state regressions extracted from native AutoStory evidence.

The fixture inventory supplies exact revisions/run IDs; additional guards use
explicitly synthetic diagnostics, not invented console measurements.
"""
import unittest
from pokesim.grid.geometry import Direction as D, Tile
from pokesim.grid.maps.world import Place
from pokesim.grid.movement import world_step
from .local_routing import LocalMap
from .runtime_world import RuntimeWorld
from .test_runtime_world import view, state
from .transition_state import Pose, Observation, Session, StateFailure, anchor_plan, clip_plan


def pose(name, x, y, facing=D.NORTH, level=3):
    return Pose(state(name, x, y, level), facing)


class TransitionStateTests(unittest.TestCase):
    def forest(self):
        return RuntimeWorld([view('frlg', n) for n in ['ViridianForest', 'Route2_ViridianForest_NorthEntrance', 'Route2_ViridianForest_SouthEntrance']])

    def test_forest_fade_or_black_text_box_does_not_confirm_warp_or_battle(self):
        session = Session(self.forest(), [pose('ViridianForest', 5, 10)])
        session.propose([D.NORTH])
        self.assertFalse(session.can_resume)
        session.observe(Observation(screen='unknown', fade=True))
        self.assertEqual({p.state.place.map for p in session.belief}, {'ViridianForest', 'Route2_ViridianForest_NorthEntrance'})
        session.observe(Observation(screen='battle', hp_box=False))
        self.assertEqual(session.screen, 'unknown')
        self.assertFalse(session.can_resume)
        session.observe(Observation(screen='overworld', map='Route2_ViridianForest_NorthEntrance',
                                    tiles=(Tile(7, 10),), queue_drained=True))
        self.assertTrue(session.can_resume)

    def test_battle_on_warp_leg_keeps_source_map_and_partial_pose(self):
        session = Session(self.forest(), [pose('ViridianForest', 5, 20)])
        session.propose([D.NORTH] * 11)
        session.observe(Observation(screen='battle', hp_box=True))
        self.assertFalse(session.can_resume)
        session.observe(Observation(screen='overworld', map='ViridianForest',
                                    tiles=(Tile(5, 19), Tile(5, 18)), queue_drained=True))
        self.assertEqual(len(session.belief), 2)
        self.assertFalse(session.can_resume)
        with self.assertRaises(StateFailure):
            session.propose([D.NORTH])
        # A recovered battle is not a transition; ambiguous pose needs localization.
        self.assertTrue(all(p.state.place.map == 'ViridianForest' for p in session.belief))

    def test_connection_delay_keeps_one_tile_short_belief(self):
        world = RuntimeWorld([view('frlg', 'CeruleanCity', flags=['FLAG_HIDE_CERULEAN_RIVAL']), view('frlg', 'Route24')])
        session = Session(world, [pose('CeruleanCity', 22, 0)])
        session.propose([D.NORTH] * 3, min_completed=3, edge_stall=True)
        self.assertEqual({p.state.place for p in session.belief},
                         {Place('Route24', Tile(10, 37)), Place('Route24', Tile(10, 38))})
        session.observe(Observation(screen='overworld', map='Route24', queue_drained=True))
        self.assertFalse(session.can_resume)  # Correct map still does not prove tile.

    def test_queued_input_invalidates_even_an_exact_early_observation(self):
        session = Session(self.forest(), [pose('ViridianForest', 29, 61)])
        session.propose([D.SOUTH], queued=[D.SOUTH])
        early = Observation(screen='overworld', map='ViridianForest', tiles=(Tile(29, 62),))
        session.observe(early)
        self.assertFalse(session.can_resume)
        self.assertGreater(len(session.belief), 1)
        session.observe(Observation(screen='overworld', map='ViridianForest', tiles=(Tile(29, 62),), queue_drained=True))
        self.assertTrue(session.can_resume)

    def test_logan_r55_both_count_and_sight_tiles_can_anchor(self):
        world = RuntimeWorld([view('bdsp', 'Route202', VAR_ROUTE_202_STATE=1)])
        belief = {pose('Route202', 27, 5, D.WEST, 0), pose('Route202', 26, 5, D.WEST, 0)}
        plan = anchor_plan(world, belief, max_presses=12)
        self.assertIsNotNone(plan)
        # Avoid trainer spawn and all uncertain/encounter/transition cells.
        for start in belief:
            at = start.state
            for d in plan.actions:
                result = world_step(world, at, d)
                if hasattr(result, 'state'):
                    at = result.state
                self.assertNotEqual(at.place.tile, Tile(26, 4))
            self.assertEqual(at, plan.arrival.state)
        session = Session(world, belief)
        session.recover(max_presses=12)
        self.assertFalse(session.can_resume)
        session.observe(Observation(screen='overworld', map='Route202',
                                    tiles=(plan.arrival.state.place.tile,), queue_drained=True))
        self.assertTrue(session.can_resume)

    def test_battle_invalidates_facing_until_observed_or_reestablished(self):
        session = Session(self.forest(), [pose('ViridianForest', 5, 20)])
        session.observe(Observation(screen='battle', hp_box=True))
        session.observe(Observation(screen='overworld', map='ViridianForest',
                                    tiles=(Tile(5, 20),), queue_drained=True))
        self.assertFalse(session.can_resume)
        self.assertIsNone(next(iter(session.belief)).facing)
        session.observe(Observation(screen='overworld', facing=D.NORTH, queue_drained=True))
        self.assertTrue(session.can_resume)

    def test_wrong_frame_or_contradictory_observation_fails_explicitly(self):
        session = Session(self.forest(), [pose('ViridianForest', 5, 20)])
        with self.assertRaises(ValueError):
            session.observe(Observation(screen='overworld', frame='decomp-global'))
        session.propose([D.NORTH])
        with self.assertRaises(StateFailure):
            session.observe(Observation(screen='overworld', map='PewterCity', queue_drained=True))
        self.assertFalse(session.can_resume)
        self.assertEqual(session.belief, frozenset())

    def test_unknown_mine_exit_stops_instead_of_inventing_b2f(self):
        world = RuntimeWorld([view('bdsp', n) for n in ['OreburghMineB1F', 'OreburghMine']])
        session = Session(world, [pose('OreburghMineB1F', 12, 20, D.SOUTH, 0)])
        with self.assertRaises(StateFailure):
            session.propose([D.SOUTH, D.SOUTH], min_completed=2)
        self.assertFalse(session.can_resume)

    def test_bdsp_mine_clip_south_merges_two_tile_shortfall_after_battle(self):
        world = RuntimeWorld([view('bdsp', 'OreburghMine')], encounter_maps=['OreburghMine'])
        belief = [pose('OreburghMine', 15, y, D.SOUTH, 0) for y in (15, 16, 17)]
        self.assertIsNone(clip_plan(world, belief, D.SOUTH, 8))
        plan = clip_plan(world, belief, D.SOUTH, 8, encounter_policy='recover')
        self.assertEqual(plan.arrival.state.place, Place('OreburghMine', Tile(15, 17)))
        session = Session(world, belief)
        session.clip(D.SOUTH, 8, encounter_policy='recover')
        session.observe(Observation(screen='battle', hp_box=True))
        self.assertFalse(session.can_resume)
        session.observe(Observation(screen='overworld', map='OreburghMine', queue_drained=True))
        self.assertFalse(session.can_resume)
        session.clip(D.SOUTH, 8, encounter_policy='recover')
        session.observe(Observation(screen='overworld', still_direction=D.SOUTH, queue_drained=True))
        self.assertFalse(session.can_resume)  # A frozen/stale frame proves nothing.
        session.observe(Observation(screen='overworld', still_direction=D.SOUTH,
                                    video_advanced=True, queue_drained=True))
        self.assertTrue(session.can_resume)
        self.assertEqual(next(iter(session.belief)).state.place, Place('OreburghMine', Tile(15, 17)))

    def test_counted_mine_leg_keeps_completed_and_missed_step_hypotheses(self):
        world = RuntimeWorld([view('bdsp', 'OreburghMine')])
        session = Session(world, [pose('OreburghMine', 15, 12, D.SOUTH, 0)])
        session.propose([D.SOUTH] * 5, min_completed=5, missed_presses=2)
        self.assertEqual({p.state.place.tile for p in session.belief}, {Tile(15, y) for y in (15, 16, 17)})
        session.observe(Observation(screen='overworld', map='OreburghMine', queue_drained=True))
        with self.assertRaises(StateFailure):
            session.propose([D.EAST] * 14)

    def test_clip_does_not_use_npc_or_different_wall_endpoints(self):
        world = RuntimeWorld([view('bdsp', 'OreburghMine')], encounter_maps=['OreburghMine'])
        # The report's next east leg can hit Machop at (20,15).
        self.assertIsNone(clip_plan(world, [pose('OreburghMine', 19, 15, D.EAST, 0)],
                                   D.EAST, 20, encounter_policy='recover'))
        belief = [pose('OreburghMine', x, 16, D.SOUTH, 0) for x in (15, 16)]
        self.assertIsNone(clip_plan(world, belief, D.SOUTH, 8, encounter_policy='recover'))

    def test_repeated_battle_interruptions_exhaust_shared_recovery_budget(self):
        world = RuntimeWorld([view('bdsp', 'OreburghMine')], encounter_maps=['OreburghMine'])
        session = Session(world, [pose('OreburghMine', 15, 15, D.SOUTH, 0)], max_recoveries=2)
        for _ in range(2):
            session.clip(D.SOUTH, 8, encounter_policy='recover')
            session.observe(Observation(screen='battle', hp_box=True))
            session.observe(Observation(screen='overworld', map='OreburghMine', tiles=(Tile(15, 15),), queue_drained=True))
        with self.assertRaisesRegex(StateFailure, 'budget exhausted'):
            session.clip(D.SOUTH, 8, encounter_policy='recover')
        self.assertFalse(session.can_resume)

    def test_synthetic_recovery_never_crosses_even_a_resolved_edge(self):
        source = dict(decomp_file='', revision='synthetic', date='2026-11-05')
        a = LocalMap(dict(name='A', source=source, tiles=['#.#', '###'],
            connections=[dict(side='north', to_map='B', offset=0)]), 'bdsp')
        b = LocalMap(dict(name='B', source=source, tiles=['###', '#.#']), 'bdsp')
        world = RuntimeWorld([a, b])
        belief = [pose('A', 1, 0, D.NORTH, 0)]
        self.assertIsNone(clip_plan(world, belief, D.NORTH, 8))
        plan = anchor_plan(world, belief, max_presses=8)
        self.assertIsNotNone(plan)
        self.assertEqual(plan.arrival.state.place.map, 'A')

    def test_synthetic_warp_on_blocked_glyph_is_not_a_wall_anchor(self):
        source = dict(decomp_file='', revision='synthetic', date='2026-11-05')
        view = LocalMap(dict(name='DiagnosticWarp', source=source,
            tiles=['#####', '#..##', '#####'], warps=[dict(x=3, y=1, enter='step_on')]), 'frlg')
        world = RuntimeWorld([view])
        belief = [pose('DiagnosticWarp', x, 1, D.EAST, 0) for x in (1, 2)]
        self.assertIsNone(clip_plan(world, belief, D.EAST, 8))

    def test_synthetic_corridor_cannot_anchor_through_npcs(self):
        corridor = LocalMap(dict(name='Diagnostic', source=dict(decomp_file='', revision='synthetic', date='2026-11-05'), tiles=['#######', '#.....#', '#######'],
            objects=[dict(name='a', kind='npc', x=1, y=1), dict(name='b', kind='npc', x=5, y=1)]), 'bdsp')
        world = RuntimeWorld([corridor])
        belief = [pose('Diagnostic', x, 1, D.EAST, 0) for x in [2, 3]]
        self.assertIsNone(anchor_plan(world, belief, max_presses=8))
        with self.assertRaises(StateFailure):
            Session(world, belief).recover(max_presses=8)
        for limit in [0, -1, 129]:
            with self.assertRaises(ValueError):
                anchor_plan(world, belief, max_presses=limit)


if __name__ == '__main__':
    unittest.main()

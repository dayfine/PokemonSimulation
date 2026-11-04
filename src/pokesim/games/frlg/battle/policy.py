"""Player strategy entry point: recovery (B) by default, planning (C) opt-in.

Tier A lives in player_strategy.attacks; B adds recovery; C adds explicit
multi-turn setup goals. Game NPC helpers are separate in npc_actions.py.
"""

from pokesim.games.frlg.battle.npc_actions import trainer_item, replacement
from pokesim.games.frlg.battle.player_strategy.attacks import attack, locked
from pokesim.games.frlg.battle.player_strategy.threat import threat
from pokesim.games.frlg.battle.player_strategy import recovery, planning

POLICY = 'B:solo-recovery/1; C:goal-based-setup/2'


def player_action(state, ai, flags, items, enable_complex_planning=False, planning_goals=None):
    if enable_complex_planning:
        return planning.choose_action(state, ai, flags, items, planning_goals or {})
    return recovery.choose_action(state, ai, flags, items)

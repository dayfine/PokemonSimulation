"""PokeGuy-replica player policy for the FRLG League, plus our current AutoStory C.

replica: C2 setup goals, but heal only when the active foe's strongest
ordinary hit could KO next turn (HP <= D), with the smallest medicine that
lifts HP above D (a Full Restore when a smaller one would not gain net HP),
and PP medicine as soon as the main STAB move (Surf) is empty.

current_c: an approximation of AutoStory PR #613's policy as run on
2026-11-16: a Full Restore whenever HP is below half in a high-risk fight
(RISK_HEALS), then C2 with foe evasion unseen and no PP medicine.
"""

from pokesim.games.frlg.battle.player_strategy import attacks, recovery, planning
from pokesim.games.frlg.battle.items import HEALS


def _residual(own):
    return own['max_hp'] // 8 * (int(own['status'] in ('psn', 'tox')) + int('leechseed' in own['volatiles']))


def ko_heal(state, danger):
    """Smallest medicine that lifts HP above D and nets HP after the expected hit."""
    own, bag = state['own'], state['bag']
    missing = own['max_hp'] - own['hp']
    options = []
    for item, amount in HEALS.items():
        gained = min(amount, missing)
        after = own['hp'] + gained
        if bag.get(item) and gained > 0 and after > danger['normal_max'] and after - danger['mean'] > own['hp']:
            options.append((gained, item))
    if options:
        return {'kind': 'item', 'item': min(options)[1]}
    for item in ('fullrestore', 'maxpotion', 'hyperpotion', 'superpotion', 'potion'):
        if bag.get(item) and missing > 0:
            return {'kind': 'item', 'item': item}
    return None


def pp_rescue(state, danger):
    """Elixir when the strongest STAB attack is empty (Surf), or B's two-empty rule."""
    own, bag = state['own'], state['bag']
    if own['hp'] <= danger['normal_max'] or own['status'] in ('slp', 'frz'):
        return None
    main_empty = any(m['pp'] == 0 and m.get('power', 0) >= 90 for m in own['moves'])
    if main_empty:
        for item in ('elixir', 'maxelixir'):
            if bag.get(item):
                return {'kind': 'item', 'item': item}
    return recovery.pp_action(state, danger)


def replica_action(state, ai, flags, items, goals):
    own = state['own']
    forced = attacks.locked(own)
    if forced:
        return forced
    choice = attacks.attack(state)
    certain = [(m['power'], -m['pp'], slot) for slot, m in attacks.usable(own)
               if planning.safe_finish(state, {'kind': 'move', 'slot': slot}, items)]
    if certain:
        choice = {'kind': 'move', 'slot': min(certain)[2]}
    finish = planning.safe_finish(state, choice, items)
    planned = planning.setup_item(state, goals)
    remaining = sum(p['hp'] > 0 for p in state['party'])
    needs_torrent = planning.needs_torrent_setup(state, goals)
    if finish and ((planned is None and not needs_torrent) or remaining == 1):
        return choice
    danger = planning.planning_risk(state, ai, flags)
    if finish and (danger['normal_max'] >= own['max_hp']
                   or any(m['id'] in ('selfdestruct', 'explosion') and m['pp'] for m in state['foe']['moves'])):
        return choice
    cure = recovery.cure_action(state, danger)
    if cure:
        return cure
    if own['hp'] <= danger['normal_max']:
        return ko_heal(state, danger) or choice
    if own['status'] in ('slp', 'frz') or 'confusion' in own['volatiles']:
        return choice
    pp = pp_rescue(state, danger)
    if pp:
        return pp
    if planned:
        return planned
    if needs_torrent:
        activation = planning.activation_action(state)
        if activation:
            return activation
    return choice


def current_c_action(state, ai, flags, items, goals):
    own, bag = state['own'], state['bag']
    if not attacks.locked(own) and own['hp'] * 2 < own['max_hp'] and bag.get('fullrestore'):
        return {'kind': 'item', 'item': 'fullrestore'}
    blind = dict(state, foe=dict(state['foe'], boosts=dict(state['foe']['boosts'], evasion=0)))
    action = planning.choose_action(blind, ai, flags, items, goals)
    if action.get('item') in ('elixir', 'maxelixir', 'ether', 'maxether'):
        return attacks.attack(state)
    return action


# replica_full: same battle play, but Super Potions top up to full HP before every fight.
POLICIES = {'replica': replica_action, 'replica_full': replica_action, 'current_c': current_c_action}

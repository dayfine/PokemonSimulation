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


MARGIN = {'on': False}


def margin(danger):
    """replica_margin: also keep one average hit in reserve (crits, Hail, confusion)."""
    return danger['mean'] if MARGIN['on'] else 0


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
    if own['hp'] <= danger['normal_max'] + margin(danger):
        if danger['normal_max'] >= own['max_hp']:
            return choice  # no medicine survives it (Sunny Day Solar Beam): attack instead of looping heals
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
def replica_margin_action(state, ai, flags, items, goals):
    MARGIN['on'] = True
    try:
        return replica_action(state, ai, flags, items, goals)
    finally:
        MARGIN['on'] = False


def c2_action(state, ai, flags, items, goals):
    """The handoff's C2 (reserve-based healing during setup), with the Surf-empty Elixir rule."""
    own = state['own']
    if not attacks.locked(own) and own['hp'] > planning.planning_risk(state, ai, flags)['normal_max']:
        pp = pp_rescue(state, planning.planning_risk(state, ai, flags))
        if pp and pp['item'] in ('elixir', 'maxelixir') and any(m['pp'] == 0 and m.get('power', 0) >= 90 for m in own['moves']):
            return pp
    return planning.choose_action(state, ai, flags, items, goals)


# Per-fight setup item budgets. Bruno keeps C2's unbudgeted use (Rock Tomb Speed repair and the
# Torrent stall; capping it at PokeGuy's 2 X Special / 1 X Speed cut Bruno to 72% in the chain sim).
# Agatha never chases Gengar's Double Team with X Accuracy (it spent 2.6-5.6 and lowered the win rate);
# the Champion keeps two X Accuracy, two X Speed and four X Special.
BUDGET = {'lorelei': {'xspecial': 4, 'xspeed': 1, 'xaccuracy': 0},
          'bruno': {'xspecial': 4, 'xspeed': 5, 'xaccuracy': 0},
          'agatha': {'xspecial': 2, 'xspeed': 1, 'xaccuracy': 0},
          'lance': {'xspecial': 3, 'xspeed': 1, 'xaccuracy': 1},
          'champion': {'xspecial': 4, 'xspeed': 2, 'xaccuracy': 2}}


def budgeted(policy):
    """Hide a setup item from the policy once this fight's budget for it is spent."""
    def action(state, ai, flags, items, goals):
        budget, entry = BUDGET.get(goals.get('_fight'), {}), goals.get('_entry_bag', {})
        bag = dict(state['bag'])
        for item, cap in budget.items():
            if entry.get(item, 0) - bag.get(item, 0) >= cap:
                bag[item] = 0
        clean = {k: v for k, v in goals.items() if not k.startswith('_')}
        return policy(dict(state, bag=bag), ai, flags, items, clean)
    return action


# Setup PokeGuy actually did on video (notes/pokeguy-league-turns.md, PokemonSimulation PR #108).
# chase_evasion False: X Accuracy goals ignore the foe's Double Team (he Surfed through +2).
VIDEO_GOALS = {
    'lorelei': {'spa': 4, 'accuracy': 0, 'outspeed': False, 'guard_accuracy': False, 'chase_evasion': False},
    'bruno': {'spa': 2, 'accuracy': 0, 'outspeed': True, 'guard_accuracy': False, 'target_torrent': True, 'chase_evasion': False},
    'agatha': {'spa': 1, 'accuracy': 0, 'outspeed': True, 'guard_accuracy': False, 'chase_evasion': False},
    'lance': {'spa': 1, 'accuracy': 1, 'outspeed': False, 'guard_accuracy': False, 'chase_evasion': False},
    'champion': {'spa': 2, 'accuracy': 1, 'outspeed': True, 'guard_accuracy': True, 'chase_evasion': False},
}


def video_action(state, ai, flags, items, goals):
    """PokeGuy as seen on video: his per-fight setup, heal only when the foe can KO us
    before we KO it (HP <= its best ordinary hit and no safe finishing hit of ours)."""
    goals = dict(VIDEO_GOALS.get(goals.get('_fight'), {}), _fight=goals.get('_fight'))
    own = state['own']
    seen = state if goals.get('chase_evasion', True) else dict(
        state, foe=dict(state['foe'], boosts=dict(state['foe']['boosts'], evasion=0)))
    forced = attacks.locked(own)
    if forced:
        return forced
    choice = attacks.attack(state)
    certain = [(m['power'], -m['pp'], slot) for slot, m in attacks.usable(own)
               if planning.safe_finish(state, {'kind': 'move', 'slot': slot}, items)]
    if certain:
        choice = {'kind': 'move', 'slot': min(certain)[2]}
    finish = planning.safe_finish(state, choice, items)
    clean = {k: v for k, v in goals.items() if not k.startswith('_')}
    planned = planning.setup_item(seen, clean)
    remaining = sum(p['hp'] > 0 for p in state['party'])
    needs_torrent = planning.needs_torrent_setup(state, clean)
    danger = planning.planning_risk(state, ai, flags)
    if finish and (own['hp'] <= danger['normal_max'] or (planned is None and not needs_torrent) or remaining == 1):
        return choice  # he attacks at 3 HP when he moves first and KOs
    cure = recovery.cure_action(state, danger)
    if cure and own['hp'] > danger['normal_max']:
        return cure
    if own['hp'] <= danger['normal_max'] < own['max_hp']:
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


POLICIES = {'video': video_action, 'c2': c2_action, 'c2_budget': budgeted(c2_action), 'replica_budget': budgeted(replica_action), 'replica': replica_action, 'replica_full': replica_action, 'replica_margin': replica_margin_action, 'current_c': current_c_action}

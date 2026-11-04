"""Tier C: opt-in multi-turn setup goals layered on tier B recovery.

Goals are declared per fight. They are not a replay of a winning trace:
status, HP, stat drops, remaining opponents and supplies determine actions.
Torrent may justify staying below one-third HP instead of healing to full.
This is a bounded heuristic, not an optimal planner or a switch strategy.
"""

from pokesim.games.frlg.battle.player_strategy import attacks, recovery
from pokesim.games.frlg.battle.player_strategy.threat import threat

ACCURACY_DROPS = {'sandattack', 'smokescreen', 'flash', 'kinesis', 'octazooka', 'mudslap'}


def torrent_active(own):
    return own['ability'] == 'torrent' and own['hp'] * 3 <= own['max_hp']


def needs_torrent_setup(state, goals):
    """Activation belongs to the opening setup window, not every later foe.

    Extra Sp. Atk can substitute for Torrent. For example, +4 without Torrent
    provides the same multiplier as +2 with Torrent, avoiding pointless stalls.
    """
    own = state['own']
    multiplier = lambda stage: (2 + max(0, stage)) / (2 + max(0, -stage))
    return (goals.get('target_torrent', False) and own['ability'] == 'torrent'
        and not torrent_active(own) and state['foe']['party_index'] == 0
        and sum(p['hp'] > 0 for p in state['party']) > 1
        and multiplier(own['boosts']['spa']) < 1.5 * multiplier(goals.get('spa', 0)))


def setup_item(state, goals):
    """Commit to stage goals across turns, repairing debuffs when needed."""
    own, bag = state['own'], state['bag']
    remaining = [p for p in state['party'] if p['hp'] > 0]
    special = own['boosts']['spa'] < goals.get('spa', 0) and bag.get('xspecial', 0)
    speed = (goals.get('outspeed', False) and bag.get('xspeed', 0) and own['boosts']['spe'] < 6
             and any(p['speed'] >= own['speed'] for p in remaining))
    accuracy = own['boosts']['accuracy'] < goals.get('accuracy', 0) and bag.get('xaccuracy', 0)
    pending = special or speed or accuracy
    if (pending and goals.get('guard_accuracy', True) and bag.get('guardspec', 0)
            and 'mist' not in own['side_conditions']
            and any(m['id'] in ACCURACY_DROPS and m['pp'] for m in state['foe']['moves'])):
        return {'kind': 'item', 'item': 'guardspec'}
    for needed, item in ((special, 'xspecial'), (speed, 'xspeed'), (accuracy, 'xaccuracy')):
        if needed:
            return {'kind': 'item', 'item': item}
    return None


def safe_finish(state, choice, items):
    """Also account for damaging NPC priority moves before calling a hit safe."""
    if not recovery.finishing_hit(state, choice, items):
        return False
    own = state['own']
    priority = own['moves'][choice['slot']].get('priority', 0)
    for move in state['foe']['moves']:
        if move['pp'] and not move['disabled'] and move.get('priority', 0) > priority:
            if max(move.get('critical', [0])) >= own['hp']:
                return False
    residual = own['max_hp'] // 8 * (int(own['status'] in ('psn', 'tox')) + int('leechseed' in own['volatiles']))
    return own['hp'] > residual or sum(p['hp'] > 0 for p in state['party']) == 1


def activation_action(state):
    """Use a productive setup/stall turn to reach Torrent against a weak foe."""
    own, bag = state['own'], state['bag']
    for item, stat in (('xspecial', 'spa'), ('xspeed', 'spe')):
        if bag.get(item, 0) and own['boosts'][stat] < 6:
            return {'kind': 'item', 'item': item}
    # Never knowingly KO the setup opponent with the fallback stall attack.
    candidates = [(max(m['damage']), i) for i, m in attacks.usable(own)
                  if 0 < max(m.get('damage', [0])) < state['foe']['hp']]
    if candidates:
        return {'kind': 'move', 'slot': min(candidates)[1]}
    return None


def choose_action(state, ai, flags, items, goals):
    forced = attacks.locked(state['own'])
    if forced:
        return forced
    own = state['own']
    choice = attacks.attack(state)
    finish = safe_finish(state, choice, items)
    planned = setup_item(state, goals)
    remaining = sum(p['hp'] > 0 for p in state['party'])
    needs_torrent = needs_torrent_setup(state, goals)
    if finish and ((planned is None and not needs_torrent) or remaining == 1):
        return choice
    danger = threat(state, ai, flags)
    cure = recovery.cure_action(state, danger)
    if cure:
        return cure
    if own['status'] in ('slp', 'frz') or 'confusion' in own['volatiles']:
        return recovery.choose_action(state, ai, flags, items)
    # A single setup turn must be survivable at the heuristic's likely damage.
    # Unlike B, a low HP fraction alone does not force healing out of Torrent.
    if own['hp'] <= danger['likely']:
        if finish:
            return choice
        return recovery.heal_action(state, danger) or choice
    pp = recovery.pp_action(state, danger)
    if pp:
        return pp
    if planned:
        return planned
    if needs_torrent:
        activation = activation_action(state)
        if activation:
            return activation
    return recovery.choose_action(state, ai, flags, items)

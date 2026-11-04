"""Tier C: opt-in multi-turn setup goals layered on tier B recovery.

Goals are declared per fight. They are not a replay of a winning trace:
status, HP, stat drops, remaining opponents and supplies determine actions.
Torrent may justify staying below one-third HP instead of healing to full.
This is a bounded heuristic, not an optimal planner or a switch strategy.
"""

from pokesim.games.frlg.battle.player_strategy import attacks, recovery
from pokesim.games.frlg.battle.player_strategy.threat import threat
from pokesim.games.frlg.battle.items import HEALS

ACCURACY_DROPS = {'sandattack', 'smokescreen', 'flash', 'kinesis', 'octazooka', 'mudslap'}


def torrent_active(own):
    return own['ability'] == 'torrent' and own['hp'] * 3 <= own['max_hp']


def special_goal(own, goals):
    target = goals.get('spa', 0)
    if goals.get('torrent_power', False) and not torrent_active(own):
        multiplier = 1.5 * (2 + target) / 2
        target = min(6, next((s for s in range(target, 7) if (2 + s) / 2 >= multiplier), 6))
    return target


def accuracy_goal(state, goals):
    return min(6, goals.get('accuracy', 0) + max(0, state['foe']['boosts']['evasion']))


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


def planning_risk(state, ai, flags):
    """C considers ordinary worst-case hits and explicit recharge windows."""
    own, foe = state['own'], state['foe']
    residual = own['max_hp'] // 8 * (int(own['status'] in ('psn', 'tox')) + int('leechseed' in own['volatiles']))
    if foe['locked_move'] == 'recharge' or (foe['status'] == 'slp' and foe['sleep_turns'] > 1):
        return {'likely': residual, 'mean': residual, 'max': residual, 'normal_max': residual}
    danger = threat(state, ai, flags)
    danger['normal_max'] = residual + max((max(m.get('damage', [0])) for _, m in attacks.usable(foe)), default=0)
    return danger


def setup_turns(state, goals, planned):
    """Budget several setup actions instead of treating each item in isolation."""
    own, bag = state['own'], state['bag']
    count = min(bag.get('xspecial', 0), max(0, special_goal(own, goals) - own['boosts']['spa']))
    count += min(bag.get('xaccuracy', 0), max(0, accuracy_goal(state, goals) - own['boosts']['accuracy']))
    if goals.get('outspeed', False) and any(p['hp'] > 0 and p['speed'] >= own['speed'] for p in state['party']):
        count += int(bag.get('xspeed', 0) > 0)
    count += int(planned is not None and planned.get('item') == 'guardspec')
    return max(1, count)


def planning_heal(state, danger, turns=1):
    """Build an HP reserve for the plan, avoiding repeated near-zero-net heals."""
    own, bag = state['own'], state['bag']
    reserve = min(own['max_hp'] * .75, danger['normal_max'] + max(0, turns - 1) * danger['mean'])
    if own['hp'] > danger['normal_max'] and own['hp'] >= reserve:
        return None
    options = []
    for item, amount in HEALS.items():
        restored = min(own['max_hp'] - own['hp'], amount)
        after = own['hp'] + restored
        if not bag.get(item) or restored <= 0 or after <= danger['normal_max']:
            continue
        expected = after - danger['mean']
        if expected <= own['hp'] and own['hp'] > danger['normal_max']:
            continue
        options.append((expected >= reserve, expected, restored, item))
    sufficient = [o for o in options if o[0]]
    if sufficient:
        chosen = min(sufficient, key=lambda o: o[2])
    elif options:
        chosen = max(options, key=lambda o: o[1])
    else:
        return None
    return {'kind': 'item', 'item': chosen[3]}


def setup_item(state, goals):
    """Commit to stage goals across turns, repairing debuffs when needed."""
    own, bag = state['own'], state['bag']
    remaining = [p for p in state['party'] if p['hp'] > 0]
    special = own['boosts']['spa'] < special_goal(own, goals) and bag.get('xspecial', 0)
    speed = (goals.get('outspeed', False) and bag.get('xspeed', 0) and own['boosts']['spe'] < 6
             and any(p['speed'] >= own['speed'] for p in remaining))
    accuracy = own['boosts']['accuracy'] < accuracy_goal(state, goals) and bag.get('xaccuracy', 0)
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
    # C values a guaranteed KO over A's equal-expected-turn PP saving.
    certain = [(m['power'], -m['pp'], slot) for slot, m in attacks.usable(own)
               if safe_finish(state, {'kind': 'move', 'slot': slot}, items)]
    if certain:
        choice = {'kind': 'move', 'slot': min(certain)[2]}
    finish = safe_finish(state, choice, items)
    planned = setup_item(state, goals)
    remaining = sum(p['hp'] > 0 for p in state['party'])
    needs_torrent = needs_torrent_setup(state, goals)
    if finish and ((planned is None and not needs_torrent) or remaining == 1):
        return choice
    danger = planning_risk(state, ai, flags)
    # Do not spend a setup turn in front of an ordinary attack that can KO
    # even at full HP (notably Koffing's Self-Destruct) when a fast KO is ready.
    if finish and danger['normal_max'] >= own['max_hp']:
        return choice
    if finish and any(m['id'] in ('selfdestruct', 'explosion') and m['pp'] for m in state['foe']['moves']):
        return choice
    cure = recovery.cure_action(state, danger)
    if cure:
        return cure
    if own['status'] in ('slp', 'frz') or 'confusion' in own['volatiles']:
        return recovery.choose_action(state, ai, flags, items)
    turns = setup_turns(state, goals, planned) if planned or needs_torrent else 1
    heal = planning_heal(state, danger, turns)
    if heal:
        return heal
    if own['hp'] <= danger['normal_max']:
        return choice
    pp = recovery.pp_action(state, danger)
    if pp:
        return pp
    if planned:
        return planned
    if needs_torrent:
        activation = activation_action(state)
        if activation:
            return activation
    return choice

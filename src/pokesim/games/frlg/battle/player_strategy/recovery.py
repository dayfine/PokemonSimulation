"""Tier B (default): tier A plus healing, status cures and PP recovery.

No X items or setup plans are chosen here. The order preserves the original
baseline's recovery choices on fights that never selected setup items.
"""

from pokesim.games.frlg.battle.npc_actions import trainer_item
from pokesim.games.frlg.battle.player_strategy.attacks import attack, locked, usable
from pokesim.games.frlg.battle.items import HEALS, CURES
from pokesim.games.frlg.battle.player_strategy.threat import threat


def finishing_hit(state, choice, items):
    own, foe = state['own'], state['foe']
    move = own['moves'][choice['slot']]
    fast = move.get('priority', 0) > 0 or own['speed'] > foe['speed']
    return (fast and own['status'] not in ('slp', 'par', 'frz') and 'confusion' not in own['volatiles']
        and not move.get('two_turn') and move.get('accuracy') == 1
        and min(move.get('damage', [0])) >= foe['hp'] and not trainer_item(state, items))


def cure_action(state, danger):
    own, bag = state['own'], state['bag']
    cure = CURES.get(own['status'])
    if own['hp'] > danger['likely']:
        candidates = (cure, 'fullheal', 'fullrestore') if cure else (
            ('fullheal', 'fullrestore') if 'confusion' in own['volatiles'] else ())
        for item in candidates:
            if bag.get(item, 0):
                return {'kind': 'item', 'item': item}
    return None


def heal_action(state, danger):
    own, bag = state['own'], state['bag']
    missing = own['max_hp'] - own['hp']
    if own['hp'] <= max(own['max_hp'] / 2, danger['max']):
        for item, heal in sorted(HEALS.items(), key=lambda pair: pair[1]):
            gained = min(heal, missing)
            if bag.get(item, 0) and gained > danger['likely'] and gained > 0:
                return {'kind': 'item', 'item': item}
    return None


def pp_action(state, danger):
    own, bag = state['own'], state['bag']
    if own['hp'] <= 2 * danger['likely'] or own['status'] in ('slp', 'frz'):
        return None
    usable_damage = [m for _, m in usable(own) if max(m.get('damage', [0])) > 0]
    empty = [(i, m) for i, m in enumerate(own['moves']) if m['pp'] == 0 and m.get('power', 0) > 0]
    if len(empty) >= 2 or not usable_damage:
        for item in ('elixir', 'maxelixir'):
            if bag.get(item):
                return {'kind': 'item', 'item': item}
        if empty:
            for item in ('ether', 'maxether'):
                if bag.get(item):
                    return {'kind': 'item', 'item': item, 'slot': max(empty, key=lambda pair: pair[1]['power'])[0]}
    return None


def choose_action(state, ai, flags, items):
    forced = locked(state['own'])
    if forced:
        return forced
    choice = attack(state)
    finishing = finishing_hit(state, choice, items)
    if finishing and not state.get('progression'):
        return choice
    danger = threat(state, ai, flags)
    if finishing:
        return pp_action(state, danger) or choice
    recover = cure_action(state, danger) or heal_action(state, danger)
    if recover:
        return recover
    own = state['own']
    if state['bag'].get('oranberry') and own['max_hp'] - own['hp'] >= 10 and own['hp'] <= own['max_hp'] / 2:
        if 10 > danger['likely']:
            return {'kind': 'item', 'item': 'oranberry'}
    return pp_action(state, danger) or choice

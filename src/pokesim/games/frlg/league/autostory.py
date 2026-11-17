"""AutoStory's League policy (Arduino-Source #613, "budgeted-setup") as the program runs it.

autostory_old: choose_budgeted() as run on console B, 2026-11-16 15:35 (lost at Agatha):
  1. we move first and the best attack's lowest roll KOs: attack;
  2. a status (not sleep) and HP > D: its cure, else a Full Heal;
  3. HP <= D: the smallest medicine that lifts HP above D and nets HP after the mean hit,
     else a Max Potion / Full Restore (over the fight's budget); D >= max HP: attack;
  4. asleep: attack;
  5. Surf empty: Elixir, Max Elixir;
  6. setup towards the plan's goals within the fight's budget, with C2's HP reserve
     (reserve heals only within the budget);
  7. attack with the strongest move.
  Between fights: a cure, Super Potions to the entry target, then a Full Restore.

autostory_new: the rows added after that run (user, 2026-11-16):
  - asleep, or a status with HP <= D: cure now (Full Restore when HP <= D, else Awakening /
    Full Heal); never attack asleep while a cure is in the bag;
  - heal choice: a heal whose gain minus D is under the foe's mean hit takes the bigger heal,
    a budgeted Hyper Potion (or Max Potion), else a Full Restore over the budget;
  - two medicine turns in a row with the foe's HP unchanged: escalate (Full Restore at KO risk),
    else attack; never a third cheap heal;
  - Strength finisher: Strength's lowest roll KOs and we move first or the foe can't KO first;
  - per-fight budgets for Hyper Potions and Full Heals;
  - between fights: Super Potions, then Hyper Potions, a Full Restore last.

The per-fight budget is the planner's (PokemonFRLG_AutoStoryLeaguePlan.cpp): Full Restores by
weight with a Champion reserve, setup items by each fight's wanted count; what a fight leaves rolls
forward. Here: cumulative budget up to this fight minus what the chain has spent of the item.
"""

from pokesim.games.frlg.battle.player_strategy import attacks, planning
from pokesim.games.frlg.battle.items import HEALS, CURES

FIGHTS = ('lorelei', 'bruno', 'agatha', 'lance', 'champion')
# The plan's setup args (StoryData/frlg-20.01.plan.json).
GOALS = {
    'lorelei': {'spa': 4, 'accuracy': 0, 'outspeed': True, 'guard_accuracy': True},
    'bruno': {'spa': 2, 'accuracy': 0, 'outspeed': True, 'guard_accuracy': True, 'target_torrent': True},
    'agatha': {'spa': 1, 'accuracy': 0, 'outspeed': True, 'guard_accuracy': True, 'torrent_power': True},
    'lance': {'spa': 3, 'accuracy': 2, 'outspeed': True, 'guard_accuracy': True},
    'champion': {'spa': 2, 'accuracy': 2, 'outspeed': True, 'guard_accuracy': True},
}
# LeaguePlan's LEAGUE_FIGHTS: FR weight, X Sp, X Spe, X Acc, GS, Elixir, and (new) Hyper, Full Heal.
ROWS = {
    'lorelei': (6, 4, 1, 0, 0, 0, 2, 2),
    'bruno': (15, 4, 5, 0, 0, 0, 1, 0),
    'agatha': (2, 2, 1, 0, 0, 0, 1, 2),
    'lance': (30, 3, 1, 1, 0, 1, 2, 1),
    'champion': (22, 4, 2, 2, 1, 1, 2, 1),
}
CHAMPION_FULL_RESTORES = 3


def _split_weight(total, weights):
    s = sum(weights)
    if s <= 0 or total <= 0:
        return [0] * len(weights)
    out = [total * w // s for w in weights]
    rem = [total * w % s for w in weights]
    for _ in range(total - sum(out)):
        best = 0
        for c in range(len(weights)):
            if rem[c] >= rem[best]:
                best = c
        out[best] += 1
        rem[best] = -1
    return out


def _split_wanted(total, wanted):
    if total >= sum(wanted):
        return list(wanted)
    champion = min(wanted[-1], total)
    return _split_weight(total - champion, wanted[:-1]) + [champion]


def plan(bag, new):
    """Per-fight budgets, by item slug, as plan_league() splits the bag."""
    fr = _split_weight(bag.get('fullrestore', 0), [ROWS[f][0] for f in FIGHTS])
    reserve = min(CHAMPION_FULL_RESTORES, bag.get('fullrestore', 0) // 2)
    for c in range(4):
        moved = min(fr[c], max(0, reserve - fr[4]))
        fr[c] -= moved
        fr[4] += moved
    columns = {'fullrestore': fr}
    for index, item in ((1, 'xspecial'), (2, 'xspeed'), (3, 'xaccuracy'), (4, 'guardspec')):
        columns[item] = _split_wanted(bag.get(item, 0), [ROWS[f][index] for f in FIGHTS])
    columns['elixir'] = _split_wanted(bag.get('elixir', 0) + bag.get('maxelixir', 0), [ROWS[f][5] for f in FIGHTS])
    if new:
        columns['hyperpotion'] = _split_wanted(bag.get('hyperpotion', 0) + bag.get('maxpotion', 0), [ROWS[f][6] for f in FIGHTS])
        columns['fullheal'] = _split_wanted(bag.get('fullheal', 0), [ROWS[f][7] for f in FIGHTS])
    cumulative = {}
    for item, split in columns.items():
        total = 0
        for c, fight in enumerate(FIGHTS):
            total += split[c]
            cumulative.setdefault(fight, {})[item] = total
    return cumulative


ALIASES = {'maxelixir': 'elixir', 'maxpotion': 'hyperpotion'}


def budget_left(goals, bag, item):
    """None: the item has no budget."""
    key = ALIASES.get(item, item)
    cum = goals['_plan'][goals['_fight']]
    if key not in cum:
        return None
    start = goals['_start_bag']
    spent = sum(start.get(i, 0) - bag.get(i, 0) for i in (key,) + tuple(k for k, v in ALIASES.items() if v == key))
    return cum[key] - spent


def within(goals, bag, item):
    if not bag.get(item):
        return False
    left = budget_left(goals, bag, item)
    return left is None or left > 0


def strongest(state):
    own = state['own']
    best = max(((sum(m['damage']) / len(m['damage']) * m['accuracy'], slot) for slot, m in attacks.usable(own)
                if m.get('damage') and max(m['damage']) > 0), default=None)
    return {'kind': 'move', 'slot': best[1]} if best else attacks.attack(state)


def _fast(state, move):
    own, foe = state['own'], state['foe']
    return move.get('priority', 0) > 0 or own['speed'] > foe['speed']


def _kos(state, move):
    return move.get('accuracy') == 1 and not move.get('two_turn') and min(move.get('damage', [0])) >= state['foe']['hp']


def sure_ko_first(state):
    own = state['own']
    if own['status'] in ('slp', 'frz'):
        return None
    hits = [(slot, m) for slot, m in attacks.usable(own) if _kos(state, m) and _fast(state, m)]
    return hits


def item(name):
    return {'kind': 'item', 'item': name}


def ko_heal_old(state, danger):
    own, bag = state['own'], state['bag']
    for name in ('potion', 'superpotion', 'hyperpotion'):
        if not bag.get(name):
            continue
        after = own['hp'] + min(own['max_hp'] - own['hp'], HEALS[name])
        if after > danger['normal_max'] and after - danger['mean'] > own['hp']:
            return item(name)
    for name in ('maxpotion', 'fullrestore'):
        if bag.get(name):
            return item(name)
    return None


def ko_heal_new(state, danger, goals):
    own, bag = state['own'], state['bag']
    for name in ('potion', 'superpotion', 'hyperpotion', 'maxpotion'):
        if not bag.get(name) or (name in ('hyperpotion', 'maxpotion') and not within(goals, bag, name)):
            continue
        gained = min(own['max_hp'] - own['hp'], HEALS[name])
        after = own['hp'] + gained
        # The heal must outpace the foe by a margin (its mean hit), or the next bigger one goes.
        if after > danger['normal_max'] and gained - danger['normal_max'] >= danger['mean']:
            return item(name)
    for name in ('fullrestore', 'maxpotion', 'hyperpotion', 'superpotion'):
        if bag.get(name):
            return item(name)
    return None


def own_cure(state, goals, new):
    own, bag = state['own'], state['bag']
    status = own['status']
    if not status or (status == 'slp' and not new):
        return None
    for name in (CURES.get(status), 'fullheal'):
        if name and bag.get(name) and (not new or name != 'fullheal' or within(goals, bag, name) or status == 'slp'):
            return item(name)
    if new and bag.get('fullheal'):
        return item('fullheal')
    return None


def reserve_heal(state, danger, reserve, goals):
    own, bag = state['own'], state['bag']
    for name in ('potion', 'superpotion', 'hyperpotion', 'maxpotion', 'fullrestore'):
        if not within(goals, bag, name):
            continue
        after = own['hp'] + min(own['max_hp'] - own['hp'], HEALS[name])
        whole = HEALS[name] == float('inf')
        if (whole and after - danger['mean'] > own['hp']) or after - danger['mean'] >= reserve:
            return item(name)
    return None


def setup(state, goals):
    own, bag, foe = state['own'], state['bag'], state['foe']
    g = GOALS[goals['_fight']]
    if any(m['id'] in ('roar', 'whirlwind') for m in foe['moves']):
        return None
    if any(_kos(state, m) for _, m in attacks.usable(own)):
        return None
    if (g.get('guard_accuracy') and within(goals, bag, 'guardspec') and 'mist' not in own['side_conditions']
            and any(m['id'] in planning.ACCURACY_DROPS and m['pp'] for m in foe['moves'])):
        return item('guardspec')
    if own['boosts']['spa'] < planning.special_goal(own, g) and within(goals, bag, 'xspecial'):
        return item('xspecial')
    if (g.get('outspeed') and own['boosts']['spe'] < 6 and within(goals, bag, 'xspeed')
            and any(p['hp'] > 0 and p['speed'] >= own['speed'] for p in state['party'])):
        return item('xspeed')
    if own['boosts']['accuracy'] < g.get('accuracy', 0) and within(goals, bag, 'xaccuracy'):
        return item('xaccuracy')
    return None


def _policy(new):
    def action(state, ai, flags, items, goals):
        own, bag = state['own'], state['bag']
        forced = attacks.locked(own)
        if forced:
            return forced
        memo = goals.setdefault('_memo', {})
        foe_hp = (state['foe']['species'], state['foe']['hp'])
        streak = memo.get('streak', 0) if memo.get('foe_hp') == foe_hp else 0
        choice = _choose(state, ai, flags, goals, new, streak)
        memo['foe_hp'] = foe_hp
        medicine = choice.get('kind') == 'item' and choice['item'] in HEALS or choice.get('item') in CURES.values() or choice.get('item') == 'fullheal'
        memo['streak'] = streak + 1 if medicine else 0
        return choice
    return action


def _choose(state, ai, flags, goals, new, streak):
    own, bag = state['own'], state['bag']
    danger = planning.planning_risk(state, ai, flags)
    D = danger['normal_max']
    fast_ko = sure_ko_first(state)
    if fast_ko:
        if new:
            for slot, m in fast_ko:
                if m['id'] == 'strength':
                    return {'kind': 'move', 'slot': slot}
        return strongest(state)
    if new:
        # Strength finisher when the foe can't KO first either.
        for slot, m in attacks.usable(own):
            if m['id'] == 'strength' and _kos(state, m) and own['hp'] > D and own['status'] not in ('slp', 'frz'):
                return {'kind': 'move', 'slot': slot}
        # Two medicine turns without the foe's HP moving: escalate, never chain.
        if streak >= 2:
            if own['hp'] <= D < own['max_hp']:
                for name in ('fullrestore', 'maxpotion'):
                    if bag.get(name):
                        return item(name)
            return strongest(state)
        # A status at KO risk: Full Restore.
        if own['status'] and own['hp'] <= D < own['max_hp'] and bag.get('fullrestore'):
            return item('fullrestore')
    if own['hp'] > D or (new and own['status'] == 'slp'):
        cure = own_cure(state, goals, new)
        if cure:
            return cure
    if own['hp'] <= D:
        if D >= own['max_hp']:
            return strongest(state)
        heal = ko_heal_new(state, danger, goals) if new else ko_heal_old(state, danger)
        return heal or strongest(state)
    if own['status'] == 'slp':
        return strongest(state)
    if any(m['id'] == 'surf' and m['pp'] == 0 for m in own['moves']):
        for name in ('elixir', 'maxelixir'):
            if bag.get(name):
                return item(name)
    planned = setup(state, goals)
    if not planned:
        return strongest(state)
    g = GOALS[goals['_fight']]
    turns = planning.setup_turns(state, g, planned)
    reserve = min(own['max_hp'] * .75, D + max(0, turns - 1) * danger['mean'])
    if own['hp'] >= reserve:
        return planned
    return reserve_heal(state, danger, reserve, goals) or strongest(state)


POLICIES = {'autostory_old': _policy(False), 'autostory_new': _policy(True)}

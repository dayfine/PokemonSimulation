"""FRLG League policy as data: a per-fight plan (JSON) plus a small state->action override table.

The plan says, for each foe slot of each fight, which moves to use (a ranking) and which setup
goals to reach first, each tied to the move it serves; what PP and items this fight must leave
for later fights (reserves); and the HP/PP to restore between fights. docs/battles/frlg-league-plan.md
holds the schema. The override table handles what a plan can't know in advance (KO risk at the
current HP and stat stages, status, a trainer's Full Restore, misses, PP actually left). Every
override names its row; the chain records it as the decision's `why`.

Rows, in order (first match wins):
  locked        a two-turn / recharge / Outrage turn: the forced move
  sure_ko       a move KOs for certain (lowest roll, accuracy incl. evasion, the foe's HP after its
                trainer's heal) and we move first (speed incl. stages): the cheapest such move
  sleep_cure    asleep or frozen with a cure: Full Restore at KO risk, else Awakening / Full Heal
  status_ko     a status and KO risk: Full Restore
  ko_heal       KO risk (HP <= the foe's worst normal hit now): the smallest heal that clears it with
                a mean hit of margin; two medicine turns without the foe's HP moving: Full Restore or
                attack; no heal survives: attack
  cure          paralysis / poison with no KO risk: its cure
  kill_order    the trainer can still heal below 1/4: an opener that leaves the foe at or above 1/4
                and lets the finisher KO, never the hit that drops it into heal range
  pp_restore    every planned move is out of PP: an Elixir not held in reserve
  (plan)        setup goal whose served move has PP; else the first planned move with PP
"""

import json
from pathlib import Path

from pokesim.games.frlg.battle.items import HEALS, CURES
from pokesim.games.frlg.battle.npc_actions import trainer_heals_below_quarter, trainer_item
from pokesim.games.frlg.battle.player_strategy import attacks, planning

PLAN_FORMAT = 'frlg-league-plan/1'
DEFAULT_PLAN = Path(__file__).with_name('plan.json')
X_STAT = {'xspecial': 'spa', 'xspeed': 'spe', 'xaccuracy': 'accuracy', 'xattack': 'atk', 'xdefend': 'def'}
# Cheapest first: what a sure KO spends.
PP_VALUE = {'strength': 0, 'bite': 1, 'surf': 2, 'blizzard': 9}
PP_ITEMS = ('elixir', 'maxelixir')


def load_plan(path=DEFAULT_PLAN):
    plan = json.loads(Path(path).read_text())
    if plan.get('format') != PLAN_FORMAT:
        raise ValueError('not a {} plan: {}'.format(PLAN_FORMAT, path))
    return plan


def item(name):
    return {'kind': 'item', 'item': name}


def fight_plan(goals):
    return goals['_league_plan']['fights'][goals['_fight']]


def foe_plan(goals, foe):
    fight = fight_plan(goals)
    foes = fight['foes']
    index = foe['party_index']
    if index < len(foes) and foes[index]['species'] == foe['species']:
        return foes[index]
    return next((f for f in foes if f['species'] == foe['species']), {'species': foe['species'], 'moves': []})


def reserve(goals, kind, name):
    return fight_plan(goals).get('reserve', {}).get(kind, {}).get(name, 0)


def spendable(goals, bag, name):
    """Bag count above this fight's reserve (items kept for later fights)."""
    return bag.get(name, 0) - reserve(goals, 'items', name)


def pp_left(goals, move):
    """PP above this fight's reserve for the move (PP kept for later fights)."""
    return move['pp'] - reserve(goals, 'pp', move['id'])


def foe_heals(state, goals):
    return trainer_heals_below_quarter(state, goals.get('_trainer_items', ()))


def foe_hp_at_our_move(state, goals):
    """The trainer uses its item before any move: a foe under 1/4 is back to full when we hit."""
    foe = state['foe']
    if trainer_item(state, goals.get('_trainer_items', ())):
        return foe['max_hp']
    return foe['hp']


def we_move_first(state, move):
    own, foe = state['own'], state['foe']
    if move.get('priority', 0) != 0:
        return move['priority'] > 0
    if foe['locked_move'] == 'recharge':
        return True
    return own['speed'] > foe['speed']  # speed includes stat stages (Rock Tomb, Scary Face) and paralysis


def sure_ko(move, hp):
    return move['accuracy'] >= 1 and not move.get('two_turn') and move.get('damage') and min(move['damage']) >= hp


def danger(state, goals):
    """KO risk this turn: residual plus the foe's worst normal hit as it stands (our current
    Def/Sp. Def stages, its stages, weather). Zero while it recharges, sleeps, uses an item,
    or charges a two-turn move it is not yet holding."""
    own, foe = state['own'], state['foe']
    residual = own['max_hp'] // 8 * (int(own['status'] in ('psn', 'tox')) + int('leechseed' in own['volatiles']))
    if (foe['locked_move'] == 'recharge' or (foe['status'] == 'slp' and foe['sleep_turns'] > 1)
            or foe['status'] == 'frz' or trainer_item(state, goals.get('_trainer_items', ()))):
        return {'normal_max': residual, 'mean': residual, 'sure': residual}
    usable = [m for _, m in attacks.usable(foe) if max(m.get('damage', [0])) > 0]
    charging = any(m['id'] == foe['locked_move'] for m in usable if m.get('two_turn'))
    sun = state['foe'].get('weather') == 'AI_WEATHER_SUN'
    hits = [m for m in usable if charging and m['id'] == foe['locked_move']
            or not m.get('two_turn') or sun and m['id'] == 'solarbeam']
    worst = max((max(m['damage']) for m in hits), default=0)
    mean = max((sum(m['damage']) / len(m['damage']) * m['accuracy'] for m in hits), default=0)
    sure = max((min(m['damage']) for m in hits), default=0)
    return {'normal_max': residual + worst, 'mean': residual + mean, 'sure': residual + sure}


def _heal(state, d, goals, fight_reserve=True):
    """The smallest heal that lifts HP above D and gains at least D plus a mean hit; else bigger."""
    own, bag = state['own'], state['bag']
    missing = own['max_hp'] - own['hp']
    for name in ('superpotion', 'hyperpotion', 'maxpotion'):
        if spendable(goals, bag, name) <= 0:
            continue
        gained = min(missing, HEALS[name])
        if own['hp'] + gained > d['normal_max'] and gained - d['normal_max'] >= d['mean']:
            return name
    if spendable(goals, bag, 'fullrestore') > 0:
        return 'fullrestore'
    if bag.get('fullrestore'):
        return 'fullrestore'  # reserve breached: dying here loses the League anyway
    for name in ('maxpotion', 'hyperpotion', 'superpotion'):
        if bag.get(name) and own['hp'] + min(missing, HEALS[name]) > d['normal_max']:
            return name
    return None


def setup_goal(state, goals, plan_foe):
    """The first unmet setup goal whose served move still has PP and whose item is spendable."""
    own, bag, foe = state['own'], state['bag'], state['foe']
    moves = {m['id']: m for _, m in attacks.usable(own)}
    for goal in plan_foe.get('setup', ()):
        served = moves.get(goal.get('serves'))
        if goal.get('serves') and (served is None or pp_left(goals, served) <= 0):
            continue
        name = goal['item']
        if spendable(goals, bag, name) <= 0:
            continue
        if name == 'guardspec':
            if 'mist' in own['side_conditions']:
                continue
            return goal
        if own['boosts'][X_STAT[name]] < goal['stage']:
            return goal
    return None


def foe_heal(state, goals, plan_foe):
    """The foe's `heal` block: below `below` HP, the smallest spendable heal that restores at least
    `heal_at_least` HP (Super Potion 50, Full Restore to full)."""
    rule = plan_foe.get('heal')
    own, bag = state['own'], state['bag']
    if not rule or own['hp'] >= rule['below']:
        return None
    missing = own['max_hp'] - own['hp']
    for name in ('superpotion', 'hyperpotion', 'maxpotion', 'fullrestore'):
        if spendable(goals, bag, name) > 0 and min(missing, HEALS[name]) >= min(missing, rule.get('heal_at_least', 0)):
            return name
    return None


def sequence_move(state, goals, plan_foe):
    """The foe's `sequence`: our n-th attack on this foe uses its n-th move (then `moves`)."""
    seq = plan_foe.get('sequence')
    if not seq:
        return None
    n = goals.setdefault('_memo', {}).get(('attacks', state['foe']['party_index']), 0)
    if n >= len(seq):
        return None
    usable = dict((m['id'], (slot, m)) for slot, m in attacks.usable(state['own']))
    return usable.get(seq[n])


def planned_move(state, goals, plan_foe):
    own = state['own']
    usable = dict((m['id'], (slot, m)) for slot, m in attacks.usable(own))
    chosen = sequence_move(state, goals, plan_foe)
    if chosen:
        return chosen
    for name in plan_foe.get('moves', ()):
        if name in usable and pp_left(goals, usable[name][1]) > 0:
            return usable[name]
    # Nothing planned has PP: the best expected hit among moves not held in reserve.
    options = [(sum(m['damage']) / len(m['damage']) * m['accuracy'], slot, m) for slot, m in attacks.usable(own)
               if m.get('damage') and max(m['damage']) > 0 and pp_left(goals, m) > 0]
    if not options:
        options = [(sum(m['damage']) / len(m['damage']) * m['accuracy'], slot, m) for slot, m in attacks.usable(own)
                   if m.get('damage')]
    if not options:
        return None
    _, slot, m = max(options, key=lambda o: o[0])
    return slot, m


def kill_order(state, goals, chosen):
    """With a trainer heal open, never drop the foe into [1, 1/4): prefer an opener whose every roll
    leaves it at or above 1/4 and after which the finisher's lowest roll KOs."""
    foe = state['foe']
    quarter = foe['max_hp'] // 4
    hp = foe['hp']
    slot, move = chosen
    rolls = move['damage']
    if not foe_heals(state, goals) or min(rolls) >= hp or not any(0 < hp - r < quarter for r in rolls):
        return None
    usable = [(s, m) for s, m in attacks.usable(state['own']) if m.get('damage') and max(m['damage']) > 0
              and pp_left(goals, m) > 0]
    finisher = max((min(m['damage']) * (m['accuracy'] >= 1) for _, m in usable), default=0)
    openers = [(sum(m['damage']), s, m) for s, m in usable
               if hp - max(m['damage']) >= quarter and hp - min(m['damage']) <= finisher]
    if not openers:
        # No two-hit kill: the strongest hit that still leaves the foe at or above 1/4.
        openers = [(sum(m['damage']), s, m) for s, m in usable if hp - max(m['damage']) >= quarter]
    if openers:
        _, s, m = max(openers, key=lambda o: o[0])
        if s != slot:
            return s, m
    return None


def _medicine(action):
    name = action.get('item')
    return action.get('kind') == 'item' and (name in HEALS or name in CURES.values() or name == 'fullheal')


def action(state, ai, flags, items, goals):
    goals['_trainer_items'] = items
    memo = goals.setdefault('_memo', {})
    foe_key = (state['foe']['species'], state['foe']['hp'])
    streak = memo.get('streak', 0) if memo.get('foe') == foe_key else 0
    why, choice = choose(state, goals, streak)
    if choice.get('kind') == 'move':
        key = ('attacks', state['foe']['party_index'])
        memo[key] = memo.get(key, 0) + 1
    memo['foe'] = foe_key
    memo['streak'] = streak + 1 if _medicine(choice) else 0
    goals['_why'] = why
    return choice


def choose(state, goals, streak):
    """(row, action): the override table, then the plan."""
    own, bag, foe = state['own'], state['bag'], state['foe']
    forced = attacks.locked(own)
    if forced:
        return 'locked', forced
    plan_foe = foe_plan(goals, foe)
    d = danger(state, goals)
    risk_mode = goals.get('_risk')
    if risk_mode in ('mean', 'sure'):
        # Riskier variants: heal only when the foe's mean hit ('mean') or its lowest roll ('sure') KOs.
        d = dict(d, normal_max=d[risk_mode])
    elif risk_mode == 'never':
        d = dict(d, normal_max=0)
    D = d['normal_max']
    target_hp = foe_hp_at_our_move(state, goals)
    awake = own['status'] not in ('slp', 'frz')
    # A sure KO waits while this foe is the plan's setup foe and we are safe: setup carries to the next foes.
    goal_first = own['hp'] > D and setup_goal(state, goals, plan_foe) is not None and sum(
        p['hp'] > 0 for p in state['party']) > 1
    heal_rule = plan_foe.get('heal') or {}
    if heal_rule.get('heal_when_can_ko') and streak < 2:
        name = foe_heal(state, goals, plan_foe)
        if name:
            return 'foe_heal', item(name)
    if awake and not goal_first:
        kos = [(PP_VALUE.get(m['id'], 5), slot, m) for slot, m in attacks.usable(own)
               if sure_ko(m, target_hp) and we_move_first(state, m) and (pp_left(goals, m) > 0 or own['hp'] <= D)]
        if kos:
            _, slot, m = min(kos, key=lambda k: k[0])
            return 'sure_ko', {'kind': 'move', 'slot': slot}
    if not awake:
        cure = CURES.get(own['status'])
        if own['hp'] <= D < own['max_hp'] and bag.get('fullrestore'):
            return 'sleep_cure', item('fullrestore')
        for name in (cure, 'fullheal', 'fullrestore'):
            if name and bag.get(name):
                return 'sleep_cure', item(name)
    if heal_rule and streak < 2:
        name = foe_heal(state, goals, plan_foe)
        if name:
            return 'foe_heal', item(name)
    risk = own['hp'] <= D
    if risk and D < own['max_hp'] and heal_rule.get('ko_rule', True):
        if own['status'] and bag.get('fullrestore'):
            return 'status_ko', item('fullrestore')
        if streak >= 2:
            if bag.get('fullrestore'):
                return 'ko_heal', item('fullrestore')
        else:
            heal = _heal(state, d, goals)
            if heal:
                return 'ko_heal', item(heal)
    if not risk and streak == 0 and own['status'] in ('par', 'psn', 'tox', 'brn'):
        for name in (CURES.get(own['status']), 'fullheal'):
            if name and spendable(goals, bag, name) > 0:
                return 'cure', item(name)
    chosen = planned_move(state, goals, plan_foe)
    if chosen is None or all(pp_left(goals, m) <= 0 for _, m in attacks.usable(own) if m['id'] in plan_foe.get('moves', ())):
        if not risk and plan_foe.get('moves'):
            for name in PP_ITEMS:
                if spendable(goals, bag, name) > 0:
                    return 'pp_restore', item(name)
    if not risk:
        goal = setup_goal(state, goals, plan_foe)
        if goal:
            turns = sum(1 for g in plan_foe.get('setup', ()) if g['item'] != 'guardspec')
            keep = min(own['max_hp'] * 0.75, D + max(0, turns - 1) * d['mean'])
            if own['hp'] >= keep or foe_hp_at_our_move(state, goals) != foe['hp'] or risk_mode in ('sure', 'never'):
                return 'plan:setup', item(goal['item'])
            heal = _heal(state, d, goals)
            if heal and heal != 'fullrestore' or (heal and spendable(goals, bag, 'fullrestore') > 0):
                return 'plan:setup_heal', item(heal)
    if chosen is None:
        return 'plan:struggle', attacks.attack(state)
    if awake and plan_foe.get('kill_order', True) and not plan_foe.get('sequence'):
        swap = kill_order(state, goals, chosen)
        if swap:
            return 'kill_order', {'kind': 'move', 'slot': swap[0]}
    return 'plan:move', {'kind': 'move', 'slot': chosen[0]}


def between(carry, max_hp, plan, next_fight, move_pp):
    """Between-fight top-ups from the plan's `between` row of the next fight: a cure, Super Potions
    (then a Full Restore) to the HP target, a PP item to the PP floor; reserves of the next fight hold."""
    used = {}
    bag = carry['bag']
    row = plan['fights'][next_fight]
    rsv = row.get('reserve', {}).get('items', {})

    def can(name):
        return bag.get(name, 0) - rsv.get(name, 0) > 0

    def use(name):
        bag[name] -= 1
        used[name] = used.get(name, 0) + 1

    if carry['status']:
        for name in (CURES.get(carry['status']), 'fullheal', 'fullrestore'):
            if name and can(name):
                use(name)
                carry['status'] = ''
                if name == 'fullrestore':
                    carry['hp'] = max_hp
                break
    target = int(max_hp * row.get('between', {}).get('hp', 1.0) + 0.999)
    for _ in range(20):
        if carry['hp'] >= target:
            break
        spare = bag.get('superpotion', 0) - rsv.get('superpotion', 0)
        if can('superpotion') and (target - carry['hp'] <= 50 * spare or not can('fullrestore')):
            use('superpotion')
            carry['hp'] = min(max_hp, carry['hp'] + 50)
        elif can('fullrestore'):
            use('fullrestore')
            carry['hp'] = max_hp
        else:
            break
    floor = row.get('between', {}).get('pp', {})
    pp = carry['pp']
    if any(pp.get(k.upper(), 0) < v for k, v in floor.items()):
        for name in PP_ITEMS:
            if can(name):
                use(name)
                for k in pp:
                    pp[k] = move_pp[k] if name == 'maxelixir' else min(move_pp[k], pp[k] + 10)
                break
    return used


FIGHTS = ('lorelei', 'bruno', 'agatha', 'lance', 'champion')


def caps(plan, fight):
    """The fight's item caps: what its accepted win may spend (top-ups before it included)."""
    return plan['fights'][fight].get('caps', {})


def reserves_from_caps(plan):
    """{fight: {item: count}}: what each fight must leave for the later fights' caps."""
    names = {name for fight in FIGHTS for name in caps(plan, fight)}
    out = {}
    for i, fight in enumerate(FIGHTS):
        later = {name: sum(caps(plan, f).get(name, 0) for f in FIGHTS[i + 1:]) for name in names}
        out[fight] = {name: n for name, n in later.items() if n}
    return out
SPECIES = {
    'lorelei': ('dewgong', 'cloyster', 'slowbro', 'jynx', 'lapras'),
    'bruno': ('onix', 'hitmonchan', 'hitmonlee', 'onix', 'machamp'),
    'agatha': ('gengar', 'golbat', 'haunter', 'arbok', 'gengar'),
    'lance': ('gyarados', 'dragonair', 'dragonair', 'aerodactyl', 'dragonite'),
    'champion': ('pidgeot', 'alakazam', 'rhydon', 'gyarados', 'arcanine', 'venusaur'),
}
SETUP_ITEMS = ('xspecial', 'xspeed', 'xaccuracy', 'guardspec')


def setup_count(foes):
    count = {}
    for foe in foes:
        for goal in foe.get('setup', ()):
            count[goal['item']] = count.get(goal['item'], 0) + goal.get('stage', 1)
    return count


def build(spec, bag):
    """A full plan from a compact spec: {fight: {'foes': {slot: {...}}, 'between': {...},
    'fr_spend': n, 'pp_reserve': {...}, 'hard_items': {...}}}. Item reserves: the setup items the
    later fights' goals need (capped by the bag), the Full Restores the later fights' fr_spend
    allows, and hard reserves (the Max Elixir until after Lance)."""
    fights = {}
    needs = []
    for fight in FIGHTS:
        row = spec[fight]
        foes = []
        for index, species in enumerate(SPECIES[fight]):
            foe = dict(row['foes'].get(index, row['foes'].get(species, {})))
            foe = {'species': species, 'moves': list(foe.get('moves', ())), 'setup': list(foe.get('setup', ()))}
            foes.append(foe)
        needs.append(setup_count(foes))
        fights[fight] = {'foes': foes, 'between': dict(row.get('between', {})),
                         'reserve': {'pp': dict(row.get('pp_reserve', {})), 'items': {}}}
    for i, fight in enumerate(FIGHTS):
        items = {}
        for name in SETUP_ITEMS:
            later = sum(n.get(name, 0) for n in needs[i + 1:])
            items[name] = min(bag.get(name, 0), later)
        later_fr = sum(spec[f].get('fr_spend', 0) for f in FIGHTS[i + 1:])
        items['fullrestore'] = min(bag.get('fullrestore', 0), later_fr)
        items.update(spec[fight].get('hard_items', {}))
        fights[fight]['reserve']['items'] = {k: v for k, v in items.items() if v}
    return {'format': PLAN_FORMAT, 'fights': fights}

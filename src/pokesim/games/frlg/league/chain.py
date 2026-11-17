"""Run the FRLG Elite Four + Champion as one continuous chain (no saves between fights).

HP, status, PP and bag carry over; between fights the policy may use bag items
(HP medicine, status cures, Elixirs). A loss anywhere ends the chain.
Stats are fixed per fight (no in-battle level-ups); a fight's stats come from
the `levels` table of the profile.
"""

import copy
import random
from collections import Counter

from pokesim.games.frlg.battle.benchmark import scenario_for, reveal
from pokesim.games.frlg.battle.npc_actions import trainer_item, replacement
from pokesim.games.frlg.battle.player_strategy.attacks import locked
from pokesim.games.frlg.league.replica import POLICIES as REPLICA_POLICIES
from pokesim.games.frlg.league import autostory

POLICIES = dict(REPLICA_POLICIES, **autostory.POLICIES)

FIGHTS = ('lorelei', 'bruno', 'agatha', 'lance', 'champion')
# PokeGuy's recorded entry HP share: Bruno 130/162, Agatha 45/165 (Torrent on), Lance and Champion full.
ENTRY_TARGET = {'bruno': 0.80, 'agatha': 0.27, 'lance': 1.0, 'champion': 1.0}
# On video he healed nothing before Bruno (130/162, kept as an 80% floor: 30% lost 26% of chains at Bruno)
# or Agatha (45/165) and fully before Lance and the
# Champion; we keep Bruno/Agatha above an Earthquake-sized floor and use Super Potions first.
VIDEO_ENTRY_TARGET = {'bruno': 0.80, 'agatha': 0.27, 'lance': 1.0, 'champion': 1.0}
MOVE_PP = {'BITE': 25, 'SURF': 15, 'BLIZZARD': 5, 'STRENGTH': 15}


def ours_at(level):
    """Our Blastoise (console B, 2026-11-16): Lv51 162/98/126/111/140/111, Lv52 165/99/129/114/144/113, Lv54 171 HP."""
    d = level - 51
    return {'hp': 162 + 3 * d, 'atk': 98 + d, 'def': 126 + 3 * d, 'spa': 111 + round(2.6 * d),
            'spd': 140 + round(3.5 * d), 'spe': 111 + 2 * d}


def fight_scenario(case, pret, carry, stats, level, only_foe=None):
    scenario = copy.deepcopy(case)
    scenario.pop('progression', None)
    player = scenario['player']
    if stats is not None:
        player['stats'] = dict(stats)
        player['level'] = level
    player['hp'] = min(carry['hp'], player['stats']['hp']) if carry['hp'] is not None else player['stats']['hp']
    player['status'] = carry['status']
    player['moves'] = [{'name': name, 'pp': pp} for name, pp in carry['pp'].items()]
    scenario['bag'] = {k: v for k, v in carry['bag'].items() if v > 0}
    scenario = scenario_for(scenario, pret)
    if only_foe:
        scenario['trainer']['party'] = [p for p in scenario['trainer']['party'] if p['species'] == only_foe.upper()]
    return scenario


def play(engine, scenario, ai, policy, seed, turn_limit=300, fight=None, extra_goals=None):
    seeds = random.Random('engine:' + seed)
    state = engine.request(command='start', scenario=scenario, seed=[seeds.randrange(65536) for _ in range(4)])
    rng = random.Random('ai:' + seed)
    known, decisions, crits = set(), [], []
    flags = scenario['trainer']['ai']
    items = [item.lower().replace('_', '') for item in scenario['trainer']['items']]
    goals = dict(scenario.get('planning_goals') or {}, _fight=fight, _entry_bag=dict(scenario['bag']), **(extra_goals or {}))
    while not state['ended'] and state['turn'] <= turn_limit:
        reveal(state, known)
        if state['needs_switch']:
            own, foe = {'kind': 'pass'}, replacement(state)
        else:
            own = policy(state, ai, flags, items, goals)
            foe = locked(state['foe']) or trainer_item(state, items) or ai.choose_move(state, flags, rng)
        decisions.append({'turn': state['turn'], 'hp': state['own']['hp'], 'max_hp': state['own']['max_hp'],
            'foe': state['foe']['species'], 'foe_hp': state['foe']['hp'], 'foe_max_hp': state['foe']['max_hp'],
            'boosts': dict(state['own']['boosts']), 'foe_evasion': state['foe']['boosts'].get('evasion', 0),
            'own': own, 'opponent': foe,
            'move': state['own']['moves'][own['slot']]['id'] if own.get('kind') == 'move' else None})
        turn = state['turn']
        state = engine.request(command='step', own=own, foe=foe)
        if any(line.startswith('|-crit|p1a') for line in state['log']):
            crits.append(turn)
    state['foe_crit_turns'] = crits
    return state, decisions


def between_fights(carry, max_hp, policy_name, next_fight):
    """Out-of-battle top-ups. Returns the items used."""
    used = Counter()
    bag = carry['bag']
    if carry['status'] and bag.get('fullheal'):
        bag['fullheal'] -= 1; used['fullheal'] += 1; carry['status'] = ''
    if policy_name.startswith('autostory'):
        return autostory_between(carry, max_hp, policy_name == 'autostory_new', next_fight)
    if policy_name == 'current_c':
        if carry['hp'] * 2 < max_hp and bag.get('fullrestore'):
            bag['fullrestore'] -= 1; used['fullrestore'] += 1; carry['hp'] = max_hp; carry['status'] = ''
        return used
    # replica: Super Potions up to PokeGuy's entry HP for the next fight; a Full Restore
    # out of battle only when a status needs it or the Super Potions run out.
    if carry['status'] and bag.get('fullrestore'):
        bag['fullrestore'] -= 1; used['fullrestore'] += 1; carry['hp'] = max_hp; carry['status'] = ''
    targets = VIDEO_ENTRY_TARGET if policy_name == 'video' else ENTRY_TARGET
    target = max_hp * (targets.get(next_fight, 1.0) if policy_name != 'replica_full' else 1.0)
    while carry['hp'] < target and bag.get('superpotion'):
        bag['superpotion'] -= 1; used['superpotion'] += 1; carry['hp'] = min(max_hp, carry['hp'] + 50)
    if carry['hp'] < target and bag.get('fullrestore'):
        bag['fullrestore'] -= 1; used['fullrestore'] += 1; carry['hp'] = max_hp
    # PP: keep Surf for the next fight; Elixir first, Max Elixir when Surf is nearly out.
    need = {'bruno': 7, 'agatha': 6, 'lance': 6, 'champion': 8}.get(next_fight, 0)
    pp = carry['pp']
    if pp['SURF'] < need or pp['BITE'] < 4:
        item = 'elixir' if bag.get('elixir') and pp['SURF'] + 10 >= need else ('maxelixir' if bag.get('maxelixir') else 'elixir')
        if bag.get(item):
            bag[item] -= 1; used[item] += 1
            for name in pp:
                pp[name] = MOVE_PP[name] if item == 'maxelixir' else min(MOVE_PP[name], pp[name] + 10)
    return used


def autostory_between(carry, max_hp, new, next_fight):
    """between_fight_action(): a cure (own, Full Heal, Full Restore); HP to the entry target with
    Super Potions, then (new) Hyper / Max Potions, a Full Restore last; Elixir to the PP floor."""
    used = Counter()
    bag = carry['bag']

    def use(item):
        bag[item] -= 1
        used[item] += 1

    cure = {'par': 'parlyzheal', 'psn': 'antidote', 'tox': 'antidote', 'slp': 'awakening'}.get(carry['status'])
    if carry['status']:
        for item in (cure, 'fullheal', 'fullrestore'):
            if item and bag.get(item):
                use(item)
                carry['status'] = ''
                if item == 'fullrestore':
                    carry['hp'] = max_hp
                break
    target = -(-max_hp * int(ENTRY_TARGET.get(next_fight, 1.0) * 100) // 100)
    order = ('superpotion', 'hyperpotion', 'maxpotion', 'fullrestore') if new else ('superpotion', 'fullrestore')
    for _ in range(20):
        if carry['hp'] >= target:
            break
        item = next((i for i in order if bag.get(i)), None)
        if item is None:
            break
        use(item)
        carry['hp'] = min(max_hp, carry['hp'] + {'superpotion': 50, 'hyperpotion': 200}.get(item, max_hp))
    need = {'bruno': 7, 'agatha': 6, 'lance': 6, 'champion': 8}.get(next_fight, 0)
    blizzard = {'lance': 5, 'champion': 2}.get(next_fight, 0)
    pp = carry['pp']
    if pp['SURF'] < need or pp['BLIZZARD'] < blizzard:
        reaches = pp['SURF'] + 10 >= need and min(5, pp['BLIZZARD'] + 10) >= blizzard
        item = next((i for i in (('elixir', 'maxelixir') if reaches else ('maxelixir', 'elixir')) if bag.get(i)), None)
        if item:
            use(item)
            for name in pp:
                pp[name] = MOVE_PP[name] if item == 'maxelixir' else min(MOVE_PP[name], pp[name] + 10)
    return used


def run_chain(engine, cases, pret, ai, policy_name, bag, levels, seed, entry_hp=None, fights=FIGHTS, only_foe=None,
              budget=None):
    """budget: per-fight item budgets {fight: {item: n}} in place of the planner's split (autostory only)."""
    policy = POLICIES[policy_name]
    carry = {'hp': entry_hp, 'status': '', 'pp': dict(MOVE_PP), 'bag': dict(bag)}
    record = {'seed': seed, 'fights': [], 'outcome': 'win'}
    extra = None
    if policy_name.startswith('autostory'):
        plan = autostory.cumulative(budget) if budget else autostory.plan(bag, policy_name == 'autostory_new')
        extra = {'_plan': plan, '_start_bag': dict(bag)}
    for index, fight in enumerate(fights):
        stats = ours_at(levels[fight]) if levels else None
        max_hp = stats['hp'] if stats else cases[fight]['player']['stats']['hp']
        if carry['hp'] is None:
            carry['hp'] = max_hp
        top = between_fights(carry, max_hp, policy_name, fight) if index else Counter()
        entry = {'hp': carry['hp'], 'max_hp': max_hp, 'pp': dict(carry['pp']), 'bag': dict(carry['bag'])}
        scenario = fight_scenario(cases[fight], pret, carry, stats, levels[fight] if levels else None, only_foe)
        state, decisions = play(engine, scenario, ai, policy, '{}:{}'.format(seed, fight), fight=fight,
            extra_goals=dict(extra) if extra else None)
        won = state['winner'] == 'Player'
        own = state['own']
        carry['hp'] = own['hp']
        carry['status'] = own.get('status', '') or ''
        carry['pp'] = {m['id'].upper(): m['pp'] for m in own['moves']}
        carry['pp'] = {k: carry['pp'].get(k, carry['pp'].get(k.lower(), 0)) for k in MOVE_PP}
        carry['bag'] = {k: v for k, v in state['bag'].items()}
        used = Counter(state['items_used'])
        attacks = sum(1 for d in decisions if d['own'].get('kind') == 'move')
        record['fights'].append({'fight': fight, 'won': won, 'entry': entry, 'between_used': dict(top),
            'used': dict(used), 'attacks': attacks, 'turns': len(decisions), 'hp_left': own['hp'],
            'foe_at_end': state['foe']['species'], 'foe_crit_turns': state['foe_crit_turns'], 'decisions': decisions})
        if not won:
            record['outcome'] = 'loss@' + fight
            break
    return record

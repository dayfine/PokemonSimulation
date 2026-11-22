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
from pokesim.games.frlg.league import autostory, planned

POLICIES = dict(REPLICA_POLICIES, planned=planned.action, **autostory.POLICIES)

FIGHTS = ('lorelei', 'bruno', 'agatha', 'lance', 'champion')
# PokeGuy's recorded entry HP share: Bruno 130/162, Agatha 45/165 (Torrent on), Lance and Champion full.
ENTRY_TARGET = {'bruno': 0.80, 'agatha': 0.27, 'lance': 1.0, 'champion': 1.0}
# On video he healed nothing before Bruno (130/162, kept as an 80% floor: 30% lost 26% of chains at Bruno)
# or Agatha (45/165) and fully before Lance and the
# Champion; we keep Bruno/Agatha above an Earthquake-sized floor and use Super Potions first.
VIDEO_ENTRY_TARGET = {'bruno': 0.80, 'agatha': 0.27, 'lance': 1.0, 'champion': 1.0}
MOVE_PP = {'BITE': 25, 'SURF': 15, 'BLIZZARD': 5, 'STRENGTH': 15}


# Console B's summary read at Lv54 (2026-11-16 15:26): 171 HP, 104/134/118/149/117.
LV54 = {'hp': 171, 'atk': 104, 'def': 134, 'spa': 118, 'spd': 149, 'spe': 117}
# The rest of our party: HM users (the console sent party slots 2-5 after a faint on 2026-11-16,
# species unread). Placeholders; what matters is that Roar/Whirlwind find a switch-in.
BENCH = [{'species': 'RATICATE', 'level': 40, 'moves': ['CUT']} for _ in range(4)]


def ours_at(level, measured=True):
    """Our Blastoise (console B, 2026-11-16): Lv51 162/98/126/111/140/111, Lv52 165/99/129/114/144/113, Lv54 171 HP.
    measured: Lv54 is the console's summary read; other levels keep the growth model's step from it."""
    if measured:
        base, model = LV54, ours_at(54, False)
        step = ours_at(level, False)
        return {k: base[k] + step[k] - model[k] for k in base}
    d = level - 51
    return {'hp': 162 + 3 * d, 'atk': 98 + d, 'def': 126 + 3 * d, 'spa': 111 + round(2.6 * d),
            'spd': 140 + round(3.5 * d), 'spe': 111 + 2 * d}


def fight_scenario(case, pret, carry, stats, level, only_foe=None, bench=True, held_item=None):
    """held_item None keeps the case's (PokeGuy's Black Glasses); '' holds nothing."""
    scenario = copy.deepcopy(case)
    if bench:
        scenario['bench'] = copy.deepcopy(BENCH)
    scenario.pop('progression', None)
    player = scenario['player']
    if held_item is not None:
        player['held_item'] = held_item
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
        lead = next((p for p in state.get('own_party', ()) if p['party_index'] == 0), None)
        if lead is not None and lead['hp'] == 0:
            state['winner'] = 'Trainer'  # Blastoise fainted: the HM users can't win
            break
        back = None
        if state['own']['party_index'] != 0:
            back = {'kind': 'switch', 'slot': lead['position']}  # dragged out by Roar/Whirlwind: switch back
        if state['needs_switch']:
            own, foe = {'kind': 'pass'}, replacement(state)
        elif state.get('own_needs_switch'):
            own, foe = back, {'kind': 'pass'}
        elif back:
            own = back
            foe = locked(state['foe']) or trainer_item(state, items) or ai.choose_move(state, flags, rng)
        else:
            own = policy(state, ai, flags, items, goals)
            if goals.get('_why'):
                own = dict(own, why=goals.pop('_why'))
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


def between_fights(carry, max_hp, policy_name, next_fight, plan=None):
    """Out-of-battle top-ups. Returns the items used."""
    if policy_name == 'planned':
        return Counter(planned.between(carry, max_hp, plan, next_fight, MOVE_PP))
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


def pokeguy_between(carry, max_hp, next_fight):
    """PokeGuy's out-of-battle play on video (state-history.json): no HP top-up before Bruno (130/162)
    or Agatha (45/165); a Full Restore to full before Lance and the Champion (his Super Potions stayed 4);
    his one Elixir before the Champion. A status is cured first (he had none; dedicated cure, Full Heal,
    Full Restore)."""
    used = Counter()
    bag = carry['bag']

    def use(item):
        bag[item] -= 1
        used[item] += 1

    if carry['status']:
        cure = {'par': 'parlyzheal', 'psn': 'antidote', 'tox': 'antidote', 'slp': 'awakening'}.get(carry['status'])
        for item in (cure, 'fullheal', 'fullrestore'):
            if item and bag.get(item):
                use(item)
                carry['status'] = ''
                if item == 'fullrestore':
                    carry['hp'] = max_hp
                break
    if next_fight in ('lance', 'champion') and carry['hp'] < max_hp and bag.get('fullrestore'):
        use('fullrestore')
        carry['hp'] = max_hp
    pp = carry['pp']
    if next_fight == 'champion' and any(pp[name] < MOVE_PP[name] for name in pp):
        item = next((i for i in ('elixir', 'maxelixir') if bag.get(i)), None)
        if item:
            use(item)
            for name in pp:
                pp[name] = MOVE_PP[name] if item == 'maxelixir' else min(MOVE_PP[name], pp[name] + 10)
    return used


def run_chain(engine, cases, pret, ai, policy_name, bag, levels, seed, entry_hp=None, fights=FIGHTS, only_foe=None,
              budget=None, plan=None, bench=True, policy_fn=None, on_between=None, between=None, held_item=None):
    """budget: per-fight item budgets {fight: {item: n}} in place of the planner's split (autostory only).
    plan: the League plan (policy 'planned'); bench: our HM users in the party (Roar/Whirlwind work).
    policy_fn: called in place of POLICIES[policy_name] (a recorder wrapping it); on_between(fight, carry
    before, max_hp, used): each between-fight top-up.
    levels None: each fight's recorded stats from the case (PokeGuy's Lv51-55).
    between: 'pokeguy' for PokeGuy's out-of-battle healing in place of the policy's own.
    held_item: None keeps each case's (PokeGuy's Black Glasses, so our-Blastoise runs held them too);
    '' for none (our console Blastoise holds nothing)."""
    policy = policy_fn or POLICIES[policy_name]
    carry = {'hp': entry_hp, 'status': '', 'pp': dict(MOVE_PP), 'bag': dict(bag)}
    record = {'seed': seed, 'fights': [], 'outcome': 'win'}
    extra = None
    if policy_name.startswith('autostory'):
        plan_ = autostory.cumulative(budget) if budget else autostory.plan(bag, policy_name == 'autostory_new')
        extra = {'_plan': plan_, '_start_bag': dict(bag)}
    if policy_name == 'planned':
        extra = {'_league_plan': plan or planned.load_plan()}
    for index, fight in enumerate(fights):
        stats = ours_at(levels[fight]) if levels else None
        max_hp = stats['hp'] if stats else cases[fight]['player']['stats']['hp']
        if carry['hp'] is None:
            carry['hp'] = max_hp
        before = copy.deepcopy(carry)
        if not index:
            top = Counter()
        elif between == 'pokeguy':
            top = pokeguy_between(carry, max_hp, fight)
        else:
            top = between_fights(carry, max_hp, policy_name, fight, extra and extra.get('_league_plan'))
        if index and on_between:
            on_between(fight, before, max_hp, top)
        entry = {'hp': carry['hp'], 'max_hp': max_hp, 'pp': dict(carry['pp']), 'bag': dict(carry['bag'])}
        scenario = fight_scenario(cases[fight], pret, carry, stats, levels[fight] if levels else None, only_foe, bench,
                                  held_item)
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

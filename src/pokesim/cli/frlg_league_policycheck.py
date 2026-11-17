"""Replay the program's League "Battle: policy:" states through the sim's AutoStory port.

PYTHONPATH=src python3 -m pokesim.cli.frlg_league_policycheck LOG --since '2026-11-16 17:47:49' --out x.json

For each policy line: rebuild the state in the engine (our HP, status, Lv from the level-ups seen,
the program's boosts, PP from the moves used, the bag from the items used; the foe out at its HP %,
the foe's stat changes read from the battle text, the foe's fainted party members removed), ask
autostory_new for its action, and compare it with the program's ("using the X" / "move N").
Between two policy lines in one fight, the HP we lost to the foe's move (net of a Full Restore and
hail) is compared with the engine's damage preview for that move (normal and crit range).
"""

import argparse
import difflib
import json
import re

from pokesim.cli.frlg_league_chain import league_cases, BAG_NOW
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.league import autostory
from pokesim.games.frlg.league.chain import fight_scenario, ours_at, MOVE_PP

PROGRAM_MOVES = {1: 'bite', 2: 'strength', 3: 'surf', 4: 'blizzard'}
BAG_NAMES = {'full-restore': 'fullrestore', 'x-special': 'xspecial', 'x-speed': 'xspeed', 'x-accuracy': 'xaccuracy',
             'guard-spec': 'guardspec', 'elixir': 'elixir', 'max-elixir': 'maxelixir', 'super-potion': 'superpotion',
             'full-heal': 'fullheal', 'parlyz-heal': 'parlyzheal', 'antidote': 'antidote'}
STATUS = {'PAR': 'par', 'PSN': 'psn', 'SLP': 'slp', 'BRN': 'brn', 'FRZ': 'frz', 'TOX': 'tox'}
STATS = {'attack': 'atk', 'defense': 'def', 'spdef': 'spd', 'spatk': 'spa', 'speed': 'spe', 'evasiveness': 'evasion', 'accuracy': 'accuracy'}
LINE = re.compile(r'^(\S+ \S+) - \[Console 0\]: (.*)$')
POLICY = re.compile(r'Battle: policy: HP (\d+)/(\d+), foe (\w+) (\d+)%, Sp\. Atk ([+-]\d+), Speed ([+-]\d+), accuracy ([+-]\d+), budget (.*?); (.*)$')
TURN = re.compile(r'Battle: turn \d+, .*?\), (no status|\w+),')
FIGHT = re.compile(r'Story: (\w+) is TRAINER_')


def events(path, since):
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            m = LINE.match(raw.rstrip('\n'))
            if m and m.group(1) >= since:
                yield m.group(1), m.group(2)


def foe_move(text, species, moves):
    head = 'foe' + species + 'used'
    if 'used' not in text or not text.startswith('foe'):
        return None
    tail = text.split('used', 1)[1]
    best = difflib.get_close_matches(tail, [m['id'] for m in moves], n=1, cutoff=.6)
    return best[0] if best else tail


def collect(path, since):
    """Policy turns with what the program saw and did, and the battle text up to the next turn."""
    turns, fight, level, status = [], None, 54, ''
    bag = dict(BAG_NOW)
    used_pp = {k: 0 for k in MOVE_PP}
    fainted, foe_boosts, current = set(), {}, None
    pending = None
    for stamp, msg in events(path, since):
        m = FIGHT.match(msg)
        if m:
            fight, fainted, foe_boosts, pending = m.group(1), set(), {}, None
            continue
        if fight is None:
            continue
        m = TURN.match(msg)
        if m:
            status = STATUS.get(m.group(1), '')
            continue
        m = POLICY.match(msg)
        if m:
            hp, max_hp, species, pct, spa, spe, acc, budget, reason = m.groups()
            if species != current:
                foe_boosts, current = {}, species
            pending = {'time': stamp, 'fight': fight, 'level': level, 'hp': int(hp), 'max_hp': int(max_hp),
                       'status': status, 'foe': species, 'foe_pct': int(pct), 'fainted': sorted(fainted),
                       'boosts': {'spa': int(spa), 'spe': int(spe), 'accuracy': int(acc)}, 'foe_boosts': dict(foe_boosts),
                       'bag': dict(bag), 'pp': {k: MOVE_PP[k] - used_pp[k] for k in MOVE_PP}, 'budget': budget,
                       'reason': reason, 'program': None, 'texts': []}
            turns.append(pending)
            continue
        if pending is None:
            continue
        m = re.match(r'Battle: using the ([\w-]+) in', msg)
        if m:
            item = BAG_NAMES.get(m.group(1), m.group(1))
            pending['program'] = item
            bag[item] = bag.get(item, 0) - 1
            continue
        m = re.match(r'Battle: move (\d)\.', msg)
        if m:
            move = PROGRAM_MOVES[int(m.group(1))]
            pending['program'] = move
            used_pp[move.upper()] += 1
            continue
        m = re.match(r'Battle: text "(.*)"\.', msg)
        if m:
            text = m.group(1)
            texts = pending['texts']
            if texts and text.startswith(texts[-1]):
                texts[-1] = text
            else:
                texts.append(text)
            if text.endswith('fainted') and text.startswith('foe'):
                fainted.add(text[3:-7])
            if 'grewtolv' in text and not (len(texts) > 1 and 'grewtolv' in texts[-2]):
                level += 1
            sm = re.match(r'foe(\w+?)s(attack|defense|spdef|spatk|speed|evasiveness|accuracy)(sharply)?(rose|fell)$', text)
            if sm:
                key = STATS[sm.group(2)]
                foe_boosts[key] = foe_boosts.get(key, 0) + (2 if sm.group(3) else 1) * (1 if sm.group(4) == 'rose' else -1)
    return turns


def build_state(engine, cases, pret, turn):
    fight = turn['fight']
    stats = ours_at(turn['level'])
    carry = {'hp': turn['hp'], 'status': turn['status'], 'pp': turn['pp'], 'bag': turn['bag']}
    scenario = fight_scenario(cases[fight], pret, carry, stats, turn['level'])
    scenario['player']['boosts'] = {k: v for k, v in turn['boosts'].items() if v}
    party = scenario['trainer']['party']
    species = autostory.FOE_SPECIES[fight]
    dead = list(turn['fainted'])
    alive = []
    for index, mon in enumerate(party):
        name = species[index]
        if name in dead:
            dead.remove(name)
            continue
        alive.append((index, mon))
    slot = next(i for i, (index, mon) in enumerate(alive) if species[index] == turn['foe'])
    true_index, out = alive.pop(slot)
    out = dict(out)
    out['boosts'] = {k: v for k, v in turn['foe_boosts'].items() if v}
    scenario['trainer']['party'] = [out] + [mon for _, mon in alive]
    state = engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
    foe_hp = max(1, round(state['foe']['max_hp'] * turn['foe_pct'] / 100))
    if foe_hp != state['foe']['hp']:
        out['hp'] = foe_hp
        state = engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
    state['foe']['party_index'] = true_index
    return scenario, state


def name_of(state, action):
    if action.get('kind') == 'item':
        return action['item']
    if action.get('kind') == 'move':
        return state['own']['moves'][action['slot']]['id']
    return str(action)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log')
    parser.add_argument('--since', default='2026-11-16 17:47:49')
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    cases, pret = league_cases()
    ai = NPCTrainerAI(pret)
    policy = autostory.POLICIES['autostory_new']
    plan = autostory.plan(BAG_NOW, True)
    turns = collect(args.log, args.since)
    goals_by_fight, rows = {}, []
    with Engine() as engine:
        for i, turn in enumerate(turns):
            scenario, state = build_state(engine, cases, pret, turn)
            goals = goals_by_fight.setdefault(turn['fight'], {'_fight': turn['fight'], '_plan': plan, '_start_bag': dict(BAG_NOW)})
            items = [it.lower().replace('_', '') for it in scenario['trainer']['items']]
            action = policy(state, ai, scenario['trainer']['ai'], items, goals)
            danger = autostory.danger(state, ai, scenario['trainer']['ai'], goals)
            sim = name_of(state, action)
            # The foe's move this turn and the HP it took, read against the next policy line.
            row = {k: turn[k] for k in ('time', 'fight', 'level', 'hp', 'status', 'foe', 'foe_pct', 'boosts', 'foe_boosts', 'reason')}
            row.update(program=turn['program'], sim=sim, agree=sim == turn['program'], sim_D=danger['normal_max'],
                       own_speed=state['own']['speed'], foe_speed=state['foe']['speed'])
            nxt = turns[i + 1] if i + 1 < len(turns) else None
            moves = [m for m in state['foe']['moves'] if m.get('damage')]
            used = [foe_move(t, turn['foe'], state['foe']['moves']) for t in turn['texts'] if t.startswith('foe' + turn['foe'][:3]) and 'used' in t]
            used = [u for u in used if u]
            row['foe_used'] = used
            trainer_item = [t for t in turn['texts'] if 'usedfull' in t or 'usedhyper' in t or 'usedsuper' in t]
            row['trainer_item'] = trainer_item
            if nxt and nxt['fight'] == turn['fight'] and used:
                start = turn['max_hp'] if turn['program'] == 'fullrestore' else turn['hp']
                hail = sum('peltedbyhail' in t for t in turn['texts']) * (turn['max_hp'] // 16)
                taken = start - nxt['hp'] - hail
                move = next((m for m in moves if m['id'] == used[-1]), None)
                crit = any('criticalhit' in t for t in turn['texts'])
                if move:
                    rng = [min(move['damage']), max(move['damage'])]
                    crng = [min(move['critical']), max(move['critical'])] if move.get('critical') else None
                    inside = (crng if crit and crng else rng)
                    row['damage'] = {'move': used[-1], 'taken': taken, 'hail': hail, 'crit': crit, 'sim_range': rng,
                                     'sim_crit_range': crng, 'in_range': inside[0] <= taken <= inside[1] if taken > 0 else None}
                else:
                    row['damage'] = {'move': used[-1], 'taken': taken, 'hail': hail, 'crit': crit, 'sim_range': None}
            # Our hit on the foe: its HP % drop to the next line (no trainer item, no berry, same foe).
            ours = next((m for m in state['own']['moves'] if m['id'] == turn['program']), None)
            berry = any('berry' in t for t in turn['texts'])
            if ours and ours.get('damage') and nxt and nxt['fight'] == turn['fight'] and nxt['foe'] == turn['foe'] \
                    and not trainer_item and not berry and not any('missed' in t or 'protected' in t for t in turn['texts']):
                top = state['foe']['max_hp']
                row['our_hit'] = {'move': turn['program'], 'pct': turn['foe_pct'] - nxt['foe_pct'],
                                  'sim_pct': [round(100 * min(ours['damage']) / top), round(100 * max(ours['damage']) / top)]}
            rows.append(row)
    open(args.out, 'w').write(json.dumps(rows, indent=1) + '\n')
    for r in rows:
        dmg = r.get('damage')
        d = ''
        if dmg:
            d = '{} took {}{} sim {}{}'.format(dmg['move'], dmg['taken'], ' (crit)' if dmg['crit'] else '', dmg['sim_crit_range'] if dmg['crit'] else dmg['sim_range'],
                                              '' if dmg.get('in_range') is not False else ' OUT')
        hit = r.get('our_hit')
        if hit:
            d += ' | our {} {}% sim {}%{}'.format(hit['move'], hit['pct'], hit['sim_pct'],
                                                 '' if hit['sim_pct'][0] - 2 <= hit['pct'] <= hit['sim_pct'][1] + 2 else ' OUT')
        print('{} {:8} {:10} {:3}% HP {:3}{:4} D{:3} prog {:12} sim {:12} {} {}'.format(
            r['time'][11:19], r['fight'], r['foe'], r['foe_pct'], r['hp'], r['status'] or '', r['sim_D'],
            str(r['program']), r['sim'], '' if r['agree'] else 'DIFF', d))
    n = len(rows)
    print('agree {}/{}'.format(sum(r['agree'] for r in rows), n))


if __name__ == '__main__':
    main()

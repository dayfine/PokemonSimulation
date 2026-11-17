"""PokeGuy's League setup as one chain (Lorelei -> Champion, HP/PP/bag carried over).

  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_pokeguy --chains 500 --seed f1 --out-dir /tmp/pokeguy-chain

Scenarios (same engine, seeds and table as frlg_league_plan eval):
  isolated  each fight alone from PokeGuy's recorded entry (HP, PP, bag), C2 with his strategies.json goals
  A         his Blastoise (recorded Lv51-55 stats), his bag at Lorelei, his between-fight healing, C2 + his goals
  B         his Blastoise and bag, our planned policy (plan.json) and its between-fight top-ups
  C         our Blastoise at Lv54 and our bag (BAG_NOW), C2 + his goals, his between-fight healing, no held item
  E         C with Black Glasses held
  P         our Blastoise at Lv54, our bag, planned policy (plan.json), no held item
  D         P with Black Glasses held (the #111 planned-54 table: those runs inherited his glasses)

A and B keep his Black Glasses. Gen 3 Black Glasses: 1.1x Sp. Atk for Dark moves (Showdown's gen3 mod;
@smogon/calc previews the same).
"""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.cli.frlg_league_chain import BAG_NOW, league_cases
from pokesim.cli.frlg_league_plan import render, table
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.league import planned
from pokesim.games.frlg.league.chain import FIGHTS, MOVE_PP, fight_scenario, play, run_chain, POLICIES


def pokeguy_bag():
    """His bag at Lorelei (state-history.json via the case): Full Restore 13 bought at the Plateau."""
    cases, _ = league_cases()
    return dict(cases['lorelei']['bag'])


def isolated(engine, cases, pret, ai, seed, bench):
    """Each fight from his recorded entry state; a record shaped like run_chain's."""
    record = {'seed': seed, 'fights': [], 'outcome': 'win'}
    for fight in FIGHTS:
        player = cases[fight]['player']
        pp = {m['name'].upper(): m['pp'] for m in player['moves']}
        carry = {'hp': player['hp'], 'status': player.get('status', ''),
                 'pp': {k: pp.get(k, 0) for k in MOVE_PP}, 'bag': dict(cases[fight]['bag'])}
        scenario = fight_scenario(cases[fight], pret, carry, None, None, bench=bench)
        state, _ = play(engine, scenario, ai, POLICIES['c2'], '{}:{}'.format(seed, fight), fight=fight)
        won = state['winner'] == 'Player'
        record['fights'].append({'fight': fight, 'won': won, 'used': dict(state['items_used']), 'between_used': {}})
        if not won and record['outcome'] == 'win':
            record['outcome'] = 'loss@' + fight
    return record


SCENARIOS = {
    'A': dict(policy='c2', bag='pokeguy', levels=None, between='pokeguy', held=None),
    'B': dict(policy='planned', bag='pokeguy', levels=None, between=None, held=None),
    'C': dict(policy='c2', bag='ours', levels=54, between='pokeguy', held=''),
    'E': dict(policy='c2', bag='ours', levels=54, between='pokeguy', held='BLACK_GLASSES'),
    'P': dict(policy='planned', bag='ours', levels=54, between=None, held=''),
    'D': dict(policy='planned', bag='ours', levels=54, between=None, held='BLACK_GLASSES'),
}


# One change at a time from P (our bag, Lv54, planned policy, no held item): (label, bag additions, level, held).
SWEEP = [
    ('base (P)', {}, 54, ''),
    ('Full Restore +1', {'fullrestore': 1}, 54, ''),
    ('Full Restore +3', {'fullrestore': 3}, 54, ''),
    ('Full Restore +5', {'fullrestore': 5}, 54, ''),
    ('Full Heal +1', {'fullheal': 1}, 54, ''),
    ('Full Heal +3', {'fullheal': 3}, 54, ''),
    ('Full Heal +5', {'fullheal': 5}, 54, ''),
    ('Awakening +1', {'awakening': 1}, 54, ''),
    ('Awakening +3', {'awakening': 3}, 54, ''),
    ('Black Glasses', {}, 54, 'BLACK_GLASSES'),
    ('Elixir +1', {'elixir': 1}, 54, ''),
    ('Max Elixir +1', {'maxelixir': 1}, 54, ''),
    ('X Accuracy +2', {'xaccuracy': 2}, 54, ''),
    ('Guard Spec +1', {'guardspec': 1}, 54, ''),
    ('Super Potion +4', {'superpotion': 4}, 54, ''),
    ('Hyper Potion +4 (costs money; reference)', {'hyperpotion': 4}, 54, ''),
    ('Lv55 (reference)', {}, 55, ''),
    ('Lv57 (reference)', {}, 57, ''),
]


def sweep_scenario(label):
    _, add, level, held = next(row for row in SWEEP if row[0] == label)
    bag = dict(BAG_NOW)
    for k, v in add.items():
        bag[k] = bag.get(k, 0) + v
    return dict(policy='planned', bag=bag, levels=level, between=None, held=held)


def _worker(job):
    name, seeds, bench = job
    cases, pret = league_cases()
    ai = NPCTrainerAI(pret)
    out = []
    with Engine() as engine:
        for seed in seeds:
            if name == 'isolated':
                out.append(isolated(engine, cases, pret, ai, seed, bench))
                continue
            s = SCENARIOS.get(name) or sweep_scenario(name)
            bag = dict(cases['lorelei']['bag']) if s['bag'] == 'pokeguy' else dict(BAG_NOW if s['bag'] == 'ours' else s['bag'])
            levels = {f: s['levels'] for f in FIGHTS} if s['levels'] else None
            plan = planned.load_plan() if s['policy'] == 'planned' else None
            record = run_chain(engine, cases, pret, ai, s['policy'], bag, levels, seed, plan=plan, bench=bench,
                               between=s['between'], held_item=s['held'])
            for fight in record['fights']:
                fight.pop('decisions')
            out.append(record)
    return out


def isolated_table(records):
    """Per fight won/total: every fight is played in every record."""
    t = table([{'fights': r['fights'], 'outcome': 'win'} for r in records])
    t['wins'] = sum(all(f['won'] for f in r['fights']) for r in records)
    t['items_per_win'] = None
    return t


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', default='isolated,A,B,C')
    parser.add_argument('--chains', type=int, default=500)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--seed', default='f1')
    parser.add_argument('--no-bench', action='store_true', help='Blastoise alone: Roar/Whirlwind fail')
    parser.add_argument('--sweep', action='store_true', help='the one-change item sweep from P (sweep.txt)')
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    seeds = ['{}:{}'.format(args.seed, i) for i in range(args.chains)]
    if args.sweep:
        return sweep(args, seeds)
    suffix = '-solo' if args.no_bench else ''
    with ProcessPoolExecutor(args.workers) as pool:
        for name in args.scenarios.split(','):
            jobs = [(name, seeds[i::args.workers], not args.no_bench) for i in range(args.workers)]
            records = [r for part in pool.map(_worker, jobs) for r in part]
            t = isolated_table(records) if name == 'isolated' else table(records)
            title = name + suffix
            if name == 'isolated':
                title += ' (each fight from his recorded entry; "League" = all five won in one seed)'
            text = render(title, t)
            print(text, flush=True)
            (args.out_dir / (name + suffix + '.txt')).write_text(text + '\n')
            (args.out_dir / (name + suffix + '.json')).write_text(json.dumps(t) + '\n')


def sweep(args, seeds):
    rows = []
    with ProcessPoolExecutor(args.workers) as pool:
        for label, *_ in SWEEP:
            jobs = [(label, seeds[i::args.workers], not args.no_bench) for i in range(args.workers)]
            t = table([r for part in pool.map(_worker, jobs) for r in part])
            champ = t['per_fight']['champion']
            rows.append((label, t['wins'], t['chains'], champ['won'], champ['reached']))
            print('{:44s} League {:4d}/{}  champion {}/{}'.format(*rows[-1]), flush=True)
    base = rows[0][1]
    lines = ['Item sweep from P: our bag (BAG_NOW), Lv54, planned policy (plan.json), no held item; '
             '{} chains, seed {}; one change per row, sorted by gain.'.format(args.chains, args.seed),
             '  {:44s} {:>14s} {:>7s} {:>17s}'.format('change', 'League', 'gain', 'champion won/reached')]
    for label, wins, n, cw, cr in sorted(rows, key=lambda r: -r[1]):
        lines.append('  {:44s} {:4d}/{} {:5.1%} {:+6.1f}pp {:6d}/{:<4d} {:4.0%}'.format(
            label, wins, n, wins / n, 100 * (wins - base) / n, cw, cr, cw / max(1, cr)))
    text = '\n'.join(lines)
    print(text)
    (args.out_dir / 'sweep.txt').write_text(text + '\n')


if __name__ == '__main__':
    main()

"""Simulate the FRLG League (Elite Four + Champion) as one continuous chain.

PYTHONPATH=src python3 -m pokesim.cli.frlg_league_chain --policy replica --chains 200 --out /tmp/chain.json
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.games.frlg.battle.engine import Engine, REPO
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.battle.run import trainer_cases, configure_strategies
from pokesim.games.frlg.league.chain import run_chain, FIGHTS

DATA = REPO / 'data/runs/pokeguy-leafgreen-15934'
BAG_NOW = {'fullrestore': 8, 'xspecial': 15, 'xspeed': 5, 'xaccuracy': 3, 'guardspec': 2, 'maxelixir': 1,
           'elixir': 1, 'superpotion': 6, 'fullheal': 2, 'parlyzheal': 2, 'antidote': 1}
LEVELS_NOW = {'lorelei': 54, 'bruno': 54, 'agatha': 55, 'lance': 55, 'champion': 56}


def league_cases():
    read = lambda name: json.loads((DATA / (name + '.json')).read_text())
    pret = read('battle-reference')
    cases = trainer_cases(read('events'), read('reference'), read('moves'), read('state-history'), pret)['cases']
    cases = configure_strategies(cases, read('strategies'))
    return {c['id']: c for c in cases if c['id'] in FIGHTS}, pret


def worker(job):
    policy, bag, levels, seeds = job
    cases, pret = league_cases()
    ai = NPCTrainerAI(pret)
    out = []
    with Engine() as engine:
        for seed in seeds:
            record = run_chain(engine, cases, pret, ai, policy, bag, levels, seed)
            for fight in record['fights']:
                fight.pop('decisions')
            out.append(record)
    return out


def summarize(records):
    n = len(records)
    wins = sum(r['outcome'] == 'win' for r in records)
    losses = Counter(r['outcome'] for r in records if r['outcome'] != 'win')
    per = {}
    for fight in FIGHTS:
        rows = [f for r in records for f in r['fights'] if f['fight'] == fight]
        if not rows:
            continue
        spend = Counter()
        for f in rows:
            spend.update(f['used']); spend.update({k: v for k, v in f['between_used'].items()})
        per[fight] = {'reached': len(rows), 'won': sum(f['won'] for f in rows),
            'mean_attacks': sum(f['attacks'] for f in rows) / len(rows),
            'mean_spend': {k: round(v / len(rows), 2) for k, v in sorted(spend.items())},
            'entry_hp_mean': sum(f['entry']['hp'] / f['entry']['max_hp'] for f in rows) / len(rows)}
    # Whole-chain item spend among wins: percentiles.
    totals = {}
    for r in records:
        if r['outcome'] != 'win':
            continue
        spend = Counter()
        for f in r['fights']:
            spend.update(f['used']); spend.update(f['between_used'])
        for k in set(spend) | set(totals):
            totals.setdefault(k, []).append(spend.get(k, 0))
    pct = lambda xs, q: sorted(xs)[min(len(xs) - 1, int(q * len(xs)))]
    spend_pct = {k: {'p50': pct(v, .5), 'p90': pct(v, .9), 'p95': pct(v, .95), 'max': max(v)} for k, v in sorted(totals.items())}
    return {'chains': n, 'wins': wins, 'win_rate': wins / n, 'losses': dict(losses), 'per_fight': per,
            'win_spend_percentiles': spend_pct}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', default='replica', choices=['video', 'c2', 'c2_budget', 'replica_budget', 'replica', 'replica_full', 'replica_margin', 'current_c', 'autostory_old', 'autostory_new'])
    parser.add_argument('--chains', type=int, default=200)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--bag', type=json.loads, default=None, help='JSON bag; default the restocked bag of 2026-11-16 (X Special 15, Super Potion 6)')
    parser.add_argument('--add', type=json.loads, default={}, help='JSON items added to the bag')
    parser.add_argument('--seed', default='s1')
    parser.add_argument('--level', type=int, default=None, help='one level for every fight (sweep)')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    bag = dict(args.bag or BAG_NOW)
    for k, v in args.add.items():
        bag[k] = bag.get(k, 0) + v
    seeds = ['{}:{}'.format(args.seed, i) for i in range(args.chains)]
    levels = {f: args.level for f in FIGHTS} if args.level else LEVELS_NOW
    jobs = [(args.policy, bag, levels, seeds[i::args.workers]) for i in range(args.workers)]
    with ProcessPoolExecutor(args.workers) as pool:
        records = [r for part in pool.map(worker, jobs) for r in part]
    summary = summarize(records)
    summary.update(policy=args.policy, bag=bag, levels=levels, seed=args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({'summary': summary, 'records': records}) + '\n')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    main()

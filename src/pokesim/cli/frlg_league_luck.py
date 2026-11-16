"""Luck check: PokeGuy's recorded League spends against the replica policy's distribution.

Each fight starts at PokeGuy's recorded entry (his stats, HP, PP, bag). For each
quantity, report the share of simulated wins that spent no more than he did.

PYTHONPATH=src python3 -m pokesim.cli.frlg_league_luck --trials 200 --out /tmp/luck.json
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.games.frlg.battle.benchmark import scenario_for
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.cli.frlg_league_chain import league_cases
from pokesim.games.frlg.league.chain import play
from pokesim.games.frlg.league.replica import POLICIES

# Bag and PP deltas between consecutive recorded League entries (docs/battles/pokeguy-conditions.md).
RECORDED = {
    'lorelei': {'fullrestore': 1, 'xspecial': 4, 'xspeed': 0, 'attacks': 7, 'surf': 1},
    'bruno': {'fullrestore': 0, 'xspecial': 2, 'xspeed': 1, 'attacks': 5, 'surf': 5},
    'agatha': {'fullrestore': 1, 'xspecial': 1, 'xspeed': 1, 'attacks': 5, 'surf': 5},
}


def worker(job):
    fight, policy, seeds = job
    cases, pret = league_cases()
    ai = NPCTrainerAI(pret)
    rows = []
    with Engine() as engine:
        scenario = scenario_for(cases[fight], pret)
        for seed in seeds:
            state, decisions = play(engine, scenario, ai, POLICIES[policy], seed)
            used = Counter(state['items_used'])
            moves = Counter(d['move'] for d in decisions if d['move'])
            rows.append({'won': state['winner'] == 'Player', 'fullrestore': used['fullrestore'],
                'xspecial': used['xspecial'], 'xspeed': used['xspeed'], 'heals': sum(used[k] for k in ('fullrestore', 'superpotion', 'potion')),
                'attacks': sum(moves.values()), 'surf': moves['surf'], 'turns': len(decisions)})
    return fight, rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--trials', type=int, default=200)
    parser.add_argument('--policy', default='replica')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    jobs = [(f, args.policy, ['luck:{}:{}'.format(f, i) for i in range(args.trials)]) for f in RECORDED]
    with ProcessPoolExecutor(len(jobs)) as pool:
        results = dict(pool.map(worker, jobs))
    report = {}
    for fight, rows in results.items():
        wins = [r for r in rows if r['won']]
        entry = {'trials': len(rows), 'win_rate': len(wins) / len(rows)}
        for key, recorded in RECORDED[fight].items():
            values = sorted(r[key] for r in wins)
            entry[key] = {'recorded': recorded, 'mean': sum(values) / len(values),
                'p50': values[len(values) // 2], 'p90': values[int(.9 * len(values))],
                'share_at_or_below_recorded': sum(v <= recorded for v in values) / len(values)}
        report[fight] = entry
    args.out.write_text(json.dumps(report, indent=1) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()

"""Search, evaluate and write the FRLG League plan (policy 'planned').

  # evaluate a plan file or the base spec against a policy as run
  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_plan eval --policy planned --level 54 --chains 500
  # coordinate search over the spec's candidate choices, then write the best plan
  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_plan search --chains 120 --write plan.json

Ranking: League win rate, then fewer items spent among won chains.
"""

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.cli.frlg_league_chain import BAG_NOW, league_cases
from pokesim.formats.contract_format import json_text
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.league import planned, specs
from pokesim.games.frlg.league.chain import FIGHTS, run_chain

ITEMS = ('fullrestore', 'superpotion', 'xspecial', 'xspeed', 'xaccuracy', 'guardspec', 'elixir', 'maxelixir',
         'fullheal', 'parlyzheal', 'antidote')


def _worker(job):
    policy, bag, level, seeds, plan, bench, keep, fights = job
    cases, pret = league_cases()
    ai = NPCTrainerAI(pret)
    out = []
    with Engine() as engine:
        for seed in seeds:
            record = run_chain(engine, cases, pret, ai, policy, bag, {f: level for f in FIGHTS}, seed, plan=plan,
                               bench=bench, fights=fights)
            if not keep:
                for fight in record['fights']:
                    fight.pop('decisions')
            out.append(record)
    return out


def evaluate(policy, plan, level=54, chains=200, workers=8, seed='p1', bag=None, bench=True, keep=False, pool=None,
             fights=FIGHTS):
    seeds = ['{}:{}'.format(seed, i) for i in range(chains)]
    jobs = [(policy, dict(bag or BAG_NOW), level, seeds[i::workers], plan, bench, keep, fights) for i in range(workers)]
    if pool is None:
        with ProcessPoolExecutor(workers) as p:
            return [r for part in p.map(_worker, jobs) for r in part]
    return [r for part in pool.map(_worker, jobs) for r in part]


def table(records):
    """Per fight: won/reached and mean spend (in battle + before it); League wins."""
    rows = {}
    for fight in FIGHTS:
        fights = [f for r in records for f in r['fights'] if f['fight'] == fight]
        spend = Counter()
        for f in fights:
            spend.update(f['used'])
            spend.update(f['between_used'])
        rows[fight] = {'reached': len(fights), 'won': sum(f['won'] for f in fights),
                       'spend': {k: round(v / max(1, len(fights)), 2) for k, v in spend.items()}}
    wins = sum(r['outcome'] == 'win' for r in records)
    won_items = [sum(sum(f['used'].values()) + sum(f['between_used'].values()) for f in r['fights'])
                 for r in records if r['outcome'] == 'win']
    return {'chains': len(records), 'wins': wins, 'per_fight': rows,
            'items_per_win': round(sum(won_items) / len(won_items), 2) if won_items else None,
            'losses': dict(Counter(r['outcome'] for r in records if r['outcome'] != 'win'))}


def render(name, t):
    lines = ['{}: League {}/{} ({:.1%}); items per won chain {}'.format(
        name, t['wins'], t['chains'], t['wins'] / t['chains'], t['items_per_win'])]
    lines.append('  {:9s} {:>12s}   {}'.format('fight', 'won/reached', 'mean spend (in battle + before)'))
    for fight, row in t['per_fight'].items():
        if not row['reached']:
            continue
        spend = ' '.join('{} {:.2f}'.format(k, row['spend'][k]) for k in ITEMS if row['spend'].get(k))
        lines.append('  {:9s} {:>5d}/{:<5d} {:4.0%}  {}'.format(fight, row['won'], row['reached'],
                                                             row['won'] / row['reached'], spend))
    return '\n'.join(lines)


def score(t):
    return (t['wins'], -(t['items_per_win'] or 99))


# Candidate choices per fight for the coordinate search: (label, path, value).
def candidates():
    g = specs.g
    return {
        'lorelei': [
            ('dewgong X Sp +2', ('lorelei', 'foes', 0, 'setup'), [g('xspecial', 2, 'bite')]),
            ('dewgong X Sp +4', ('lorelei', 'foes', 0, 'setup'), [g('xspecial', 4, 'bite')]),
            ('dewgong surf first', ('lorelei', 'foes', 0, 'moves'), ['surf', 'bite']),
            ('fr_spend 3', ('lorelei', 'fr_spend'), 3),
        ],
        'bruno': [
            ('onix X Sp +2 only', ('bruno', 'foes', 0, 'setup'), [g('xspecial', 2, 'surf')]),
            ('onix X Sp +2, X Spe +2', ('bruno', 'foes', 0, 'setup'), [g('xspecial', 2, 'surf'), g('xspeed', 2, 'surf')]),
            ('onix no setup', ('bruno', 'foes', 0, 'setup'), []),
            ('entry 100%', ('bruno', 'between', 'hp'), 1.0),
        ],
        'agatha': [
            ('gengar +X Acc 1', ('agatha', 'foes', 0, 'setup'),
             [g('xspecial', 2, 'bite'), g('xspeed', 1, 'bite'), g('xaccuracy', 1, 'bite')]),
            ('gengar X Sp +3', ('agatha', 'foes', 0, 'setup'), [g('xspecial', 3, 'bite'), g('xspeed', 1, 'bite')]),
            ('entry 100%', ('agatha', 'between', 'hp'), 1.0),
            ('entry 80%', ('agatha', 'between', 'hp'), 0.8),
        ],
        'lance': [
            ('gyarados X Sp +3, X Acc +2', ('lance', 'foes', 0, 'setup'),
             [g('xspecial', 3, 'blizzard'), g('xaccuracy', 2, 'blizzard')]),
            ('gyarados X Sp +2 only', ('lance', 'foes', 0, 'setup'), [g('xspecial', 2, 'blizzard')]),
            ('gyarados blizzard', ('lance', 'foes', 0, 'moves'), ['blizzard', 'bite']),
            ('fr_spend 3', ('lance', 'fr_spend'), 3),
        ],
        'champion': [
            ('pidgeot X Sp +3', ('champion', 'foes', 0, 'setup'),
             [g('guardspec'), g('xspecial', 3, 'blizzard'), g('xaccuracy', 2, 'blizzard'), g('xspeed', 1, 'blizzard')]),
            ('pidgeot no X Speed', ('champion', 'foes', 0, 'setup'),
             [g('guardspec'), g('xspecial', 2, 'blizzard'), g('xaccuracy', 2, 'blizzard')]),
            ('pidgeot X Acc +1', ('champion', 'foes', 0, 'setup'),
             [g('guardspec'), g('xspecial', 2, 'blizzard'), g('xaccuracy', 1, 'blizzard'), g('xspeed', 1, 'blizzard')]),
            ('gyarados blizzard', ('champion', 'foes', 3, 'moves'), ['blizzard', 'bite']),
            ('fr_spend 3', ('champion', 'fr_spend'), 3),
        ],
    }


def search(spec, level, chains, workers, rounds, log):
    bag = dict(BAG_NOW)
    best_spec = spec
    with ProcessPoolExecutor(workers) as pool:
        best = table(evaluate('planned', planned.build(spec, bag), level, chains, workers, pool=pool))
        log('base: ' + render('base', best).splitlines()[0])
        for r in range(rounds):
            improved = False
            for fight, options in candidates().items():
                for label, path, value in options:
                    trial = specs.variant(best_spec, path, value)
                    t = table(evaluate('planned', planned.build(trial, bag), level, chains, workers, pool=pool))
                    log('round {} {} / {}: {} wins, items/win {}'.format(r, fight, label, t['wins'], t['items_per_win']))
                    if score(t) > score(best):
                        best, best_spec, improved = t, trial, True
                        log('  -> kept')
            if not improved:
                break
    return best_spec, best


# Champion alone, from full HP and PP, with what a won chain typically has left.
CHAMPION_BAG = {'fullrestore': 3, 'xspecial': 4, 'xspeed': 2, 'xaccuracy': 2, 'guardspec': 1, 'superpotion': 2,
                'maxelixir': 0, 'elixir': 0}


def champion(plan, args):
    g = specs.g
    setups = {
        'no setup': [],
        'X Sp +2': [g('xspecial', 2, 'blizzard')],
        'X Sp +2, X Acc +2': [g('xspecial', 2, 'blizzard'), g('xaccuracy', 2, 'blizzard')],
        'GS, X Sp +2, X Acc +2, X Spe +1': [g('guardspec'), g('xspecial', 2, 'blizzard'), g('xaccuracy', 2, 'blizzard'),
                                            g('xspeed', 1, 'blizzard')],
        'GS, X Sp +3, X Acc +2, X Spe +1': [g('guardspec'), g('xspecial', 3, 'blizzard'), g('xaccuracy', 2, 'blizzard'),
                                            g('xspeed', 1, 'blizzard')],
        'GS, X Sp +4, X Acc +2, X Spe +1': [g('guardspec'), g('xspecial', 4, 'blizzard'), g('xaccuracy', 2, 'blizzard'),
                                            g('xspeed', 1, 'blizzard')],
    }
    for name, setup in setups.items():
        for bench in (True, False):
            trial = json.loads(json.dumps(plan))
            trial['fights']['champion']['foes'][0]['setup'] = setup
            trial['fights']['champion']['reserve'] = {'pp': {}, 'items': {}}
            records = evaluate('planned', trial, args.level, args.chains, args.workers, args.seed, bag=CHAMPION_BAG,
                               bench=bench, fights=('champion',))
            t = table(records)
            losses = Counter(r['fights'][-1]['foe_at_end'] for r in records if r['outcome'] != 'win')
            print('{:34s} whirlwind {:5s} won {:4d}/{:<4d} {:4.0%}  lost at {}'.format(
                name, 'works' if bench else 'fails', t['wins'], t['chains'], t['wins'] / t['chains'], dict(losses)),
                flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['eval', 'search', 'champion'])
    parser.add_argument('--policy', default='planned')
    parser.add_argument('--plan', type=Path, default=None, help='plan JSON (default: built from the base spec)')
    parser.add_argument('--level', type=int, default=54)
    parser.add_argument('--chains', type=int, default=200)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--seed', default='p1')
    parser.add_argument('--rounds', type=int, default=2)
    parser.add_argument('--no-bench', action='store_true', help='Blastoise alone: Roar/Whirlwind fail')
    parser.add_argument('--write', type=Path, default=None, help='search: write the best plan JSON here')
    parser.add_argument('--out', type=Path, default=None, help='eval: write the summary table JSON here')
    args = parser.parse_args(argv)
    if args.mode == 'search':
        spec, best = search(specs.BASE, args.level, args.chains, args.workers, args.rounds, lambda s: print(s, flush=True))
        print(render('best', best))
        if args.write:
            args.write.write_text(json_text(planned.build(spec, BAG_NOW)))
        return
    plan = planned.load_plan(args.plan) if args.plan else planned.build(specs.BASE, BAG_NOW)
    if args.mode == 'champion':
        champion(plan, args)
        return
    records = evaluate(args.policy, plan, args.level, args.chains, args.workers, args.seed, bench=not args.no_bench)
    t = table(records)
    print(render('{} Lv{}'.format(args.policy, args.level), t))
    if args.out:
        args.out.write_text(json.dumps(t) + '\n')


if __name__ == '__main__':
    main()

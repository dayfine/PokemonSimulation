"""Per-fight tables from frlg_league_chain outputs: won / reached, item spend mean / p75 / p90.

PYTHONPATH=src python3 -m pokesim.cli.frlg_league_spend a.json [b.json ...] [--propose p75 --bag '{...}']

Spend counts the fight's in-battle items plus the top-ups before it, over the chains that
reached the fight. --propose splits the bag by each fight's spend quantile (largest remainder
when the quantiles overshoot the bag) and prints the --budget JSON for frlg_league_chain.
"""

import argparse
import json
from collections import Counter

from pokesim.games.frlg.league.autostory import FIGHTS

ITEMS = ('fullrestore', 'xspecial', 'xspeed', 'xaccuracy', 'guardspec', 'elixir', 'fullheal', 'superpotion', 'parlyzheal', 'antidote')
SHORT = {'fullrestore': 'FR', 'xspecial': 'XSp', 'xspeed': 'XSpe', 'xaccuracy': 'XAcc', 'guardspec': 'GS', 'elixir': 'Elix',
         'fullheal': 'FH', 'superpotion': 'SupP', 'parlyzheal': 'PrzH', 'antidote': 'Anti'}


def quantile(xs, q):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(q * len(xs)))] if xs else 0


def spends(records):
    out = {}
    for r in records:
        for f in r['fights']:
            c = Counter(f['used'])
            c.update(f['between_used'])
            c['elixir'] += c.pop('maxelixir', 0)
            out.setdefault(f['fight'], []).append((f['won'], c))
    return out


def table(path):
    data = json.loads(open(path).read())
    records, summary = data['records'], data['summary']
    rows = spends(records)
    lines = ['{}: chains {}, League won {} ({:.1%})'.format(path.rsplit('/', 1)[-1], summary['chains'], summary['wins'], summary['win_rate'])]
    lines.append('{:9} {:>15}  '.format('fight', 'won/reached') + '  '.join('{:>13}'.format(SHORT[i] + ' m/p75/p90') for i in ITEMS))
    for fight in FIGHTS:
        if fight not in rows:
            continue
        rs = rows[fight]
        won = sum(w for w, _ in rs)
        cells = []
        for item in ITEMS:
            xs = [c.get(item, 0) for _, c in rs]
            cells.append('{:>13}'.format('{:.2f}/{}/{}'.format(sum(xs) / len(xs), quantile(xs, .75), quantile(xs, .9))))
        lines.append('{:9} {:>8}/{:<4} {:3.0%}  '.format(fight, won, len(rs), won / len(rs)) + '  '.join(cells))
    return '\n'.join(lines), rows


def propose(rows, bag, q):
    """Each fight's q-quantile spend among chains that won it, scaled down to the bag by largest remainder."""
    budget = {f: {} for f in FIGHTS}
    for item in ('fullrestore', 'xspecial', 'xspeed', 'xaccuracy', 'guardspec', 'elixir', 'fullheal'):
        want = [quantile([c.get(item, 0) for w, c in rows.get(f, []) if w] or [0], q) for f in FIGHTS]
        total = bag.get(item, 0) + (bag.get('maxelixir', 0) if item == 'elixir' else 0)
        if sum(want) > total:
            exact = [total * w / sum(want) for w in want]
            got = [int(x) for x in exact]
            for i in sorted(range(len(FIGHTS)), key=lambda i: -(exact[i] - got[i]))[:total - sum(got)]:
                got[i] += 1
        else:
            got = list(want)
            got[-1] += total - sum(want)  # what's left goes to the Champion
        for f, n in zip(FIGHTS, got):
            budget[f][item] = n
    return budget


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+')
    parser.add_argument('--propose', type=float, default=None, help='quantile, e.g. 0.75')
    parser.add_argument('--bag', type=json.loads, default=None)
    args = parser.parse_args(argv)
    for path in args.paths:
        text, rows = table(path)
        print(text + '\n')
    if args.propose is not None:
        print(json.dumps(propose(rows, args.bag, args.propose)))


if __name__ == '__main__':
    main()

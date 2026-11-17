"""plan.json's per-fight contracts as one table: a row per boundary (Enter Lorelei, Exit Lorelei, ... Enter Champion).

  PYTHONPATH=src python3 -m pokesim.games.frlg.league.contracts [--markdown] [--fill boundaries.json]

Each fight's `contract`:
  topup  the most the top-up before the fight may spend (it comes out of the fight's own caps)
  entry  after that top-up: HP as the sim's entries had it (median / 10th percentile), PP floors, the least of
         each item in the bag
  exit   what an accepted win leaves at least: items (hard, the bag minus every cap so far), the Blizzard reserve;
         HP median / 10th percentile and Surf median / lowest over the sim's accepted wins (informative)
  pass   expected_pass (a win within the caps, so the exit holds, per try), min_pass (passes of 10 that 95% of
         10-try batches reach) and reset_budget (tries for ~95% to pass at least once)
With no PP item before an E4 fight, its Surf entry is the lowest the last fight left in the sim.
The bridge: exit of X minus Y's top-up = entry of Y. test_plan_contracts.py checks the arithmetic.
"""

import argparse
import json
import math
from pathlib import Path

from pokesim.games.frlg.league import planned

ITEMS = ('fullrestore', 'xspecial', 'xspeed', 'xaccuracy', 'guardspec', 'superpotion', 'elixir', 'maxelixir')
HEADERS = ('Boundary', 'HP', 'Surf/Blizzard PP', 'Full Restore', 'X Special', 'X Speed', 'X Accuracy',
           'Guard Spec', 'Super Potion', 'Elixir', 'Max Elixir')


def contract(plan, fight):
    return plan['fights'][fight]['contract']


def _n(v):
    return str(int(round(v)))


def rows(plan):
    """[boundary, HP, PP, item counts...] per boundary, as strings. HP and Surf the sim measured say so."""
    out = []
    for fight in planned.FIGHTS:
        c = contract(plan, fight)
        e, x = c['entry'], c['exit']
        sim = e['hp_sim']
        if sim['p10'] == sim['median']:
            hp = '{} (always)'.format(_n(sim['median']))
        else:
            hp = 'median {}, 1 in 10 below {}'.format(_n(sim['median']), _n(sim['p10']))
        # Surf is hard only where the top-up has a PP item; elsewhere it is the lowest the sim saw.
        hard = any(c['topup'].get(k) for k in ('elixir', 'maxelixir')) or fight == planned.FIGHTS[0]
        surf = '>= {}'.format(e['pp']['surf']) if hard else '{} (sim low)'.format(e['pp']['surf'])
        out.append(['Enter ' + fight.capitalize(), hp, '{} / >= {}'.format(surf, e['pp']['blizzard'])] +
                   [str(e['items'][k]) for k in ITEMS])
        out.append(['Exit ' + fight.capitalize(),
                    'median {}, 1 in 10 below {}'.format(_n(x['hp']['median']), _n(x['hp']['p10'])),
                    '{} (low {}) / {}'.format(_n(x['surf']['median']), x['surf']['min'],
                                              '>= {}'.format(x['pp']['blizzard']) if 'blizzard' in x['pp'] else 'any')] +
                   [str(x['items'][k]) for k in ITEMS])
    return out


NAMES = {'fullrestore': 'Full Restore', 'xspecial': 'X Special', 'xspeed': 'X Speed', 'xaccuracy': 'X Accuracy',
         'guardspec': 'Guard Spec', 'superpotion': 'Super Potion', 'elixir': 'Elixir', 'maxelixir': 'Max Elixir'}
PLURAL = ('fullrestore', 'superpotion', 'elixir', 'maxelixir')
LOW_PASS = 0.40  # below this, or min_pass <= 2 of 10, a 10-try check can't tell bad luck from a broken plan
LOW_MIN_PASS = 2


def weak(c):
    return c['pass']['expected_pass'] < LOW_PASS or c['pass']['min_pass']['k'] <= LOW_MIN_PASS


def fight_lines(plan):
    """Per fight: the goal, the pass rule (the caps, the heal before it included) and the pass figures."""
    out = []
    for fight in planned.FIGHTS:
        row = plan['fights'][fight]
        c, p = row['contract'], row['contract']['pass']
        caps = ', '.join('{} {}{}'.format(n, NAMES[k], 's' if n > 1 and k in PLURAL else '')
                         for k, n in row['caps'].items() if n)
        out.append('{}. Goal: {}. Pass: a win using at most {} (the heal before it included){}. '
                   'Pass rate {:.0%} per try (about {:.2f} tries); 95% of 10-try checks see at least {} pass(es); '
                   'reset budget {} tries.{}'.format(
                       fight.capitalize(), row['goal'], caps,
                       '; a Roar or Whirlwind that lands is a reset' if row.get('reset', {}).get('roar') else '',
                       p['expected_pass'], 1 / p['expected_pass'], p['min_pass']['k'], p['reset_budget'],
                       '  LOW: a 10-try check cannot tell bad luck from a broken plan.' if weak(c) else ''))
    return out


def render(plan, markdown=False):
    table = rows(plan)
    if markdown:
        lines = ['| ' + ' | '.join(HEADERS) + ' |', '|' + '---|' * len(HEADERS)]
        lines += ['| ' + ' | '.join(r) + ' |' for r in table]
        return '\n'.join(lines)
    widths = [max(len(h), *(len(r[i]) for r in table)) for i, h in enumerate(HEADERS)]
    fmt = '  '.join('{:<%d}' % w for w in widths)
    return '\n'.join([fmt.format(*HEADERS)] + [fmt.format(*r) for r in table])


def binom_cdf(k, n, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))


def pass_figures(p, n=10):
    """expected_pass p (a win that meets the exit contract, per try); min_pass: the most passes k of n tries that
    95% of n-try batches reach, P(K <= k-1) < 5%; reset_budget: ceil(3 / p) tries, ~95% to pass at least once."""
    k = max(k for k in range(n + 1) if k == 0 or binom_cdf(k - 1, n, p) < 0.05)
    return {'expected_pass': round(p, 3), 'min_pass': {'k': k, 'of': n, 'rate': k / n},
            'reset_budget': math.ceil(3 / p) if p else None}


def _num(v):
    return int(v) if float(v).is_integer() else v


def build(plan, bag, sim):
    """{fight: contract} from the caps, the bag and the chain's boundary figures (frlg_league_final's
    boundaries.json). Items: exit = the bag less every cap so far; entry = the last exit less the most the top-up
    may take (one heal: up to two Super Potions or a Full Restore, as the fight's caps allow; the Elixir before
    the Champion). Surf before an E4 fight (no PP item) is the lowest the last fight left in the sim."""
    out, left = {}, {k: bag[k] for k in ITEMS}
    prev = dict(left)
    for i, fight in enumerate(planned.FIGHTS):
        row, s = plan['fights'][fight], sim[fight]
        caps = row['caps']
        topup = {}
        if i:
            topup = {k: min(n, caps.get(k, 0)) for k, n in (('superpotion', 2), ('fullrestore', 1)) if caps.get(k)}
            if row['between'].get('pp'):  # one PP item: the first the caps allow
                topup.update(next(({k: 1} for k in planned.PP_ITEMS if caps.get(k)), {}))
        for k in ITEMS:
            left[k] -= caps.get(k, 0)
        floor = row['between'].get('pp', {})
        if i == 0:
            pp = {'surf': s['entry']['pp_min']['surf'], 'blizzard': s['entry']['pp_min']['blizzard']}
        elif topup.get('elixir') or topup.get('maxelixir'):
            pp = dict(floor)
        else:
            pp = {'surf': prev_surf_min, 'blizzard': prev_pp_blizzard}
        hp = s['entry']['hp']
        out[fight] = {
            'topup': topup,
            'entry': {'hp_sim': {'median': _num(hp['median']), 'p10': _num(hp['p10'])}, 'pp': pp,
                      'items': {k: prev[k] - topup.get(k, 0) for k in ITEMS}},
            'exit': {'hp': {'median': _num(s['exit']['hp']['median']), 'p10': _num(s['exit']['hp']['p10'])},
                     'surf': {'median': _num(s['exit']['pp_median']['surf']), 'min': s['exit']['pp_min']['surf']},
                     'pp': dict(row['reserve']['pp']), 'items': dict(left)},
            'pass': pass_figures(s['accepted'] / s['runs']),
        }
        prev_pp_blizzard = row['reserve']['pp'].get('blizzard', 0)
        prev_surf_min = s['exit']['pp_min']['surf']
        prev = dict(left)
    return out


def dump(contract):
    """One contract as plan.json's hand layout (indented for a fight row)."""
    d = json.dumps
    e, x = contract['entry'], contract['exit']
    return ('"contract": {\n'
            '        "topup": %s,\n'
            '        "entry": {"hp_sim": %s, "pp": %s,\n'
            '                  "items": %s},\n'
            '        "exit": {"hp": %s, "surf": %s, "pp": %s,\n'
            '                 "items": %s},\n'
            '        "pass": %s\n'
            '      }') % (d(contract['topup']), d(e['hp_sim']), d(e['pp']), d(e['items']), d(x['hp']), d(x['surf']),
                          d(x['pp']), d(x['items']), d(contract['pass']))


def fill(path, contracts):
    """Rewrite each fight's `contract` block in plan.json, keeping the rest of the file's layout."""
    text = Path(path).read_text()
    for fight, c in contracts.items():
        start = text.index('"contract": {', text.index('"{}": {{'.format(fight)))
        depth, end = 0, start + len('"contract": ')
        for j in range(end, len(text)):
            depth += {'{': 1, '}': -1}.get(text[j], 0)
            if depth == 0:
                end = j + 1
                break
        text = text[:start] + dump(c) + text[end:]
    assert {f: v['contract'] for f, v in json.loads(text)['fights'].items()} == contracts, 'contract dump drifted'
    Path(path).write_text(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--markdown', action='store_true')
    parser.add_argument('--fill', type=Path, help='boundaries.json from frlg_league_final: rewrite the contracts')
    args = parser.parse_args(argv)
    if args.fill:
        from pokesim.cli.frlg_league_chain import BAG_NOW
        fill(planned.DEFAULT_PLAN, build(planned.load_plan(), BAG_NOW, json.loads(args.fill.read_text())))
    print(render(planned.load_plan(), args.markdown))


if __name__ == '__main__':
    main()

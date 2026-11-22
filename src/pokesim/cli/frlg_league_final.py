"""FRLG League final plan: plan.json's per-fight item caps as accept rules, the Super Potion split, the chain forward.

  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_final --runs 1000 --out-dir ~/BDSPLab/notes/e4-sim/retry

Same setup as frlg_league_retry: our Blastoise Lv54 (console stats), BAG_NOW, policy 'planned', plan.json.

Accept rule per fight: a win (a Roar / Whirlwind that lands is a reset, a failed try) that spends no more of any item
than the fight's `caps` (between-fight top-ups before it included). The fight's entry bag holds exactly what the plan
leaves it (reserve + cap of every capped item), so the policy can spend each cap and no more (only the KO-risk heal
breaches a reserve, and such a win is rejected). Uncapped items (Elixir, cures) carry over from the previous fight.
Bruno's early reset (`reset.after_foe`): when Onix #1 falls, reset if our Speed is still lowered and all its X Speed
cap is spent; such a try costs RESET_COST of a full fight.

Steps:
  search  Super Potion caps 0..4 per fight (Lance with and without Dragonite's heal block), each from the previous
          fight's accepted wins under the current split; the split (sum <= the bag's 6) with the fewest expected
          tries; twice, the second time from the first split's pools.
  chain   the chosen split forward: each fight's entries sampled from the previous fight's accepted wins.

--chain-only skips the search and runs plan.json as it is; both write the boundary figures (entry / exit HP, PP,
item minimums, top-up spend over accepted wins) to boundaries.json for plan.json's `contract` rows.
"""

import argparse
import copy
import itertools
import json
import statistics
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.cli import frlg_league_retry as R
from pokesim.cli.frlg_league_chain import BAG_NOW
from pokesim.games.frlg.league import planned
from pokesim.games.frlg.league.contracts import pass_figures

FIGHTS = planned.FIGHTS
RESET_COST = 0.2  # soft reset + walking in + Onix #1's turns, as a share of a full fight
SP_CAPS = (0, 1, 2, 3, 4)
LEDGER = ('fullrestore', 'superpotion', 'xspecial', 'xspeed', 'xaccuracy', 'guardspec', 'elixir', 'maxelixir')
NAMES = {'fullrestore': 'Full Restore', 'superpotion': 'Super Potion', 'xspecial': 'X Special', 'xspeed': 'X Speed',
         'xaccuracy': 'X Accuracy', 'guardspec': 'Guard Spec', 'elixir': 'Elixir', 'maxelixir': 'Max Elixir'}


def with_split(base, sp, dragonite_heal=True):
    """plan with Super Potion caps sp (per fight) and reserves recomputed from all caps."""
    plan = copy.deepcopy(base)
    for fight, n in zip(FIGHTS, sp):
        plan['fights'][fight]['caps']['superpotion'] = n
    if not dragonite_heal:
        plan['fights']['lance']['foes'][4].pop('heal', None)
    for fight, items in planned.reserves_from_caps(plan).items():
        plan['fights'][fight]['reserve']['items'] = items
    return plan


def entry(carry, plan, fight):
    """The carry with every capped item at what the plan leaves this fight (reserve + cap)."""
    carry = copy.deepcopy(carry)
    row = plan['fights'][fight]
    for name, cap in row['caps'].items():
        carry['bag'][name] = row['reserve']['items'].get(name, 0) + cap
    return carry


def entries(seeds, plan, fight, pool):
    rows = R.entries_for(seeds, fight, pool, 0)
    return [(seed, entry(carry, plan, fight)) for seed, carry in rows]


def early_reset(r, plan, fight):
    rule = plan['fights'][fight].get('reset', {}).get('after_foe')
    if not rule:
        return False
    first = plan['fights'][fight]['foes'][rule['index']]['species'].upper()
    used = {}
    for foe, _, spe, action, _, _ in r['trace']:
        if foe != first:
            return spe < rule['speed_below'] and all(used.get(k, 0) >= v for k, v in rule['items_used'].items())
        used[action] = used.get(action, 0) + 1
    return False


def accept(r, plan, fight):
    caps = plan['fights'][fight]['caps']
    return (r['won'] and not early_reset(r, plan, fight)
            and all(r['used'].get(name, 0) <= cap for name, cap in caps.items()))


def stats(rs, plan, fight):
    acc = [r for r in rs if accept(r, plan, fight)]
    early = sum(early_reset(r, plan, fight) for r in rs)
    n = len(rs)
    return {'n': n, 'acc': acc, 'p': len(acc) / n, 'tries': n / len(acc) if acc else float('inf'),
            'cost': (n - early * (1 - RESET_COST)) / len(acc) if acc else float('inf'),
            'early': early / n, 'roar': sum(r['reset'] for r in rs) / n, 'win': sum(r['won'] for r in rs) / n,
            'lost': sum(r['lost'] for r in rs) / n}


def chain(ex, workers, plan, seeds, cells_for=None):
    """Forward chain under plan: {fight: (results, stats)}; cells_for(fight, pool) adds side cells per fight."""
    pool = [R.full_carry(BAG_NOW)]
    out, side = {}, {}
    for i, fight in enumerate(FIGHTS):
        cells = {'main': (fight, plan, None, entries(seeds, plan, fight, pool), i > 0)}
        if cells_for:
            cells.update(cells_for(fight, pool))
        res = R.run_cells(ex, cells, workers)
        rs = res.pop('main')
        out[fight] = (rs, stats(rs, plan, fight))
        side[fight] = res
        pool = [r['end'] for r in out[fight][1]['acc']]
        if not pool:
            break
    return out, side


def search(ex, workers, base, seeds, sp, log):
    """Per-fight tries for each Super Potion cap from the current split's pools; the best split with sum <= 6."""
    def cells_for(fight, pool):
        cells = {}
        for n in SP_CAPS:
            for heal in ((True, False) if fight == 'lance' else (True,)):
                trial = list(sp)
                trial[FIGHTS.index(fight)] = n
                plan = with_split(base, trial, heal)
                cells[(n, heal)] = (fight, plan, None, entries(seeds, plan, fight, pool), fight != 'lorelei')
        return cells

    _, side = chain(ex, workers, with_split(base, sp), seeds, cells_for)
    curve = {}
    log.append('  Super Potion cap search from split {} ({} runs per cell): expected tries per fight'.format(
        list(sp), len(seeds)))
    log.append('    {:22s} '.format('fight') + ' '.join('{:>7s}'.format('SP<={}'.format(n)) for n in SP_CAPS))
    for fight in FIGHTS:
        for heal in ((True, False) if fight == 'lance' else (True,)):
            row = []
            for n in SP_CAPS:
                trial = list(sp)
                trial[FIGHTS.index(fight)] = n
                s = stats(side[fight][(n, heal)], with_split(base, trial, heal), fight)
                curve[(fight, n, heal)] = s['tries']
                row.append(s['tries'])
            label = fight + ('' if fight != 'lance' else (' (Dragonite heal)' if heal else ' (no Dragonite heal)'))
            log.append('    {:22s} '.format(label) + ' '.join('{:>7.2f}'.format(t) for t in row))
    best = None
    for split in itertools.product(SP_CAPS, repeat=len(FIGHTS)):
        if sum(split) > BAG_NOW['superpotion']:
            continue
        for heal in (True, False):
            total = sum(curve[(f, n, heal if f == 'lance' else True)] for f, n in zip(FIGHTS, split))
            # Ties within 0.02 tries: fewer Super Potions, then no Dragonite block.
            key = (round(total / 0.02), sum(split), heal)
            if best is None or key < best[0]:
                best = (key, split, heal, total)
    log.append('    -> split {} Dragonite heal {}: {:.2f} tries (sum of per-fight curves)'.format(
        list(best[1]), 'on' if best[2] else 'off', best[3]))
    return list(best[1]), best[2]


def q(xs, f):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(f * len(xs)))] if xs else 0


def render(plan, out, runs):
    lines = ['FRLG League final plan (plan.json), chain forward, {} runs per fight; entries = the previous fight\'s '
             'accepted wins.'.format(runs),
             'Accept = win (Roar / Whirlwind = reset) AND every item used <= cap (top-ups before the fight count).', '',
             'TABLE 1. Goal and result per fight']
    for fight in FIGHTS:
        row = plan['fights'][fight]
        rs, s = out[fight]
        caps = row['caps']
        rule = ', '.join('{} <= {}'.format(NAMES[k], v) for k, v in caps.items() if v or k in ('fullrestore', 'superpotion'))
        acc = s['acc']
        sp = [r['used'].get('superpotion', 0) for r in acc]
        fr = [r['used'].get('fullrestore', 0) for r in acc]
        dist = '/'.join(str(sum(1 for x in fr if x == k)) for k in range(caps['fullrestore'] + 1))
        lines.append('  {}: {}'.format(fight.upper(), row['goal']))
        lines.append('    accept rule: win, {}{}'.format(rule, '; early reset: after Onix #1, Speed < 0 with 3 X Speed spent'
                                                          if row.get('reset', {}).get('after_foe') else ''))
        lines.append('    accepted per try {:5.1%} (win {:5.1%}, Roar reset {:5.1%}, early reset {:5.1%}, loss {:5.1%})'
                     '  expected tries {:.2f}{}'.format(
                         s['p'], s['win'], s['roar'], s['early'], s['lost'], s['tries'],
                         '  (fight-time {:.2f}: an early reset costs {})'.format(s['cost'], RESET_COST)
                         if s['early'] else ''))
        lines.append('    Super Potions used median {} / 90th {}  (mean {:.2f});  Full Restores used mean {:.2f}, '
                     'count 0..{}: {}'.format(statistics.median(sp) if sp else 0, q(sp, 0.9),
                                               sum(sp) / max(1, len(sp)), sum(fr) / max(1, len(fr)),
                                               caps['fullrestore'], dist))
    total = sum(out[f][1]['tries'] for f in FIGHTS)
    lines.append('  Total expected tries: {:.2f}  (fight-time {:.2f})'.format(total, sum(out[f][1]['cost'] for f in FIGHTS)))
    lines.append('')
    lines.append('  {:9s} {:>8s} {:>7s} {:>8s} {:>9s} {:>9s}  {}'.format(
        'fight', 'acc/try', 'tries', 'SP med', 'SP 90th', 'FR mean', 'accept rule (caps)'))
    for fight in FIGHTS:
        rs, s = out[fight]
        caps = plan['fights'][fight]['caps']
        sp = [r['used'].get('superpotion', 0) for r in s['acc']]
        fr = [r['used'].get('fullrestore', 0) for r in s['acc']]
        short = {'fullrestore': 'FR', 'superpotion': 'SP', 'xspecial': 'XSp', 'xspeed': 'XSpe', 'xaccuracy': 'XAcc',
                 'guardspec': 'GSpec', 'maxelixir': 'MaxElix', 'elixir': 'Elix'}
        lines.append('  {:9s} {:>8.1%} {:>7.2f} {:>8} {:>9} {:>9.2f}  {}'.format(
            fight, s['p'], s['tries'], statistics.median(sp) if sp else 0, q(sp, 0.9), sum(fr) / max(1, len(fr)),
            ' '.join('{}<={}'.format(short[k], v) for k, v in caps.items() if v or k in ('fullrestore', 'superpotion'))))
    lines.append('')
    lines.append('TABLE 2. Item ledger: cap per fight (mean used in accepted wins)')
    lines.append('  {:13s} '.format('item') + ' '.join('{:>12s}'.format(f) for f in FIGHTS) +
                 '  {:>5s} {:>4s} {:>6s} {:>10s}'.format('caps', 'bag', 'spare', 'mean used'))
    for name in LEDGER:
        cells, cap_sum, used_sum = [], 0, 0.0
        for fight in FIGHTS:
            cap = plan['fights'][fight]['caps'].get(name)
            acc = out[fight][1]['acc']
            used = sum(r['used'].get(name, 0) for r in acc) / max(1, len(acc))
            used_sum += used
            cap_sum += cap or 0
            cells.append('{:>12s}'.format('{} ({:.2f})'.format('-' if cap is None else cap, used)))
        bag = BAG_NOW.get(name, 0)
        lines.append('  {:13s} '.format(NAMES[name]) + ' '.join(cells) +
                     '  {:>5d} {:>4d} {:>6d} {:>10.2f}'.format(cap_sum, bag, bag - cap_sum, used_sum))
    lines.append('  (- = uncapped: carried from the previous fight; Elixir is spent by whichever top-up needs it first.)')
    lines.append('')
    lines.append('TABLE 3. PP at each fight\'s entry (after top-ups), accepted wins; PP items already spent before it')
    lines.append('  {:9s} {:>9s} {:>9s} {:>12s} {:>12s} {:>14s} {:>14s}'.format(
        'fight', 'Surf min', 'Surf med', 'Blizzard min', 'Blizz < 4', 'Elixir gone', 'MaxElixir gone'))
    for fight in FIGHTS:
        acc = out[fight][1]['acc']
        surf = [r['pre']['entry']['pp']['SURF'] for r in acc]
        bliz = [r['pre']['entry']['pp']['BLIZZARD'] for r in acc]
        # The bag at entry is after the top-up; spent = BAG_NOW minus what is left plus what this fight used.
        el = [BAG_NOW['elixir'] - r['end']['bag'].get('elixir', 0) - r['used'].get('elixir', 0) for r in acc]
        mel = [BAG_NOW['maxelixir'] - r['end']['bag'].get('maxelixir', 0) - r['used'].get('maxelixir', 0) for r in acc]
        n = max(1, len(acc))
        lines.append('  {:9s} {:>9d} {:>9} {:>12d} {:>12.1%} {:>14.1%} {:>14.1%}'.format(
            fight, min(surf, default=0), statistics.median(surf) if surf else 0, min(bliz, default=0),
            sum(b < 4 for b in bliz) / n, sum(e > 0 for e in el) / n, sum(e > 0 for e in mel) / n))
    return '\n'.join(lines)


def boundaries(out):
    """Per fight, over its accepted wins: HP / PP after the top-up (entry) and at the end (exit), the least of each
    item left at the end, the most the top-up spent; the figures plan.json's `contract` rows quote."""
    rows = {}
    for fight in FIGHTS:
        rs, s = out[fight]
        acc = s['acc']
        hp_in = [r['pre']['entry']['hp'] for r in acc]
        hp_out = [r['end']['hp'] for r in acc]
        rows[fight] = {
            'tries': round(s['tries'], 2), 'accepted': len(acc), 'runs': s['n'],
            'entry': {'hp': {'min': min(hp_in), 'p10': q(hp_in, 0.1), 'median': statistics.median(hp_in)},
                      'pp_min': {m.lower(): min(r['pre']['entry']['pp'][m] for r in acc) for m in ('SURF', 'BLIZZARD')}},
            'exit': {'hp': {'min': min(hp_out), 'p10': q(hp_out, 0.1), 'median': statistics.median(hp_out)},
                     'pp_min': {m.lower(): min(r['end']['pp'][m] for r in acc) for m in ('SURF', 'BLIZZARD')},
                     'pp_median': {m.lower(): statistics.median(r['end']['pp'][m] for r in acc)
                                   for m in ('SURF', 'BLIZZARD')},
                     'items_min': {k: min(r['end']['bag'].get(k, 0) for r in acc) for k in LEDGER}},
            'topup_max': {k: max(r['top'].get(k, 0) for r in acc) for k in LEDGER},
        }
        rows[fight].update(pass_figures(s['p']))
    return rows


def with_caps(base, fr, sp):
    """plan with Full Restore caps fr and Super Potion caps sp (per fight), reserves recomputed."""
    plan = copy.deepcopy(base)
    for fight, f, s in zip(FIGHTS, fr, sp):
        plan['fights'][fight]['caps'].update(fullrestore=f, superpotion=s)
    for fight, items in planned.reserves_from_caps(plan).items():
        plan['fights'][fight]['reserve']['items'] = items
    return plan


def fr_range(fight):
    return range(1, 5) if fight == 'champion' else range(0, 4)


def search_caps(ex, workers, base, seeds, log):
    """Per-fight tries for each (Full Restore, Super Potion) cap pair, from the current caps' accepted pools;
    the split using at most the bag's Full Restores and Super Potions with the fewest expected tries."""
    fr0 = [base['fights'][f]['caps']['fullrestore'] for f in FIGHTS]
    sp0 = [base['fights'][f]['caps']['superpotion'] for f in FIGHTS]

    def cells_for(fight, pool):
        cells = {}
        i = FIGHTS.index(fight)
        for f in fr_range(fight):
            for s in range(4):
                fr, sp = list(fr0), list(sp0)
                fr[i], sp[i] = f, s
                plan = with_caps(base, fr, sp)
                cells[(f, s)] = (fight, plan, None, entries(seeds, plan, fight, pool), i > 0)
        return cells

    _, side = chain(ex, workers, base, seeds, cells_for)
    curve = {}
    log.append('Full Restore x Super Potion cap search from FR {} SP {} ({} runs per cell): expected tries'.format(
        fr0, sp0, len(seeds)))
    for fight in FIGHTS:
        i = FIGHTS.index(fight)
        for f in fr_range(fight):
            row = []
            for s in range(4):
                fr, sp = list(fr0), list(sp0)
                fr[i], sp[i] = f, s
                curve[(fight, f, s)] = stats(side[fight][(f, s)], with_caps(base, fr, sp), fight)['tries']
                row.append(curve[(fight, f, s)])
            log.append('    {:9s} FR<={}  '.format(fight, f) + ' '.join('SP<={} {:6.2f}'.format(s, x)
                                                                    for s, x in enumerate(row)))
    best = None
    choices = [[(f, s) for f in fr_range(x) for s in range(4)] for x in FIGHTS]
    for combo in itertools.product(*choices):
        if sum(c[0] for c in combo) > BAG_NOW['fullrestore'] or sum(c[1] for c in combo) > BAG_NOW['superpotion']:
            continue
        total = sum(curve[(x, f, s)] for x, (f, s) in zip(FIGHTS, combo))
        if total == float('inf'):
            continue
        key = (round(total / 0.02), sum(c[1] for c in combo))
        if best is None or key < best[0]:
            best = (key, combo, total)
    fr, sp = [c[0] for c in best[1]], [c[1] for c in best[1]]
    log.append('    -> FR {} SP {}: {:.2f} tries (sum of per-fight curves)'.format(fr, sp, best[2]))
    return fr, sp


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runs', type=int, default=1000)
    parser.add_argument('--search-runs', type=int, default=600)
    parser.add_argument('--workers', type=int, default=9)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--write-plan', action='store_true', help='write the chosen split into plan.json')
    parser.add_argument('--chain-only', action='store_true', help='skip the search: run plan.json as it is')
    parser.add_argument('--plan', type=Path, default=planned.DEFAULT_PLAN, help='plan file (default plan.json)')
    parser.add_argument('--cap-search', action='store_true',
                        help='search Full Restore x Super Potion caps, then run the chain with the best split')
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    base = planned.load_plan(args.plan)
    sp = [base['fights'][f]['caps']['superpotion'] for f in FIGHTS]
    heal = True
    log = ['Super Potion split search (objective: total expected tries; Super Potions <= {})'.format(
        BAG_NOW['superpotion'])]
    with ProcessPoolExecutor(args.workers, initializer=R._init) as ex:
        search_seeds = ['s:{}'.format(i) for i in range(args.search_runs)]
        if args.cap_search:
            fr, sp = search_caps(ex, args.workers, base, search_seeds, log)
            print('\n'.join(log), flush=True)
            base = with_caps(base, fr, sp)
        for _ in range(0 if args.chain_only or args.cap_search else 2):
            sp, heal = search(ex, args.workers, base, search_seeds, sp, log)
            print('\n'.join(log), flush=True)
        plan = base if args.chain_only or args.cap_search else with_split(base, sp, heal)
        seeds = ['f:{}'.format(i) for i in range(args.runs)]
        out, _ = chain(ex, args.workers, plan, seeds)
    text = render(plan, out, args.runs) + '\n\n' + '\n'.join(log)
    print(text)
    (args.out_dir / ('caps-chain.txt' if args.cap_search else 'chain.txt' if args.chain_only else 'final.txt')).write_text(text + '\n')
    (args.out_dir / 'boundaries.json').write_text(json.dumps(boundaries(out), indent=1) + '\n')
    if args.write_plan:
        planned.DEFAULT_PLAN.write_text(json_dump(plan))


def json_dump(plan):
    """plan.json in its hand layout: only caps, reserves and the Dragonite block change, so patch those lines."""
    text = planned.DEFAULT_PLAN.read_text()
    import re
    for fight in FIGHTS:
        row = plan['fights'][fight]
        for key, value in (('caps', row['caps']), ('items', row['reserve']['items'])):
            pattern = r'("{}":\s*)\{{[^{{}}]*\}}'.format(key)
            start = text.index('"{}": {{'.format(fight))
            if key == 'items':  # the reserve's, not the contract's
                start = text.index('"reserve": {', start)
            m = re.compile(pattern).search(text, start)
            text = text[:m.start()] + m.group(1) + json.dumps(value).replace('{"', '{"').replace(', ', ', ') + text[m.end():]
    if 'heal' not in plan['fights']['lance']['foes'][4]:
        text = text.replace('"setup": [], "heal": {"below": 80, "heal_at_least": 50}}\n      ],\n      "between": {"hp": 1.0, "pp": {"surf": 4',
                            '"setup": []}\n      ],\n      "between": {"hp": 1.0, "pp": {"surf": 4')
    assert json.loads(text) == plan, 'plan.json patch drifted'
    return text


if __name__ == '__main__':
    main()

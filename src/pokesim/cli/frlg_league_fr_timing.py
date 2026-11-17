"""FRLG League: does Lorelei need a heal, and when are Full Restores / Super Potions spent along the chain.

  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_fr_timing --runs 2000 --out-dir ~/BDSPLab/notes/e4-sim/retry

Same setup and accept rule as frlg_league_final (plan.json caps, entries = the previous fight's accepted wins).

Steps:
  lorelei  four Lorelei variants from full HP/PP, bag as the plan: (i) the plan; (ii) no Lapras heal block;
           (iii) never heal (no heal block, no KO-risk heal, no status heal: medicine is held out of the bag);
           (iv) heal only when the foe's lowest roll KOs (no heal block). Win %, Full Restores used, accepted %
           at Full Restore caps 0 and 1, and the losses by foe and cause.
  chains   the chain forward with the plan, with the best Lorelei variant (its Full Restore cap moved to the
           Champion when it wins with none), and with Lance's top-up at 80% HP (Super Potions re-split). Per
           chain: every Full Restore and Super Potion of the accepted wins, as a top-up before a fight or an
           in-fight use by foe and policy row.
"""

import argparse
import copy
import itertools
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.cli import frlg_league_final as F
from pokesim.cli import frlg_league_retry as R
from pokesim.cli.frlg_league_chain import BAG_NOW
from pokesim.games.frlg.battle.items import CURES, HEALS
from pokesim.games.frlg.league import planned

FIGHTS = planned.FIGHTS
MEDICINE = sorted(set(HEALS) | set(CURES.values()) | {'fullheal'})
TIMED = (('fullrestore', 'Full Restore'), ('superpotion', 'Super Potion'))
# Lorelei variants: (label, drop Lapras's heal block, risk mode, hold medicine out of the bag).
LORELEI = {
    'plan': ('(i) plan: Lapras heal block + KO-risk heal', False, None, False),
    'no_block': ('(ii) no Lapras heal block', True, None, False),
    'never': ('(iii) never heal', True, 'never', True),
    'sure': ('(iv) heal only on a sure-KO next hit', True, 'sure', False),
}


def _job(job):
    """frlg_league_retry._job, with medicine held out of the bag for the fight and returned after it."""
    fight, plan, risk, entries, top_up, strip = job
    out = []
    for seed, carry in entries:
        held = {}
        if strip:
            carry = copy.deepcopy(carry)
            held = {k: carry['bag'].pop(k) for k in MEDICINE if carry['bag'].get(k)}
        r = R.run_fight(fight, carry, plan, seed, risk, top_up)
        for k, v in held.items():
            r['end']['bag'][k] = r['end']['bag'].get(k, 0) + v
        out.append(r)
    return out


def run_cells(ex, cells, workers):
    """cells: {key: (fight, plan, risk, entries, top_up, strip)} -> {key: [results]}."""
    jobs, keys = [], []
    for key, cell in cells.items():
        for i in range(workers):
            jobs.append(cell[:3] + (cell[3][i::workers],) + cell[4:])
            keys.append(key)
    out = {key: [] for key in cells}
    for key, part in zip(keys, ex.map(_job, jobs)):
        out[key].extend(part)
    return out


def lorelei_plan(base, variant):
    plan = copy.deepcopy(base)
    if LORELEI[variant][1]:
        plan['fights']['lorelei']['foes'][4].pop('heal', None)
    return plan


def with_caps(base, fr=None, sp=None, lance_hp=None):
    """base with Full Restore caps fr / Super Potion caps sp (per fight), Lance's top-up HP; reserves recomputed."""
    plan = copy.deepcopy(base)
    for key, caps in (('fullrestore', fr), ('superpotion', sp)):
        for fight, n in zip(FIGHTS, caps or ()):
            plan['fights'][fight]['caps'][key] = n
    if lance_hp is not None:
        plan['fights']['lance']['between']['hp'] = lance_hp
    for fight, items in planned.reserves_from_caps(plan).items():
        plan['fights'][fight]['reserve']['items'] = items
    return plan


def chain(ex, workers, plan, seeds, lorelei='plan', side_for=None):
    """frlg_league_final.chain with a Lorelei variant: {fight: (results, stats)}, {fight: side cells}."""
    pool = [R.full_carry(BAG_NOW)]
    out, side = {}, {}
    _, _, risk, strip = LORELEI[lorelei]
    for i, fight in enumerate(FIGHTS):
        cell = (fight, plan, risk if i == 0 else None, F.entries(seeds, plan, fight, pool), i > 0,
                strip and i == 0)
        cells = {'main': cell}
        if side_for:
            cells.update(side_for(fight, pool))
        res = run_cells(ex, cells, workers)
        rs = res.pop('main')
        out[fight] = (rs, F.stats(rs, plan, fight))
        side[fight] = res
        pool = [r['end'] for r in out[fight][1]['acc']]
        if not pool:
            break
    return out, side


def loss_cause(r):
    """'<foe>: <cause>' for a loss: Hail chip, confusion self-hit, Perish Song, else the foe's move (+ crit)."""
    c = r['cause']
    foe = str(c['foe']).lower()
    text = ' '.join(r.get('ko_log', ())).lower()
    if '[from] hail' in text:
        why = 'Hail chip'
    elif '[from] confusion' in text:
        why = 'confusion self-hit'
    elif 'perish' in text:
        why = 'Perish Song'
    elif c['move']:
        why = c['move'] + (' crit' if c['crit'] else '')
    else:
        why = 'other'
    return '{}: {}'.format(foe, why)


def render_lorelei(rows, runs):
    lines = ['TABLE A. Lorelei variants, {} runs each from full HP/PP, bag as the plan '
             '(accept also needs Super Potion <= 0, X Special <= 6)'.format(runs),
             '  {:44s} {:>6s} {:>6s} {:>16s} {:>8s} {:>8s} {:>7s}'.format(
                 'variant', 'win', 'loss', 'FR used 0/1/2+', 'acc FR0', 'acc FR1', 'FR mean')]
    for key, rs in rows.items():
        wins = [r for r in rs if r['won']]
        fr = Counter(min(2, r['used'].get('fullrestore', 0)) for r in wins)
        acc = {k: sum(r['won'] and r['used'].get('fullrestore', 0) <= k and r['used'].get('superpotion', 0) == 0
                      and r['used'].get('xspecial', 0) <= 6 for r in rs) / len(rs) for k in (0, 1)}
        lines.append('  {:44s} {:>6.1%} {:>6.1%} {:>16s} {:>8.1%} {:>8.1%} {:>7.2f}'.format(
            LORELEI[key][0], len(wins) / len(rs), sum(r['lost'] for r in rs) / len(rs),
            '/'.join('{:.0%}'.format(fr[k] / max(1, len(wins))) for k in range(3)), acc[0], acc[1],
            sum(r['used'].get('fullrestore', 0) for r in wins) / max(1, len(wins))))
    lines.append('')
    lines.append('  Losses by foe and cause (the killing blow; share of all runs)')
    for key, rs in rows.items():
        losses = Counter(loss_cause(r) for r in rs if r['lost'])
        lines.append('    {:44s} '.format(LORELEI[key][0]) +
                     (', '.join('{} {:.1%}'.format(k, v / len(rs)) for k, v in losses.most_common(8)) or 'none'))
    lines.append('')
    lines.append('  In-fight medicine in wins (uses per win, by foe / policy row)')
    for key, rs in rows.items():
        wins = [r for r in rs if r['won']]
        uses = Counter('{} {} {}'.format(item, foe.lower(), why) for r in wins for foe, why, item, _ in r['items']
                       if item in MEDICINE)
        lines.append('    {:44s} '.format(LORELEI[key][0]) +
                     (', '.join('{} {:.2f}'.format(k, v / max(1, len(wins))) for k, v in uses.most_common(6))
                      or 'none'))
    return '\n'.join(lines)


def render_timing(title, plan, out):
    lines = [title]
    total = sum(out[f][1]['tries'] for f in FIGHTS)
    lines.append('  per-fight tries: ' + ', '.join('{} {:.2f}'.format(f, out[f][1]['tries']) for f in FIGHTS) +
                 ';  total expected tries {:.2f}'.format(total))
    lines.append('  caps: ' + ', '.join('{} FR<={} SP<={}'.format(
        f, plan['fights'][f]['caps']['fullrestore'], plan['fights'][f]['caps']['superpotion']) for f in FIGHTS) +
        ';  Lance top-up to {:.0%} HP'.format(plan['fights']['lance']['between'].get('hp', 1.0)))
    for name, label in TIMED:
        rows = []
        for fight in FIGHTS:
            acc = out[fight][1]['acc']
            n = max(1, len(acc))
            top = sum(r['top'].get(name, 0) for r in acc) / n
            rows.append((fight, 'top-up before it', top))
            uses = Counter('{} / {}'.format(foe.lower(), why) for r in acc for foe, why, item, _ in r['items']
                           if item == name)
            for k, v in sorted(uses.items(), key=lambda kv: -kv[1]):
                rows.append((fight, 'in-fight ' + k, v / n))
        grand = sum(x for _, _, x in rows)
        lines.append('  {}: mean per accepted win, share of all {}s along an accepted chain ({:.2f} per chain)'.format(
            label, label, grand))
        lines.append('    {:9s} {:44s} {:>8s} {:>7s}'.format('fight', 'when', 'mean', 'share'))
        for fight, when, x in rows:
            if x < 0.005:
                continue
            lines.append('    {:9s} {:44s} {:>8.2f} {:>7.1%}'.format(fight, when, x, x / grand if grand else 0))
    return '\n'.join(lines)


def sp_search(ex, workers, base, seeds, sp, lorelei, log):
    """frlg_league_final.search for one base plan (Dragonite heal as in base): per-fight Super Potion cap curves
    from the current split's pools; the split with the fewest expected tries (sum <= the bag's 6)."""
    def side_for(fight, pool):
        cells = {}
        _, _, risk, strip = LORELEI[lorelei]
        first = fight == 'lorelei'
        for n in F.SP_CAPS:
            trial = list(sp)
            trial[FIGHTS.index(fight)] = n
            plan = with_caps(base, sp=trial)
            cells[n] = (fight, plan, risk if first else None, F.entries(seeds, plan, fight, pool), not first,
                        strip and first)
        return cells

    _, side = chain(ex, workers, with_caps(base, sp=sp), seeds, lorelei, side_for)
    curve = {}
    log.append('  Super Potion cap search from split {} ({} runs per cell): expected tries per fight'.format(
        list(sp), len(seeds)))
    for fight in FIGHTS:
        row = []
        for n in F.SP_CAPS:
            trial = list(sp)
            trial[FIGHTS.index(fight)] = n
            curve[(fight, n)] = F.stats(side[fight][n], with_caps(base, sp=trial), fight)['tries']
            row.append(curve[(fight, n)])
        log.append('    {:10s} '.format(fight) + ' '.join('{:>7.2f}'.format(t) for t in row))
    best = min((s for s in itertools.product(F.SP_CAPS, repeat=len(FIGHTS)) if sum(s) <= BAG_NOW['superpotion']),
               key=lambda s: (round(sum(curve[(f, n)] for f, n in zip(FIGHTS, s)) / 0.02), sum(s)))
    log.append('    -> split {}: {:.2f} tries (sum of per-fight curves)'.format(
        list(best), sum(curve[(f, n)] for f, n in zip(FIGHTS, best))))
    return list(best)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runs', type=int, default=2000)
    parser.add_argument('--search-runs', type=int, default=600)
    parser.add_argument('--workers', type=int, default=9)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--skip-lance80', action='store_true')
    parser.add_argument('--cap1-variant', choices=sorted(LORELEI),
                        help='only chain this Lorelei variant forward at the plan\'s caps; append to fr-timing.txt')
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    base = planned.load_plan()
    seeds = ['t:{}'.format(i) for i in range(args.runs)]
    if args.cap1_variant:
        plan = lorelei_plan(base, args.cap1_variant)
        with ProcessPoolExecutor(args.workers, initializer=R._init) as ex:
            out, _ = chain(ex, args.workers, plan, seeds, args.cap1_variant)
        text = render_timing('TABLE E. Chain forward with Lorelei variant {} at the plan\'s caps (Full Restore <= 1) '
                             '({} runs per fight)'.format(LORELEI[args.cap1_variant][0], args.runs), plan, out)
        print(text)
        path = args.out_dir / 'fr-timing.txt'
        path.write_text(path.read_text() + '\n' + text + '\n')
        return
    texts = []

    def emit(text):
        texts.append(text)
        print(text + '\n', flush=True)
        (args.out_dir / 'fr-timing.txt').write_text('\n\n'.join(texts) + '\n')

    with ProcessPoolExecutor(args.workers, initializer=R._init) as ex:
        cells = {}
        for key, (_, _, risk, strip) in LORELEI.items():
            plan = lorelei_plan(base, key)
            cells[key] = ('lorelei', plan, risk, F.entries(seeds, plan, 'lorelei', [R.full_carry(BAG_NOW)]),
                          False, strip)
        rows = run_cells(ex, cells, args.workers)
        emit(render_lorelei(rows, args.runs))

        # The best variant: most accepted per try at Full Restore cap 0, if it beats the plan at cap 1.
        def acc(key, k):
            return sum(r['won'] and r['used'].get('fullrestore', 0) <= k and r['used'].get('superpotion', 0) == 0
                       for r in rows[key]) / len(rows[key])
        best = max(LORELEI, key=lambda k: acc(k, 0))
        fr = [base['fights'][f]['caps']['fullrestore'] for f in FIGHTS]
        sp = [base['fights'][f]['caps']['superpotion'] for f in FIGHTS]

        out, _ = chain(ex, args.workers, base, seeds)
        plan_total = sum(out[f][1]['tries'] for f in FIGHTS)
        emit(render_timing('TABLE B. Item timing, chain forward with the current plan ({} runs per fight)'.format(
            args.runs), base, out))

        # Lorelei at Full Restore cap 0 with the best variant; its Full Restore moves to the Champion.
        new = lorelei_plan(with_caps(base, fr=[0] + fr[1:4] + [fr[4] + 1]), best)
        out, _ = chain(ex, args.workers, new, seeds, best)
        emit(render_timing('TABLE C. Chain forward with Lorelei variant {} at Full Restore cap 0 ({:.1%} accepted '
                           'per try alone; the plan at cap 1: {:.1%}), its Full Restore moved to the Champion '
                           '({} runs per fight)'.format(LORELEI[best][0], acc(best, 0), acc('plan', 1), args.runs),
                           new, out))
        totals = {'new': sum(out[f][1]['tries'] for f in FIGHTS)}

        if not args.skip_lance80:
            start, best = (new, best) if totals['new'] < plan_total else (base, 'plan')
            lance80 = with_caps(start, lance_hp=0.8)
            log = ['Super Potion re-split with Lance\'s top-up at 80% HP (objective: total expected tries)']
            split = sp_search(ex, args.workers, lance80, ['u:{}'.format(i) for i in range(args.search_runs)], sp,
                              best, log)
            plan = with_caps(lance80, sp=split)
            out, _ = chain(ex, args.workers, plan, seeds, best)
            emit(render_timing('TABLE D. Lance top-up to 80% HP, Super Potions re-split to {} ({} runs per '
                               'fight)'.format(split, args.runs), plan, out) + '\n\n' + '\n'.join(log))


if __name__ == '__main__':
    main()

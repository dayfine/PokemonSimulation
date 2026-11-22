"""FRLG League tuning on top of the retry model: per-foe heal blocks, Bruno's early-reset rule, Lapras kill order.

  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_tuning --runs 500 --out-dir ~/BDSPLab/notes/e4-sim/retry

Same setup as frlg_league_retry: our Blastoise Lv54, BAG_NOW, no held item, policy 'planned', paired seeds.
Entries follow the recommended accept rules: Lorelei X Sp +6 (FR <= 1) -> Bruno plan (FR <= 2) -> Agatha (FR 0)
-> Lance (late_heal). A fight's FR budget k = the plan's reserve set so exactly k are spendable.

Parts:
  heal    per-foe `heal` block thresholds (below HP, heal_at_least) for Bruno's Machamp and Hitmonlee, Lapras and
          Lance's Dragonite: win per try, P(win and FR <= 1 / 2), FR used.
  bruno   Onix #1's opening (its first two moves, crits) and our HP / Speed stage when Onix #1 falls; reset rules
          ("after Onix #1, reset if HP < X or Speed < 0") scored by cost per accepted win with a reset try
          costing RESET_COST of a full fight; X Speed cap 1 vs 3 at Bruno and what 0 X Speed does to Agatha and
          the Champion.
  lapras  Lapras kill order at +6: the plan (Bite, Strength, kill-order row) vs Strength -> Bite -> Bite vs Bite only.
"""

import argparse
import copy
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.cli import frlg_league_retry as R
from pokesim.cli.frlg_league_chain import BAG_NOW
from pokesim.games.frlg.league import planned

RESET_COST = 0.2  # a soft reset at the start of Bruno + walking in + Onix #1's few turns, vs a whole fight
BELOW = (None, 60, 80, 100, 120, 140)
AT_LEAST = (50, 100)
MOVE_ABBR = {'rocktomb': 'RT', 'earthquake': 'EQ', 'irontail': 'IT', 'roar': 'Roar'}


def pct(x):
    return '{:5.1%}'.format(x)


def tries(p):
    return 1 / p if p > 0 else float('inf')


def with_foe(plan, fight, index, **fields):
    plan = copy.deepcopy(plan)
    foe = plan['fights'][fight]['foes'][index]
    for k, v in fields.items():
        if v is None:
            foe.pop(k, None)
        else:
            foe[k] = v
    return plan


def heal_block(below, at_least):
    return None if below is None else {'below': below, 'heal_at_least': at_least}


def acc(rs, k):
    return len(R.accepted(rs, k)) / len(rs)


def fr_mean(rs, k):
    a = R.accepted(rs, k)
    return sum(r['fr'] for r in a) / max(1, len(a))


class Ctx:
    def __init__(self, ex, runs, workers):
        self.ex, self.workers = ex, workers
        self.seeds = ['t1:{}'.format(i) for i in range(runs)]
        self.base = planned.load_plan()

    def run(self, cells):
        return R.run_cells(self.ex, cells, self.workers)

    def plan(self, fight, variant, k, base=None):
        return R.run_plan(base or self.base, fight, variant, k)

    def cell(self, fight, plan, risk, pool, top_up=True, fr=R.FR_POOL):
        return (fight, plan, risk, R.entries_for(self.seeds, fight, pool, fr), top_up)


def pools(ctx):
    """Entry pools along the recommended rules."""
    out = {}
    rs = ctx.run({0: ctx.cell('lorelei', ctx.plan('lorelei', 'more_setup', 1), None, [R.full_carry(BAG_NOW)], False)})[0]
    out['bruno'] = [r['end'] for r in R.accepted(rs, 1)]
    out['lorelei_runs'] = rs
    rs = ctx.run({0: ctx.cell('bruno', ctx.plan('bruno', 'plan', 2), None, out['bruno'])})[0]
    out['agatha'] = [r['end'] for r in R.accepted(rs, 2)]
    rs = ctx.run({0: ctx.cell('agatha', ctx.plan('agatha', 'plan', 0), None, out['agatha'])})[0]
    out['lance'] = [r['end'] for r in R.accepted(rs, 0)]
    return out


# ---------------------------------------------------------------- heal blocks

HEAL_TARGETS = [
    # (label, fight, foe index, variant, entry pool key or None for full)
    ('Bruno Machamp', 'bruno', 4, 'plan', 'bruno'),
    ('Bruno Hitmonlee', 'bruno', 2, 'plan', 'bruno'),
    ('Lorelei Lapras', 'lorelei', 4, 'more_setup', None),
    ('Lance Dragonite', 'lance', 4, 'late_heal', 'lance'),
]


def heal_search(ctx, entry_pools):
    """Grid per foe; Bruno's Hitmonlee search keeps the chosen Machamp block. Returns (text, chosen blocks)."""
    lines = ['TABLE 4. Per-foe heal blocks: heal when HP < below with the smallest spendable heal restoring >= '
             'heal_at_least (Super Potion 50, Full Restore to full); the default KO-risk heal still applies.',
             '  {} runs per cell; P(k) = P(win and FR <= k) with the FR budget k; tries = 1/P(k=2).'.format(len(ctx.seeds)),
             '  {:18s} {:>6s} {:>8s}  {:>8s} {:>7s} {:>7s} {:>6s} {:>9s}'.format(
                 'foe', 'below', 'at_least', 'win(k=2)', 'P(k=1)', 'P(k=2)', 'tries', 'FR|acc k2')]
    chosen = {}
    for label, fight, index, variant, pool_key in HEAL_TARGETS:
        base = ctx.base
        for (f, i), block in chosen.items():
            if f == fight:
                base = with_foe(base, f, i, heal=block)
        pool = entry_pools[pool_key] if pool_key else [R.full_carry(BAG_NOW)]
        risk = R.E4_VARIANTS[variant]['risk']
        cells = {}
        for below in BELOW:
            for at_least in (AT_LEAST if below is not None else (0,)):
                for k in (1, 2):
                    plan = with_foe(ctx.plan(fight, variant, k, base), fight, index, heal=heal_block(below, at_least))
                    cells[(below, at_least, k)] = ctx.cell(fight, plan, risk, pool, top_up=pool_key is not None)
        out = ctx.run(cells)
        best = None
        for below in BELOW:
            for at_least in (AT_LEAST if below is not None else (0,)):
                r1, r2 = out[(below, at_least, 1)], out[(below, at_least, 2)]
                p2 = acc(r2, 2)
                row = (tries(p2), below, at_least)
                best = row if best is None or row[0] < best[0] - 0.02 else best  # prefer no block on ties
                lines.append('  {:18s} {:>6s} {:>8s}  {:>8s} {:>7s} {:>7s} {:>6.2f} {:>9.2f}'.format(
                    label, str(below or 'off'), str(at_least or '-'), pct(sum(r['won'] for r in r2) / len(r2)),
                    pct(acc(r1, 1)), pct(p2), tries(p2), fr_mean(r2, 2)))
        if best[1] is not None:
            chosen[(fight, index)] = heal_block(best[1], best[2])
        lines.append('  {:18s} -> chosen: {}'.format(label, chosen.get((fight, index), 'no block (default KO-risk rule)')))
        lines.append('')
    return '\n'.join(lines), chosen


# ---------------------------------------------------------------- Bruno opening / reset

def opening(r):
    """Onix #1's first two moves (with * for a crit), and our state when Onix #1 falls (None: lost on it)."""
    onix = []
    check = None
    for foe, hp, spe, own, foe_move, crit in r['trace']:
        if foe != 'ONIX':
            check = {'hp': hp, 'spe': spe}
            break
        if foe_move:
            onix.append(MOVE_ABBR.get(foe_move, foe_move) + ('*' if crit else ''))
    xspeed = sum(1 for t in r['trace'][:len(onix) + 8] if t[0] == 'ONIX' and t[3] == 'xspeed')
    return '/'.join(onix[:2]) or '-', check, xspeed


def reset_cost(rs, k, rule):
    """(cost per accepted win in full fights, P(reset), P(accept | no reset), full fights, resets) for a rule."""
    n = len(rs)
    resets = acc_n = 0
    for r in rs:
        _, check, _ = opening(r)
        if check is not None and rule(check):
            resets += 1
        elif r['won'] and not r['reset'] and r['fr'] <= k:
            acc_n += 1
    if not acc_n:
        return float('inf'), resets / n, 0.0, float('inf'), float('inf')
    full = (n - resets) / acc_n
    return full + RESET_COST * resets / acc_n, resets / n, acc_n / max(1, n - resets), full, resets / acc_n


def bruno_part(ctx, entry_pools, chosen, champ_leftover):
    lines = ['TABLE 5. Bruno opening and early reset (plan + chosen heal blocks, {} runs per cell, entries = Lorelei '
             'wins with FR <= 1)'.format(len(ctx.seeds) * 2)]
    seeds2 = ['t1:{}'.format(i) for i in range(len(ctx.seeds) * 2)]
    base = ctx.base
    for (f, i), block in chosen.items():
        if f == 'bruno':
            base = with_foe(base, f, i, heal=block)
    cells = {}
    for cap in (1, 3):
        for k in (1, 2):
            plan = ctx.plan('bruno', 'plan', k, base)
            plan['fights']['bruno']['reserve']['items']['xspeed'] = BAG_NOW['xspeed'] - cap
            cells[(cap, k)] = ('bruno', plan, None, R.entries_for(seeds2, 'bruno', entry_pools['bruno'], R.FR_POOL), True)
    out = ctx.run(cells)
    # Openings
    lines.append('  By Onix #1\'s first two moves (* = crit), X Speed cap 3:')
    lines.append('    {:12s} {:>6s} {:>9s} {:>8s} {:>8s} {:>10s} {:>9s}'.format(
        'opening', 'share', 'win/try', 'P(k=1)', 'P(k=2)', 'HP after', 'Spe < 0'))
    groups = defaultdict(lambda: {1: [], 2: []})
    for k in (1, 2):
        for r in out[(3, k)]:
            groups[opening(r)[0]][k].append(r)
    for name, g in sorted(groups.items(), key=lambda kv: -len(kv[1][2])):
        if len(g[2]) < 10:
            continue
        checks = [opening(r)[1] for r in g[2] if opening(r)[1]]
        hp = sorted(c['hp'] for c in checks)
        lines.append('    {:12s} {:>6s} {:>9s} {:>8s} {:>8s} {:>10s} {:>9s}'.format(
            name, pct(len(g[2]) / len(out[(3, 2)])), pct(sum(r['won'] for r in g[2]) / len(g[2])),
            pct(acc(g[1], 1)) if g[1] else '-', pct(acc(g[2], 2)),
            str(hp[len(hp) // 2]) if hp else '-', pct(sum(c['spe'] < 0 for c in checks) / max(1, len(checks)))))
    # HP bins
    lines.append('  By HP when Onix #1 falls (X Speed cap 3, k=2): P(accept | HP bin)')
    bins = defaultdict(list)
    for r in out[(3, 2)]:
        check = opening(r)[1]
        key = 'lost' if check is None else min(check['hp'] // 30 * 30, 150)
        bins[key].append(r)
    for key in sorted(bins, key=lambda b: (b == 'lost', b if b != 'lost' else 0)):
        rs = bins[key]
        label = key if key == 'lost' else '{}-{}'.format(key, key + 29 if key < 150 else 171)
        lines.append('    HP {:>8s}: share {}  P(accept k=2) {}'.format(str(label), pct(len(rs) / len(out[(3, 2)])), pct(acc(rs, 2))))
    # Rules
    lines.append('  Reset rules (decided when Onix #1 falls; a reset try costs {} of a full fight):'.format(RESET_COST))
    lines.append('    {:6s} {:4s} {:28s} {:>8s} {:>9s} {:>9s} {:>8s} {:>8s}'.format(
        'X Spe', 'k', 'rule', 'cost', 'P(reset)', 'P(acc|go)', 'fights', 'resets'))
    best = {}
    for cap in (1, 3):
        for k in (1, 2):
            rows = []
            for x in range(0, 171, 10):
                for spe in (False, True):
                    rule = (lambda x, spe: lambda c: c['hp'] < x or (spe and c['spe'] < 0))(x, spe)
                    name = 'HP < {}{}'.format(x, ' or Spe < 0' if spe else '') if x or spe else 'never reset'
                    rows.append((reset_cost(out[(cap, k)], k, rule), name, x, spe))
            rows.sort(key=lambda r: r[0][0])
            base_row = next(r for r in rows if r[1] == 'never reset')
            for r in [base_row] + [r for r in rows[:3] if r is not base_row]:
                c = r[0]
                lines.append('    {:6d} {:4d} {:28s} {:>8.2f} {:>9s} {:>9s} {:>8.2f} {:>8.2f}'.format(
                    cap, k, r[1], c[0], pct(c[1]), pct(c[2]), c[3], c[4]))
            best[(cap, k)] = rows[0]
    # X Speed use
    used = Counter(min(sum(1 for t in r['trace'] if t[3] == 'xspeed'), 3) for r in out[(3, 2)])
    lines.append('  X Speed used at Bruno with cap 3 (k=2): ' + ', '.join(
        '{} {}'.format(n, pct(used[n] / len(out[(3, 2)]))) for n in range(4)))
    # Effect of X Speed on Agatha / Champion
    cells = {}
    for xs in (1, 0):
        # Agatha's reserve keeps 1 X Speed for the Champion: bag 2 = Agatha has 1 spendable, bag 1 = none.
        pool = [dict(c, bag=dict(c['bag'], xspeed=xs + 1)) for c in entry_pools['agatha']]
        cells[('agatha', xs)] = ctx.cell('agatha', ctx.plan('agatha', 'plan', 0), None, pool)
        for c in (3, 4):
            bag = dict(champ_leftover, xspeed=xs)
            cells[('champion', xs, c)] = ctx.cell('champion', R.run_plan(ctx.base, 'champion', champ='plan'), None,
                                                  [R.full_carry(bag)], top_up=False, fr=c)
    eff = ctx.run(cells)
    lines.append('  X Speed left for later fights (Agatha needs 1, the Champion 1; 5 in the bag):')
    lines.append('    Agatha FR 0 accept: with 1 X Speed {}, with none {}'.format(
        pct(acc(eff[('agatha', 1)], 0)), pct(acc(eff[('agatha', 0)], 0))))
    for c in (3, 4):
        lines.append('    Champion c={} (full HP, leftover bag): with 1 X Speed {}, with none {}'.format(
            c, pct(sum(r['won'] for r in eff[('champion', 1, c)]) / len(ctx.seeds)),
            pct(sum(r['won'] for r in eff[('champion', 0, c)]) / len(ctx.seeds))))
    lines.append('')
    lines.append(xsp3_part(ctx, entry_pools, base, out))
    return '\n'.join(lines), best


def xsp3_part(ctx, entry_pools, base, bruno_out):
    """A 3rd X Special at Bruno, used on Hitmonchan (after Onix #1, whose Roar is the only one in Bruno's team),
    for a Surf OHKO on Machamp; Agatha's Gengar setup drops from +3 to +2 to pay for it."""
    cells = {}
    for k in (1, 2):
        plan = with_foe(ctx.plan('bruno', 'plan', k, base), 'bruno', 1,
                        setup=[{'item': 'xspecial', 'stage': 3, 'serves': 'surf'}])
        plan['fights']['bruno']['reserve']['items']['xspecial'] -= 1
        plan['fights']['bruno']['reserve']['items']['xspeed'] = BAG_NOW['xspeed'] - 3
        cells[('bruno', k)] = ('bruno', plan, None,
                               R.entries_for(['t1:{}'.format(i) for i in range(len(ctx.seeds) * 2)], 'bruno',
                                             entry_pools['bruno'], R.FR_POOL), True)
    agatha_plus2 = copy.deepcopy(ctx.plan('agatha', 'plan', 0))
    for g in agatha_plus2['fights']['agatha']['foes'][0]['setup']:
        if g['item'] == 'xspecial':
            g['stage'] = 2
    pool = [dict(c, bag=dict(c['bag'], xspecial=c['bag'].get('xspecial', 0) - 1)) for c in entry_pools['agatha']]
    cells[('agatha', 3)] = ctx.cell('agatha', ctx.plan('agatha', 'plan', 0), None, entry_pools['agatha'])
    cells[('agatha', 2)] = ctx.cell('agatha', agatha_plus2, None, pool)
    out = ctx.run(cells)
    base2, x2 = acc(bruno_out[(3, 2)], 2), acc(out[('bruno', 2)], 2)
    base1, x1 = acc(bruno_out[(3, 1)], 1), acc(out[('bruno', 1)], 1)
    a3, a2 = acc(out[('agatha', 3)], 0), acc(out[('agatha', 2)], 0)
    win = lambda rs: pct(sum(r['won'] for r in rs) / len(rs))
    machamp_ohko = lambda rs: pct(sum(1 for r in rs if sum(1 for t in r['trace'] if t[0] == 'MACHAMP' and t[3] == 'surf') == 1
                                       and r['won']) / max(1, sum(1 for r in rs if any(t[0] == 'MACHAMP' for t in r['trace']))))
    lines = ['TABLE 5b. 3rd X Special at Bruno (on Hitmonchan, +3 Sp. Atk; X Speed cap 3), paid by Agatha\'s Gengar +3 -> +2',
             '  {:28s} {:>8s} {:>8s} {:>8s} {:>10s} {:>15s}'.format('', 'win/try', 'P(k=1)', 'P(k=2)', 'FR|acc k2',
                                                                    'Machamp 1 Surf'),
             '  {:28s} {:>8s} {:>8s} {:>8s} {:>10.2f} {:>15s}'.format('Bruno plan (+2)', win(bruno_out[(3, 2)]), pct(base1),
                                                                   pct(base2), fr_mean(bruno_out[(3, 2)], 2),
                                                                   machamp_ohko(bruno_out[(3, 2)])),
             '  {:28s} {:>8s} {:>8s} {:>8s} {:>10.2f} {:>15s}'.format('Bruno +3 after Onix #1', win(out[('bruno', 2)]),
                                                                   pct(x1), pct(x2), fr_mean(out[('bruno', 2)], 2),
                                                                   machamp_ohko(out[('bruno', 2)])),
             '  Agatha FR 0 accept: Gengar +3 {}  ->  +2 {}'.format(pct(a3), pct(a2)),
             '  Net expected tries (Bruno k=2 + Agatha k=0): {:+.2f}   (Bruno {:+.2f}, Agatha {:+.2f});  with Bruno k=1: {:+.2f}'.format(
                 tries(x2) - tries(base2) + tries(a2) - tries(a3), tries(x2) - tries(base2), tries(a2) - tries(a3),
                 tries(x1) - tries(base1) + tries(a2) - tries(a3))]
    return '\n'.join(lines)


# ---------------------------------------------------------------- Lapras

def lapras_part(ctx, chosen):
    lines = ['TABLE 6. Lapras kill order (Lorelei with X Sp +6 on Dewgong, from full; {} runs; FR budget 2)'.format(
        len(ctx.seeds)),
             '  KO by move 3 = Lapras down within our first 3 attacks on it; damage = HP lost while facing Lapras; FR = '
             'our Full Restores while facing Lapras.',
             '  {:28s} {:>8s} {:>9s} {:>9s} {:>8s} {:>8s} {:>9s}'.format(
                 'order', 'reached', 'KO by 3', 'attacks', 'damage', 'FR', 'Lorelei')]
    base = ctx.base
    if ('lorelei', 4) in chosen:
        base = with_foe(base, 'lorelei', 4, heal=chosen[('lorelei', 4)])
    orders = {
        'plan (Bite/Strength, kill order)': {},
        'Strength -> Bite -> Bite': {'sequence': ['strength', 'bite', 'bite']},
        'Bite only (x4)': {'moves': ['bite'], 'kill_order': False},
    }
    cells = {}
    for name, fields in orders.items():
        plan = with_foe(ctx.plan('lorelei', 'more_setup', 2, base), 'lorelei', 4, **fields)
        cells[name] = ctx.cell('lorelei', plan, None, [R.full_carry(BAG_NOW)], top_up=False)
    out = ctx.run(cells)
    for name, rs in out.items():
        reached = [r for r in rs if any(t[0] == 'LAPRAS' for t in r['trace'])]
        kos, attacks, dmg, frs = 0, [], [], []
        for r in reached:
            seg = [t for t in r['trace'] if t[0] == 'LAPRAS']
            n_att = sum(1 for t in seg if t[3] in ('bite', 'strength', 'surf', 'blizzard'))
            hps = [t[1] for t in seg] + [r['end']['hp']]
            dmg.append(sum(max(0, a - b) for a, b in zip(hps, hps[1:])))
            frs.append(sum(1 for t in seg if t[3] == 'fullrestore'))
            attacks.append(n_att)
            kos += r['won'] and n_att <= 3
        n = max(1, len(reached))
        lines.append('  {:28s} {:>8s} {:>9s} {:>9.2f} {:>8.1f} {:>8.2f} {:>9s}'.format(
            name, pct(len(reached) / len(rs)), pct(kos / n), sum(attacks) / n, sum(dmg) / n, sum(frs) / n,
            pct(sum(r['won'] for r in rs) / len(rs))))
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runs', type=int, default=500)
    parser.add_argument('--workers', type=int, default=9)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(args.workers, initializer=R._init) as ex:
        ctx = Ctx(ex, args.runs, args.workers)
        entry_pools = pools(ctx)
        print('pools', {k: len(v) for k, v in entry_pools.items()}, flush=True)
        heal_text, chosen = heal_search(ctx, entry_pools)
        print(heal_text, flush=True)
        leftover = R.median_bag(entry_pools['lance'])
        bruno_text, _ = bruno_part(ctx, entry_pools, chosen, leftover)
        print(bruno_text, flush=True)
        lapras_text = lapras_part(ctx, chosen)
        print(lapras_text, flush=True)
    text = '\n\n'.join([heal_text, bruno_text, lapras_text])
    (args.out_dir / 'tuning.txt').write_text(text + '\n')


if __name__ == '__main__':
    main()

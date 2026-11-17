"""FRLG League worked backwards: retry each fight from a save until it wins cheaply.

  PYTHONPATH=src python3 -m pokesim.cli.frlg_league_retry --runs 500 --seed r1 --out-dir ~/BDSPLab/notes/e4-sim/retry

A loss does not save, and the game can be saved between League rooms, so each fight is retried until a
win that spends at most k Full Restores (its accept rule). Expected tries per accepted win = 1 / P(win and
FR <= k). With k per E4 fight and c Full Restores left for the Champion (sum 8, BAG_NOW), the expected
total tries is the sum over the five fights.

Setup P of #113: our Blastoise Lv54 (console stats), BAG_NOW, no held item, policy 'planned' (plan.json).

Model:
  * Budget k: the fight's Full Restore reserve is set so exactly k are spendable (the in-fight heal still
    breaches it to avoid a KO; such a win spends > k and is rejected). Out-of-battle top-ups before the
    fight (plan.json `between`) count toward the fight's Full Restores. k = 8 is "no budget" (the FR
    distribution of won fights).
  * Entry state (HP, status, PP, the non-FR bag): sampled from the previous fight's accepted wins of the
    current plan at k = 3, then the plan's between-fight top-up (Super Potions to its HP target, Elixir
    to its PP floor). Lorelei starts full with BAG_NOW. Same seeds across k and variants (paired).
  * E4 variants: plan; late_heal (heal only when the foe's mean hit KOs, not its worst roll);
    more_setup (+2 X Special stages on the plan's setup foe); risky (both).
  * Bruno and the Champion: a Roar / Whirlwind that lands is a soft reset (the console reloads the save before
    the fight): the try ends there, neither a loss nor an accepted win, and counts as one try.
  * Bruno 'pokeguy' (PokeGuy's line): +2 Sp. Atk (again after a reset-free Roar on any foe), X Speed when Rock
    Tomb drops Speed, Surf everything, heal only when the foe's lowest roll KOs; 'pokeguy_noheal' never heals.
  * Champion: Full Restores at entry c = 0..8, four setups on Pidgeot (plan, risky, safer, long), three entry
    states (sampled from Lance's accepted wins; full HP/PP with the median leftover bag; full HP/PP with
    BAG_NOW's whole non-FR bag).
"""

import argparse
import atexit
import copy
import itertools
import json
import random
import statistics
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from pokesim.cli.frlg_league_chain import BAG_NOW, league_cases
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.league import planned
from pokesim.games.frlg.league.chain import MOVE_PP, POLICIES, fight_scenario, ours_at, play

LEVEL = 54
E4 = ('lorelei', 'bruno', 'agatha', 'lance')
KS = (0, 1, 2, 3, 4, 8)
FR_POOL = 8
POOL_K = 3
# Bruno and the Champion: a Roar / Whirlwind that lands means soft reset and reload the save before the fight.
# The try ends there: no loss, no accepted win, one try spent.
RESET_FIGHTS = ('bruno', 'champion')
E4_VARIANTS = {
    'plan': dict(risk=None, extra_xsp=0),
    'late_heal': dict(risk='mean', extra_xsp=0),
    'more_setup': dict(risk=None, extra_xsp=2),
    'risky': dict(risk='mean', extra_xsp=2),
    # PokeGuy's Bruno (events.json 1:49:15-1:50:49): +2 Sp. Atk on Onix (again on any foe after a Roar), X Speed
    # when Rock Tomb drops Speed, Surf everything, heal only when the lowest roll KOs (or never).
    'pokeguy': dict(risk='sure', extra_xsp=0, fights=('bruno',)),
    'pokeguy_noheal': dict(risk='never', extra_xsp=0, fights=('bruno',)),
}
POKEGUY_BRUNO_SETUP = [{'item': 'xspecial', 'stage': 2, 'serves': 'surf'},
                       {'item': 'xspeed', 'stage': 0, 'serves': 'surf'}]


def variants_for(fight):
    return [v for v, spec in E4_VARIANTS.items() if fight in spec.get('fights', E4)]


def goal(item, stage=1, serves='blizzard'):
    g = {'item': item, 'stage': stage}
    if item != 'guardspec':
        g['serves'] = serves
    return g


CHAMP_SETUPS = {
    'plan': [goal('guardspec'), goal('xspecial', 2), goal('xaccuracy', 2), goal('xspeed', 1)],
    'risky': [goal('xspecial', 2), goal('xspeed', 1)],
    'safer': [goal('guardspec'), goal('xspecial', 2), goal('xaccuracy', 3), goal('xspeed', 1)],
    # Long setup: Pidgeot's Whirlwind resets the boosts more often than the extra stages pay back.
    'long': [goal('guardspec'), goal('xspecial', 4), goal('xaccuracy', 3), goal('xspeed', 2)],
}
CHAMP_ENTRIES = ('sampled', 'leftover', 'fullbag')
X_ITEMS = ('xspecial', 'xspeed', 'xaccuracy', 'guardspec')

_W = {}


def _init():
    cases, pret = league_cases()
    engine = Engine().__enter__()
    atexit.register(engine.__exit__)
    _W.update(cases=cases, pret=pret, ai=NPCTrainerAI(pret), engine=engine, plan=planned.load_plan(),
              stats=ours_at(LEVEL))


def run_plan(base, fight, variant='plan', k=None, champ=None):
    plan = copy.deepcopy(base)
    row = plan['fights'][fight]
    extra = E4_VARIANTS[variant]['extra_xsp'] if fight in E4 else 0
    for g in row['foes'][0]['setup']:
        if g['item'] == 'xspecial':
            g['stage'] += extra
    if variant.startswith('pokeguy'):
        for foe in row['foes']:
            foe['moves'] = ['surf']
            foe['setup'] = copy.deepcopy(POKEGUY_BRUNO_SETUP)
    if champ:
        plan['fights']['champion']['foes'][0]['setup'] = copy.deepcopy(CHAMP_SETUPS[champ])
    items = row['reserve']['items']
    if k is not None:
        items['fullrestore'] = FR_POOL - k
    else:
        items.pop('fullrestore', None)
    return plan


def full_carry(bag):
    return {'hp': None, 'status': '', 'pp': dict(MOVE_PP), 'bag': dict(bag)}


def run_fight(fight, carry_in, plan, seed, risk, top_up):
    w = _W
    carry = copy.deepcopy(carry_in)
    max_hp = w['stats']['hp']
    if carry['hp'] is None:
        carry['hp'] = max_hp
    pre = {'hp': carry['hp'], 'superpotion': carry['bag'].get('superpotion', 0)}
    top = planned.between(carry, max_hp, plan, fight, MOVE_PP) if top_up else {}
    pre['entry'] = {'hp': carry['hp'], 'pp': dict(carry['pp'])}
    scenario = fight_scenario(w['cases'][fight], w['pret'], carry, w['stats'], LEVEL, None, True, '')
    goals = {'_league_plan': plan}
    if risk:
        goals['_risk'] = risk
    state, decisions = play(w['engine'], scenario, w['ai'], POLICIES['planned'], '{}:{}'.format(seed, fight),
                            fight=fight, extra_goals=goals)
    own = state['own']
    pp = {m['id'].upper(): m['pp'] for m in own['moves']}
    used = Counter(state['items_used'])
    used.update(top)
    last = decisions[-1] if decisions else {}
    cause = {'roared': any(d['own'].get('kind') == 'switch' for d in decisions), 'foe': last.get('foe'),
             'move': last.get('foe_move'), 'crit': last.get('turn') in state['foe_crit_turns']}
    reset = cause['roared'] and fight in RESET_FIGHTS
    return {'won': state['winner'] == 'Player' and not reset, 'reset': reset,
            'lost': state['winner'] != 'Player' and not reset, 'fr': used.get('fullrestore', 0), 'used': dict(used),
            'pre': pre, 'turns': len(decisions), 'cause': cause,
            # Per decision: foe, our HP, Speed stage, our action (move id or item), foe move, foe crit.
            'trace': [(str(d['foe']).upper(), d['hp'], d['boosts'].get('spe', 0),
                       d['move'] or d['own'].get('item') or d['own'].get('kind'), d['foe_move'],
                       d['turn'] in state['foe_crit_turns']) for d in decisions],
            'end': {'hp': own['hp'], 'status': own.get('status', '') or '',
                    'pp': {k: pp.get(k, 0) for k in MOVE_PP}, 'bag': {k: v for k, v in state['bag'].items()}}}


def _job(job):
    fight, plan, risk, entries, top_up = job
    return [run_fight(fight, carry, plan, seed, risk, top_up) for seed, carry in entries]


def entries_for(seeds, fight, pool, fr):
    """(seed, carry) per run: a carry sampled from the pool (seeded per run), Full Restores set to fr."""
    out = []
    for seed in seeds:
        carry = copy.deepcopy(pool[random.Random('entry:{}:{}'.format(seed, fight)).randrange(len(pool))])
        carry['bag']['fullrestore'] = fr
        out.append((seed, carry))
    return out


def run_cells(pool_exec, cells, workers):
    """cells: {key: (fight, plan, risk, entries, top_up)} -> {key: [results]} in one parallel sweep."""
    jobs, keys = [], []
    for key, (fight, plan, risk, entries, top_up) in cells.items():
        for i in range(workers):
            jobs.append((fight, plan, risk, entries[i::workers], top_up))
            keys.append(key)
    out = {key: [] for key in cells}
    for key, part in zip(keys, pool_exec.map(_job, jobs)):
        out[key].extend(part)
    return out


def accepted(results, k):
    return [r for r in results if r['won'] and r['fr'] <= k]


def rate(results, k):
    return len(accepted(results, k)) / len(results)


def tries(p):
    return 1 / p if p > 0 else float('inf')


def e4_sweep(ex, seeds, workers, base):
    """Per E4 fight: every variant x k from the sampled entry, plus the plan from full HP/PP."""
    results, pools = {}, {}
    pool = [full_carry(BAG_NOW)]
    for index, fight in enumerate(E4):
        cells = {}
        for variant in variants_for(fight):
            v = E4_VARIANTS[variant]
            for k in KS:
                cells[(variant, k)] = (fight, run_plan(base, fight, variant, k), v['risk'],
                                       entries_for(seeds, fight, pool, FR_POOL), index > 0)
        full_bag = dict(BAG_NOW)
        for earlier in E4[:index]:
            for name, n in planned.setup_count(base['fights'][earlier]['foes']).items():
                full_bag[name] -= n
        for variant in variants_for(fight):
            if variant not in ('plan', 'pokeguy', 'pokeguy_noheal'):
                continue
            name = 'full' if variant == 'plan' else 'full_' + variant
            for k in KS:
                cells[(name, k)] = (fight, run_plan(base, fight, variant, k), E4_VARIANTS[variant]['risk'],
                                    entries_for(seeds, fight, [full_carry(full_bag)], FR_POOL), False)
        out = run_cells(ex, cells, workers)
        results[fight] = out
        pool = [r['end'] for r in accepted(out[('plan', POOL_K)], POOL_K)]
        pools[fight] = pool
        print('{}: plan k=3 accept {:.1%}'.format(fight, len(pool) / len(seeds)), flush=True)
    return results, pools


def median_bag(pool):
    names = sorted({n for c in pool for n in c['bag']})
    return {n: int(statistics.median(c['bag'].get(n, 0) for c in pool)) for n in names}


def champion_sweep(ex, seeds, workers, base, lance_pool):
    leftover = median_bag(lance_pool)
    fullbag = dict(BAG_NOW)
    cells = {}
    for setup in CHAMP_SETUPS:
        plan = run_plan(base, 'champion', champ=setup)
        for c in range(FR_POOL + 1):
            cells[('sampled', setup, c)] = ('champion', plan, None, entries_for(seeds, 'champion', lance_pool, c), True)
            for mode, bag in (('leftover', leftover), ('fullbag', fullbag)):
                cells[(mode, setup, c)] = ('champion', plan, None,
                                           entries_for(seeds, 'champion', [full_carry(bag)], c), False)
    out = run_cells(ex, cells, workers)
    resets = {key: sum(r['reset'] for r in rs) / len(rs) for key, rs in out.items()}
    return {key: sum(r['won'] for r in rs) / len(rs) for key, rs in out.items()}, leftover, resets


def x_use(e4_variants, champ):
    use = Counter()
    for fight, variant in zip(E4, e4_variants):
        foes = copy.deepcopy(_PLAN['fights'][fight]['foes'])
        for g in foes[0]['setup']:
            if g['item'] == 'xspecial':
                g['stage'] += E4_VARIANTS[variant]['extra_xsp']
        use.update(planned.setup_count(foes))
    use.update(planned.setup_count([{'setup': CHAMP_SETUPS[champ]}]))
    return use


def allocations(e4, champ_win):
    """Every (k, variant) per E4 fight and Champion setup with sum k + c = 8 and X items within BAG_NOW."""
    rows = []
    options = {f: [(k, v, rate(e4[f][(v, k)], k)) for k in KS if k <= 4 for v in variants_for(f)] for f in E4}
    for combo in itertools.product(*(options[f] for f in E4)):
        c = FR_POOL - sum(o[0] for o in combo)
        if c < 0:
            continue
        for champ in CHAMP_SETUPS:
            use = x_use([o[1] for o in combo], champ)
            if any(use[n] > BAG_NOW.get(n, 0) for n in X_ITEMS):
                continue
            w = champ_win[('sampled', champ, c)]
            total = sum(tries(o[2]) for o in combo) + tries(w)
            rows.append({'k': [o[0] for o in combo], 'variants': [o[1] for o in combo], 'p': [o[2] for o in combo],
                         'champ': champ, 'c': c, 'win': w, 'total': total, 'x': dict(use)})
    rows.sort(key=lambda r: r['total'])
    return rows


def validate(ex, seeds, workers, base, row):
    """Item 4 check: the allocation played forward with its own accept rules and pools."""
    pool = [full_carry(BAG_NOW)]
    out = []
    for index, (fight, k, variant) in enumerate(zip(E4, row['k'], row['variants'])):
        plan = run_plan(base, fight, variant, k, champ=row['champ'])
        rs = run_cells(ex, {0: (fight, plan, E4_VARIANTS[variant]['risk'],
                                entries_for(seeds, fight, pool, FR_POOL), index > 0)}, workers)[0]
        acc = accepted(rs, k)
        out.append((fight, len(acc) / len(rs)))
        pool = [r['end'] for r in acc]
        if not pool:
            return out, 0.0
    plan = run_plan(base, 'champion', champ=row['champ'])
    rs = run_cells(ex, {0: ('champion', plan, None, entries_for(seeds, 'champion', pool, row['c']), True)}, workers)[0]
    return out, sum(r['won'] for r in rs) / len(rs)


_PLAN = planned.load_plan()


def pct(x):
    return '{:5.1%}'.format(x)


def render_champion(champ_win, leftover, runs, seed, champ_reset):
    lines = ['TABLE 1. Champion alone: win rate by Full Restores at entry ({} runs per cell, seed {})'.format(runs, seed),
             '  setups on Pidgeot: plan = Guard Spec, X Sp +2, X Acc +2, X Spe +1;  risky = X Sp +2, X Spe +1;',
             '                     safer = plan with X Acc +3;  long = Guard Spec, X Sp +4, X Acc +3, X Spe +2',
             '  entry sampled  = HP/PP/bag of Lance\'s accepted wins (plan, FR <= 3), then the plan\'s top-up '
             '(Super Potions to full HP, Elixir/Max Elixir to Surf 8 / Blizzard 4); a Full Restore spent on that '
             'top-up comes out of c',
             '  entry leftover = full HP, all PP (Blizzard 5/5), median non-FR bag left after the E4: ' +
             ', '.join('{} {}'.format(k, v) for k, v in leftover.items() if v and k != 'fullrestore'),
             '  entry fullbag  = full HP, all PP, BAG_NOW\'s whole non-FR bag',
             '  {:9s} {:7s} '.format('entry', 'setup') + ' '.join('{:>6s}'.format('c=%d' % c) for c in range(FR_POOL + 1))]
    for mode in CHAMP_ENTRIES:
        for setup in CHAMP_SETUPS:
            lines.append('  {:9s} {:7s} '.format(mode, setup) + ' '.join(
                '{:>6s}'.format(pct(champ_win[(mode, setup, c)]).strip()) for c in range(FR_POOL + 1)))
    lines.append('  Win = per try: a Whirlwind/Roar that lands is a reset (a failed try), counted apart from losses.')
    lines.append('  Reset / loss per try (entry sampled):')
    for setup in CHAMP_SETUPS:
        lines.append('    {:7s} '.format(setup) + '  '.join('c={} reset {} loss {}'.format(
            c, pct(champ_reset[('sampled', setup, c)]),
            pct(1 - champ_win[('sampled', setup, c)] - champ_reset[('sampled', setup, c)])) for c in (2, 4, 8)))
    return '\n'.join(lines)


def render_e4(e4, runs, seed):
    lines = ['TABLE 2. Each E4 fight alone ({} runs per cell, seed {}, paired seeds across k and variants)'.format(runs, seed),
             '  entry: sampled from the previous fight\'s accepted wins (plan, FR <= 3) + the plan\'s between-fight '
             'top-up (Bruno/Agatha 80% HP, Lance 100%); Lorelei full with BAG_NOW.  "full" = the plan from full HP/PP.',
             '  P(acc k) = P(win and FR <= k) with the fight\'s FR budget set to k (k spendable); tries = 1/P.',
             '  FR in won fights: k=8 (no budget) run; win% = that run\'s win rate.']
    for fight in E4:
        lines.append('')
        lines.append('  {}'.format(fight.upper()))
        lines.append('    {:11s} {:>6s}  {:>24s}  '.format('variant', 'win%', 'FR used in wins 0/1/2/3/4+') +
                     '  '.join('P(k={}) tries'.format(k) for k in range(4)))
        names = variants_for(fight) + [n for n in ('full', 'full_pokeguy', 'full_pokeguy_noheal') if (n, 8) in e4[fight]]
        for variant in names:
            free = e4[fight][(variant, 8)]
            wins = [r for r in free if r['won']]
            dist = Counter(min(r['fr'], 4) for r in wins)
            dist_s = '/'.join('{:.0%}'.format(dist[i] / max(1, len(wins))) for i in range(5))
            cells = '  '.join('{} {:>5.1f}'.format(pct(rate(e4[fight][(variant, k)], k)),
                                                    tries(rate(e4[fight][(variant, k)], k))) for k in range(4))
            lines.append('    {:11s} {:>6s}  {:>24s}  {}'.format(variant, pct(len(wins) / len(free)), dist_s, cells))
    return '\n'.join(lines)


def render_alloc(rows, checks, runs):
    lines = ['TABLE 3. Backward budget: k Full Restores accepted per E4 fight + c for the Champion = 8',
             '  per fight the variant is part of the choice; X Special/Speed/Accuracy and Guard Spec use within BAG_NOW '
             '(15/5/3/2); Super Potions, Elixir and Max Elixir carried in the sampled entry states.',
             '  total tries = sum of 1/P(accept) over the four E4 fights + 1/P(Champion win at c, sampled entry).',
             '  {:16s} {:44s} {:7s} {:>3s} {:>9s} {:>8s} {:>10s}'.format(
                 'k L/B/A/Lance', 'E4 variants', 'champ', 'c', 'champ win', 'tries', 'X Sp/Spe/Acc/GS')]

    def line(tag, r):
        x = r['x']
        return '  {:16s} {:44s} {:7s} {:>3d} {:>9s} {:>8.1f} {:>10s}{}'.format(
            '/'.join(map(str, r['k'])), ','.join(r['variants']), r['champ'], r['c'], pct(r['win']), r['total'],
            '{}/{}/{}/{}'.format(*(x.get(n, 0) for n in X_ITEMS)), tag)

    seen, top = set(), []
    for r in rows:  # one row per allocation: the best variants for it (ties differ only in no-op variants)
        key = (tuple(r['k']), r['c'], r['champ'])
        if key not in seen:
            seen.add(key)
            top.append(r)
        if len(top) == 5:
            break
    for r in top:
        lines.append(line('', r))
    c4 = next(r for r in rows if r['c'] == 4)
    lines.append(line('   <- best with c=4', c4))
    plan_only = next(r for r in rows if all(v == 'plan' for v in r['variants']) and r['champ'] == 'plan')
    lines.append(line('   <- best with the current plan everywhere', plan_only))
    lines.append('')
    lines.append('  Forward check (item 4): each row played forward with its own accept rules, next entry sampled '
                 'from that fight\'s accepted wins ({} runs per fight):'.format(runs))
    for tag, (per_fight, win) in checks:
        lines.append('    {:28s} '.format(tag) + '  '.join('{} {}'.format(f, pct(p)) for f, p in per_fight) +
                     '  champion win {}'.format(pct(win)))
    return '\n'.join(lines)


def bruno_report(e4):
    """Bruno: the PokeGuy line against the plan and late_heal, and how the losses happen."""
    rows = e4['bruno']
    lines = ['BRUNO: PokeGuy\'s line (pokeguy = heal only on a sure KO, i.e. lowest roll >= HP; pokeguy_noheal = never heal)',
             '  entry sampled = Lorelei\'s accepted wins + 80% HP top-up; full = full HP/PP.  FR dist from the k=8 run.',
             '  win% per try; reset = Roar landed (soft reset, a failed try); loss = a real loss.',
             '  {:22s} {:>6s} {:>6s} {:>6s}  {:>22s}  {:>7s} {:>7s} {:>7s}'.format(
                 'variant / entry', 'win%', 'reset', 'loss', 'FR in wins 0/1/2/3/4+', 'P(k=0)', 'P(k=1)', 'P(k=2)')]
    names = [('plan', 'sampled'), ('late_heal', 'sampled'), ('pokeguy', 'sampled'), ('pokeguy_noheal', 'sampled'),
             ('full', 'full (plan)'), ('full_pokeguy', 'full (pokeguy)'), ('full_pokeguy_noheal', 'full (noheal)')]
    for key, label in names:
        free = rows[(key, 8)]
        wins = [r for r in free if r['won']]
        dist = Counter(min(r['fr'], 4) for r in wins)
        lines.append('  {:22s} {:>6s} {:>6s} {:>6s}  {:>22s}  '.format(
            (key.replace('full_', '') if key != 'full' else 'plan') + ' / ' + label.split(' ')[0], pct(len(wins) / len(free)),
            pct(sum(r['reset'] for r in free) / len(free)), pct(sum(r['lost'] for r in free) / len(free)),
            '/'.join('{:.0%}'.format(dist[i] / max(1, len(wins))) for i in range(5))) +
            ' '.join('{:>7s}'.format(pct(rate(rows[(key, k)], k))) for k in range(3)))
    lines.append('')
    lines.append('  Loss causes (k=8 runs, real losses only, the killing blow)')
    for key, label in names:
        losses = [r for r in rows[(key, 8)] if r['lost']]
        if not losses:
            continue
        n = len(losses)
        kills = Counter()
        for r in losses:
            c = r['cause']
            if c['foe'] == 'MACHAMP' or (c['foe'] or '').lower() == 'machamp':
                kills['Machamp'] += 1
            elif c['move'] == 'earthquake' and c['crit']:
                kills['Earthquake crit'] += 1
            elif c['move'] == 'machpunch':
                kills['Mach Punch'] += 1
            else:
                kills['{} {}{}'.format(str(c['foe']).lower(), c['move'], ' crit' if c['crit'] else '')] += 1
        lines.append('    {:22s} losses {:3d}  '.format(key.replace('full_', '') + ' / ' + label.split(' ')[0], n) +
            ', '.join('{} {:.0%}'.format(k, v / n) for k, v in kills.most_common(6)))
    return '\n'.join(lines)


def entry_hp_effect(e4, pools, base_seeds):
    """Does a weaker accepted win (low end HP / fewer Super Potions) hurt the next fight? Plan, k = 2."""
    lines = ['  Entry effect (plan, k=2): next fight\'s P(accept) by the previous win\'s end HP and Super Potions left']
    max_hp = ours_at(LEVEL)['hp']
    for prev, fight in zip(E4[:-1], E4[1:]):
        rs = e4[fight][('plan', 2)]
        lo = [r for r in rs if r['pre']['hp'] < 0.5 * max_hp]
        hi = [r for r in rs if r['pre']['hp'] >= 0.5 * max_hp]
        sp_lo = [r for r in rs if r['pre']['superpotion'] <= 2]
        sp_hi = [r for r in rs if r['pre']['superpotion'] > 2]
        lines.append('    {} after {}: end HP <50% {} (n={}), >=50% {} (n={});  Super Potions <=2 {} (n={}), >2 {} (n={})'.format(
            fight, prev, pct(rate(lo, 2)) if lo else '  -  ', len(lo), pct(rate(hi, 2)) if hi else '  -  ', len(hi),
            pct(rate(sp_lo, 2)) if sp_lo else '  -  ', len(sp_lo), pct(rate(sp_hi, 2)) if sp_hi else '  -  ', len(sp_hi)))
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--runs', type=int, default=500)
    parser.add_argument('--workers', type=int, default=9)
    parser.add_argument('--seed', default='r1')
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    seeds = ['{}:{}'.format(args.seed, i) for i in range(args.runs)]
    base = planned.load_plan()
    with ProcessPoolExecutor(args.workers, initializer=_init) as ex:
        e4, pools = e4_sweep(ex, seeds, args.workers, base)
        champ_win, leftover, champ_reset = champion_sweep(ex, seeds, args.workers, base, pools['lance'])
        print('champion done', flush=True)
        rows = allocations(e4, champ_win)
        c4 = next(r for r in rows if r['c'] == 4)
        checks = [('best: ' + '/'.join(map(str, rows[0]['k'])) + ' c=%d' % rows[0]['c'],
                   validate(ex, seeds, args.workers, base, rows[0])),
                  ('c=4: ' + '/'.join(map(str, c4['k'])), validate(ex, seeds, args.workers, base, c4))]
    text = '\n\n'.join([render_champion(champ_win, leftover, args.runs, args.seed, champ_reset), render_e4(e4, args.runs, args.seed),
                        entry_hp_effect(e4, pools, seeds), bruno_report(e4), render_alloc(rows, checks, args.runs)])
    print(text)
    (args.out_dir / 'tables.txt').write_text(text + '\n')
    (args.out_dir / 'allocations.json').write_text(json.dumps(rows[:50], indent=1) + '\n')
    summary = {'champion': {'/'.join(map(str, k)): v for k, v in champ_win.items()},
               'e4': {f: {'{}/{}'.format(*key): {'win': sum(r['won'] for r in rs) / len(rs),
                                                 'accept': rate(rs, key[1]) if key[1] < 8 else None,
                                                 'reset': sum(r['reset'] for r in rs) / len(rs),
                                                 'fr_in_wins': dict(Counter(r['fr'] for r in rs if r['won']))}
                          for key, rs in e4[f].items()} for f in E4}}
    (args.out_dir / 'summary.json').write_text(json.dumps(summary) + '\n')


if __name__ == '__main__':
    main()

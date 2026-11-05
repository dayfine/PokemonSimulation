"""Publish both FRLG entry contracts and rankings without changing the run ledger.

PYTHONPATH=src python3 -m pokesim.cli.frlg_conditions
"""

import argparse
import copy
import json
from pathlib import Path

from pokesim.cli.frlg_run_battles import DATA
from pokesim.cli.frlg_preparation import preparation_cases
from pokesim.games.frlg.battle.engine import REPO
from pokesim.games.frlg.battle.benchmark import scenario_for
from pokesim.games.frlg.battle.run import trainer_cases
from pokesim.games.frlg.battle.sampling import confidence_sequence
from pokesim.games.frlg.progression.ledger import fingerprint


def resolve_conditions(inputs, reference, pret, baseline, preparation, plan):
    """Resolve every contract and attach only measurements of that entry state."""
    if plan.get('format') != 'pokesim-frlg-preparation-plan/1':
        raise ValueError('Unsupported preparation plan')
    if plan.get('default_prepared_variant') != 'recorded':
        raise ValueError('Unspecified fights must retain recorded preconditions')
    cases = inputs['cases']
    ids = {c['id'] for c in cases}
    if set(plan['requirements']) - ids or set(plan['pending_full_hp_tests']) - ids:
        raise ValueError('Preparation plan names unknown fights')
    complex_source = plan['complex_results']
    if (inputs['source_sha256'] != baseline['run_inputs']['source_sha256']
            or inputs['source_sha256'] != complex_source['source_sha256']):
        raise ValueError('Benchmark and entry-state sources disagree')
    if preparation['scenario_sha256'] != fingerprint(preparation_cases(cases, reference)):
        raise ValueError('Preparation results no longer match the entry scenarios')
    for source in (baseline, preparation, complex_source, plan['supplemental_rest_results']):
        if source['pret_snapshot_sha256'] != fingerprint(pret):
            raise ValueError('Opponent or move data changed since measurement')
    old = {r['id']: r for r in baseline['results']}
    complex_rows = {r['id']: r for r in complex_source['results']}
    prep = {(r['fight'], r['variant']): r for r in preparation['results']}
    extra = {r['id']: r for r in plan['supplemental_rest_results']['results']}
    if set(old) != ids or set(complex_rows) - ids or set(extra) - ids:
        raise ValueError('Measured fights do not match the route')
    # Cover all original candidate arms, including alternatives not selected.
    family = len(old) + len(complex_rows) + len(prep) + len(extra)

    def measured(row, source):
        wins, trials = row['wins'], row['battles']
        return {'wins': wins, 'trials': trials, 'probability': wins / trials,
                'bounds': confidence_sequence(wins, trials, .05 / family), 'source': source}

    result = []
    for case in cases:
        fight = case['id']
        tier = 'C' if fight in complex_rows else ('B' if old[fight]['mean_items_used'] else 'A')
        recorded = measured(old[fight], 'original benchmark, seed 1')
        strategy = {'tier': tier, 'policy': 'historical A/B recovery behavior'}
        if fight in complex_rows:
            recorded = measured(complex_rows[fight], 'C2 held-out benchmark, seed 4')
            strategy.update(policy=complex_source['policy'],
                            planning_goals=complex_rows[fight]['planning_goals'],
                            implementation_revision=complex_source['revision'])
        elif (fight, 'recorded') in prep:
            recorded = measured(prep[(fight, 'recorded')], 'preparation control, seed 11')
            strategy['policy'] = 'B:solo-recovery/1'
        prepared = copy.copy(case)
        prepared['player'] = copy.deepcopy(case['player'])
        prepared_result = dict(recorded)
        requirement = plan['requirements'].get(fight)
        if requirement:
            if requirement['action'] != 'full-rest' or requirement['additional_battle_items']:
                raise ValueError('Only measured full-rest preparation is supported')
            if not all(requirement[k] is True for k in
                       ('requires_full_hp', 'requires_full_pp', 'requires_clear_status')):
                raise ValueError('Full rest requires HP, PP and status restoration')
            player = prepared['player']
            player['hp'], player['status'] = player['stats']['hp'], ''
            for move in player['moves']:
                move['pp'] = reference['move_pp'][move['name']]
            row = prep.get((fight, 'full-rest'), extra.get(fight))
            if row is None or row['starting_hp'] != player['hp'] or row['moves'] != player['moves']:
                raise ValueError('No matching full-rest measurement for ' + fight)
            if fight in extra:
                scenario = dict(prepared, id=fight + '/full-rest')
                expected = plan['supplemental_rest_results']['input_sha256_by_fight'][fight]
                if fingerprint(scenario_for(scenario, pret)) != expected:
                    raise ValueError('Supplemental rest inputs changed for ' + fight)
            prepared_result = measured(row, 'full rest, seed ' + ('12' if fight in extra else '11'))
        result.append({'id': fight, 'recorded': case, 'prepared': prepared,
                       'strategy': strategy, 'requirement': requirement,
                       'pending_full_hp_test': fight in plan['pending_full_hp_tests'],
                       'results': {'recorded': recorded, 'prepared': prepared_result}})
    return {'family_size': family, 'fights': result}


def ranking(rows, variant):
    return sorted(rows, key=lambda row: row['results'][variant]['probability'])[:10]


def conditions_markdown(report, pret, plan):
    rows = report['fights']
    lines = ['# Pokeguy FRLG: fight preconditions and two variants', '',
        'The recorded variant uses the sourced speedrun entry. The prepared variant requires a full rest '
        'before six named fights; all other entries remain identical to recorded. These are independent '
        'battle contracts, not a newly reconciled continuous route.', '',
        'A full rest means maximum HP, clear status, and maximum PP on all known moves. It does not add '
        'battle items or change level, EXP, IVs, EVs, moves, held items, badges, or strategy. '
        'Shopping/pickup planning and propagation of changed outcomes into later entries remain separate work.', '',
        'Both variants use the latest measured C2 policy for the twelve setup fights. That implementation '
        'is pinned to [PR #37](https://github.com/dayfine/PokemonSimulation/pull/37) at `' +
        plan['complex_results']['revision'] + '`. Other measurements retain their stated policy and seed. '
        'Recorded entry does not mean a replay of Pokeguy\'s button presses.', '',
        'Speed-EV diagnostics and Dig substitutions are excluded from these rankings. In particular, '
        'Surge retains raw Speed 47. Later C healing candidates retain their tested HP until rerun.', '',
        'Intervals are recomputed at 95% simultaneous coverage over all {} measured candidate arms '
        'and all sampling looks. Some intervals exceed the original precision target after combining '
        'experiments. Close point-estimate ranks are not established differences. All-win samples '
        'do not establish a 100% true win probability.'.format(report['family_size']), '',
        '## Required healing stops', '',
        '| Fight | Recorded HP → prepared HP | Requirement before entry |', '|---|---:|---|']
    for row in rows:
        if row['requirement']:
            a, b = row['recorded']['player'], row['prepared']['player']
            lines.append('| {} | {} → {}/{} | Full HP + full PP + clear status. {} |'.format(
                row['id'], a['hp'], b['hp'], b['stats']['hp'], row['requirement']['opportunity']))
    for variant in ('prepared', 'recorded'):
        lines += ['', '## Top ten: ' + variant + ' variant', '',
                  '| Rank | Fight | Tier | Entry HP | Preparation | Win rate | Simultaneous interval |',
                  '|---:|---|---|---:|---|---:|---:|']
        for rank, row in enumerate(ranking(rows, variant), 1):
            p, r = row[variant]['player'], row['results'][variant]
            label = 'Full HP + PP' if variant == 'prepared' and row['requirement'] else 'Recorded entry'
            lines.append('| {} | {} | {} | {}/{} | {} | {:.1%} | {:.1%}–{:.1%} |'.format(
                rank, row['id'], row['strategy']['tier'], p['hp'], p['stats']['hp'], label,
                r['probability'], *r['bounds']))
    lines += ['', '## Contract for every fight', '',
        'Stats are raw summary stats, before badge boosts, in HP/Atk/Def/SpA/SpD/Spe order. '
        'EVs are earned totals; the recorded summary stats remain authoritative until live recalculation. '
        'Each trainer ID resolves its full party, moves, items and AI flags in '
        '`data/runs/pokeguy-leafgreen-15934/battle-reference.json`. '
        'Solo lead, no player switching, and the NPC/engine approximations of the benchmark still apply.', '',
        'Each entry starts a fresh battle with zero stat stages, no existing volatile conditions '
        'or field effects, and the opposing party at full HP and PP. Badge boosts and Torrent '
        'are applied by the engine. EXP/EV awards and level-up learning occur after actual knockouts. '
        'The lab rival also enables the modeled tutorial behavior.', '',
        'Shared starter profile: Mild, IVs HP28/Atk25/Def16/SpA31/SpD21/Spe27, male, Torrent. '
        'Every bag below is the complete supported battle-consumable bag, not a minimum shopping list. '
        'Unlisted battle items are unavailable; no items are silently replenished by resting.', '']
    order = ('hp', 'atk', 'def', 'spa', 'spd', 'spe')
    for row in rows:
        case, player = row['recorded'], row['recorded']['player']
        trainer = pret['trainers'][case['trainer']]
        bag = ', '.join('{} ×{}'.format(k, v) for k, v in sorted(case['bag'].items()) if v) or 'none'
        party = ', '.join('{} Lv{}'.format(m['species'], m['level']) for m in trainer['party'])
        lines += ['### ' + row['id'], '',
            'Opponent: `{}` — {}.'.format(case['trainer'], party), '',
            '{} Lv{}; EXP {}; raw stats {}; earned EVs {}; status {}; held item {}; badges {}.'.format(
                player['species'], player['level'], case['progression']['exp'],
                '/'.join(str(player['stats'][s]) for s in order),
                '/'.join(str(case['progression']['evs'][s]) for s in order),
                player['status'] or 'clear', player['held_item'] or 'none', ', '.join(case['badges']) or 'none'), '',
            'Battle bag: ' + bag + '.', '',
            'Player strategy: {}. Policy: `{}`.'.format(row['strategy']['tier'], row['strategy']['policy'])]
        if 'planning_goals' in row['strategy']:
            lines += ['Setup goals: `' + json.dumps(row['strategy']['planning_goals'], sort_keys=True) + '`.']
        if row['pending_full_hp_test']:
            lines += ['Full-heal comparison pending: retain this tested HP/setup condition for both variants.']
        lines += ['', '| Variant | Entry HP | Exact moves and remaining PP | Win sample |', '|---|---:|---|---:|']
        for variant in ('recorded', 'prepared'):
            p, r = row[variant]['player'], row['results'][variant]
            moves = ', '.join('{}: {}'.format(m['name'], m['pp']) for m in p['moves'])
            lines.append('| {} | {}/{} | {} | {}/{} ({:.1%}) |'.format(
                variant, p['hp'], p['stats']['hp'], moves, r['wins'], r['trials'], r['probability']))
        lines += ['', 'Result source: recorded — {}; prepared — {}.'.format(
            row['results']['recorded']['source'], row['results']['prepared']['source']), '']
    lines += ['## Reproduce', '', '```sh', 'PYTHONPATH=src python3 -m pokesim.cli.frlg_conditions', '```', '',
        'The preparation plan contains pinned C2 and supplemental rest counters. The latter used seed 12: '
        'Sammy 158/160, Liam 120/120, Brock 120/120. No top-ten reordering is presented as new simulation. '
        'The other results come from the existing original and preparation benchmark reports.', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=REPO / 'docs/battles/pokeguy-conditions.md')
    args = parser.parse_args(argv)
    read = lambda name: json.loads((DATA / (name + '.json')).read_text())
    pret, reference, plan = read('battle-reference'), read('reference'), read('battle-preparation')
    inputs = trainer_cases(read('events'), reference, read('moves'), read('state-history'), pret)
    baseline = json.loads((REPO / 'docs/battles/pokeguy-trainers.json').read_text())
    prep = json.loads((REPO / 'docs/battles/pokeguy-preparation.json').read_text())
    report = resolve_conditions(inputs, reference, pret, baseline, prep, plan)
    args.out.write_text(conditions_markdown(report, pret, plan))
    for row in ranking(report['fights'], 'prepared'):
        print('{}: {:.1%} ({})'.format(row['id'], row['results']['prepared']['probability'],
                                     'full rest' if row['requirement'] else 'recorded entry'))


if __name__ == '__main__':
    main()

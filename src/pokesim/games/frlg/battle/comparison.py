"""Compare fresh C trials with the historical baseline, reusing the other 57.

The retained cohort is selected after inspecting the baseline. Recompute
its intervals with half the error budget across ALL original cases, then
allocate the other half to fresh C trials. No retained fight needs rerunning.
The ranking combines historical retained-policy estimates and updated C;
it is not a fresh measurement of B on unobserved battle states.
"""

import copy

from pokesim.games.frlg.battle.run import summarize
from pokesim.games.frlg.battle.sampling import confidence_sequence
from pokesim.games.frlg.progression.ledger import fingerprint


def compare_strategies(baseline, updated):
    old = {r['id']: r for r in baseline['results']}
    fresh = {r['id']: r for r in summarize(updated)['results']}
    if not fresh or set(fresh) - set(old):
        raise ValueError('Updated fights must be a nonempty subset of the baseline')
    if updated['seed'] == baseline['seed']:
        raise ValueError('Use a fresh validation seed after developing the strategy')
    if any(r['player_strategy'] != 'C' for r in fresh.values()):
        raise ValueError('Only opted-in C fights belong in this comparison')
    if updated['run_inputs']['source_sha256'] != baseline['run_inputs']['source_sha256']:
        raise ValueError('Recorded inputs changed; retained baseline cannot be reused')
    if updated['pret_snapshot_sha256'] != baseline['pret_snapshot_sha256']:
        raise ValueError('NPC snapshot changed; isolate player-strategy changes')
    if updated['sampling']['alpha_per_case'] > .025 / len(fresh) + 1e-15:
        raise ValueError('Fresh C intervals must reserve half the confidence error budget')
    original_bounds = {name: confidence_sequence(row['wins'], row['battles'], .025 / len(old))
                       for name, row in old.items()}
    rows, changes = [], []
    for name, before in old.items():
        if name in fresh:
            after = fresh[name]
            bounds = after['confidence_sequence']['bounds']
            delta_bounds = [bounds[0] - original_bounds[name][1], bounds[1] - original_bounds[name][0]]
            changes.append({'id': name, 'old_probability': before['win_probability'],
                'new_probability': after['win_probability'], 'delta_percentage_points': 100 * (after['win_probability'] - before['win_probability']),
                'old_bounds': original_bounds[name], 'new_bounds': bounds,
                'delta_percentage_point_bounds': [100 * v for v in delta_bounds],
                'comparison': 'improved' if delta_bounds[0] > 0 else 'regressed' if delta_bounds[1] < 0 else 'unresolved',
                'old_trials': before['battles'], 'new_trials': after['battles'],
                'stop_reason': after['confidence_sequence']['stop_reason'],
                'mean_items_used': after['mean_items_used'], 'planning_goals': after['planning_goals'],
                'example_seeds': after['example_seeds']})
            row, tier, origin = after, 'C', 'fresh C trials'
        else:
            row = copy.deepcopy(before)
            row['confidence_sequence']['bounds'] = original_bounds[name]
            tier, origin = ('B' if row['mean_items_used'] else 'A'), 'retained baseline'
        rows.append({'id': name, 'win_probability': row['win_probability'],
            'bounds': row['confidence_sequence']['bounds'], 'trials': row['battles'],
            'tier': tier, 'result_origin': origin, 'starting_state': row['starting_state']})
    return {'format': 'pokesim-frlg-strategy-comparison/1',
        'baseline_summary_fingerprint': fingerprint(baseline), 'baseline_policy': baseline['policy'],
        'updated_policy': updated['policy'], 'validation_seed': updated['seed'],
        'updated_implementation_sha256': updated['implementation_sha256'],
        'updated_run_inputs': updated['run_inputs'], 'pret_snapshot_sha256': updated['pret_snapshot_sha256'],
        'confidence': {'simultaneous_all_retained_and_updated': .95,
            'original_family_size': len(old), 'original_alpha_per_case': .025 / len(old),
            'updated_alpha_per_case': updated['sampling']['alpha_per_case'],
            'note': 'Original bounds recomputed with 97.5% family coverage; fresh C family has at least 97.5%. The union bound covers the combined ranking and change intervals at 95%, including data-dependent C selection. Retained bounds may exceed the old 10-point precision target.'},
        'retained_case_ids': [name for name in old if name not in fresh],
        'new_trials': sum(r['battles'] for r in fresh.values()),
        'turn_limit_outcomes': sum(r['outcomes'].get('turn_limit', 0) for r in fresh.values()),
        'changes': changes, 'top_ten': sorted(rows, key=lambda r: r['win_probability'])[:10]}


def comparison_markdown(report):
    lines = ['# Type C strategy comparison', '',
        'Only the {} opted-in C fights were rerun. The other {} retain their published baseline point estimates. '.format(len(report['changes']), len(report['retained_case_ids'])) + 
        'That retained cohort is historical-policy data, not a new probability measurement of the refactored B controller.', '',
        'The fresh validation uses seed {} and {:,} trials. The original 69-fight table remains unchanged. '
        'The NPC model and recorded player inputs are unchanged.'.format(report['validation_seed'], report['new_trials']), '',
        '## Old and new C estimates', '',
        'Changes are percentage points. “Unresolved” means the simultaneous change interval includes zero; '
        'a larger point estimate alone does not establish improvement.', '',
        '| Fight | Baseline | New C | Change | New trials | Evidence |',
        '|---|---:|---:|---:|---:|---|']
    for r in report['changes']:
        lines.append('| {} | {:.1%} | {:.1%} | {:+.1f} pp | {} | {} |'.format(
            r['id'], r['old_probability'], r['new_probability'], r['delta_percentage_points'], r['new_trials'], r['comparison']))
    lines += ['', '## New top ten by point estimate', '',
        '| Rank | Fight | Win rate | Simultaneous interval | Tier | Data |',
        '|---:|---|---:|---:|---|---|']
    for rank, r in enumerate(report['top_ten'], 1):
        lines.append('| {} | {} | {:.1%} | {:.1%}–{:.1%} | {} | {} |'.format(
            rank, r['id'], r['win_probability'], *r['bounds'], r['tier'], r['result_origin']))
    lines += ['', '## Interpretation and reproduction', '',
        'The combined intervals and change intervals have at least 95% simultaneous coverage under the model. '
        'Half the error budget covers all original cases before retaining any subset; half covers the fresh C trials. '
        'Retained bounds were widened slightly without rerunning those fights. Only the fresh C intervals are sampled '
        'to the new 10-percentage-point width target.', '',
        'These are conditional solo-lead estimates, not cartridge measurements or a route completion probability. '
        'The original NPC replacement approximation remains, including possible departures from the video’s enemy order. '
        'Player switching is not implemented.', '',
        '```sh', 'PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles --complex-only --seed 4 --out /tmp/pokeguy-c.json',
        '```', '', 'The [machine-readable comparison](pokeguy-c-comparison.json) records bounds, goals, item use, '
        'seeds and provenance. See [strategy layers](player-strategies.md) and the [historical baseline](pokeguy-trainers.md).', '']
    return '\n'.join(lines)

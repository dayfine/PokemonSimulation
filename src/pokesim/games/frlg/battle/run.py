"""Build independent trainer experiments from a reconciled FRLG run ledger.

Each fight starts at the recorded entry state. Monte Carlo outcomes do not
rewrite later snapshots: these are conditional per-battle rates, not a run
completion probability or a replay of the recorded winning button presses.
"""

import copy
import hashlib

from pokesim.games.frlg.battle.engine import REPO
from pokesim.games.frlg.battle.npc_ai import move_id
from pokesim.games.frlg.battle.schema import ITEMS
from pokesim.games.frlg.progression.ledger import audit, fingerprint
from pokesim.games.frlg.progression.states import reconstruct_states


def implementation_hashes():
    """Pin the local simulator and reconstruction code alongside source data."""
    paths = [p for p in (REPO / 'src/pokesim/games/frlg').rglob('*.py') if not p.name.startswith('test_')]
    paths += list((REPO / 'engines/frlg-showdown').glob('*.cjs'))
    paths += [REPO / 'src/pokesim/cli/frlg_run_battles.py']
    return {str(p.relative_to(REPO)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def configure_strategies(cases, config):
    """B is default; only explicitly enabled fights use tier C's goal planner."""
    if config.get('format') != 'pokesim-frlg-player-strategies/1' or config.get('default') != 'recovery':
        raise ValueError('Unsupported player strategy configuration')
    unknown = set(config['fights']) - {c['id'] for c in cases}
    if unknown:
        raise ValueError('Strategy configuration names unknown fights: ' + ', '.join(sorted(unknown)))
    result = copy.deepcopy(cases)
    for case in result:
        settings = config['fights'].get(case['id'], {})
        case['enable_complex_planning'] = settings.get('enable_complex_planning', False)
        if 'planning_goals' in settings:
            case['planning_goals'] = copy.deepcopy(settings['planning_goals'])
    return result


def trainer_cases(route, reference, moves, history, battle_reference):
    """Use sourced HP, raw stats, PP, badges and inventory for every trainer."""
    states = reconstruct_states(route, reference, moves, history)
    exp = {r['event']: r for r in audit(route, reference, 'observed_wild_wins')['timeline']}
    decisions = {move_id(d['move']): {k: d[k] for k in ('action', 'replaces') if k in d}
                 for d in moves['decisions'] if d['method'] == 'level_up'}
    species = {move_id(k): v for k, v in reference['species'].items()}
    cases = []
    for entry in states['battles']:
        if entry['kind'] != 'trainer_battle':
            continue
        start = entry['starting_state']
        player = {k: copy.deepcopy(start[k]) for k in
                  ('species', 'level', 'hp', 'stats', 'nature', 'ivs', 'gender', 'ability', 'held_item', 'status')}
        player['moves'] = [{'name': name, 'pp': pp} for name, pp in start['pp'].items()]
        cases.append({'id': entry['event'], 'trainer': entry['trainer'], 'video_start': entry['video_start'],
            'tutorial': entry['event'] == 'lab-rival',
            'player': player, 'badges': start['badges'],
            'bag': {move_id(k): v for k, v in start['battle_bag'].items() if move_id(k) in ITEMS},
            'progression': {'exp': exp[entry['event']]['exp_before'], 'evs': start['evs_earned'],
                'ivs': start['ivs'], 'nature': reference['natures'][start['nature']],
                'thresholds': reference['growth_curves'][reference['species'][start['species']]['growth_rate']],
                'species': species, 'decisions': decisions, 'badges': start['badges']}})
    if {c['trainer'] for c in cases} != set(battle_reference['trainers']):
        raise ValueError('Battle reference must cover exactly the route trainers')
    return {'cases': cases, 'source_sha256': {name: fingerprint(value) for name, value in
        (('route', route), ('progression_reference', reference), ('moves', moves), ('state_history', history))},
        'checks_passed': len(states['checks_passed'])}


def summarize(report):
    """Small review artifact; full generated reports retain inputs and traces."""
    result = {k: v for k, v in report.items() if k not in ('results', 'progression_reference')}
    result['format'] = 'pokesim-frlg-run-summary/1'
    rows = []
    for battle in report['results']:
        row = {k: battle[k] for k in ('id', 'battles', 'maximum_battles', 'wins', 'win_probability', 'outcomes',
            'confidence_sequence', 'mean_turns', 'mean_items_used', 'losses_by_foe')}
        player = battle['inputs']['player']
        row['starting_state'] = {k: player[k] for k in ('species', 'level', 'hp')}
        row['starting_state']['max_hp'] = player['stats']['hp']
        row['video_start'] = battle['inputs']['video_start']
        row['player_strategy'] = 'C' if battle['inputs'].get('enable_complex_planning', False) else 'B'
        if row['player_strategy'] == 'C':
            row['planning_goals'] = battle['inputs'].get('planning_goals', {})
        row['example_seeds'] = {outcome: sample['seed'] for outcome, sample in battle['examples'].items()}
        rows.append(row)
    result['results'] = rows
    return result


def results_markdown(summary):
    """Readable conditional rates with simultaneous uncertainty and sample cost."""
    rows = summary['results']
    total = sum(r['battles'] for r in rows)
    cap = max(r['maximum_battles'] for r in rows)
    confidence = summary['sampling']['confidence_all_cases_all_looks']
    width = summary['sampling']['target_interval_width']
    policy = summary['policy'].split('progression cases: ')[-1]
    lines = ['# Pokeguy trainer win-rate estimates', '',
        'All 69 trainer fights, each reset to its recorded entry state. These are model estimates for our '
        '`{}` policy, not measurements of Pokeguy’s play or a whole-run completion probability.'.format(policy), '',
        'Seed {}; {} trials in total. Intervals have {:.0%} simultaneous coverage across all 69 battles '
        'and all adaptive sampling looks, conditional on the model. The target is a total interval width '
        'of {:.0f} percentage points; the per-case cap is {:,} trials and the turn limit is {}.'.format(
            summary['seed'], total, confidence, width * 100, cap, summary['turn_limit']), '',
        'See [method, inputs and limitations](pokeguy-benchmark.md), '
        '[machine-readable summary](pokeguy-trainers.json), and '
        '[starting states](../progression/pokeguy-states.md). An all-win sample still has a lower bound below 100%.', '',
        '| Battle | Level | HP on entry | Wins / trials | Estimate | Simultaneous interval | Stop |',
        '|---|---:|---:|---:|---:|---:|---|']
    for row in rows:
        start = row['starting_state']
        low, high = row['confidence_sequence']['bounds']
        lines.append('| [{}](https://www.youtube.com/watch?v=CbfjWuRWH10&t={}) | {} | {}/{} | {}/{} | {:.1%} | {:.1%}–{:.1%} | {} |'.format(
            row['id'], row['video_start'], start['level'], start['hp'], start['max_hp'], row['wins'], row['battles'],
            row['win_probability'], low, high, row['confidence_sequence']['stop_reason']))
    limits = sum(r['outcomes'].get('turn_limit', 0) for r in rows)
    lines += ['', '{} turn-limit outcomes counted as non-wins. Wild/scripted fights, captures and escapes '
        'are outside this trainer report. The selected profile uses Mild and Attack IV25; engine/AI and input '
        'uncertainty are not included in the sampling intervals.'.format(limits), '']
    return '\n'.join(lines)

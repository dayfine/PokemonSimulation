"""Compare early FRLG preparation choices without changing the recorded run.

PYTHONPATH=src python3 -m pokesim.cli.frlg_preparation --out /tmp/frlg-preparation.json
The full output contains exact scenarios and example traces; .summary.json is compact.
"""

import argparse
import copy
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from pokesim.cli.frlg_run_battles import DATA, evaluate_case
from pokesim.games.frlg.battle.run import implementation_hashes, trainer_cases
from pokesim.games.frlg.progression.stats import summary_stats
from pokesim.games.frlg.progression.ledger import fingerprint


def preparation_cases(cases, reference):
    """Explicit counterfactuals; keep B fixed and each fight independent."""
    originals = {c['id']: c for c in cases}
    result = []
    menu = {
        'pewter-liam': ['recorded', 'full-hp', 'carry-potion', 'pre-potion', 'full-hp-carry-potion'],
        'brock': ['recorded', 'full-hp', 'carry-potion', 'pre-potion', 'full-hp-carry-potion'],
        'cerulean-rival': ['recorded', 'full-rest'],
        'ssanne-rival': ['recorded', 'full-hp', 'full-rest', 'dig', 'speed', 'dig-speed'],
        'surge': ['recorded', 'dig', 'speed', 'dig-speed'],
        'forest-sammy': ['recorded', 'full-hp', 'carry-potion', 'speed'],
        'mtmoon-josh': ['recorded', 'full-rest'],
    }
    speed_targets = {'forest-sammy': 15, 'ssanne-rival': 48, 'surge': 54}
    for fight, variants in menu.items():
        for variant in variants:
            case = copy.deepcopy(originals[fight])
            case['id'] = fight + '/' + variant
            case['preparation'] = {'fight': fight, 'variant': variant}
            player = case['player']
            if variant in ('full-hp', 'full-rest', 'full-hp-carry-potion'):
                player['hp'] = player['stats']['hp']
            if variant == 'full-rest':
                player['status'] = ''
                for move in player['moves']:
                    move['pp'] = reference['move_pp'][move['name']]
            if variant in ('carry-potion', 'full-hp-carry-potion'):
                case['bag']['potion'] = case['bag'].get('potion', 0) + 1
            if variant == 'pre-potion':
                player['hp'] = min(player['stats']['hp'], player['hp'] + 20)
                case['preparation']['potions_used_before_battle'] = 1
            if variant in ('dig', 'dig-speed'):
                # TM28 is obtainable after the Cerulean rival, before these fights.
                for move in player['moves']:
                    if move['name'] == 'WATER_GUN':
                        move.update(name='DIG', pp=10)
                        break
                else:
                    raise ValueError('Expected Water Gun slot')
            if variant in ('speed', 'dig-speed'):
                target = speed_targets[fight]
                progression = case['progression']
                base = reference['species'][player['species']]['base_stats']
                original_ev = progression['evs']['spe']
                for ev in range(original_ev, 256):
                    progression['evs']['spe'] = ev
                    stats = summary_stats(base, player['level'], progression['ivs'],
                                          progression['evs'], progression['nature'])
                    if stats['spe'] >= target:
                        break
                else:
                    raise ValueError('Speed target cannot be reached at this level')
                player['stats']['spe'] = stats['spe']
                case['preparation'].update(speed_ev_before=original_ev, speed_ev_after=ev,
                    diagnostic='Speed EVs changed at fixed EXP; a legal training route has not been planned.')
            result.append(case)
    return result


def compact_report(reports, cases, seed):
    rows = []
    for case in cases:
        row = reports[case['id']]['results'][0]
        rows.append(dict(case['preparation'], starting_hp=case['player']['hp'],
            maximum_hp=case['player']['stats']['hp'], raw_speed=case['player']['stats']['spe'],
            moves=case['player']['moves'], bag=case['bag'],
            **{k: row[k] for k in ('battles', 'wins', 'win_probability', 'confidence_sequence',
                                 'mean_items_used', 'losses_by_foe', 'outcomes')}))
    first = reports[cases[0]['id']]
    return {'format': 'pokesim-frlg-preparation/1', 'seed': seed, 'family_size': len(cases), 'confidence_all_variants': .95,
        'target_interval_width': .10, 'implementation_sha256': implementation_hashes(),
        'scenario_sha256': fingerprint(cases),
        'experiment_implementation_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'pret_source': first['pret_source'], 'pret_snapshot_sha256': first['pret_snapshot_sha256'],
        'engine': first['engine'], 'engine_lock_sha256': first['engine_lock_sha256'],
        'policy': first['policy'],
        'conditioning': 'Independent entry-state scenarios using unchanged B recovery policy. '
            'Full HP preserves recorded PP; full rest restores HP, status and PP. '
            'Speed variants are diagnostics, not a planned legal training route. '
            'Intervals cover this experiment, not previous benchmarks or model error.',
        'results': rows}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3)
    parser.add_argument('--seed', type=int, default=11)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error('--workers must be positive')
    read = lambda name: json.loads((DATA / (name + '.json')).read_text())
    pret, reference = read('battle-reference'), read('reference')
    inputs = trainer_cases(read('events'), reference, read('moves'), read('state-history'), pret)
    cases = preparation_cases(inputs['cases'], reference)
    reports = {}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=min(args.workers, len(cases))) as pool:
        jobs = {pool.submit(evaluate_case, c, pret, 3000, args.seed, .10, len(cases)): c['id']
                for c in cases}
        for future in as_completed(jobs):
            case_id = jobs[future]
            reports[case_id] = future.result()
            row = reports[case_id]['results'][0]
            print('{}: {}/{} ({:.1%})'.format(case_id, row['wins'], row['battles'],
                                           row['win_probability']), flush=True)
            checkpoint = args.out.with_suffix('.checkpoint.json')
            temporary = checkpoint.with_suffix('.tmp')
            temporary.write_text(json.dumps(reports) + '\n')
            temporary.replace(checkpoint)
    args.out.write_text(json.dumps({'seed': args.seed, 'reports': reports}, indent=2) + '\n')
    args.out.with_suffix('.summary.json').write_text(
        json.dumps(compact_report(reports, cases, args.seed), indent=2) + '\n')


if __name__ == '__main__':
    main()

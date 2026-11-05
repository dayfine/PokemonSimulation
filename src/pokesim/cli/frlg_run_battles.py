"""Estimate conditional win rates for all trainer battles in Pokeguy's FRLG run.

PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles --out /tmp/pokeguy-battles.json
"""

import argparse
import json
from pathlib import Path
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

from pokesim.games.frlg.battle.benchmark import evaluate
from pokesim.games.frlg.battle.engine import REPO
from pokesim.games.frlg.battle.run import trainer_cases, summarize, results_markdown, implementation_hashes, configure_strategies
from pokesim.games.frlg.progression.ledger import fingerprint
from pokesim.games.frlg.battle.sampling import AdaptiveSampling
from pokesim.games.frlg.battle.comparison import compare_strategies, comparison_markdown

DATA = REPO / 'data/runs/pokeguy-leafgreen-15934'


def evaluate_case(case, pret, maximum, seed, width, family, confidence=.95):
    """Independent worker; retain the full family's confidence correction."""
    return evaluate([case], pret, battles=maximum, seed=seed, turn_limit=300,
        sampling=AdaptiveSampling(width=width, confidence=confidence), family_size=family)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DATA)
    parser.add_argument('--case', action='append')
    parser.add_argument('--battles', type=int, default=3000, help='Maximum trials per battle')
    parser.add_argument('--interval-width', type=float, default=.10)
    parser.add_argument('--seed', type=int, help='Default 1, or held-out validation seed 4 for --complex-only')
    parser.add_argument('--complex-only', action='store_true', help='Rerun opted-in C fights, reserving confidence budget for retained baseline data')
    parser.add_argument('--workers', type=int, default=3, help='Independent Python/Node workers')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error('--workers must be positive')
    if args.battles < 20 or not 0 < args.interval_width < 1:
        parser.error('Use at least 20 trials and an interval width between zero and one')
    read = lambda name: json.loads((args.data / (name + '.json')).read_text())
    pret = read('battle-reference')
    inputs = trainer_cases(read('events'), read('reference'), read('moves'), read('state-history'), pret)
    cases = inputs.pop('cases')
    configuration = args.data / 'strategies.json'
    if configuration.exists():
        config = json.loads(configuration.read_text())
        cases = configure_strategies(cases, config)
        inputs['strategy_config_sha256'] = fingerprint(config)
    if args.complex_only:
        cases = [c for c in cases if c.get('enable_complex_planning', False)]
        if not cases:
            parser.error('No fights explicitly enable complex planning')
    complex_family = len(cases)
    if args.case:
        unknown = set(args.case) - {c['id'] for c in cases}
        if unknown:
            parser.error('Unknown case: ' + ', '.join(sorted(unknown)))
        cases = [c for c in cases if c['id'] in args.case]
    seed = args.seed if args.seed is not None else (4 if args.complex_only else 1)
    # Reserve half the confidence error budget for the retained original
    # benchmark. Its intervals can be recomputed without rerunning those fights.
    family = complex_family if args.complex_only else len(cases)
    confidence = .975 if args.complex_only else .95
    reports = {}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=min(args.workers, len(cases))) as pool:
        jobs = {pool.submit(evaluate_case, c, pret, args.battles, seed, args.interval_width, family, confidence): c['id'] for c in cases}
        for future in as_completed(jobs):
            result = future.result()
            reports[jobs[future]] = result
            row = result['results'][0]
            print('{}: {}/{} wins ({}/{})'.format(row['id'], row['wins'], row['battles'], len(reports), len(cases)), file=sys.stderr)
            checkpoint = args.out.with_suffix('.checkpoint.json')
            temporary = checkpoint.with_suffix('.tmp')
            temporary.write_text(json.dumps({'partial': True, 'family_size': family, 'seed': seed,
                'run_inputs': inputs, 'completed': list(reports), 'results': [r['results'][0] for r in reports.values()]}) + '\n')
            temporary.replace(checkpoint)
    report = reports[cases[0]['id']]
    report['results'] = [reports[c['id']]['results'][0] for c in cases]
    report['run_inputs'] = inputs
    report['implementation_sha256'] = implementation_hashes()
    report['conditioning'] = 'Each battle starts independently at its recorded entry state; no whole-run completion probability is claimed.'
    # The same large progression reference applies to every case.
    report['progression_reference'] = cases[0]['progression']['species']
    for row in report['results']:
        row['inputs']['progression'].pop('species')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    summary = summarize(report)
    args.out.with_suffix('.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    if len(cases) == 69:
        args.out.with_suffix('.md').write_text(results_markdown(summary))
    if args.complex_only and not args.case:
        baseline = json.loads((REPO / 'docs/battles/pokeguy-trainers.json').read_text())
        compared = compare_strategies(baseline, report)
        args.out.with_suffix('.comparison.json').write_text(json.dumps(compared, indent=2) + '\n')
        args.out.with_suffix('.comparison.md').write_text(comparison_markdown(compared))
    for row in report['results']:
        low, high = row['confidence_sequence']['bounds']
        print('{}: {}/{} wins; {:.1%}–{:.1%}; {}'.format(row['id'], row['wins'], row['battles'],
            low, high, row['confidence_sequence']['stop_reason']))
    return 0


if __name__ == '__main__':
    main()

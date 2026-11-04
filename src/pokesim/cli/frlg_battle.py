"""Run the four FRLG trainer benchmarks using Python policies and Showdown.

    npm ci --omit=optional --prefix engines/frlg-showdown
    PYTHONPATH=src python3 -m pokesim.cli.frlg_battle --battles 1000 --out /tmp/frlg.json

Prints one win-rate line per case and writes a JSON report with confidence
intervals, exact inputs, model limitations, and example win/loss traces.
"""

import argparse
import json
from pathlib import Path
import sys

from pokesim.games.frlg.battle.benchmark import evaluate
from pokesim.games.frlg.battle.engine import REPO
from pokesim.games.frlg.battle.sampling import AdaptiveSampling

DATA = REPO / "data" / "games" / "frlg" / "battles"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DATA / "cases.json")
    parser.add_argument("--pret", type=Path, default=DATA / "pret.json")
    parser.add_argument("--case", action="append", help="Case ID; repeat to select several")
    parser.add_argument("--battles", type=int, help="Fixed count or adaptive cap; default 1000 fixed / 2000 adaptive")
    parser.add_argument("--adaptive", action="store_true", help="Stop when an anytime-valid interval is sufficiently narrow")
    parser.add_argument("--interval-width", type=float, default=0.10, help="Target total interval width (adaptive only)")
    parser.add_argument("--confidence", type=float, default=0.95, help="Simultaneous confidence across cases and interim looks")
    parser.add_argument("--min-battles", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--turn-limit", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if not args.adaptive and (args.interval_width, args.confidence, args.min_battles, args.batch_size) != (0.10, 0.95, 20, 20):
        parser.error("Sampling width/confidence/minimum/batch options require --adaptive")
    cases = json.loads(args.cases.read_text())["cases"]
    if args.case:
        unknown = set(args.case) - {c["id"] for c in cases}
        if unknown:
            parser.error("Unknown case: " + ", ".join(sorted(unknown)))
        cases = [c for c in cases if c["id"] in args.case]
    try:
        sampling = AdaptiveSampling(args.interval_width, args.confidence, args.min_battles, args.batch_size) if args.adaptive else None
        maximum = args.battles if args.battles is not None else (2000 if args.adaptive else 1000)
        report = evaluate(cases, json.loads(args.pret.read_text()), maximum, args.seed, args.turn_limit,
            sampling=sampling,
            progress=lambda name, done, total: print("{}: {}/{}".format(name, done, total), file=sys.stderr))
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    for result in report["results"]:
        sequential = result.get("confidence_sequence")
        low, high = sequential["bounds"] if sequential else result["wilson_95"]
        label = ("{:.0%} simultaneous CS; {}".format(
            report["sampling"]["confidence_all_cases_all_looks"], sequential["stop_reason"])) if sequential else "95% CI"
        print("{}: {}/{} wins ({:.1%}; {} {:.1%}–{:.1%})".format(
            result["id"], result["wins"], result["battles"], result["win_probability"], label, low, high))
    return 0


if __name__ == "__main__":
    main()

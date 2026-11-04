"""Run the four FRLG trainer benchmarks using Python policies and Showdown.

    npm ci --omit=optional --prefix engines/frlg-showdown
    PYTHONPATH=src python3 -m pokesim.cli.battle --battles 1000 --out /tmp/frlg.json

Prints one win-rate line per case and writes a JSON report with confidence
intervals, exact inputs, model limitations, and example win/loss traces.
"""

import argparse
import json
from pathlib import Path
import sys

from pokesim.battle.benchmark import evaluate
from pokesim.battle.engine import REPO

DATA = REPO / "data" / "games" / "frlg" / "battles"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DATA / "cases.json")
    parser.add_argument("--pret", type=Path, default=DATA / "pret.json")
    parser.add_argument("--case", action="append", help="Case ID; repeat to select several")
    parser.add_argument("--battles", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--turn-limit", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    cases = json.loads(args.cases.read_text())["cases"]
    if args.case:
        unknown = set(args.case) - {c["id"] for c in cases}
        if unknown:
            parser.error("Unknown case: " + ", ".join(sorted(unknown)))
        cases = [c for c in cases if c["id"] in args.case]
    try:
        report = evaluate(cases, json.loads(args.pret.read_text()), args.battles, args.seed, args.turn_limit,
            progress=lambda name, done, total: print("{}: {}/{}".format(name, done, total), file=sys.stderr))
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    for result in report["results"]:
        low, high = result["wilson_95"]
        print("{}: {}/{} wins ({:.1%}; 95% CI {:.1%}–{:.1%})".format(
            result["id"], result["wins"], result["battles"], result["win_probability"], low, high))
    return 0


if __name__ == "__main__":
    main()

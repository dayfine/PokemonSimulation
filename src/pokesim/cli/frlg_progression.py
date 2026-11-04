"""Reproduce Pokeguy's full-route EXP audit from local trainer/species data.

    PYTHONPATH=src python3 -m pokesim.cli.frlg_progression --out /tmp/exp-audit

Writes report.json and report.md, including after-each-foe EXP and after-each-
battle levels in flee-all-wild mode and observed-wild-wins control mode.
"""

import argparse
import json
from pathlib import Path

from pokesim.games.frlg.progression.ledger import compare, markdown_report

DATA = Path(__file__).resolve().parents[3] / "data" / "runs" / "pokeguy-leafgreen-15934"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", type=Path, default=DATA / "events.json")
    parser.add_argument("--reference", type=Path, default=DATA / "reference.json")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = compare(json.loads(args.route.read_text()), json.loads(args.reference.read_text()))
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "report.md").write_text(markdown_report(report))
    for run in report["runs"]:
        print("{}: final Lv{}, {}/{} level checkpoints match; {} EXP discrepancies".format(run["mode"],
            run["final_level"], run["matching_levels"], run["level_checks"], len(run["exp_mismatches"])))
    return 0


if __name__ == "__main__":
    main()

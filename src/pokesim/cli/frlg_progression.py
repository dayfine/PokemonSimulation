"""Reproduce Pokeguy's full-route EXP audit from local trainer/species data.

    PYTHONPATH=src python3 -m pokesim.cli.frlg_progression --out /tmp/exp-audit

Writes report.json and report.md, including after-each-foe EXP and after-each-
battle levels in flee-all-wild mode and observed-wild-wins control mode.
For the bundled route it also writes moves.json and moves.md, reconstructing
the observed lead's moves before/after each battle and defeated opponent.
states.json and states.md reconcile player stats, HP/status, PP, and tracked
inventory on entry to each recorded encounter; they are not battle outcomes.
"""

import argparse
import json
from pathlib import Path

from pokesim.games.frlg.progression.ledger import compare, markdown_report
from pokesim.games.frlg.progression.moves import reconstruct_moves, moves_markdown
from pokesim.games.frlg.progression.states import reconstruct_states, states_markdown

DATA = Path(__file__).resolve().parents[3] / "data" / "runs" / "pokeguy-leafgreen-15934"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", type=Path, default=DATA / "events.json")
    parser.add_argument("--reference", type=Path, default=DATA / "reference.json")
    parser.add_argument("--moves", type=Path, help="Move decisions; defaults to moves.json for the bundled route")
    parser.add_argument("--state-history", type=Path, help="Recorded state events; defaults to state-history.json for the bundled route")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        route, reference = json.loads(args.route.read_text()), json.loads(args.reference.read_text())
        report = compare(route, reference)
        move_path = args.moves or (DATA / "moves.json" if args.route.resolve() == (DATA / "events.json").resolve() else None)
        moves = reconstruct_moves(route, reference, json.loads(move_path.read_text())) if move_path else None
        state_path = args.state_history or (DATA / "state-history.json" if args.route.resolve() == (DATA / "events.json").resolve() else None)
        if state_path and not move_path:
            raise ValueError("State reconstruction requires a matching --moves history")
        states = reconstruct_states(route, reference, json.loads(move_path.read_text()), json.loads(state_path.read_text())) if state_path else None
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.out / "report.md").write_text(markdown_report(report))
    if moves:
        (args.out / "moves.json").write_text(json.dumps(moves, indent=2) + "\n")
        (args.out / "moves.md").write_text(moves_markdown(moves))
    if states:
        (args.out / "states.json").write_text(json.dumps(states, indent=2) + "\n")
        (args.out / "states.md").write_text(states_markdown(states))
    for run in report["runs"]:
        print("{}: final Lv{}, {}/{} level checkpoints match; {} EXP discrepancies".format(run["mode"],
            run["final_level"], run["matching_levels"], run["level_checks"], len(run["exp_mismatches"])))
    return 0


if __name__ == "__main__":
    main()

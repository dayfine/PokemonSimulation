"""Reconstruct FRLG move membership from sourced learning/forgetting decisions.

This follows the recorded run, including its two wild wins. It does not
infer controller slots, PP, or decisions for the flee-all counterfactual.
"""

from collections import defaultdict

from pokesim.games.frlg.progression.ledger import audit, fingerprint, video_time


def reconstruct_moves(route, reference, history):
    """Carry moves through every battle, checking level-up offers against pret."""
    if history.get("format") != "pokesim-frlg-moves/1":
        raise ValueError("Unsupported move history format")
    run = audit(route, reference, "observed_wild_wins")
    events = {e["id"]: e for e in route["events"]}
    grouped, ids = defaultdict(list), set()
    for decision in history["decisions"]:
        when = decision["when"]
        event = events.get(when["event"])
        phase = when["at"]
        if not event or phase not in ("before", "after", "after_foe"):
            raise ValueError("Unknown move decision anchor")
        if phase == "after_foe":
            count = len(event["observed_party"]) if event["kind"] == "trainer_battle" else int(
                event["kind"] in ("wild_battle", "scripted_battle") and event["outcome"] == "defeated")
            if type(when.get("foe_index")) is not int or not 0 <= when["foe_index"] < count:
                raise ValueError("Invalid move decision foe index")
        if decision["id"] in ids or not decision.get("evidence"):
            raise ValueError("Duplicate or unsourced move decision")
        if decision["video_start"] > decision["video_end"]:
            raise ValueError("Invalid move decision video range")
        if phase == "before" and decision["video_end"] > event["video_start"]:
            raise ValueError("Move decision happens after its before anchor")
        ids.add(decision["id"])
        grouped[(event["id"], phase, when.get("foe_index"))].append(decision)

    species = route["lead"]["species"]
    known = []
    for entry in reference["species"][species]["learnset"]:
        if entry["level"] <= route["lead"]["level"] and entry["move"] not in known:
            known.append(entry["move"])
    known = known[-4:]
    if known != history["initial_moves"]:
        raise ValueError("Initial moves differ from the pret starter learnset")
    battles, applied = [], []

    def apply(event_id, phase, lower, upper, index=None, level_up=False):
        decisions = grouped[(event_id, phase, index)]
        learnset = reference["species"][species]["learnset"]
        offers = {(m["level"], m["move"]) for m in learnset
                  if level_up and lower < m["level"] <= upper and m["move"] not in known}
        handled = set()
        for decision in decisions:
            move, old = decision["move"], decision.get("replaces")
            before = list(known)
            if decision["method"] == "level_up":
                offer = (decision["level"], move)
                if offer not in offers:
                    raise ValueError("Move is not offered at this level/species: " + decision["id"])
                if offer in handled:
                    raise ValueError("Duplicate decision for a level-up offer")
                handled.add(offer)
            if move in known:
                raise ValueError("Move is already known: " + move)
            if decision["action"] == "decline":
                if old is not None:
                    raise ValueError("Declining a move cannot delete another move")
            elif decision["action"] == "learn":
                if old is not None:
                    if old not in known:
                        raise ValueError("Forgotten move is not known: " + str(old))
                    known[known.index(old)] = move
                elif len(known) < 4:
                    known.append(move)
                else:
                    raise ValueError("Learning a fifth move requires a replacement")
            else:
                raise ValueError("Unknown move decision action")
            applied.append({**decision, "species": species, "moves_before": before, "moves_after": list(known)})
        if offers != handled:
            raise ValueError("Missing level-up move decision at " + event_id)

    for event, row in zip(route["events"], run["timeline"]):
        name = event["id"]
        apply(name, "before", row["level_before"], row["level_before"])
        before = list(known)
        foes = []
        for index, foe in enumerate(row["defeats"]):
            entry = list(known)
            apply(name, "after_foe", foe["level_before"], foe["level_after"], index, level_up=True)
            foes.append({"foe_index": index, "opponent": foe["species"],
                "level_before": foe["level_before"], "level_after": foe["level_after"],
                "moves_before": entry, "moves_after": list(known)})
        if event["kind"] == "evolution":
            species = event["species"]
        apply(name, "after", row["level_before"], row["level_after"], level_up=event["kind"] == "rare_candy")
        if event["kind"] in ("trainer_battle", "wild_battle", "scripted_battle"):
            battles.append({"event": name, "kind": event["kind"], "species": species,
                "video_start": event["video_start"], "video_end": event["video_end"],
                "level_before": row["level_before"], "level_after": row["level_after"],
                "moves_before": before, "moves_after": list(known), "foes": foes})
    if len(applied) != len(history["decisions"]):
        raise ValueError("Unapplied move decision")
    by_event = {b["event"]: b for b in battles}
    for check in history["menu_checks"]:
        if not check.get("evidence") or set(by_event[check["event"]]["moves_before"]) != set(check["moves"]):
            raise ValueError("Moves disagree with recorded menu: " + check["event"])
    return {"format": "pokesim-frlg-moves-report/1", "mode": run["mode"],
        "route_sha256": fingerprint(route), "reference_sha256": fingerprint(reference),
        "history_sha256": fingerprint(history), "source": history["source"],
        "scope": history["scope"], "initial_moves": history["initial_moves"],
        "changes": applied, "menu_checks": history["menu_checks"],
        "slot_order_notes": history["slot_order_notes"], "battles": battles}


def move_names(moves):
    return ", ".join(m.replace("_", " ").title() for m in moves)


def moves_markdown(report):
    """Show sourced changes and the lead's move set for every recorded battle."""
    lines = ["# Pokeguy's Squirtle-line move history", "",
        "Recorded-run reconstruction from the video notes and pinned pret level-up learnsets.", "",
        "Moves below are **membership lists, not controller slot order or PP**. Video times are playback ranges from sampled review; they are not exact button-edge timestamps. The two slot-reorder windows described below remain unresolved.", "",
        "Disable and exhausted PP do not remove a known move; this report tracks learned moves, not turn-by-turn legal actions.", "",
        "This follows the observed wild wins and Rare Candies. It does not apply the recorded learning times to the flee-all counterfactual.", "",
        "## Learning and replacement points", "",
        "Initial Lv5 Squirtle: " + move_names(report["initial_moves"]) + ".", "",
        "| Video range | Anchor | Decision | Moves afterward |", "|---|---|---|---|"]
    for change in report["changes"]:
        when = change["when"]
        anchor = when["event"] + " / " + when["at"]
        if "foe_index" in when:
            anchor += " " + str(when["foe_index"] + 1)
        label = change["action"] + " " + move_names([change["move"]])
        if change.get("replaces"):
            label += " over " + move_names([change["replaces"]])
        label += " (" + change["method"] + (", Lv" + str(change["level"]) if "level" in change else "") + ")"
        lines.append("| [{}–{}]({}&t={}) | {} | {} | {} |".format(
            video_time(change["video_start"]), video_time(change["video_end"]), report["source"]["video"],
            change["video_start"], anchor, label, move_names(change["moves_after"])))
    lines += ["", "## Move set for every battle", "",
        "Changes after a knockout apply only to subsequent opponents. For example, Brock is fought with Bubble and learns Water Gun after Onix; Misty is fought without Water Pulse. JSON output also records the lead's move set before and after every defeated opponent.", "",
        "| Video start | Battle | Level before | Moves on entry | Moves on exit |", "|---|---|---:|---|---|"]
    for battle in report["battles"]:
        lines.append("| [{}]({}&t={}) | {} | {} | {} | {} |".format(video_time(battle["video_start"]),
            report["source"]["video"], battle["video_start"], battle["event"], battle["level_before"],
            move_names(battle["moves_before"]), move_names(battle["moves_after"])))
    lines += ["", "## Slot-order observations", ""]
    lines.extend("- " + item["detail"] for item in report["slot_order_notes"])
    lines += ["", "Six recorded full-menu checks match the reconstructed move membership. Source lines and evidence are in moves.json; learnset levels come from pret. Received TMs/HMs are not treated as learned until the teaching event. Cut on Rattata and Fly on Pidgey do not change the lead's moves.", ""]
    return "\n".join(lines)

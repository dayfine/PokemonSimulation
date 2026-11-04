"""Audit a timestamped route against recorded levels without fitting to them."""

from collections import Counter
import hashlib
import json

from pokesim.games.frlg.progression.experience import defeat_exp, level_at, rare_candy

MODES = ("flee_all_wild", "observed_wild_wins")


def validate(route, data):
    """Check identity, chronology, solo-EXP assumptions, and full trainer parties."""
    if route.get("format") != "pokesim-frlg-route/1" or data.get("format") != "pokesim-frlg-exp-data/1":
        raise ValueError("Unsupported route or EXP data format")
    lead = route["lead"]
    if lead.get("exp_share") or lead.get("participants") != 1:
        raise ValueError("This route audit requires solo participation without Exp. Share")
    if lead["species"] != "SQUIRTLE" or lead["level"] != 5:
        raise ValueError("This milestone starts with the Lv5 Squirtle gift")
    seen, previous = set(), -1
    for event in route["events"]:
        if event["id"] in seen:
            raise ValueError("Duplicate event " + event["id"])
        seen.add(event["id"])
        if event["video_start"] < previous or event["video_end"] < event["video_start"]:
            raise ValueError("Events are not chronological: " + event["id"])
        previous = event["video_start"]
        if not event.get("evidence"):
            raise ValueError("Missing source evidence for " + event["id"])
        if event["kind"] == "trainer_battle":
            party = data["trainers"][event["trainer"]]["party"]
            signature = lambda mons: Counter((m["species"], m["level"]) for m in mons)
            if signature(party) != signature(event["observed_party"]):
                raise ValueError("Trainer party differs from route notes: " + event["id"])
            for check in event.get("observations", []) + event.get("observed_exp", []):
                if "foe_index" in check and not 0 <= check["foe_index"] < len(party):
                    raise ValueError("Invalid foe index in " + event["id"])
        elif event["kind"] in ("wild_battle", "scripted_battle"):
            if event["outcome"] not in ("defeated", "caught", "fled"):
                raise ValueError("Unsupported battle outcome in " + event["id"])
        elif event["kind"] not in ("wild_battle", "scripted_battle", "demonstration", "rare_candy", "evolution", "checkpoint"):
            raise ValueError("Unsupported event kind " + event["kind"])
        for check in event.get("observations", []):
            if check["at"] not in ("before", "after", "after_foe") or not 1 <= check["level"] <= 100:
                raise ValueError("Invalid level observation in " + event["id"])


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def audit(route, data, mode="flee_all_wild"):
    """Calculate from the initial threshold, never from a later observed level."""
    validate(route, data)
    if mode not in MODES:
        raise ValueError("Unknown wild EXP mode " + mode)
    thresholds = data["growth_curves"][data["species"][route["lead"]["species"]]["growth_rate"]]
    exp = thresholds[route["lead"]["level"]]
    rows, checks, exp_checks = [], [], []

    def observe(event, phase, index=None):
        for observation in event.get("observations", []):
            if observation["at"] != phase or (phase == "after_foe" and observation["foe_index"] != index):
                continue
            predicted = level_at(exp, thresholds)
            checks.append({"event": event["id"], "at": phase,
                **({"foe_index": index} if index is not None else {}),
                "basis": observation.get("basis", "unspecified"),
                "observed_level": observation["level"], "predicted_level": predicted,
                "delta": predicted - observation["level"], "match": predicted == observation["level"]})

    for event in route["events"]:
        check_start, exp_check_start = len(checks), len(exp_checks)
        before = exp
        observe(event, "before")
        row = {"event": event["id"], "kind": event["kind"],
            "video_start": event["video_start"], "video_end": event["video_end"],
            "exp_before": exp, "level_before": level_at(exp, thresholds), "defeats": []}
        if event["kind"] == "trainer_battle":
            row["trainer"] = event["trainer"]
            row["trainer_name"] = data["trainers"][event["trainer"]]["name"]
            foes = event["observed_party"]
        elif event["kind"] in ("wild_battle", "scripted_battle"):
            row.update(opponent=event["opponent"], outcome=event["outcome"])
            foes = [event["opponent"]] if event["outcome"] == "defeated" else []
        else:
            foes = []
        for index, foe in enumerate(foes):
            yield_ = data["species"][foe["species"]]["exp_yield"]
            calculated = defeat_exp(yield_, foe["level"], trainer=event["kind"] == "trainer_battle",
                participants=route["lead"]["participants"], lucky_egg=route["lead"]["lucky_egg"], traded=route["lead"]["traded"])
            included = event["kind"] != "wild_battle" or mode == "observed_wild_wins"
            award = calculated if included and level_at(exp, thresholds) < 100 else 0
            old = exp
            exp = min(exp + award, thresholds[100])
            row["defeats"].append({**foe, "base_exp_yield": yield_, "calculated_exp": calculated,
                "applied_exp": exp - old, "included": included,
                "exp_before": old, "exp_after": exp,
                "level_before": level_at(old, thresholds), "level_after": level_at(exp, thresholds)})
            expected = event.get("observed_exp", [])
            if isinstance(expected, int):
                expected = [{"foe_index": 0, "exp": expected}]
            for reading in expected:
                if reading["foe_index"] == index:
                    exp_checks.append({"event": event["id"], "foe_index": index,
                        "observed_exp": reading["exp"], "calculated_exp": calculated,
                        "match": calculated == reading["exp"], "included_in_mode": included})
            observe(event, "after_foe", index)
        if event["kind"] == "rare_candy":
            exp = rare_candy(exp, thresholds)
        if event["kind"] == "evolution":
            row["eligible_for_observed_evolution"] = level_at(exp, thresholds) >= event["minimum_level"]
        observe(event, "after")
        row.update(exp_after=exp, level_after=level_at(exp, thresholds), exp_gained=exp - before,
                   level_checks=checks[check_start:], exp_checks=exp_checks[exp_check_start:])
        rows.append(row)
    mismatches = [c for c in checks if not c["match"]]
    return {"mode": mode, "final_level": level_at(exp, thresholds), "final_exp": exp,
        "trainer_battles": sum(e["kind"] == "trainer_battle" for e in route["events"]),
        "trainer_foes": sum(len(e["observed_party"]) for e in route["events"] if e["kind"] == "trainer_battle"),
        "rare_candies": sum(e["kind"] == "rare_candy" for e in route["events"]),
        "level_checks": len(checks), "matching_levels": len(checks) - len(mismatches),
        "level_checks_by_basis": {basis: {"checks": sum(c["basis"] == basis for c in checks),
            "matches": sum(c["basis"] == basis and c["match"] for c in checks)}
            for basis in sorted({c["basis"] for c in checks})},
        "level_mismatches": mismatches, "exp_checks": len(exp_checks),
        "exp_mismatches": [c for c in exp_checks if not c["match"]], "timeline": rows}


def compare(route, data):
    """Both the requested counterfactual and a control for the observed route."""
    return {"format": "pokesim-frlg-exp-report/1", "route_source": route["source"],
        "pret_source": data["source"], "route_sha256": fingerprint(route), "reference_sha256": fingerprint(data),
        "assumptions": route["assumptions"], "runs": [audit(route, data, mode) for mode in MODES]}


def video_time(seconds):
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return "{}:{:02d}:{:02d}".format(hours, minutes, seconds)


def markdown_report(report):
    """Human-readable after-each-battle table plus every discrepant observation."""
    requested, control = report["runs"]
    lines = ["# Pokeguy LeafGreen EXP audit", "", "Generated from the curated video-note ledger and pinned pret data.", "",
        "The comparison uses explicit level statements and continuity checkpoints carried forward from the existing visual-review notes; this is not a new continuous review of the video.", "",
        "Flee mode omits the two documented random wild wins (24 + 15 EXP). Both modes include seven Rare Candies and the scripted Tower Marowak defeat. Captures, escapes, and the old man's demonstration award no lead EXP.", "",
        "Rare Candies set EXP to the next level threshold. Levels are calculated from the Lv5 starter's initial 135 EXP, never reset to an observed level. Matching checkpoints include repeated before/after levels and are not independent trials.", "",
        "| Mode | Final level | Final EXP | All level checkpoints matched | Explicit notes levels matched | EXP readings matched |",
        "|---|---:|---:|---:|---:|---:|"]
    for run in report["runs"]:
        explicit = run["level_checks_by_basis"].get("explicit_level_in_notes", {"matches": 0, "checks": 0})
        lines.append("| {} | {} | {} | {}/{} | {}/{} | {}/{} |".format(run["mode"], run["final_level"], run["final_exp"], run["matching_levels"],
            run["level_checks"], explicit["matches"], explicit["checks"], run["exp_checks"] - len(run["exp_mismatches"]), run["exp_checks"]))
    lines += ["", "## After each battle and Rare Candy", "", "Video timestamps are playback times; trainer parties and defeat order are in events.json and the JSON report.", "",
        "| Video | Event | Opponents in defeat order | EXP gained, flee / control | Total EXP, flee / control | Level after, flee / control | Notes level after |",
        "|---|---|---|---:|---:|---:|---:|"]
    for left, right in zip(requested["timeline"], control["timeline"]):
        if left["kind"] not in ("trainer_battle", "wild_battle", "scripted_battle", "rare_candy"):
            continue
        observed = [str(c["observed_level"]) for c in right["level_checks"] if c["at"] == "after"]
        party = ", ".join("{} Lv{}".format(m["species"].replace("_", " ").title(), m["level"]) for m in right["defeats"])
        if "opponent" in right:
            party = "{} Lv{} ({})".format(right["opponent"]["species"].title(), right["opponent"]["level"], right["outcome"])
        lines.append("| [{}]({}&t={}) | {} | {} | {} / {} | {} / {} | {} / {} | {} |".format(
            video_time(left["video_end"]), report["route_source"]["video"], left["video_end"], left["event"],
            party or "—", left["exp_gained"], right["exp_gained"], left["exp_after"], right["exp_after"],
            left["level_after"], right["level_after"], ", ".join(observed) or "—"))
    for run in report["runs"]:
        lines += ["", "## Discrepancies: " + run["mode"], ""]
        if not run["level_mismatches"]:
            lines.append("No level discrepancies at the recorded checkpoints.")
        for check in run["level_mismatches"]:
            where = check["at"] + (" " + str(check["foe_index"] + 1) if "foe_index" in check else "")
            lines.append("- {} ({}, {}): predicted {}, notes {}.".format(check["event"], where, check["basis"], check["predicted_level"], check["observed_level"]))
        for check in run["exp_mismatches"]:
            lines.append("- {} foe {} EXP: calculated {}, notes {}.".format(check["event"], check["foe_index"] + 1, check["calculated_exp"], check["observed_exp"]))
    return "\n".join(lines) + "\n"

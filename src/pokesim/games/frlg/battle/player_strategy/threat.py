"""Deterministic NPC-damage sampling for our recovery and planning decisions."""

from collections import Counter
from functools import lru_cache
import json
import random


def threat(state, ai, flags, samples=32):
    """An 80th percentile next-turn loss estimate, including existing residuals.

    This is a decision heuristic; Showdown determines the actual turn outcome.
    Sampling uses a separate fixed stream and does not reveal the battle seed.
    """
    # The heuristic uses a fixed private RNG. Repeated states therefore have
    # identical estimates and can share work across Monte Carlo trials.
    key = json.dumps({'own': state['own'], 'foe': state['foe']}, sort_keys=True)
    return dict(_threat(key, ai, tuple(flags), samples))


@lru_cache(maxsize=2048)
def _threat(key, ai, flags, samples):
    state = json.loads(key)
    rng, counts = random.Random(0), Counter()
    for _ in range(samples):
        counts[ai.choose_move(state, flags, rng)["slot"]] += 1
    own, foe = state["own"], state["foe"]
    residual = own["max_hp"] // 8 * (int(own["status"] in ("psn", "tox")) + int("leechseed" in own["volatiles"]))
    losses = [(residual, 0.0)]
    for slot, count in counts.items():
        move = foe["moves"][slot]
        weight = count / samples
        hit = move["accuracy"] * (0.75 if foe["status"] == "par" else 1)
        if foe["status"] == "slp" and foe["sleep_turns"] > 1:
            hit = 0
        losses.append((residual, weight * (1 - hit)))
        for roll in move["damage"]:
            losses.append((roll + residual, weight * hit * 15 / 16 / len(move["damage"])))
        for roll in move["critical"]:
            losses.append((roll + residual, weight * hit / 16 / len(move["critical"])))
    cumulative, likely = 0.0, residual
    for loss, weight in sorted(losses):
        cumulative += weight
        likely = loss
        if cumulative >= 0.8:
            break
    return {"likely": likely, "mean": sum(loss * weight for loss, weight in losses),
            "max": max(loss for loss, weight in losses if weight)}



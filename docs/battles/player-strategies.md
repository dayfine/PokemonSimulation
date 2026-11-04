# Incremental FRLG player strategies

The entry point is `battle/policy.py:player_action`. The game NPC stays in
`npc_ai.py` and `npc_actions.py`; A/B/C below control our lead.

| Layer | Code | Adds |
|---|---|---|
| A | `player_strategy/attacks.py` | Attack selection, effective damage, PP and locked moves |
| B — default | `player_strategy/recovery.py` | A plus healing, status cures and PP medicine |
| C — explicit opt-in | `player_strategy/planning.py` | B primitives plus multi-turn stage goals, HP reserves and opening setup windows |

B does not select X items. C is selected only by
`enable_complex_planning: true`; having progression data alone does not enable it.
The run's `data/runs/pokeguy-leafgreen-15934/strategies.json` enables exactly the
12 previously classified C fights. Each entry declares its setup goals. The
other 57 fights stay on B, and all their frozen published example traces replay
identically after the refactor. That regression check is not a new probability
measurement of B on unobserved states.

```json
{
  "enable_complex_planning": true,
  "planning_goals": {
    "spa": 2,
    "accuracy": 0,
    "outspeed": true,
    "target_torrent": true,
    "guard_accuracy": true
  }
}
```

C is goal-based, not a literal replay of winning button presses. It can repair
Speed/Accuracy losses, counter opposing evasion, cure status, heal to fund the
remaining setup turns, and use recharge windows. It prefers a guaranteed KO
over a weaker move with the same rounded expected turn count. It avoids
spending setup turns in front of Self-Destruct when a fast KO is available.
Guard Spec can protect a setup from accuracy-lowering attacks; it does not
prevent the opponent's Double Team or Minimize.

For Torrent setups, C can retain low HP for a finishing hit, confine deliberate
activation to the opening opponent, or use extra Sp. Atk stages instead of
chasing low HP indefinitely. `torrent_power` can preserve an opening Surf
plan's damage multiplier through extra stages if healing removes Torrent.
The goals include both video-informed targets and explicitly proposed targets;
their provenance is recorded in the configuration. They are not an optimal
solver and do not implement player switching.

## Rerun the changed cohort

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles \
  --complex-only --seed 4 --out /tmp/pokeguy-c.json
```

This runs only opted-in C fights, with a fresh validation seed, and emits full
traces, a summary and an old/new comparison with the new top ten. Development
runs used separate seeds before the seed-4 policy and goals were frozen.
See [the checked comparison](pokeguy-c-comparison.md).

The comparison retains the 57 old point estimates and identifies them as
historical baseline data. To preserve a 95% simultaneous guarantee after
selecting which fights to update, it recomputes intervals for all original
69 cases with half the error budget, then reserves half for the fresh C family.
The retained intervals can widen slightly without new trials. Only the new C
intervals are sampled to the new 10-percentage-point width target.

The planner can consume different quantities of items from the video. Later
fights still start from their recorded bags: this is not yet a sustainable
whole-route policy or a route completion probability. The NPC model and its
replacement-order approximations remain unchanged in this comparison.

## Bruno: strategy versus luck

The reviewed video uses two X Specials and an X Speed that compensates Rock
Tomb, with HP progressing 130 → 114 → 79 → 42. At 42/162 HP, Torrent is active.
The five opponents then fall to one Surf apiece. Under the pinned damage model,
Machamp has 183 HP and Blastoise is faster after the Speed correction:

| State | Noncritical Surf damage to Machamp |
|---|---:|
| +1 Sp. Atk, above Torrent range | 95–112 |
| +2 Sp. Atk, above Torrent range | 127–150 |
| +2 Sp. Atk, Torrent active | 189–223 |

Thus the observed Machamp knockout does not need a lucky damage roll or a
critical hit in this model. The old controller usually stopped after one
X Special or healed away Torrent; 1,276 of its 1,318 losses ended to Machamp's
Cross Chop. C improves the modeled rate from 30.6% to 95.9% in the fresh run.
That is evidence of a player-policy weakness in the old result, not an exact
estimate of Pokeguy's own policy or proof that his opening setup was risk-free.

## Resource planning

[League PP requirements](league-pp-requirements.md) record the recovery capability
the current entry states assume. A separate logistics process will resolve pickups,
purchases and timing; the independent battle benchmark does not solve that route.

## Historical baseline

`pokeguy-trainers.json` and its table remain the original
`solo-setup-heal/4` experiment, with code hashes recorded in the JSON. The
corresponding pre-layer source is available at commit `c47da06`. Current code
uses B by default and the explicit C configuration; running the current CLI
is a new experiment rather than regenerating that historical policy silently.

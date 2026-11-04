# Pokeguy full-run battle benchmark: input readiness

The [recorded starting-state ledger](../progression/pokeguy-states.md) now
reconciles player inputs for all 69 trainer battles and nine wild/scripted
encounters, under its declared profile and event assumptions. It corrects
approximate PP summaries and resolves the late Elixir and Bruno item-use
questions using focused video review. The source catalog below preserves the
input audit; the coverage table records implemented behavior and remaining
approximations.

The [full trainer benchmark](pokeguy-benchmark.md) now constructs and executes
all 69 run-specific trainer scenarios. The four AutoStory fixtures remain
separate experiments, with different stats, HP, moves and supplies.

## Current coverage

| Input | Current support | Remaining scope |
|---|---|---|
| Trainer identity, parties, moves, IVs, personalities, held items and AI | Full 69-trainer pinned import | NPC helpers and voluntary switching remain approximate/omitted. |
| Player entry state | Reconciled HP/status, raw stats, PP, badges, held item and tracked bag | Sensitivity to the alternative Attack IV24 profile is separate. |
| Live EXP/EVs/level-ups | Knockout awards, stat/HP refresh and level-up move decisions | Evolution happens after battle; the next recorded entry state supplies it. |
| Our player policy | Move/heal/cure, safe PP recovery and X-item setup heuristic | Not optimal play or the runner’s recorded strategy; Guard Spec/Dire Hit actions are not selected. |
| Sampling | Adaptive anytime-valid intervals, joint confidence correction and independent workers | Sampling bounds exclude engine/input/model error. |
| Wild/scripted encounters | Player states recorded | Combat rates and capture/escape objectives are not in the trainer report. |

There are **72 fights with a defeat-the-opponent objective**: 69 trainers,
two random wild wins, and the scripted Marowak. Two captures and four escapes
also enter battle, bringing the route ledger to 78 lead encounters. The old
man's demonstration is not the starter's battle. Capture/escape success rates
need explicit objectives and engine support, rather than silently calling
them trainer wins.

## The existing fixtures differ materially

| Encounter | Recorded starting level and HP | Current benchmark fixture |
|---|---|---|
| Misty | Lv20, 54/59 | Lv20, 60/60 |
| Cerulean rival | Lv21, 32/61 | Lv22, 65/65 |
| S.S. Anne rival | Lv27, 37/76 | Lv27, 78/78 |
| Lt. Surge | Lv28, 79/79 | Lv29, 83/83 |

Moves and bags also differ. For example, the run's Misty lead knows Mega Kick
and Water Gun and has seven Potions remaining; the existing fixture has two
Potions and a different move set. These can produce different win rates even
with identical mechanics and sampling.

## Purchases and bag reconciliation

The sourced machine-readable
[inventory audit](../../data/runs/pokeguy-leafgreen-15934/inventory-audit.json)
catalogs the following transactions. It deliberately is **not** a runnable
scenario file or a complete bag at every battle.

| Video range | Shop | Purchases |
|---|---|---|
| 13:58–14:08 | Pewter | 9 Potions, 3 Awakenings, 3 Repels |
| 37:24–37:37 | Vermilion | 5 Super Potions, 3 Parlyz Heals, 3 Repels |
| 54:18–54:29 | Lavender | 4 Escape Ropes, 7 Super Repels |
| 1:02:42–1:02:55 | Celadon 5F | 6 X Speeds, 21 X Specials, 5 X Accuracies, 2 Guard Specs |
| 1:46:15–1:46:21 | Indigo Plateau | 13 Full Restores by quantity/money reconciliation; purchase-menu quantity not directly read |

Purchases alone do not give the bag. The ledger also needs, for example,
the early Antidote pickup, seven Rare Candies, Ether/Elixir pickups and uses,
the Oran Berry, a found Full Restore, and each between-battle/in-battle use.
TM/HM teaching consumes or retains items according to FRLG rules. Healing at
the S.S. Anne cabin restores HP/PP/status without consuming bag medicine.
The old man's demo bag must not be copied into the player's inventory.

The original observations are now annotated with these resolutions:

- Ether's target is constrained to Mega Kick by subsequent uses and unchanged
  Water Pulse PP; the menu target is still not directly read.
- Lorelei's narrative says two X Specials, but readings progress from 15 before
  the fight to 13, 12, then 11. The starting-state ledger
  conserves four consumed items without inventing their exact turn placement.
- Focused Bruno frames confirm two X Specials, one X Speed, and no X Accuracy.
  Later pre-Lance counts confirm the carry-forward.
- The late Elixir is now directly reviewed before entering the Champion room.
- The Plateau heal is supported by full HP and PP, while the nurse interaction
  itself is not directly captured in the sampled review.

For consumables, replay `previous count + acquisitions - uses - removals` and
check every direct bag reading. Mark a battle complete only when its allowed
items and quantities are known or the experiment explicitly declares a range
or assumption. If an input remains a range, simulate the plausible scenarios
and report the sensitivity instead of replacing the unknown with zero.

## Benchmark definition and build order

The first full-route report should estimate **each battle independently from
the recorded starting state**, with a named, state-dependent player strategy.
Each trial resets that battle's HP, PP, bag, EXP, and other inputs. Random
outcomes can require different move/healing choices, so a fixed list of the
successful video's button presses is not a complete policy.

Those are conditional per-battle probabilities. They are not a route-clear
probability: carrying simulated HP/PP/bag outcomes into later fights is a
separate route simulation. Do not multiply the observed-state estimates and
present the product as the run's completion probability.

The full trainer runner implements the import, live progression, bag actions
and adaptive sampling. Every trainer matchup executes in integration checks;
its live awards and stat changes are cross-checked against the independent
Python progression model. This is implementation validation, not proof of
cartridge-equivalent NPC behavior or video-equivalent turn outcomes. See
[remaining gaps](GAPS.md) before interpreting the rates.

# Pokeguy full-run battle benchmark: input readiness

We can reconstruct the route, but **we do not yet have 69 validated,
run-specific battle scenarios**. The current four-case benchmark uses older
AutoStory fixtures. Adaptive sampling now works on those fixtures; it does
not make them a reconstruction of Pokeguy's run.

## Available versus missing

| Input | Current evidence | Work still required |
|---|---|---|
| Battle identity and order | 69 trainers / 199 trainer Pokémon in the route ledger | Add the two wild wins and scripted Tower Marowak to the combat objective; capture/escape encounters have different success criteria. |
| Trainer species and levels | All 69 trainer parties resolved against pinned pret | The battle snapshot includes complete battle data for only four trainers; import the other 65 trainers' moves, stats, abilities, items, flags, and reachable NPC AI paths. |
| Player EXP and level | Recorded-route reconciliation matches the notes | Connect awards to live battles, including HP/stat changes and move-learning decisions between enemy Pokémon. |
| Player nature / IVs / EVs | Mild; five IVs resolved, Attack 24–25 from gameplay (overlay says 25); EV checkpoints reconciled in investigation notes | Implement the EV/stat builder and generate each battle's raw stats. Use EVs from the last stat recalculation when relevant, not automatically all EVs earned since then. Record the Attack choice or run both candidates. |
| Player moves | Nine changes / four refusals tracked for all 69 trainers | Feed the route-derived sets into battle scenarios; expand the battle move snapshot. Two slot-reorder times remain unknown but do not change membership. |
| Player HP / status | Many direct readings and before/after damage/healing observations | Reconcile a starting-state checkpoint before each fight; do not assume full HP. |
| Player PP | Move-menu readings, attack counts, teaching events, cabin heal, and PP medicines are documented | Reconcile PP before every fight, including inferred Ether target and unsampled Elixir use. Do not assume full PP. |
| Bag inventory | Five shopping stops and many receipts, uses, and bag views | Build a quantity ledger for purchases, pickups, gifts, item uses, teaching, equipping, discards, and sales. Unknown counts remain unknown. Current catalog is partial. |
| Badges / held item / party | Badge order, BlackGlasses equip, and Plateau deposits documented | Export their state at each fight; receiving BlackGlasses is not the same as equipping it. HM helpers are present before the League but the observed lead fights solo. |
| Our player policy | Existing greedy move/heal policy | It cannot use X items, PP medicine, or setup turns. Add tested bag actions and define a state-dependent setup/heal strategy before claiming to evaluate the runner's approach. |
| NPC / mechanics coverage | Four-trainer script interpreter and tested Gen 3 adapter boundaries | Add the required AI instructions, field-aware previews, and encounter-specific mechanics checks as the imported move set expands; track approximations. |

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
| 1:46:15–1:46:21 | Indigo Plateau | Full Restores; likely 13 by reconciliation, quantity not directly read in purchase menu |

Purchases alone do not give the bag. The ledger also needs, for example,
the early Antidote pickup, seven Rare Candies, Ether/Elixir pickups and uses,
the Oran Berry, a found Full Restore, and each between-battle/in-battle use.
TM/HM teaching consumes or retains items according to FRLG rules. Healing at
the S.S. Anne cabin restores HP/PP/status without consuming bag medicine.
The old man's demo bag must not be copied into the player's inventory.

Concrete unresolved observations include:

- Ether's target is inferred to be Mega Kick; the menu target is not directly read.
- Lorelei's narrative says two X Specials, but readings progress from 15 before
  the fight to 13, 12, then 11. Resolve the item count and turn timing against
  the video; do not encode the prose as exactly two setup turns.
- X Speed / X Accuracy selections around the League do not always show a
  completed use. Keep exact turn timing separate from later quantity constraints.
- The late Elixir is inferred from restored PP at an unsampled point.
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

Build in this order:

1. Reconcile source-backed inventory, HP/status, and PP snapshots at every fight.
2. Generate raw stats from the reconciled progression, nature/IV choice, and EVs.
3. Expand trainer/move/AI import; make unsupported behavior explicit per encounter.
4. Implement and test live level-ups, X-item/setup turns, held items, and PP items.
5. Replay representative early, setup-heavy, and League battles against video
   checkpoints before running every scenario.
6. Use the [adaptive sampler](adaptive-sampling.md) on each validated scenario;
   report bounds, sample count, stop reason, assumptions, and example losses.

The sampler is ready. The full-run scenario inputs and engine/policy coverage
remain the gating work; this milestone does not report win rates for all 69.

# FRLG battle benchmarks

Answer: given a solo Squirtle-line lead, its stats, HP, moves and PP, the bag,
and a named trainer, how often does this policy win under this model?

The [Pokeguy trainer benchmark](pokeguy-benchmark.md) now runs all 69 trainer
battles from reconciled entry states, with live progression and setup items.
See [the complete results table](pokeguy-trainers.md).
Its conditional win rates are separate from the original AutoStory experiments
below.

The original four cases are Misty, the Cerulean rival, the S.S. Anne rival, and Lt.
Surge. They come from the FRLG AutoStory source fixtures. This milestone
keeps evaluation and policies in Python and reuses existing battle mechanics.
It runs locally without a Showdown server, account, or network connection.

[Adaptive sampling](adaptive-sampling.md) can stop easy cases early while
reporting anytime-valid uncertainty bounds and unresolved budget limits.
The [Pokeguy input audit](pokeguy-readiness.md) records the provenance and
remaining model limitations of the full trainer benchmark.

Our adapter lives in [`engines/frlg-showdown/`](../../engines/frlg-showdown/README.md)
and targets **FireRed / LeafGreen (Gen 3)**. Showdown and Smogon's calculator
support many generations; this adapter fixes the generation to 3 and supplies
FRLG-specific story-battle behavior. It is not a general cross-game bridge.

## Run

Install Node 22+ and Python 3.8+, then from the repository root:

```sh
npm ci --omit=optional --prefix engines/frlg-showdown
PYTHONPATH=src python3 -m pokesim.cli.frlg_battle --battles 1000 --seed 1 --out /tmp/frlg.json
```

For one encounter:

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_battle --case surge-m73 --battles 1000 --seed 1 --out /tmp/surge.json
```

The CLI prints wins and a 95% Wilson interval for each encounter. The JSON
report records the full inputs, source revision and input hashes, engine
versions and lockfile hash, seed, policies, turn limit, item consumption,
conditions captured before faint cleanup, the final damage effect, and one example of each observed outcome. Each example
contains the trial index, engine seed, decisions, and Showdown event log.
Identical inputs and seeds reproduce results; wall-clock log entries are removed.
The standard 1,000-trial run takes a few minutes on a development laptop.

The [checked-in baseline report](frlg-baseline.json) is an experiment under
these policies and assumptions. It is not a measurement of console win rates.
The interval describes sampling uncertainty, not inaccuracies in the model.
The saved baseline retains the lockfile hash from before the adapter package
rename; the pinned dependency versions did not change with that rename.

## Baseline results

With seed 1 and 1,000 battles per case:

| Encounter | Wins | Estimated probability | 95% Wilson interval |
|---|---:|---:|---:|
| Misty, m51 | 787 | 78.7% | 76.1–81.1% |
| Cerulean rival, m56 | 494 | 49.4% | 46.3–52.5% |
| S.S. Anne rival, Lv27 | 329 | 32.9% | 30.1–35.9% |
| Lt. Surge, m73 | 481 | 48.1% | 45.0–51.2% |

The traces expose concrete failure modes: 22 Misty losses ended in confusion
self-damage; 393 of the 506 Cerulean losses and 609 of the 671 S.S. Anne
losses occurred while seeded. Every Surge loss ended against Raichu. Conditions
can overlap and do not establish causation; the final damage effects and
example logs are in the report. These results are a baseline for validation
and policy comparisons, rather than replacements for console observations.

## Inputs and provenance

`data/games/frlg/battles/cases.json` contains the experiment cases. Each
case links to a specific Arduino-Source commit and describes which inputs
were measured versus assumed:

| Case | Summary inputs | Preparation scenario |
|---|---|---|
| `misty-m51` | Wartortle Lv20, 60 HP, Bite/Tail Whip/Bubble/Withdraw; other stats assumed | 2 Potions; Boulder badge |
| `cerulean-m56` | Wartortle Lv22, 65 HP, Bite/Water Pulse/Bubble/Withdraw; other stats assumed | 15 Potions, 2 Awakenings, 1 Parlyz Heal; Misty already beaten |
| `ssanne-27` | Wartortle Lv27, 78 HP, Bite/Water Pulse/Bubble/Withdraw; other stats assumed | 15 Potions, 1 Antidote |
| `surge-m73` | Wartortle Lv29; all six stats measured: HP83/Atk44/Def59/SpA51/SpD64/Spe49; Bite/Water Pulse/Bubble/Dig | 14 Potions; Boulder and Cascade badges |

All cases start at full HP and base PP. The older fixtures assumed neutral
nature, IV15, EV0 where a stat was unread. These assumptions are preserved
and explicitly recorded; the output is not presented as a reconstruction of
an entire observed run. The player cannot switch and a fainted lead loses.
Level, stats, and moves stay fixed during each battle; experience and
mid-battle level-ups are not modeled.

To experiment, copy `cases.json` and use `--cases /path/to/cases.json`.
Specify **all six raw summary stats**, current `hp` if below maximum, and
current PP with `{"name": "BITE", "pp": 7}` instead of a move name. Badge
boosts are applied separately in battle, so do not include them in summary
stats. Bag item counts are explicit, including potion types. The first
milestone validates against the imported trainer and move set; extending
that set requires importing and testing the new AI paths.

Optional initial `player.boosts` supplies temporary stages independently of
the six summary stats, for example `{"atk": -1, "def": 2, "spe": 1}`.
The supported stage keys are `atk`, `def`, `spa`, `spd`, `spe`, `accuracy`,
and `evasion`, each an integer from -6 through +6. HP has no stage. Move
effects update these stages during the battle. Attack and defensive stages
are passed to Smogon with raw stats; Speed and turn order come from Showdown;
accuracy/evasion use the adapter's pret stage table. Gen 3 critical previews
ignore negative attacking stages and positive defending stages while retaining
favorable stages. Supplying a stage does not implement an X-item bag action.

The pret snapshot includes parties, moves, level-up default moves, IV scaling,
name-derived natures, trainer item order, AI flags, and reachable script
instructions. It keeps provenance hashes for each source file. No ROM or
compiled decomp is required.

To regenerate the exact source snapshot:

```sh
git clone https://github.com/pret/pokefirered.git external/pokefirered
git -C external/pokefirered checkout ce6406d8c2eaf46d543c8a2606de0c3cb1951982
PYTHONPATH=src python3 -m pokesim.games.frlg.battle.pret --repo external/pokefirered --out /tmp/pret.json
cmp /tmp/pret.json data/games/frlg/battles/pret.json
```

## Architecture and policies

```text
Python experiment + policies  <--- JSON lines --->  local Node bridge
        |                                           |
  pinned pret snapshot                    Pokémon Showdown Gen 3 turns
                                          Smogon calculator previews
```

- Python controls opponent scoring scripts, player choices, trainer items,
  compulsory opponent replacements, seeded repetitions, and reporting.
- Showdown controls actual damage, move effects, statuses, abilities,
  critical hits, accuracy, PP, turn order, residual damage, and multi-turn moves.
- Smogon's calculator supplies preview damage rolls for decision-making;
  measured stats survive the calculator's internal cloning.
- Bag items are queued events at priority 6, before attacks. They consume
  the user's turn without triggering sleep countdown, confusion checks,
  paralysis checks, or move PP usage. They still permit end-of-turn damage.
  An in-progress Dig cannot be interrupted with a bag item.
- No npm dependency is patched, and the bridge remains pinned and independently
  tested because it uses Showdown's Side/action-queue interfaces.

`src/pokesim/games/frlg/battle/npc_ai.py` / `NPCTrainerAI` is the **game NPC trainer's
move-selection policy**. Its current snapshot covers Misty, the Cerulean rival
with Bulbasaur, the S.S. Anne rival with Ivysaur, and Lt. Surge. It is not our
player AI. The interpreter executes the imported `CHECK_BAD_MOVE`,
`CHECK_VIABILITY`, and `TRY_TO_FAINT` branches. It samples the AI's per-move
simulated damage rolls, follows its randomized scoring, and preserves its
best-score selection behavior. It tracks revealed player moves. Unknown
instructions raise an error instead of silently falling back to a generic AI.
Trainer items use pret's HP thresholds, status cures, single-use inventory,
and item-slot restrictions as the enemy party shrinks.

Our player policy, `policy.py:player_action`, named `solo-greedy-heal/1`, chooses a move by expected turns to
KO, accuracy, and PP conservation. It prioritizes a reliable finishing hit,
uses available status cures when the turn is survivable, and selects the
smallest useful healing item when hurt. It estimates next-turn damage from
32 samples of the opponent policy and existing poison/Leech Seed damage,
using the 80th percentile to avoid Potion loops that heal less than each hit.
It does not optimize the whole battle or reproduce every historical C++ choice.
`policy.py:trainer_item` and `policy.py:replacement` are NPC helpers for bag
items and compulsory replacements; the benchmark calls these separately from
`NPCTrainerAI`'s move scoring.

## Fidelity limits and next decision

The prototype establishes that a reusable engine can handle the mechanics
and accept bag turns. **It does not establish cartridge-equivalent win rates.**

- AI damage helpers use Smogon calculations, not pret's `AI_CalcDmg` routine.
  Type/speed/ability queries use the engine state; this is not a complete port
  of the cartridge's imperfect-information and history behavior.
- Opponents make compulsory replacements with pret-derived type-first and
  damage-fallback rules. Voluntary switching is not modeled.
- AI randomness and engine randomness use independent seeded streams. They
  do not reproduce the cartridge's shared RNG stream or frame-dependent seeds.
- The engine uses Showdown Gen 3 mechanics. Cartridge-specific differences
  beyond the tested adapter boundaries still require validation.
- The policy uses approximate damage previews for decisions under confusion,
  sleep, and multi-turn moves. The actual outcome of those turns is simulated
  by Showdown. More rollouts cannot fix a biased policy or an incorrect state.
- Loss conditions are descriptive: e.g. a loss while seeded does not prove
  Leech Seed caused it. Turn-limit non-wins are reported separately.

The old C++ estimates are comparison points, not test assertions. Misty's
confusion, Torrent, different healing choices, and source assumptions can
change the answer. Before expansion, replay the recorded console cases with
fully read inputs, inspect representative losses, and decide whether improving
AI fidelity or player policy gives the most useful next result.

See the [implementation gap review](GAPS.md) for concrete missing behavior,
its effect on these estimates, and the next work needed for the Pokeguy route.

## Verification

```sh
npm test --prefix engines/frlg-showdown
POKESIM_REQUIRE_BATTLE=1 PYTHONPATH=src python3 -m unittest pokesim.games.frlg.battle.test_battle
POKEFIRERED_DIR=external/pokefirered PYTHONPATH=src python3 -m unittest pokesim.games.frlg.battle.test_battle.BattleDataTest.test_reimport_real_pret_snapshot
```

The standard Python suite runs data checks without npm and skips the
engine integration checks if dependencies are absent. A dedicated CI job
installs pinned dependencies and requires the real bridge checks.

Sources: [Showdown simulator API](https://github.com/smogon/pokemon-showdown/blob/master/sim/SIMULATOR.md),
[Smogon calculator](https://github.com/smogon/damage-calc),
[pret trainer creation](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_main.c),
[pret AI scripts](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/data/battle_ai_scripts.s),
[pret switching and items](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_ai_switch_items.c).

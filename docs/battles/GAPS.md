# FRLG battle simulation coverage and remaining gaps

The [Pokeguy trainer benchmark](pokeguy-benchmark.md) imports all 69 trainer
parties, uses reconciled starting states, awards live solo EXP/EVs, handles
level-up stats/HP/moves, and supports setup/PP bag actions. It is a model-based
benchmark with a named player policy; it is not cartridge-equivalent emulation.

## Covered boundaries

| Area | Implementation and checks |
|---|---|
| Seven stat stages | Physical/special stages -6 through +6; critical bypass rules; actual speed order; accuracy/evasion previews |
| Live progression | Simulated faint events award EXP/EVs before replacement, refresh stats/HP on level increase, and apply recorded move-learning choices; all 69 matchups cross-checked against independent Python calculations |
| Inventory actions | Healing/cures, Oran Berry, Gen 3 X items, Guard Spec, Dire Hit, PP restoration; turn cost, PP preservation, stage caps and five-turn Mist checked |
| Full trainer import | All route parties, held items, IVs, deterministic personalities/natures, moves, AI flags and reachable scoring instructions; revision/hash-stamped and reproducible |
| Fields and multi-hit moves | Weather/screens feed damage previews; multi-hit policy previews use distributions; Showdown samples actual hits |
| Compulsory choices | Locked moves in any slot, recharge, faint replacements and switch-move replacements |
| Opening tutorial | Guaranteed initial player hit and suppression of critical hits before first damage |
| Sampling | Anytime-valid intervals with a joint confidence correction across the requested case family, including process-parallel execution |

## Gaps that affect interpretation

| Priority | Gap | Consequence / next work |
|---|---|---|
| 1 | Wild/scripted and capture/escape objectives | This report covers trainers. Add the two wild wins and Tower Marowak, with explicit wild stat/personality assumptions. Define success for captures and escapes before reporting rates. |
| 1 | NPC helper and history parity | Scoring scripts are source-derived, but damage, first-turn/protection/history/weather queries and knowledge of abilities remain approximate. Compare individual scores/choices with pret traces before claiming cartridge parity. |
| 1 | HM helpers and forced player switches | Before the Plateau deposits, the recorded party has helpers. The solo-lead model omits them, so Roar/Whirlwind can fail where the real party would force a switch. Add their states and a return-to-lead policy for party-accurate results. |
| 1 | NPC voluntary switching | No `ShouldSwitch` policy. Baton Pass and other move-forced requests execute, but a trainer cannot proactively retreat from a poor matchup or Perish Song. |
| 1 | Accuracy parity | Preview uses pret's combined accuracy-minus-evasion stage table; Showdown can apply separate factors. Ability/item/volatile hit modifiers are incompletely represented in previews. Align actual hit and preview arithmetic with cartridge cases. |
| 2 | Threat estimates | The player heuristic assumes a 1/16 critical rate and simplifies residual/status effects. High-critical moves, escalating toxic damage and volatile interactions can bias healing/setup choices even though actual turns resolve them. |
| 2 | Policy quality and information | Full roster knowledge, greedy attack/heal/setup choices, no player switching. It is neither optimal play nor Pokeguy's policy. Guard Spec/Dire Hit actions exist but are not chosen by this heuristic. |
| 2 | Input sensitivity | The report selects overlay Attack IV25 and recorded preparation assumptions. Compare the surviving IV24 profile and any uncertain inputs separately. |
| 2 | Whole-route outcome | Fights reset to recorded entry states. Carrying random HP/PP/bag outcomes and preparation policy forward is a different experiment; conditional rates must not be multiplied as a route-clear probability. |

Increasing trials shrinks sampling uncertainty, not model error. The Python AI
and Showdown engine have separate seeded streams rather than the cartridge's
shared, frame-dependent RNG.

## Code ownership

- `npc_ai.py:NPCTrainerAI`: opposing game NPC move scoring from pret scripts.
- `policy.py:player_action`, `attack`, `threat`, `setup_action`: our player's choices.
- `policy.py:trainer_item`, `replacement`: NPC medicines and replacement choices.
- `run.py`: recorded-state trainer case builder, independent of trial outcomes.
- `engine.cjs`: actual turns, bag actions, fields, locks and state export.
- `progression.cjs`: live knockout awards, raw-stat refresh and move learning.
- `damage.cjs`: Smogon previews and FRLG accuracy-stage preview.

Sources: pinned npm implementations, pret's
[`battle_main.c`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_main.c),
[`battle_script_commands.c`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c),
[`battle_ai_script_commands.c`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_ai_script_commands.c), and
[`battle_ai_switch_items.c`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_ai_switch_items.c).

# Battle simulation gaps and next work

This review describes the implementation in PR #31. The benchmark answers a
fixed-state, solo-lead question. Reconstructing Pokeguy's full run needs more
than expanding the trainer list. The priorities below distinguish missing
model behavior from choices made by our player strategy.

## Stat stages: supported and checked

All seven stages are carried in Showdown state. `damage.cjs` passes the
attacking and defending stages to Smogon alongside measured raw stats; it
does not manually multiply raw stats by stages. Double-applying stages would
give incorrect damage and critical-hit behavior.

| Change | Current calculation | Verification |
|---|---|---|
| Attack / Defense | Smogon Gen 3 physical damage | Each stage -6 through +6, hand-calculated damage, live Tail Whip/Withdraw |
| Sp. Atk / Sp. Def | Smogon Gen 3 special damage | Each stage -6 through +6, hand-calculated damage |
| Speed | Showdown `getStat('spe')` and action queue | Positive/negative initial stages change exported speed and actual move order |
| Accuracy / Evasion | Adapter's pret accuracy-stage table; Showdown resolves actual hits | Positive/negative stages, cancellation, combined caps, always-hit Shock Wave |
| Critical hits | Smogon/Showdown Gen 3 damage rules | Negative attack and positive defense stages ignored; favorable stages retained |

Initial player stages are validated as integers in [-6, +6] for the seven
supported keys. Raw HP is independent and has no stage. These checks do not
claim parity for every ability, field effect, or accuracy modifier.

## Next priorities

| Priority | Gap | Why it matters / required follow-up |
|---|---|---|
| 1 | Reconstruct the run's actual starting stats, HP, moves, PP, and bag | Most current fixtures have assumed stats and start fully healed. They are AutoStory experiments, not Pokeguy reconstructions. Use the run ledger and measured video checkpoints; retain uncertainty where unread. |
| 1 | EXP, EVs, and mid-battle level-ups | `benchmark.py` holds levels/stats/moves fixed for the entire battle. The separate EXP ledger does not update live Showdown combatants. Wire awards into faint/replacement handling, recalculate stats/HP, and handle move learning before evaluating the full route. |
| 1 | X-item actions and a setup strategy | The schema and `applyBag` currently accept healing/cure items only. Pokeguy uses X Special, X Speed, X Accuracy, and other setup supplies. Add tested turn actions and duration/cap behavior, then a player strategy that can choose them. Initial boosts are not a substitute for spending a setup turn. |
| 2 | NPC damage helpers and information history | `NPCTrainerAI` follows imported pret branches but substitutes Smogon damage for `AI_CalcDmg` and uses engine-derived queries. Port the helpers/history and compare individual scores/choices against pret traces before claiming cartridge-equivalent NPC decisions. |
| 2 | NPC voluntary switches | Only compulsory replacements are implemented. Add the relevant `ShouldSwitch` logic and correct action priority before expanding to encounters where switching changes outcomes. |
| 2 | Field-aware previews | `damage.cjs:rolls` does not pass a `calc.Field`; weather, Reflect, Light Screen, and other field effects can affect actual turns without affecting policy previews. The NPC interpreter's `get_weather` opcode currently returns no weather for the named encounter set. Map supported live field state and test preview-versus-engine damage before adding weather/screen encounters. |
| 2 | Accuracy parity with FRLG | The preview uses pret's combined accuracy-minus-evasion stage and integer table. Showdown's Gen 3 hit routine applies separate stage factors. These can disagree when both stages change or at rounding boundaries. The preview also omits ability/item/volatile hit modifiers. Align actual hits and previews, with cartridge-derived cases, before treating general accuracy results as exact. |
| 3 | Critical probabilities and residual threat estimates | `policy.py:threat` assumes a 1/16 critical rate and a flat poison/Leech Seed estimate. It omits changing critical rates, escalating toxic damage, and several volatile/turn interactions. Showdown resolves actual turns, but the player's heal decision can be biased. Derive these probabilities/state effects or use explicit turn rollouts. |
| 3 | Wider move/effect coverage | The imported AI scripts cover the current move snapshot. Multi-hit previews explicitly fail; more moves require expanded import coverage, relevant field/state translation, and mechanics checks. Do not silently treat unimplemented effects as ordinary attacks. |

The player policy is another source of variation: `player_action` is a greedy
move/heal heuristic, not an optimal battle solver or a transcription of the
runner's choices. Its threat samples may consult the modeled NPC's full move
set. Decide whether the next experiment measures that policy, a recorded
runner strategy, or a policy restricted to information available to a real
player, and label the resulting win probability accordingly.

The NPC interpreter also uses a separate seeded RNG stream from Showdown.
It preserves reproducibility, not the cartridge's shared, frame-dependent RNG
sequence. More Monte Carlo samples shrink sampling error but do not resolve
any of the model gaps above.

## Code ownership

- `npc_ai.py:NPCTrainerAI`: game NPC move scoring/selection from imported pret scripts.
- `policy.py:player_action`, `attack`, `threat`: our player move, cure, and healing strategy.
- `policy.py:trainer_item`, `replacement`: NPC item and compulsory replacement helpers.
- `engine.cjs`: actual Showdown turns, live stats/effects, bag actions, and state export.
- `damage.cjs`: Smogon damage previews plus the FRLG accuracy-stage preview.

Primary implementation references: pinned local npm sources
`@smogon/calc/dist/mechanics/gen3.js` and
`pokemon-showdown/data/mods/gen3/scripts.ts`; pret's
[`Cmd_accuracycheck` and EXP/damage commands](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c),
[`battle_ai_script_commands.c`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_ai_script_commands.c), and
[`battle_ai_switch_items.c`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_ai_switch_items.c).

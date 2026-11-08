# Shared story execution and FRLG coverage

Checkpoint supplies, save/failure policy and handoff/resume are shared concepts;
see [the common checkpoint contract](CHECKPOINT_CONTRACT.md). The initial
step/pose/checkpoint codec is implemented separately from the pending evaluated
game-table exports, policy binding and execution parity.

Agreed follow-up: once the small exported FRLG and BDSP checkpoints work,
write the rest of FRLG as shared story-event data, support handoff/takeover for
programs such as RNG manipulation, and execute that data through the shared
story engine with game-specific adapters. This is an implementation plan;
export, JSON binding and handoff/resume are not implemented by this document.

The [shared simulation guide](README.md) defines repository responsibilities:
share versioned plans/maps/scenario inputs and expectations, exercise production
native code and Python models independently, and compare their supported traces.
Keep implementation-specific tests with their owning repository.

## Ordered milestones

Current checkpoint (2026-11-08): FRLG Parcel `00.05` is authored in lean JSON and loaded by the native story table in Arduino #260. Its native Linux/Windows/macOS tests and the paired byte-equality/seven-scenario Python gate pass. PokemonSimulation #73 holds the schema, strict reader and reusable replay engine. The broad native/Python trace-comparison diagnostic (#258) remains separate; live timing, effective runtime policy and full execution parity are not established.

The user chose two practical migration gates: **load the authored data through the existing native story table/engine**, and **run the same JSON through PokemonSimulation**. Keep export snapshots as regression fixtures, not as the authoring format. `declared_after` remains an explicit native fallback, not observed state. This replaces the earlier mandatory export-first sequencing.

1. **Land the FRLG pilot.** Merge PokemonSimulation #73 and Arduino #260 after review. The C++ Parcel event list is removed; save-menu configuration remains game-owned.
2. **Prove the shape on BDSP.** [The mine/Roark pilot](../../data/story/bdsp-mine-pilot/README.md) migrates current #226 revision `0738cd55b` and its 15 events. Preserve BDSP's save-card/failure policy, walking/door variants and multi-tile beliefs. Native integration and Python scenario checks are independent gates; scripted observations cannot prove live transitions or native cost/retry parity. The paired drafts are PokemonSimulation #74 and Arduino #263. Python CI, local native syntax and code health pass; full native CI is running.
3. **Add one handoff/resume example.** Use the actual FRLG starter RNG boundary. Suspend before transfer, verify a linked return receipt/state, and resume once. Reject stale/duplicate/wrong-plan returns and invalidate state affected by reset/load. Do this before scaling the full format.
4. **Write and enable FRLG incrementally.** Migrate existing native checkpoints first, then draft the remaining Pokeguy story through Champion. Track authored, bound and replay-validated coverage separately. Include navigation transitions/recovery and battle histories against pinned data; expose missing map/executor/battle inputs rather than successful placeholders.

The FRLG coverage index should list checkpoint ID, story objective, source
revision/evidence, entering requirements, authored events, execution bindings,
replay coverage and outstanding gaps. This distinguishes a readable full-game
draft from an executable or validated full-game plan. Use existing native
checkpoint IDs where they exist; proposed IDs are explicitly marked proposed.

## One engine, game-owned actions

The wire representation is separate from in-memory types. A shared parser
validates the envelope and resolves versioned symbolic bindings; each game
adapter parses its own typed payloads. Keep the existing runtime-polymorphic
`StoryStepExecutor` boundary unless implementation evidence warrants changing it.
A game's payload may internally be a variant without templating the engine.

The shared engine owns event order, requirement/skip evaluation, attempts,
save/retry policy, suspension/resume and outcome logging. Game executors own
controller actions, observations and game-specific transition/battle semantics.
Python consumes the same events through an offline adapter; it does not send
console input or claim unsupported actions succeeded. Do not create a separate
JSON-only native engine with different ordering or retry behavior.

Unknown action kinds, versions or bindings fail before controller input. An
authored expected effect does not become observed state merely because an
executor returns. Existing native fallback behavior must remain distinguishable
from independent evidence. Strengthening that behavior is a separate tested
change, not an accidental consequence of JSON migration.

## Handoff and takeover

Treat handoff as an explicit event and suspended run state, not a delay, a
successful no-op or an arbitrary shell command. Initial support can be a
user-mediated program switch; a supervised in-process dispatcher can follow.
An RNG program is selected through a registered program/capability binding.

A handoff request declares:

- A stable handoff ID, target program/capability and versioned parameters.
- Entry requirements and the evidence needed to establish them.
- Which state the target may change, including save/reset timeline, party,
  inventory, flags, map and pose; unreported changes remain unknown.
- The continuation event, return requirements, verification bindings and
  bounded failure/retry policy. Resume does not imply retrying the RNG program.

The engine first completes or cancels queued input through the native adapter
and confirms a safe suspension boundary. It writes a durable suspension record
with plan/config/DataPins, checkpoint/event/attempt IDs, current state and its
evidence, save identity/timeline when known, and the continuation. A missing save
identity stays explicitly unknown and may block a continuation that requires it.
Only then may another executor take control. Exactly one executor owns console
actions; switching programs must also respect existing device ownership rules.
Suspending a story does not implicitly release another process's device lease.

The returning program or operator provides a receipt linked to that handoff and
attempt, with outcome, changed-state claims and supporting evidence. Program
completion alone cannot establish the requested RNG result or a safe location.
The story adapter verifies return requirements, invalidates stale derived state,
and resumes at the declared continuation only after verification succeeds.
Mismatched, stale or duplicate receipts cannot advance the cursor twice. Failed,
cancelled or unverifiable returns leave the story suspended or explicitly failed.

If the target loads/resets a save, its return must identify that boundary.
Invalidate pose/route caches and restore or recompute once-per-save preparation,
skip conditions and retry state according to the actual save timeline. Never
carry forward later-story assumptions from the suspended run blindly.

Illustrative FRLG flow, **not a bound executable checkpoint**:

```text
story reaches an evidenced boundary suitable for the selected RNG program
  -> suspend and record handoff H / attempt A
  -> RNG program takes control and returns a result linked to H / A
  -> verify requested result, party and save/location requirements
  -> invalidate state affected by any reset/load
  -> continue at the declared story event, or stay suspended with the unmet input
```

The actual RNG checkpoint, target program, reset behavior and verification
requirements must come from its native implementation; they are not inferred
from this sketch. Python replay uses scripted receipts and evidence, not RNG
hardware execution or an assumed successful outcome.

### Starter RNG return: save before the rival

The first handoff pilot must introduce a dedicated checkpoint immediately after a verified successful Starter RNG return. Confirm the returned starter and an overworld state in which saving is available, save it, and verify save completion **before** moving toward the rival trigger. Only then can a failure reload the new save. A failed/unconfirmed save stops without resetting to the pre-RNG save.

The current native `rows_after_starter_rng()` resumes at the rival portion of `00.04b`, and `after_shiny_starter()` sets `has_save = false` until that row saves after the battle. That is the current implementation, not a verified game restriction requiring delayed saving. Replace that grouping in the handoff slice; do not encode the delay as a universal rule. Native/Python tests must cover saving before the rival, failed/unconfirmed save without reload, and retry from the newly confirmed save. No console validation or production change is claimed by this plan note.

## Acceptance tests

Keep native tests beside their owning sources and Python tests beside their
modules. Share serialized events and scenario inputs/expectations across repos.

- The first two checkpoints preserve ordering and every active field across
  export/import; scripted native and Python replay agree on supported outcomes.
- Unsupported bindings, unmet prerequisites and unconfirmed effects cannot
  advance execution. Test interruption and exhausted recovery as well as success.
- Handoff sends no further story input while suspended. Resume succeeds once
  with verified state; stale/duplicate/wrong-plan receipts, missing observations,
  cancellation and target failure cannot silently advance the plan.
- Reset/load during handoff invalidates stale state and respects once-per-save
  and retry semantics. Queue cancellation and exclusive executor ownership have
  native tests; offline replay alone cannot verify controller timing.
- The FRLG coverage index accounts for every main-story segment and labels
  authored, bound and replay-validated coverage separately. Missing coverage is
  visible rather than represented by placeholder actions that report success.

## Full FRLG world and Pokeguy plan expansion

The user also requests all FRLG maps and a full story-event plan following
Pokeguy's reviewed LeafGreen run through the first Champion victory. Keep
this expansion as separate reviewable slices from native capture/import.

1. Inventory the complete pinned `pret/pokefirered` map catalog and stage a
   full-map candidate. The current source pin contains **425 distinct maps**;
   the approved runtime pack contains **53**, leaving **372** uncovered. This
   includes optional/postgame/link maps as catalog data, even though the first
   story plan ends at Champion. Record exclusions and unsupported mechanics.
2. Extend the builder beyond its current selected-map mode. Audit all warp and
   edge destinations and unsupported behaviors before approval. The current
   builder reports some non-collision behaviors as floor and pre-opens certain
   scripted tiles (for example Vermilion Gym beams); that is not sufficient for
   a stateful full-game plan. Preserve source-baseline versus corrected or
   story-state geometry, and expose unresolved cases rather than inventing
   walkability. Check source game/version differences against the LeafGreen run.
3. Publish the reviewed full-map pack with regenerated manifests/hashes, then
   adopt the approved revision in native consumers. Adding destinations can
   change existing maps' warp/connection links; review those changes explicitly.
   Do not overwrite the approved 53-map pack with unreviewed generated output.
4. Author a complete Pokeguy story-event draft, by named story segments. Reuse
   `data/runs/pokeguy-leafgreen-15934/` for the 69 trainer battles, wild defeats,
   captures, EXP/EV, move and inventory evidence. Extend it with traversal,
   conversations, key-item/HM use, purchases, heals, puzzle/flag changes and
   map transitions. Preserve video timestamps and source-note provenance.
5. Link every draft event to a game binding, map/landmark, state requirements,
   expected effects, evidence status and outstanding uncertainty. Existing
   battle/progression ledgers do not prove tile paths or all overworld actions.
   Missing coordinates/bindings must remain unresolved, not successful no-ops.
6. Enable and replay supported segments incrementally through the shared
   engine after the two-checkpoint parity gate. Compare generated battle/state
   histories against existing ledgers and report event/map/executor coverage.

Use readable symbolic goals where available. Distinguish this speedrun plan
from the native hand-run AutoStory table (including the current Parcel capture)
and from recommended non-speedrun healing/preparation variants. Full authored
coverage can precede full execution support; label both honestly.

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

## Ordered milestones

Implementation checkpoint: the [Parcel Python diagnostic](../../data/story/parcel-pilot/README.md)
binds the captured events to approved maps and synthetic observations. Native
trace comparison, actual runtime/save/retry policy export and BDSP capture remain
open; this is not completion of milestone 1.

1. **Prove the event boundary.** Export evaluated FRLG Parcel `00.05` and BDSP
   mine/Roark `01.03` checkpoints, preserving their complete actions, conditions,
   game extensions and save/retry behavior. Bind the same serialized data to
   native scripted execution and Python replay. Compare ordered actions, state
   evidence, interruptions and failures, not just whether both runs finish.
2. **Make shared events executable.** Add strict parsing and binding around the
   existing shared native engine and per-game executors. Author these two
   checkpoints as data only after parity passes; remove their duplicate C++
   authoring. Include a handoff/resume example before scaling up the format.
3. **Write the complete FRLG plan.** Use the readable, symbolic style of the
   [PLZA draft](PLZA_OPENING_DRAFT.md), with checkpoint requirements, actions,
   expected effects and unresolved bindings. Cover the selected main story from
   new game through the first Champion victory; track postgame separately.
   Migrate existing native checkpoints first, then draft uncovered sections.
   Full authored coverage can precede full executor coverage, but each section
   must state which it has. No invented routes, party state or battle win rates.
4. **Bind and evaluate incrementally.** Enable supported FRLG checkpoints in
   order; replay navigation, transitions, recovery and battle histories against
   pinned data. Report missing maps, executors or battle inputs as blockers.
   Repeat the proven shared contract for BDSP without assuming FRLG semantics.

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

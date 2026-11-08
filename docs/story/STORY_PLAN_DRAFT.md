# Story plans: early wire-format draft

Checkpoint supplies, save/failure policy and handoff/resume are shared concepts;
see [the common checkpoint contract](CHECKPOINT_CONTRACT.md). The initial
step/pose/checkpoint codec is implemented separately from the pending evaluated
game-table exports, policy binding and execution parity.

**For review, not execution.** Start by serializing the evaluated native tables
and binding them to the existing executors. The games already share ordered
`StoryStep`/`StoryCheckpoint` records and `StoryStepExecutor`; their behavior and
checkpoint extensions differ substantially. Sharing JSON must preserve those
differences. This draft does not add a second story engine or a console runner.

Read the [FRLG Parcel example](examples/frlg-parcel.draft.json) (3 authored events)
and [BDSP mine/Roark example](examples/bdsp-mine-roark.draft.json) (16 authored
events). They are hand transcriptions of the complete **authored rows**, with
source revisions/file hashes. They are not native exports or lossless native
round trips. Program-generated saves/reloads, options, implicit defaults and
runtime state still require exporter support and are marked unbound.

The [PLZA opening draft](PLZA_OPENING_DRAFT.md) adds a third-game design probe:
intro plus Main Missions 01–03, with real-time battles, capture/research goals
and symbolic landmarks. It is guide-authored; none of its game profiles are
bound to an exporter, executor or simulator yet.

The [execution follow-up](EXECUTION_PLAN.md) specifies the shared engine/adapters,
program handoff/resume contract, and complete FRLG story coverage after the
first real checkpoint exports prove the format.

## Where the two shapes actually differ

| Concern | FRLG | BDSP | Shared contract |
|---|---|---|---|
| Checkpoint extras | Supplies, START-menu shape, live-start and RNG handoff | Failure/save policy and expected save-card location | Typed checkpoint extension, not a universal flat record full of irrelevant fields |
| `ROUTE.variant` | Running with B versus walking | Planner cost profile: default, town, robust, line | Goal + game movement/planning profile; running and route costs are separate concepts |
| `LEGS.variant` | Movement mode; legs receive FRLG walker semantics | Counted taps, wall holds, dialogue/map-banner variants | Fixed leg data + explicit execution profile; a tile count is not automatically a safe wall bound |
| `STEP` | Commonly one trigger/door/ledge step; variants for trainer sight | With a different `pose_after.map`, the default may run through a doorway until fade and settle | Adapter-defined action, not one universal button press or one-tile displacement |
| Scene | FRLG dialogue/scene executor | Prior door action may already have consumed the arrival dialogue; A/B variants | Scene intent with explicit observation/effect ownership; do not apply its effects twice |
| Position | Often one tile; facing can be unknown | Tile sets, named regions, adjacent-door alternatives, rooms without known tiles | Tagged pose belief and frame, not one mandatory coordinate |
| Battle readiness | Supplies and move knowledge plus battle policy | Different party, ruleset and executor configuration | Explicit requirements and pinned game rules; unknown party/HP/bag never becomes a default win rate |

Both have native `GAME` actions. Route and scene actions can also have special
per-game semantics; do not reserve extensions only for `GAME` and assume every
other kind is identical. `skip_if`, preparation once per save, handoff/resume
and failure handling must survive export where supported. The native `skip_if` means all named conditions hold and the list is nonempty;
an empty list must not skip every action. The FRLG snapshot also has
`once_per_save` while the inspected BDSP shared header lacks that field, so
capabilities must be tied to the actual executor revision, not just the game
name. A failed/unsupported action cannot be skipped as a successful no-op.

Concrete example: BDSP `01.03/into_the_coal_room` is authored as `STEP SOUTH`,
but it goes from the entrance hall into B2F. Treating that record as a single
tile move would give a very different simulation. Its action profile and
unconfirmed arrival need to be resolved by the BDSP adapter.

## Proposed record shape

A plan has game/version, source/plan identity, **DataPins**, requirements, runtime
execution settings, and ordered checkpoints. Each checkpoint has its start
belief, save/retry/handoff policy, game extension and ordered events. Each event
has a stable ID, reason, action, requirements/skip conditions, expected effects,
observation policy and bounded recovery where supplied. Event IDs are scoped by
plan/checkpoint; retries add attempt IDs, not duplicate semantic event IDs.

An action is a tagged common record (`route`, `legs`, `step`, `talk`, `answer`,
`scene`, `battle`, `train`, `heal`, `shop`, `save`, `ready`, `game_action`) with
only the fields relevant to that action. `game` carries a namespace, payload
version, profile and typed parameters. The examples initially retain the native
`variant` in those parameters so migration cannot quietly reinterpret it.
Those names need a versioned binding catalog before any execution.

```json
{
  "id": "south_to_the_rock",
  "action": {
    "kind": "legs",
    "legs": [{"direction": "south", "tiles": 8}],
    "game": {"namespace": "bdsp", "version": 1, "profile": "legs", "parameters": {"native_variant": "to_wall"}}
  },
  "declared_after": {
    "pose": {"map": "OreburghMine", "frame": "runtime-local", "where": {"kind": "tiles", "tiles": [[15, 10]]}, "facing": "south"},
    "evidence": "authored-native-fallback"
  }
}
```

This is the source table's claim, **not a verified wall or measured arrival**.
The mine map is an explicit blocker in the BDSP example. A simulated hold must
prove safe convergence from the actual belief, respecting warps and interrupts;
an executor reporting completion does not authorize replacing the belief with
`declared_after`. The native fallback is retained for review, not promoted into
new observation evidence. For parity, keep the native declared/reported pose
separate from the independent physical pose belief. Exporting existing fallback
behavior does not change it; strengthening live confirmation needs its own native
behavior change and regression tests.

**DataPins** identify exact inputs: map publishing revision + manifest hash,
trainer/species/move/item data and ruleset revisions, and executor/profile schema
versions. They differ from the native program source revision and from a save
identity. A candidate map pin is not a bound compatible map. The BDSP example
keeps its candidate unbound because the native tree contains unresolved map
deltas. Both examples leave the executor binding and battle rules unbound.

**Pose** has map/frame, a tagged location (`tiles`, named point/region, alternatives,
or explicitly unknown) and optional facing/elevation as supplied. A missing
facing is unknown, not north. Two candidate tiles must remain two candidates.
Named-point offsets are resolved only against the bound map; an unbound point
cannot be replaced with a guessed coordinate. A room name without tiles is not
an empty navigable map. Save-card town text alone does not prove a tile pose.

**Requirement** is a typed predicate with scope and an evidence policy. Examples:
`bag_at_least(item="potion", quantity=1)`, `party_move_known(slot=0, move="cut")`,
`pose_in(belief)`, `story_flag(...)`, `save_location(...)`. These are illustrative
predicates, not new requirements asserted for either example. Distinguish
minimum quantities from exact inventory and observed facts from author
assumptions. Runtime option references (starter, language, check level, strategy)
are resolved from a recorded run configuration, not implicit Python defaults.

The examples keep `party`, `inventory` and story flags **unspecified**. FRLG's
value-initialized native `Supplies` record is an executor bookkeeping default,
not evidence that the loaded bag is empty or the starter is healthy. No battle
probability should be produced until its actual inputs are available.

## Types, parsing and execution

Keep the JSON storage format separate from the in-memory action types. A game
payload `T` can indeed be a `std::variant` of its own actions. That need not
force the shared engine itself to become a template.

For the first implementation, retain the existing runtime-polymorphic
`StoryStepExecutor`: parse/validate the common envelope, let the selected game
adapter parse its versioned profiles into game-owned typed actions, then bind to
the current shared/game checkpoint types. No function pointers or closures are
serialized. An adapter must reject an unsupported profile before input is sent.
A universal unvalidated `map<string, JsonValue>` is not an execution contract.

The same wire records can feed a Python adapter. It must return unsupported or
needs-input for actions it cannot model; navigation-only playback cannot claim
the story, scene effects, purchases or battles have succeeded. A templated
`Action<T>`/engine remains an implementation option if it later simplifies the
native binding; it should not decide the wire format now.

Outcome types should distinguish these concepts:

| Type | Contents / meaning |
|---|---|
| `ActionStatus` | completed, already satisfied, failed, unsupported, needs input/observation |
| `Observation` | Actual screen state, map/pose belief, party/bag reads, timestamp/frame and evidence reference; omissions remain unknown |
| `EffectEvidence` | Claimed effect plus basis: observed, source-derived expectation, or authored assumption; which action/observation supports it |
| `Failure` | Stable code, event/attempt ID, known state and uncertainty, recoverability and exhausted budget |

For example, seeing the overworld return after the Parcel scene does not by
itself measure the bag's item count. Preserve source-derived expected receipt
separately from an observed inventory update. A transition that already played
a scene can mark that scene already satisfied only with appropriate evidence.

A run log references the plan/config and DataPins, then records ordered action
requests, observations, outcomes, interruptions and recovery. Do not overwrite
planned targets with observations or use a successful route as proof of battle
readiness. Save/reload boundaries invalidate transient state and one-time
preparations according to the actual native policy.

## Small next implementation

1. Native offline exporter emits the evaluated FRLG `00.05` and BDSP `01.03`
   rows, their game extras, resolved defaults/runtime configuration, symbolic
   bindings and save/attempt envelopes. Compare event order, every active field
   and poses against the actual native tables in registered native tests.
2. Agree on the profile catalog and schemas using those exports. Add strict
   JSON parsing/binding and round-trip tests in each native owner. Preserve
   meaningful zero/false; absence is allowed only where the schema defines it.
3. Replay the same exported data through native scripted executors and Python,
   comparing actions, beliefs, effects and failures. Unsupported scenes/battle
   inputs remain explicit gaps. Only then move authored checkpoints out of C++.

The early examples intentionally do not claim a schema validator, native
exporter, battle simulator binding or end-to-end story execution exists yet.
Their point is to review the boundary before encoding accidental differences as
universal behavior.

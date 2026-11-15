# Shared checkpoint state and policy

Checkpoint supplies, save/retry behavior and handoff/resume are shared concepts.
FRLG and BDSP currently store them in different native checkpoint extensions;
the target wire envelope should organize them by meaning, not game name.

This is the envelope design accompanying the first implemented common-record
codec. Evaluated game-table export, envelope binding and execution parity remain
pending. The existing hand-transcribed examples remain review inputs.

## Common fields and game bindings

| Shared field | FRLG today | BDSP today | Target meaning |
|---|---|---|---|
| Entry requirements | Start pose; additional checks in the executor | Start pose and save-card location check | Predicates required to start, with observation requirements; unknown party/bag stays unspecified. |
| Tracked state | `Supplies`, including item counts, party moves/PP and battle observations | Tracked separately in executor/walker state | Typed state plus its evidence basis. A constructor default is bookkeeping, not an observation or an entry requirement. |
| Entry mode | `live_start` for RNG takeovers | Usually reload/start from the row's save | Load the checkpoint save or verify the current live state. |
| Save policy | Save at checkpoint end, with `StartMenu` layout | Save before the row, validated with `saves_in` | Before/after/never, expected save location, and a versioned save/verification binding. |
| Failure policy | Shared segment attempts/recovery options | `StoryFailure` plus segment attempt options | Stop or bounded recovery/reload/retry; effective limits come from resolved run options. |
| Handoff | SID Helper, Starter RNG, Gift RNG | No corresponding authored row yet | Registered program/capability, suspension boundary, receipt and verified continuation. |

A save-menu layout remains a parameter of the game adapter's save binding.
The decision to save, its timing and its required result belong to the shared
policy. Likewise, a display string such as `Oreburgh City` is interpreted by a
save-location binding; it is not a measured map/tile pose.

Both games can use every shared policy. Absence of an authored BDSP handoff does
not require a different engine or a BDSP-only checkpoint type.

## Proposed envelope

A future `pokesim-story-plan/1` envelope carries:

- Source identity and DataPins: exact maps, rules/data and binding revisions.
- Resolved runtime configuration, or explicit unbound inputs before execution.
- Entry requirements and tracked state, kept separate.
- Common entry/save/failure/handoff policy with effective bounds.
- The ordered common checkpoint record and its game-specific action bindings.

Bindings select registered capabilities with versioned typed parameters. They
are not executable callbacks, shell commands or a universal unchecked dictionary
that the engine treats as successful. Unknown bindings fail before input.

An adapter exports what its native implementation actually supplies. For example,
FRLG Parcel's value-initialized `Supplies` must be labeled native bookkeeping;
it does not prove an empty bag, full HP or the current moves. BDSP's save-card
check verifies a location label, not a starting tile. Neither becomes evidence
merely because a JSON record contains the expected value.

Policy defaults must be specified once in the shared contract. Exporters must
not replace unresolved run-option values with guessed attempts, speed, language,
starter or battle strategy. Exporting current behavior precedes changing it.

## Implemented common record boundary

The native `Pokemon_StoryStepJson` reader and Python
`pokesim.story.checkpoint_wire` (`read_story_checkpoint`, `read_story_step`,
`read_grid_pose`, `read_declared_pose`) read these records:

```json
{
  "id": "example",
  "title": "Synthetic checkpoint",
  "start": {"map": "ExampleMap", "tiles": [[1, 2], [1, 3]]},
  "events": [
    {"id": "to_door", "kind": "route", "args": {"target": {"map": "ExampleMap", "tiles": [[4, 0]], "facing": "north"}}},
    {"id": "buy", "kind": "game_action", "action": "mart", "args": {"map": "ExampleMart", "budget": 3000}},
    {"id": "answer_no", "kind": "answer", "args": {"yes": false}}
  ]
}
```

This is a codec example, not an exported game plan. The common record has no
implicit save, retry, handoff, inventory or observed effects. Those need the
validated envelope and game bindings above. Loading this record does not run it.

A step names an `action` (empty: its kind's default) and the `args` that action
takes. The built-in actions are `route` and `ready` (`target` pose), `legs`
(`legs`, `fight_wild`), `face` (`direction`), `answer` (`yes`), `fight`
(`may_lose`), `train` (`battles`) and `shop` (`items`); a game adds its own,
each arg typed (boolean, integer, word, direction, grid_pose, legs, words,
items, integer_rows, timed_legs) and required or given a fallback. Both readers
check the args against the action's spec and fill in the fallbacks. Native
`MASH` is named `scene`; `GAME` is `game_action` and must name its action.

A pose is `{"map", "tiles", "facing"}`: several tiles are alternatives, no tiles
is any tile of the map, and an absent facing is unknown. A `start` or
`declared_after` may instead be a zone, `{"place", "spot", "heading"}`, for a
game with no tiles. A `declared_after` is the fallback declaration, not an
observation. Unknown fields, kinds, actions and args, missing required args,
malformed pairs, duplicate event IDs and invalid primitive types fail.

The authored plans in `data/story/` and the replay still use the older record
(poses with `certainty`/`where`, per-kind step fields, `variant`, `sections`
and `notes`), read by `read_checkpoint`; the native reader no longer reads it.
`schemas/story-checkpoint.schema.json` describes only that older record, not
the v2 common record. For v2, `pokesim.story.checkpoint_wire` and
`data/story/wire-conformance.json` are authoritative.

## Validation and next slice

`data/story/wire-conformance.json` (`pokesim-story-wire-cases/2`) holds
synthetic input/expectation vectors for every step kind, the built-in and test
game actions (declared in its `actions`), poses and checkpoints. An accepted
case's `read` is the record as read, args with their fallbacks. Python and the
native reader consume the same file. These tests are not captured controller
replay.

Next, export evaluated FRLG `00.05` and BDSP `01.03` through game adapters that
populate the shared envelope, then compare all native fields and policy/state
initialization. Bind the same serialized records into the existing engine and
Python replay before replacing either game's C++ authoring tables. Full FRLG
coverage and verified RNG handoff/resume follow that parity gate.

The first native authored-table capture adapter and strict importer are described
in [Native exports](NATIVE_EXPORTS.md). Captures preserve raw fields and keep the
policy/state/execution envelope explicitly unbound.

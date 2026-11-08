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

The new native `Pokemon_StoryStepJson` codec and Python
`pokesim.story.checkpoint_wire` reader cover these records:

```json
{
  "id": "example",
  "title": "Synthetic checkpoint",
  "start": {"map": "ExampleMap", "certainty": "set", "where": {"kind": "tiles", "tiles": [[1, 2], [1, 3]]}},
  "events": [{"id": "answer_no", "kind": "answer", "yes": false}]
}
```

This is a codec example, not an exported game plan. The common record has no
implicit save, retry, handoff, inventory or observed effects. Those need the
validated envelope and game bindings above. Loading this record does not run it.

The codec retains every shared `StoryStep` field, including `variant`, `skip_if`,
`fight_wild`, `may_lose`, training count, items and declared arrival. Native `MASH`
is named `scene`; `GAME` is `game_action`. A `declared_after` is the native
fallback declaration, not an observation. Optional start/target/arrival poses
preserve absence, certainty, tile alternatives and unknown facing.

Only declared native defaults may be omitted: empty text/lists, north input
direction, false `fight_wild`/`may_lose`, true `yes`, and zero `battles`. In
particular, `yes: false` survives. A north action direction is an input parameter;
an absent pose facing remains unknown. Zero coordinates and zero quantities or
leg counts remain intact. Structural encoding does not approve a zero-quantity
shop request or prove a route feasible; native authoring/execution validation
still applies after binding.

Unknown fields, action/position tags, malformed pairs, duplicate event IDs and
invalid primitive types fail. Native non-tile `Position` subtypes are unsupported
rather than converted to an empty belief. The first FRLG/BDSP adapters will bind
these tile poses to their runtime-local frames through pinned map identities.

## Validation and next slice

`data/story/wire-conformance.json` contains synthetic input/expectation vectors
for every common step kind and the difficult defaults/uncertainty cases. Python
and the native executable consume the same data. Native-only cases cover the
in-memory boundary. These tests are not captured controller replay.

Next, export evaluated FRLG `00.05` and BDSP `01.03` through game adapters that
populate the shared envelope, then compare all native fields and policy/state
initialization. Bind the same serialized records into the existing engine and
Python replay before replacing either game's C++ authoring tables. Full FRLG
coverage and verified RNG handoff/resume follow that parity gate.

# Shared story data and simulation testing

PokemonSimulation and Arduino-Source should consume the same versioned story
plans, approved maps and regression scenarios. Each repository tests its own
implementation. Maintain one scenario with shared inputs and expectations,
not two handwritten copies of its route or story.

## What each repository verifies

| Responsibility | Arduino-Source | PokemonSimulation |
|---|---|---|
| Story execution | Exercise the production C++ engine and game executors with simulated observations. | Interpret shared event data through Python game models for offline evaluation. |
| Navigation and recovery | Verify the actual planner/walker, movement accounting, queued-input handling and recovery/rejoin behavior. | Check map geometry, movement rules, uncertainty, safe anchors and plan feasibility. |
| Battles and resources | Verify native battle action selection, observations and executor integration. | Evaluate battle risk, progression, inventory and preparation policies using the appropriate game rules. |
| Evidence limits | Simulation does not establish real detector accuracy, controller timing or game behavior. | Python agreement does not establish correctness of the production C++ code or hardware execution. |

These are ownership boundaries, not a claim that every capability is implemented.
The existing shared native engine remains the execution engine; loading JSON
must not introduce a second native engine with different ordering/retry rules.
The Python interpreter is an independent offline implementation of the shared
contract, with explicit limits on supported game actions.

## One scenario, two consumers

A shared fixture should record:

- A stable scenario ID, source revision/checkpoint/run evidence and evidence
  status: observed, source-derived or synthetic.
- Immutable plan/map/fixture identities and relevant game/version/policy inputs.
- Initial state and uncertainty: map, pose candidates, facing, flags, inventory
  and any observations or queued movement needed by the scenario.
- Actions and injected observations/interruptions, followed by explicit expected
  state, evidence, recovery, failure or suspension outcomes.

Use separate `input` and `expectation` records. Both implementations consume the
same fixture and check the fields they support. Coverage reports must identify
unsupported fields rather than dropping them or treating them as success.
Consumers pin published revisions/hashes; they must not independently edit
copied fixtures. Change the canonical scenario, review it, then update pins.

For example, a BDSP southward walk interrupted by a wild battle can leave two
possible tiles. Native tests verify the production walker does not turn a
nominal step count into confirmed displacement, and that recovery/replanning
uses the surviving hypotheses. Python checks the same possibilities and whether
a bounded wall maneuver safely converges. Both assert the specified outcome;
trace comparison exposes disagreements in intermediate state or semantics.
This example does not assert that every interruption leaves exactly two tiles.

Keep expectations independent of the implementation under test where possible.
A captured native report is useful replay evidence, but reproducing it in Python
is not an independent proof that the native result was correct. Preserve source
or run evidence and negative controls, and label reconstructed/unreported fields.

## Which tests should run twice?

Run a small shared conformance suite on both sides for supported story ordering,
requirements, transitions, interruption/recovery and explicit failure semantics.
Compare meaningful traces: event order, state/evidence changes, pose hypotheses,
recovery/rejoin decisions and failure or suspension outcomes. Finishing both
runs is insufficient. Require identical route/leg choices only when their
planner policies and cost models match; otherwise compare the agreed invariants.

Keep detailed implementation tests with their owner: C++ queue/controller and
detector integration tests in Arduino-Source; Python data validation, progression
and large battle-probability analyses here. Do not port every unit test to the
other language. A discovered cross-repository regression should become a shared
case when both implementations support the relevant behavior. Tests stay beside
their sources in each repository.

Neither suite replaces console validation. In particular, simulated stillness
or a modeled warp does not prove that the real detector confirmed a wall or
transition at the right time.

## Current status and next gate

Implemented here:

- [Pinned navigation conformance](../navigation/CONFORMANCE.md), consumed by
  Python and native game adapters.
- [Native recovery report replay](../navigation/ENCOUNTER_RECOVERY.md), with
  documented limits on facing, queued input, timing and reconstructed state.
- [FRLG Parcel `00.05` capture/import validation](NATIVE_EXPORTS.md), from the
  evaluated native table. This validates authored data, not story execution.

Next: bind Parcel's maps, actions, requirements, entry evidence and effective
save/retry policy, then exercise the same serialized events through the existing
native engine and Python replay. Cover success, interruptions, unmet requirements
and unsupported bindings before replacing duplicate native authoring tables.
Unknown bindings must fail before execution; expected effects cannot substitute
for observations. Add the evaluated BDSP mine/Roark `01.03` capture and repeat the
contract with BDSP semantics.

The [execution plan](EXECUTION_PLAN.md) tracks implementation, handoff/resume and
full PokeGuy FRLG authoring. The [checkpoint contract](CHECKPOINT_CONTRACT.md),
[native export boundary](NATIVE_EXPORTS.md) and [story draft](STORY_PLAN_DRAFT.md)
distinguish existing exchange data from proposed executable plans. Full authored
coverage, bound execution and validated replay remain separate milestones.

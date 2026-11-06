# Exact encounter-recovery state checks

This adds four Python semantic diagnostics to the #45 inventory. They establish
an exact expected-state oracle for the next native log adapter; they do **not**
yet establish native encounter/controller parity. The eight spatial fixtures
from #46 remain the currently shared native/Python contract.

```sh
PYTHONPATH=src python3 -m pokesim.cli.transitions \
  --case logan-interrupted-queued-leg --output /tmp/recovery.json
PYTHONPATH=src python3 -m pokesim.cli.transitions \
  --case forest-interrupted-warp-approach --output /tmp/forest-recovery.json
PYTHONPATH=src python3 -m unittest pokesim.maps.test_transition_replay \
  pokesim.maps.test_transition_state
```

The catalog still pins the unchanged #44 map bytes. Each new case identifies
its source map/run context in `evidence` and labels the injected sequence in
`derivation`. An injected battle/observation is not a captured detector result.
No pending mine/house terrain corrections are imported.

| Case | Required behavior |
|---|---|
| `logan-interrupted-queued-leg` | From Route 202 `(26,5)`, two east inputs plus one queued east input leave all four prefix tiles `(26..29,5)` possible after a wild interruption. Facing is unknown. Recovery before drained inputs fails without spending a retry. An east clip predicts `(30,5)` but does not confirm it. Frozen video cannot confirm a wall. Advancing stillness plus drained inputs confirms `(30,5)`, facing east; a supplied west leg then reaches `(29,5)`. |
| `logan-recovery-budget` | Three interrupted clips consume the shared attempt budget. The fourth fails, clears trusted poses and prevents continuation. Escaping battles does not replenish retries. |
| `logan-npc-cannot-confirm-anchor` | North clipping from the Logan hypotheses is unsafe because Logan occupies `(26,4)`. Recovery fails and latches; a later precise pose report does not silently clear that failure. |
| `forest-interrupted-warp-approach` | An interrupted north input plus queued north input near the Forest cave keeps both source-map and gate-arrival hypotheses. Drained map evidence narrows this to two Forest tiles, with unknown facing. North clipping must fail because the ray reaches a warp rather than a safe wall. |

The explicit west leg in the first case tests continuation **from the confirmed
anchor**. It is not evidence that native/Python planners choose the same route,
or a full automatic route-cursor rejoin test.

## Exact expectation format

New events use `{"event": "expect", "state": {...}}`. The state must contain
all fields below and no extras:

```json
{
  "belief": [
    {"map": "Route202", "tile": [30, 5], "facing": "east", "elevation": 0}
  ],
  "can_resume": true,
  "screen": "overworld",
  "queue_drained": true,
  "awaiting": false,
  "remaining_recoveries": 2,
  "failure": null
}
```

`belief` is the complete list of hypotheses, sorted by map, x/y, elevation,
then facing (`null` before named directions). Unknown facing is `null`, not the
last commanded direction. JSON types are compared exactly: `false` differs
from `0`. Wrong tiles/facing with the same candidate count fail. Older
`candidates`/`can_resume` assertions remain supported for historical cases.
Trace records now also expose `awaiting`, matching the state expectation.

The Forest case uncovered a missing `Place` import in trainer-sight hazard
handling. It previously raised `NameError` when a visible trainer supplied an
open sight ray. The fix retains the hazard exclusion, with a separate synthetic
trainer-sight clipping regression. It does not relax terrain or recovery safety.

## Next native acceptance gate

Retain the existing registered FRLG/BDSP walker tests. Add native event exporters
or adapters that produce these same state records from actual walker reports,
including completed-count bounds, queued/cancelled input, map evidence and
unknown facing. First match the candidate sets and recovery budgets. Then match
confirmed anchor and route rejoin outcomes. Unsupported trainer approach,
transition evidence or escape outcomes must be reported rather than guessed.

Native controller and detector timing remain Arduino tests. BDSP mine/house
same-map conformance still requires reviewed map/arrival alignment. Neither
these diagnostics nor a passing spatial prediction proves live recovery safe.

## First actual native replay: BDSP Route 202

The next slice exports seven **registered native C++ tests**, running the real
BDSP route planner and `walk_route()` through its existing `GridSimRouteIO`.
[The captured bundle](../../data/navigation/native-recovery/bdsp-route202.json)
contains actual I/O reports, physical simulated poses, returned positions and
shared `[Route]` plan/replan/end logs. Python replays those native-selected legs
on the same map bytes; it does not choose replacement routes or copy the native
recovery algorithm.

All cases start at Route 202 `(26,5)`, facing east, targeting `(28,5)`.
`VAR_ROUTE_202_STATE=1`, Running Shoes available, and native movement policy RUN
are explicit preconditions. The map SHA256 matches the approved publishing
revision in the bundle. These remain injected, already-cleared encounters on a
real map, not recorded console inputs or an encounter-escape simulation.

| Native case | Checked outcome |
|---|---|
| `last-tap-before` | The second east tap is interrupted before movement: credit is 2 chunks but physical position is `(27,5)`. Native retains candidate tiles `(26..28,5)`, anchors east at `(30,5)`, then replans/walks west to `(28,5)`. |
| `last-tap-after` | The interrupted tap physically finishes at `(28,5)`. Native conservatively retains the same candidates, anchors and returns correctly. |
| `interrupted-wall-retry` | First recovery hold is interrupted; the second reaches the wall and the route reaches its original goal. |
| `last-wall-retry-succeeds` | Three interrupted wall holds, then success on the fourth wall attempt. |
| `interrupted-wall-budget` | Four interrupted wall attempts exhaust the native limit. No arrival or trusted returned pose is exported. |
| `first-tap-unknown-origin` | Encounter on the first input may predate this leg; fail before any recovery hold. |
| `reported-unknown-origin` | An explicit MAY_PRECEDE_LEG report likewise fails before recovery. |

**The retry policies differ.** Native BDSP permits an initial wall attempt plus
three retries for that wall leg. Python `Session` defaults to three recovery
calls total across a session. This slice measures the native policy explicitly;
it does not equate the two budgets or change either policy.

Native `walk_route()` returns positions without facing evidence, so exported
`declared` poses keep facing `null`. `physical` facing comes from GridSim and is
checked independently. Native internal facing belief, queue draining, advancing
video/stillness confirmation, detector timing and a global retry budget remain
**unverified**. A native `(walked)` log is preserved as its stated basis; an
`(assumed)` end cannot silently pass as a walked end in this profile.

```sh
# Check the reviewed native capture against current hash-matched map bytes.
PYTHONPATH=src python3 -m pokesim.maps.bdsp_native_recovery_replay check

# Also verify exporter/map Git blobs at the recorded native source revision.
PYTHONPATH=src python3 -m pokesim.maps.bdsp_native_recovery_replay check \
  --native-source /path/to/Arduino-Source

# After successfully running the registered native tests, wrap their stdout.
# Fetch the publishing repo first: capture trusts cached origin/main.
PYTHONPATH=src python3 -m pokesim.maps.bdsp_native_recovery_replay capture \
  --stdout /tmp/native-test-stdout.log --native-source /path/to/Arduino-Source \
  --source . --trace /tmp/bdsp-route202-candidate.json
```

The exporter emits `POKESIM_NATIVE_REPLAY` only after each native case's own
assertions pass. Capture requires the complete seven-case inventory and a clean
committed native worktree, verifies matching native/published map bytes and
records the full native revision plus exporter checksum. The exporter rejects
fractional simulated positions instead of rounding them to tiles. It does not attest that
a particular executable was built from those Git objects; retain the successful
native build/test record alongside a regenerated capture. The default checker
verifies local map bytes and semantics; optional native-source checking verifies
Git provenance, not remote publication approval of the native candidate.

The native exporter is locally committed on `bdsp/native-route-replay` at
`0bd414eabe477beb2be044cfe5057c5bec548db6`, based on the prepared #46 native
adapter. Its three-file change adds tests/export only. All 61 focused registered
BDSP tests pass locally, including the seven exports; code health passes
against `bdsp/navigation-conformance`. The focused runner compiles actual native
movement/planner/walker sources; unused image I/O stubs throw if invoked.
Focused and broader runs produce identical seven-case captures. Native publication and GitHub CI remain
pending the initial-push approval. No runtime recovery algorithm or terrain was
changed by this slice.

Next: add the corresponding actual FRLG walker export; expose and test missing
queue/observation/facing facts, then compare complete #47 state snapshots. The
current BDSP replay proves candidate-tile and supplied-leg geometry agreement,
native automatic recovery/rejoin outcomes, and the explicitly tested native
retry/origin rules. It is not yet full native/Python state-machine equivalence.

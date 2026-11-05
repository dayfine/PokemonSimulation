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

# Shared navigation conformance

The first pack contains **eight exact spatial fixtures**, consumed independently
by Python and registered native C++ tests. It is deliberately smaller than the
uncertainty/observation inventory in [TRANSITION_SCENARIOS.md](TRANSITION_SCENARIOS.md).
It caught a real Python discrepancy: omitted FRLG elevation grids must default
to ground level **3**, as native `elevation_at()` does, rather than 0.

The canonical data is [cases.json](../../data/navigation/conformance/v1/cases.json).
Case rows have separate `input` and `expectation` objects. Maps are identified by
game, name and exact raw-byte SHA256, with an immutable reviewed map revision.
All coordinates use `runtime-local`; an elevation or facing difference fails.

```sh
PYTHONPATH=src python3 -m pokesim.maps.conformance
PYTHONPATH=src python3 -m pokesim.maps.conformance --game bdsp
PYTHONPATH=src python3 -m unittest pokesim.maps.test_conformance \
  pokesim.maps.test_conformance_sync
```

The runner checks on-disk map hashes; it does **not** approve publication or
establish that those maps match a console. `conformance_sync` separately checks
Git source provenance and approval of the pinned map revision. Existing
`consumer_sync` map adoption protections remain in place.

## Cases and evidence

The map pin is Simulation #45's main revision
`4f6db528960e305cf49c53c89ec91adbffb168a9`. No terrain corrections from pending
Arduino #226 were imported. The raw maps are unchanged from #44.

| ID | Input and exact expectation | Evidence / scope |
|---|---|---|
| `frlg-forest-north-entry` | Forest `(5,10)` north twice → north gate `(7,10)` north, then `(7,9)` north. | Forest gate entry from the #213/#216/#224 scenario inventory; reduced spatial diagnostic, not a native story replay. |
| `frlg-north-mat-north` | Gate's south mat `(7,10)`, north → `(7,9)` on the same map. | Native directional-mat rule; pressing away from a mat must not warp. |
| `frlg-north-mat-return` | Same mat, south → Forest `(5,10)`, facing south. | Mat departure plus cave arrival's automatic south walk-out. |
| `frlg-route2-gate-entry` | Route 2 `(5,52)` north → south gate `(7,10)`, facing north. | Route 2 gate warp metadata. |
| `frlg-cerulean-edge-round-trip` | Cerulean `(22,0)` north → Route 24 `(10,39)`; south returns exactly. | #216/#219 bridge/border context; exercises offset 12, **not** connection timing. Rival hide flag explicit. |
| `bdsp-route202-open-step` | Route 202 `(27,5)` east → `(28,5)`. | Control case on the byte-identical Route 202 map. |
| `bdsp-r55-east-anchor` | Possible `(26,5)` / `(27,5)`, east hold ≤8 tiles → `(30,5)`, east, maximum walking distance 4. | #226 Logan r55 localization context, as recorded in the inventory. Scene state 1 explicit. |
| `bdsp-r55-npc-is-not-wall` | Same belief, north hold → **no safe anchor**. | Logan at `(26,4)` must not be used as a wall. |

See the [source revision/run inventory](TRANSITION_SCENARIOS.md) for original
PR heads and run evidence. These inputs specify fixed D-pad legs; the adapters
must not choose a goal using the expected answer or substitute synthetic maps.
Native fixture ID tables make inventory changes reviewable. Python validates
all rows and native adapters compare complete resulting JSON objects, not only
candidate counts or a successful return code.

## Native boundary and adoption

The native shared helper embeds `cases.json` plus `pin.json` through the existing
CMake text-resource mechanism, verifies the fixture digest and the relevant
actual embedded map bytes, then supplies cases to game adapters. It does not
execute a controller or implement a second movement model.

FRLG exposes `predict_overworld_press()` around the planner's existing private
`press()` implementation. BDSP calls its existing `step()` and
`wall_recovery_candidates()` functions. The BDSP fixture asks for **one fixed
direction** and two distinct position hypotheses: a returned one-hold anchor
must match that direction and the budget. This does not compare the Python BFS
planner's ordering with native minimum-hold search.

Python's clip budget includes the final blocked press. Canonical `walk_tiles`
and native `Hold.tiles` count only walking, so Python normalizes by subtracting
one. A hold predicts the stop; confirming stillness still requires the runtime
observation/input-drain contract from #45.

The native draft copies initially pin candidate fixture commit
`d4a191d1a6587d4728d15aa7ef9ff8fa344ab2e5`. This is explicitly a **preview**, not
approved data on main. After this publisher PR merges, advance to its full main
commit SHA and remove preview mode. Do not label a preview as main-approved by
editing the pin manually.

```sh
# In this repo. Preview is opt-in on both operations during draft review.
PYTHONPATH=src python3 -m pokesim.maps.conformance_sync update \
  --source . --consumer /path/to/Arduino-Source \
  --revision FULL_FIXTURE_COMMIT --preview
PYTHONPATH=src python3 -m pokesim.maps.conformance_sync check \
  --source . --consumer /path/to/Arduino-Source --preview

# After publisher merge, update promotes an intact preview to approved data.
PYTHONPATH=src python3 -m pokesim.maps.conformance_sync update \
  --source . --consumer /path/to/Arduino-Source --revision FULL_MAIN_COMMIT
PYTHONPATH=src python3 -m pokesim.maps.conformance_sync check \
  --source . --consumer /path/to/Arduino-Source
```

The tool reads immutable Git blobs. An unapproved map revision fails even in
preview mode. Drifted fixture bytes or unrelated JSON resources are rejected
before an existing export is overwritten. `--offline` explicitly trusts cached
`origin/main`; normal operation fetches. Resource files and map JSON must have
LF bytes in native checkouts (the native prerequisite adds `.gitattributes`).

## Validation checkpoint and remaining work

November 5 offline checkpoint: 64 focused registered FRLG tests and 54 focused
registered BDSP tests pass, including respectively six and four new tests
(shared rows plus deliberate map-drift rejection). The local runners compile
actual production sources; unused BDSP image I/O stubs throw if invoked. These
are local focused results, not claims of full app CI or console validation.

This pack establishes exact step/warp/edge arrival and one-direction wall-clip
parity for the selected inputs. It does not establish these remaining gates:

- Normalize native interruption reports into shared uncertainty events and
  compare complete pose sets, lost facing, queued movement, budgets, failure
  reasons and route rejoin with Python. Retain the existing native walker tests.
- Add same-board synthetic diagnostics for unknown edges, doors, ledges and
  NPCs; label them synthetic and keep real map cases separately identifiable.
- Reconcile the existing BDSP mine/house map differences through the reviewed
  map-publishing process before asserting identical-map mine/house conformance.
  Never change terrain merely to make a route pass.
- Add multi-leg route conformance with explicit route policy/cost settings.
  Optimal leg choices and costs remain unverified; equal endpoints do not prove
  those planners make identical decisions.
- Install fixture pin checking in native owning-branch CI after adoption; do not
  claim that a documented check command is already an active workflow.
- Test real controller/detector timing and transition judgments in Arduino.
  Spatial prediction passing alone does not prove encounter recovery is safe.

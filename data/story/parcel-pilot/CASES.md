# Replay scenarios

Generated from [cases.json](cases.json); edit that file and regenerate this view.

All observations and interruptions are synthetic. Actions are modeled requests,
not controller timing or verified console behavior. Press counts are not moved tiles.
Scene contents are supplied observations, not simulated button-by-button dialogue.
A signal is consumed only if its event is reached; listing a receipt does not grant the item at entry.

## parcel-all-events

Walk from Oak’s Lab to Viridian, enter the Mart, and receive Oak’s Parcel.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: overworld.

**Injected observations / interruptions:**

- `parcel_from_clerk`: overworld scene result at ViridianCity_Mart [4, 3] facing west (elevation 3); received: 1 × oak-parcel.

**Expected result:** `model_complete`.

- Completed events: `below_mart_door`, `mart_door`, `parcel_from_clerk`.
- Pose: ViridianCity_Mart [4, 3] facing west (elevation 3).
- Received: 1 × oak-parcel.

**Exact action checking:** enabled; the entire ordered list follows.

| # | Event | Expected request |
|---|---|---|
| 1 | `below_mart_door` | Press west × 1 on PalletTown_ProfessorOaksLab |
| 2 | `below_mart_door` | Press south × 5 on PalletTown_ProfessorOaksLab |
| 3 | `below_mart_door` | Press west × 4 on PalletTown |
| 4 | `below_mart_door` | Press north × 15 on PalletTown |
| 5 | `below_mart_door` | Press north × 7 on Route1 |
| 6 | `below_mart_door` | Press west × 4 on Route1 |
| 7 | `below_mart_door` | Press north × 5 on Route1 |
| 8 | `below_mart_door` | Press east × 4 on Route1 |
| 9 | `below_mart_door` | Press north × 6 on Route1 |
| 10 | `below_mart_door` | Press west × 2 on Route1 |
| 11 | `below_mart_door` | Press north × 4 on Route1 |
| 12 | `below_mart_door` | Press east × 6 on Route1 |
| 13 | `below_mart_door` | Press north × 15 on Route1 |
| 14 | `below_mart_door` | Press west × 6 on Route1 |
| 15 | `below_mart_door` | Press north × 3 on Route1 |
| 16 | `below_mart_door` | Press north × 19 on ViridianCity |
| 17 | `below_mart_door` | Press east × 14 on ViridianCity |
| 18 | `below_mart_door` | Face north on ViridianCity |
| 19 | `mart_door` | Press north × 1 on ViridianCity |
| 20 | `parcel_from_clerk` | Request scene via scripted-scene/1 |

## entry-not-overworld

A dialogue screen is supplied at entry: request no actions.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: dialogue.

**Injected observations / interruptions:**

- `parcel_from_clerk`: overworld scene result at ViridianCity_Mart [4, 3] facing west (elevation 3); received: 1 × oak-parcel.

**Expected result:** `stopped` / entry_requirement_failed.

- Completed events: none.
- Pose: PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3).
- Received: nothing.

**Exact action checking:** enabled; the entire ordered list follows.

No actions may be requested.

## missing-scene-evidence

Reach the Mart, but the clerk scene has no supplied observation.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: overworld.

**Injected observations / interruptions:**

- None.

**Expected result:** `stopped` / scene_evidence_missing_or_mismatched.

- Completed events: `below_mart_door`, `mart_door`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## missing-parcel-receipt

The clerk scene reports the right pose but no Parcel receipt.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: overworld.

**Injected observations / interruptions:**

- `parcel_from_clerk`: overworld scene result at ViridianCity_Mart [4, 3] facing west (elevation 3); received: nothing.

**Expected result:** `stopped` / scene_evidence_missing_or_mismatched.

- Completed events: `below_mart_door`, `mart_door`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## wrong-scene-arrival

The clerk scene reports a Parcel but the wrong facing.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: overworld.

**Injected observations / interruptions:**

- `parcel_from_clerk`: overworld scene result at ViridianCity_Mart [4, 3] facing east (elevation 3); received: 1 × oak-parcel.

**Expected result:** `stopped` / scene_evidence_missing_or_mismatched.

- Completed events: `below_mart_door`, `mart_door`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## unconfirmed-mart-transition

Request the Mart entry step, but its transition cannot be confirmed.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: overworld.

**Injected observations / interruptions:**

- `parcel_from_clerk`: overworld scene result at ViridianCity_Mart [4, 3] facing west (elevation 3); received: 1 × oak-parcel.
- `mart_door`: transition cannot be confirmed.

**Expected result:** `stopped` / transition_unconfirmed.

- Completed events: `below_mart_door`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** enabled; the entire ordered list follows.

| # | Event | Expected request |
|---|---|---|
| 1 | `below_mart_door` | Press west × 1 on PalletTown_ProfessorOaksLab |
| 2 | `below_mart_door` | Press south × 5 on PalletTown_ProfessorOaksLab |
| 3 | `below_mart_door` | Press west × 4 on PalletTown |
| 4 | `below_mart_door` | Press north × 15 on PalletTown |
| 5 | `below_mart_door` | Press north × 7 on Route1 |
| 6 | `below_mart_door` | Press west × 4 on Route1 |
| 7 | `below_mart_door` | Press north × 5 on Route1 |
| 8 | `below_mart_door` | Press east × 4 on Route1 |
| 9 | `below_mart_door` | Press north × 6 on Route1 |
| 10 | `below_mart_door` | Press west × 2 on Route1 |
| 11 | `below_mart_door` | Press north × 4 on Route1 |
| 12 | `below_mart_door` | Press east × 6 on Route1 |
| 13 | `below_mart_door` | Press north × 15 on Route1 |
| 14 | `below_mart_door` | Press west × 6 on Route1 |
| 15 | `below_mart_door` | Press north × 3 on Route1 |
| 16 | `below_mart_door` | Press north × 19 on ViridianCity |
| 17 | `below_mart_door` | Press east × 14 on ViridianCity |
| 18 | `below_mart_door` | Face north on ViridianCity |
| 19 | `mart_door` | Press north × 1 on ViridianCity |

## interrupted-route1-grass

A Route 1 encounter interrupts movement; retain both tiles and stop before the Mart.

**Start:** PalletTown_ProfessorOaksLab [7, 8] facing south (elevation 3); screen: overworld.

**Injected observations / interruptions:**

- `parcel_from_clerk`: overworld scene result at ViridianCity_Mart [4, 3] facing west (elevation 3); received: 1 × oak-parcel.
- `below_mart_door`: encounter interrupts north input from Route1 [12, 39] facing north (elevation 3).

**Expected result:** `stopped` / encounter_requires_recovery.

- Completed events: none.
- Pose: unknown.
- Received: nothing.
- Candidates: Route1 [12, 39] facing unknown (elevation 3); Route1 [12, 38] facing unknown (elevation 3).

**Exact action checking:** enabled; the entire ordered list follows.

| # | Event | Expected request |
|---|---|---|
| 1 | `below_mart_door` | Press west × 1 on PalletTown_ProfessorOaksLab |
| 2 | `below_mart_door` | Press south × 5 on PalletTown_ProfessorOaksLab |
| 3 | `below_mart_door` | Press west × 4 on PalletTown |
| 4 | `below_mart_door` | Press north × 15 on PalletTown |
| 5 | `below_mart_door` | Press north × 1 on Route1; last input interrupted |

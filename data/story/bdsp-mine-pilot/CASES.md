# Replay scenarios

Generated from [cases.json](cases.json); edit that file and regenerate this view.

All observations and interruptions are synthetic. Actions are modeled requests,
not controller timing or verified console behavior. Walk distances are requested, not confirmed displacement.
An interrupted walk keeps its requested distance; uncertainty/progress is checked separately.
Scene contents are supplied observations, not simulated button-by-button dialogue.
A signal is consumed only if its event is reached; listing a receipt does not grant the item at entry.

## mine-all-events

All 15 events from current #226, with explicitly scripted door, dialogue, scene, Hiker-clearance and healing evidence.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `roark`: scripted dialogue at OreburghMine [18, 29] facing north (elevation 0); result: `{"npc": "roark"}`.
- `roark_smashes_the_rock`: scripted overworld at OreburghMine [18, 29] facing north (elevation 0); result: `{"departed": "roark"}`.
- `up_to_the_hall`: scripted overworld at OreburghMineB1F [12, 21] facing north (elevation 0); result: `{"transition": true}`.
- `out_of_the_mine`: scripted overworld at OreburghCity [46, 59] facing north (elevation 0); result: `{"transition": true}`.
- `north_to_the_centers_wall`: synthetic clearance window for hiker_0; encounter: `null`.
- `heal_oreburgh`: scripted overworld at OreburghCity [47, 21] facing south (elevation 0); result: `{"party_healed": true}`.

**Expected result:** `model_complete`.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`, `to_roarks_corner`, `beside_roarks_rock`, `below_roark`, `roark`, `roark_smashes_the_rock`, `below_the_coal_rooms_warp`, `up_to_the_hall`, `out_of_the_mine`, `north_to_the_centers_wall`, `east_below_the_centers_door`, `heal_oreburgh`.
- Pose: OreburghCity [47, 21] facing south (elevation 0).
- Received: nothing.

**Exact action checking:** enabled; the entire ordered list follows.

| # | Event | Expected request |
|---|---|---|
| 1 | `above_the_mine` | Walk south for 36 tiles on OreburghCity |
| 2 | `above_the_mine` | Walk west for 1 tile on OreburghCity |
| 3 | `above_the_mine` | Face south on OreburghCity |
| 4 | `into_the_mine` | Follow the OreburghCity corridor south through the door to OreburghMineB1F. |
| 5 | `into_the_coal_room` | Follow the OreburghMineB1F corridor south through the door to OreburghMine. |
| 6 | `south_to_the_rock` | Walk south for 8 tiles on OreburghMine |
| 7 | `to_roarks_corner` | Walk east for 1 tile on OreburghMine |
| 8 | `to_roarks_corner` | Walk south for 2 tiles on OreburghMine |
| 9 | `to_roarks_corner` | Walk west for 1 tile on OreburghMine |
| 10 | `to_roarks_corner` | Walk south for 5 tiles on OreburghMine |
| 11 | `to_roarks_corner` | Walk east for 14 tiles on OreburghMine |
| 12 | `to_roarks_corner` | Walk south for 10 tiles on OreburghMine |
| 13 | `to_roarks_corner` | Walk west for 2 tiles on OreburghMine |
| 14 | `to_roarks_corner` | Walk south for 2 tiles on OreburghMine |
| 15 | `to_roarks_corner` | Walk west for 7 tiles on OreburghMine |
| 16 | `beside_roarks_rock` | Walk south for 1 tile on OreburghMine |
| 17 | `below_roark` | Walk west for 2 tiles on OreburghMine |
| 18 | `roark` | Face north on OreburghMine |
| 19 | `roark` | Talk to roark. |
| 20 | `roark_smashes_the_rock` | Request scene via bdsp-scene-observation/1 |
| 21 | `below_the_coal_rooms_warp` | Walk east for 9 tiles on OreburghMine |
| 22 | `below_the_coal_rooms_warp` | Walk north for 3 tiles on OreburghMine |
| 23 | `below_the_coal_rooms_warp` | Walk east for 2 tiles on OreburghMine |
| 24 | `below_the_coal_rooms_warp` | Walk north for 10 tiles on OreburghMine |
| 25 | `below_the_coal_rooms_warp` | Walk west for 14 tiles on OreburghMine |
| 26 | `below_the_coal_rooms_warp` | Walk north for 5 tiles on OreburghMine |
| 27 | `below_the_coal_rooms_warp` | Walk east for 1 tile on OreburghMine |
| 28 | `below_the_coal_rooms_warp` | Walk north for 2 tiles on OreburghMine |
| 29 | `below_the_coal_rooms_warp` | Walk west for 1 tile on OreburghMine |
| 30 | `below_the_coal_rooms_warp` | Walk north for 7 tiles on OreburghMine |
| 31 | `up_to_the_hall` | Follow the OreburghMine corridor north through the door to OreburghMineB1F. |
| 32 | `out_of_the_mine` | Follow the OreburghMineB1F corridor north through the door to OreburghCity. |
| 33 | `north_to_the_centers_wall` | Walk north for 38 tiles on OreburghCity |
| 34 | `east_below_the_centers_door` | Walk east for 1 tile on OreburghCity |
| 35 | `heal_oreburgh` | Heal at the Pokemon Center and return outside. |

## entry-not-overworld

Reject a wrong entry screen before any story action.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: dialogue.

**Injected observations / interruptions:**

- None.

**Expected result:** `stopped` / entry_requirement_failed.

- Completed events: none.
- Pose: OreburghCity [47, 21] facing south (elevation 0).
- Received: nothing.

**Exact action checking:** enabled; the entire ordered list follows.

No actions may be requested.

## mine-arrival-unconfirmed

Reach the city mine doorway, but do not assume B1F arrival without evidence.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.

**Expected result:** `stopped` / observation_missing_or_mismatched.

- Completed events: `above_the_mine`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** enabled; the entire ordered list follows.

| # | Event | Expected request |
|---|---|---|
| 1 | `above_the_mine` | Walk south for 36 tiles on OreburghCity |
| 2 | `above_the_mine` | Walk west for 1 tile on OreburghCity |
| 3 | `above_the_mine` | Face south on OreburghCity |
| 4 | `into_the_mine` | Follow the OreburghCity corridor south through the door to OreburghMineB1F. |

## interrupted-before-roark

A battle during the south-five leg leaves two candidate tiles and unknown facing; stop before Roark instead of crediting requested distance.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `to_roarks_corner`: synthetic clearance window for no wandering NPCs; encounter: `{"kind": "wild-encounter", "from": {"map": "OreburghMine", "tile": [15, 12], "elevation": 0, "facing": "south"}, "direction": "south"}`.

**Expected result:** `stopped` / encounter_requires_recovery.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`.
- Pose: unknown.
- Received: nothing.
- Candidates: OreburghMine [15, 12] facing unknown (elevation 0); OreburghMine [15, 13] facing unknown (elevation 0).

**Exact action checking:** enabled; the entire ordered list follows.

| # | Event | Expected request |
|---|---|---|
| 1 | `above_the_mine` | Walk south for 36 tiles on OreburghCity |
| 2 | `above_the_mine` | Walk west for 1 tile on OreburghCity |
| 3 | `above_the_mine` | Face south on OreburghCity |
| 4 | `into_the_mine` | Follow the OreburghCity corridor south through the door to OreburghMineB1F. |
| 5 | `into_the_coal_room` | Follow the OreburghMineB1F corridor south through the door to OreburghMine. |
| 6 | `south_to_the_rock` | Walk south for 8 tiles on OreburghMine |
| 7 | `to_roarks_corner` | Walk east for 1 tile on OreburghMine |
| 8 | `to_roarks_corner` | Walk south for 2 tiles on OreburghMine |
| 9 | `to_roarks_corner` | Walk west for 1 tile on OreburghMine |
| 10 | `to_roarks_corner` | Walk south for 5 tiles on OreburghMine |

## roark-dialogue-unconfirmed

Standing below Roark and requesting talk does not prove a conversation opened.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `roark_smashes_the_rock`: scripted overworld at OreburghMine [18, 29] facing north (elevation 0); result: `{"departed": "roark"}`.
- `up_to_the_hall`: scripted overworld at OreburghMineB1F [12, 21] facing north (elevation 0); result: `{"transition": true}`.
- `out_of_the_mine`: scripted overworld at OreburghCity [46, 59] facing north (elevation 0); result: `{"transition": true}`.
- `north_to_the_centers_wall`: synthetic clearance window for hiker_0; encounter: `null`.
- `heal_oreburgh`: scripted overworld at OreburghCity [47, 21] facing south (elevation 0); result: `{"party_healed": true}`.

**Expected result:** `stopped` / dialogue_unconfirmed.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`, `to_roarks_corner`, `beside_roarks_rock`, `below_roark`.
- Pose: OreburghMine [18, 29] facing north (elevation 0).
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## roark-departure-unconfirmed

Do not accept the authored scene pose without the scripted Roark-departure result.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `roark`: scripted dialogue at OreburghMine [18, 29] facing north (elevation 0); result: `{"npc": "roark"}`.
- `roark_smashes_the_rock`: scripted overworld at OreburghMine [18, 29] facing north (elevation 0); result: `{"departed": "somebody_else"}`.
- `up_to_the_hall`: scripted overworld at OreburghMineB1F [12, 21] facing north (elevation 0); result: `{"transition": true}`.
- `out_of_the_mine`: scripted overworld at OreburghCity [46, 59] facing north (elevation 0); result: `{"transition": true}`.
- `north_to_the_centers_wall`: synthetic clearance window for hiker_0; encounter: `null`.
- `heal_oreburgh`: scripted overworld at OreburghCity [47, 21] facing south (elevation 0); result: `{"party_healed": true}`.

**Expected result:** `stopped` / observation_missing_or_mismatched.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`, `to_roarks_corner`, `beside_roarks_rock`, `below_roark`, `roark`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## mine-exit-unconfirmed

Stop at the B1F north doorway before the city-wall leg when the exit observation is missing.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `roark`: scripted dialogue at OreburghMine [18, 29] facing north (elevation 0); result: `{"npc": "roark"}`.
- `roark_smashes_the_rock`: scripted overworld at OreburghMine [18, 29] facing north (elevation 0); result: `{"departed": "roark"}`.
- `up_to_the_hall`: scripted overworld at OreburghMineB1F [12, 21] facing north (elevation 0); result: `{"transition": true}`.
- `north_to_the_centers_wall`: synthetic clearance window for hiker_0; encounter: `null`.
- `heal_oreburgh`: scripted overworld at OreburghCity [47, 21] facing south (elevation 0); result: `{"party_healed": true}`.

**Expected result:** `stopped` / observation_missing_or_mismatched.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`, `to_roarks_corner`, `beside_roarks_rock`, `below_roark`, `roark`, `roark_smashes_the_rock`, `below_the_coal_rooms_warp`, `up_to_the_hall`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## hiker-clearance-unconfirmed

The 37-38 tile north walk encounters the Hiker wandering region; no clearance window means stop before entering it.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `roark`: scripted dialogue at OreburghMine [18, 29] facing north (elevation 0); result: `{"npc": "roark"}`.
- `roark_smashes_the_rock`: scripted overworld at OreburghMine [18, 29] facing north (elevation 0); result: `{"departed": "roark"}`.
- `up_to_the_hall`: scripted overworld at OreburghMineB1F [12, 21] facing north (elevation 0); result: `{"transition": true}`.
- `out_of_the_mine`: scripted overworld at OreburghCity [46, 59] facing north (elevation 0); result: `{"transition": true}`.
- `heal_oreburgh`: scripted overworld at OreburghCity [47, 21] facing south (elevation 0); result: `{"party_healed": true}`.

**Expected result:** `stopped` / dynamic_npc_clearance_unconfirmed.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`, `to_roarks_corner`, `beside_roarks_rock`, `below_roark`, `roark`, `roark_smashes_the_rock`, `below_the_coal_rooms_warp`, `up_to_the_hall`, `out_of_the_mine`.
- Pose: OreburghCity [46, 28] facing north (elevation 0).
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

## heal-unconfirmed

A heal request does not establish healed party or final position without its receipt.

**Start:** OreburghCity [47, 21] facing south (elevation 0); screen: overworld.

**Injected observations / interruptions:**

- `above_the_mine`: synthetic clearance window for hiker_0; encounter: `null`.
- `into_the_mine`: scripted overworld at OreburghMineB1F [12, 1] facing south (elevation 0); result: `{"transition": true}`.
- `into_the_coal_room`: scripted overworld at OreburghMine [15, 2] facing south (elevation 0); result: `{"transition": true}`.
- `roark`: scripted dialogue at OreburghMine [18, 29] facing north (elevation 0); result: `{"npc": "roark"}`.
- `roark_smashes_the_rock`: scripted overworld at OreburghMine [18, 29] facing north (elevation 0); result: `{"departed": "roark"}`.
- `up_to_the_hall`: scripted overworld at OreburghMineB1F [12, 21] facing north (elevation 0); result: `{"transition": true}`.
- `out_of_the_mine`: scripted overworld at OreburghCity [46, 59] facing north (elevation 0); result: `{"transition": true}`.
- `north_to_the_centers_wall`: synthetic clearance window for hiker_0; encounter: `null`.

**Expected result:** `stopped` / observation_missing_or_mismatched.

- Completed events: `above_the_mine`, `into_the_mine`, `into_the_coal_room`, `south_to_the_rock`, `to_roarks_corner`, `beside_roarks_rock`, `below_roark`, `roark`, `roark_smashes_the_rock`, `below_the_coal_rooms_warp`, `up_to_the_hall`, `out_of_the_mine`, `north_to_the_centers_wall`, `east_below_the_centers_door`.
- Pose: unknown.
- Received: nothing.

**Exact action checking:** disabled; this case checks outcomes only.

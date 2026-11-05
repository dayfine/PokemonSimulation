# Transition and localization regression inventory

## Problem and solution

The shared problem is **continuing a route from a position the walker has not
actually established**. A map transition, a battle interruption or a short leg
can leave the character on a different map/tile, or facing a different way,
than the route assumes. Later inputs then compound that error.

Transition handling and recovery are related, but are not the same operation:

| Operation | Question it answers | Responsibility |
|---|---|---|
| Transition handling | Did we change maps, and where/how did we arrive? | Model door/cave/mat/edge entry, arrival displacement, facing and coordinate offsets; confirm the actual destination from observations. A fade alone is insufficient. |
| Recovery | Where could we be, and how can we safely continue? | Preserve every plausible pose after uncertainty; find a safe localization action, confirm its result and replan from that anchor. A completed input count alone is insufficient. |

A correctly confirmed transition needs no recovery. An interrupted ordinary
walk can need recovery without changing maps. An unconfirmed transition can
need recovery too, but holding toward a wall is safe only when every remaining
hypothesis supports that action. A warp, NPC or unknown edge is not a wall.

### Example: FRLG Forest gate — transition handling

From Forest `(5,10)`, north enters the cave warp and predicts arrival at the
north gate's `(7,10)`, facing north. Another north input moves to `(7,9)` on the
same gate map. Returning south from the mat at `(7,10)` warps to Forest and
includes its south-facing cave walk-out.

If a battle wipe is mistaken for the transition fade, the player may still be
in Forest. Keep the possible source/destination poses until drained-input and
map/position evidence distinguish them; do not begin the next map's route merely
because the screen went dark. See `forest-north-gate` and
`forest-interrupted-warp-approach` below and in the case catalog.

### Example: BDSP mine corridor — recovery without a transition

The reported `below_roark` route intended to reach row 17 before walking east.
After encounters, the character was reported on row 15 and the east leg met
Machop. The deployed revision and exact physical cause are unknown; tests
explicitly inject both an interrupted step that moved and one that did not.

Instead of crediting each interrupted input as movement, retain the possible
rows. If the reviewed map proves they all share a safe south ray, clip south
until the wall confirms a common anchor, then replan the east leg from there.
Do not resume the old east leg while assuming row 17. Retry interrupted clips
within a budget; stop if the anchor cannot be established. The exact native
story-step tests and current map limitations are recorded below.

### What this chain adds

- **Python #45:** map-transition predictions, pose uncertainty, observation
  confirmation and bounded recovery/clipping (`runtime_world.py` and
  `transition_state.py`). **Arduino #227–229:** shared wall-anchor search and
  FRLG/BDSP native integration, with actual walker regressions.
- **#46:** eight exact spatial fixtures checked independently in Python/native.
  [CONFORMANCE.md](CONFORMANCE.md) describes the native handoff and pin checks.
- **#47:** four Python recovery diagnostics with exact state snapshots, plus a
  trainer-sight import fix. [ENCOUNTER_RECOVERY.md](ENCOUNTER_RECOVERY.md) lists
  those cases and what they prove. They are not yet native event-replay parity.
- **Next:** replay actual native walker reports against the model, then verify
  full confirmation and automatic route rejoin. Keep absent observations and
  game-specific retry policies explicit. Timing and live detectors stay native.

The remainder of this document is the detailed source/run inventory and its
known gaps; start here for the problem, then use the examples below as evidence.

## Fixture scope

This slice separates **predicted movement**, **possible poses**, and **observed
arrival**. It uses the unchanged maps published at PokemonSimulation
`86cbad9144970e546a2fa4ee5d49cfea7905de3c` (#44). No #226 map correction is
imported. The [semantic cases](../../src/pokesim/maps/scenarios/transition-cases.json)
are reduced regression inputs, not exported native AutoStory plans.

## Run and review

```sh
PYTHONPATH=src python3 -m pokesim.cli.transitions --case forest-north-gate \
  --output /tmp/forest-trace.json --draw-dir /tmp/forest-views
PYTHONPATH=src python3 -m pokesim.cli.transitions --case mine-south-clip-after-battle \
  --output /tmp/mine-trace.json --draw-dir /tmp/mine-views
PYTHONPATH=src python3 -m pokesim.cli.transitions --case mine-pack-gap
PYTHONPATH=src python3 -m unittest pokesim.maps.test_runtime_world \
  pokesim.maps.test_transition_state pokesim.maps.test_transition_replay
```

The CLI verifies the catalog's immutable map pin against cached `origin/main`,
including manifest and whole-game map hashes. It does not fetch. Its JSON keeps
map provenance, context, source references, candidate poses, observations,
remaining recovery attempts and failures. `checks_passed=true` means the
regression assertions passed; `mine-pack-gap` deliberately still has a failure
and `can_resume=false`. Unknown event kinds fail instead of being skipped.

Review [the drawings](scenarios/README.md), then `runtime_world.py` for
predictions, `transition_state.py` for confirmation/recovery, and their colocated
tests. `transition_replay.py` interprets only the small versioned semantic
fixture format. It is not a native story parser or production walker.

## Inspected sources

Heads fetched and PR descriptions, issue comments and review comments inspected
on November 5, 2026. #213 had two issue comments; the other requested PRs had no
issue/review comments at these snapshots. PR prose is evidence of a report,
not independent console validation. Source tests were read; C++ suites and
consoles were not run here.

| Fork PR | Exact inspected head | Relevant evidence |
|---|---|---|
| [213](https://github.com/dayfine/Arduino-Source/pull/213) | `891b8f97e2e1399011431942c18079c532a19b5d` | Core, forest re-anchoring, wall-check diagnostic, checkpoint table. |
| [214](https://github.com/dayfine/Arduino-Source/pull/214) | `326daebe7758771293904a259a18217b57559341` | RNG stage dependency; no additional transition regression selected. |
| [215](https://github.com/dayfine/Arduino-Source/pull/215) | `5b9b65a752dc124403501f30cf281d4c7f9cd29c` | Mt. Moon ladders; late battle/warp-leg distinctions. |
| [216](https://github.com/dayfine/Arduino-Source/pull/216) | `831a22c423fc0ab1918fba85fb667d18c31c1691` | Forest simulator faults, bridge entry shortfall and bounded trainer approach. |
| [219](https://github.com/dayfine/Arduino-Source/pull/219) | `360701b053f294cae5e652e2bcfb60fd25608306` | Connection delay, capture's two possible tiles, Bill's changed position. |
| [222](https://github.com/dayfine/Arduino-Source/pull/222) | `b48afbc830f4b4c34cf94eb1aba85c2654a69938` | Later house/Underground/S.S. Anne route context; PR says no console validation yet. |
| [224](https://github.com/dayfine/Arduino-Source/pull/224) | `51c0ce6128e5981da56b370a770874b96a1e129f` | Aggregate native recovery implementation and later route state. |
| [226](https://github.com/dayfine/Arduino-Source/pull/226) | `f8bdd62b9df4dbf285f93853147295e0552a0367` | Mine failures, missed fade/banner exits, house story arrivals, Logan r55. |
| [167](https://github.com/dayfine/Arduino-Source/pull/167) | `df6b1e47472f2448861eb72f4c432ead1d7c408c` | #226's `bdsp/sim` parent; simulator lineage, not an additional publishing pin. |

The [FRLG run ledger](https://github.com/dayfine/Arduino-Source/blob/11cbf77e0271e97b3639f9d5d419d0549ebec0bf/autostory/frlg/lab/newgame-firered-console-B.md)
is on the Arduino `agents` branch at the linked revision. Lab build hashes below
are ledger identifiers, not a claim that a PR head was the deployed binary.
Unknown fields remain explicitly unknown; no capture files are copied here.

## Scenarios and preconditions

Every coordinate below is **runtime-local to its named map**, not screen
pixels or a DP/Platinum matrix coordinate. Executable cases declare initial
pose(s), elevation, facing, flags and scene variables in JSON. Unlisted flags
are treated as unset by this static adapter. No party/battle outcome is inferred.

1. **Forest north gate: fade mistaken for battle.** Native
   [test_forest_north_gate / test_battle_on_warp_leg](https://github.com/dayfine/Arduino-Source/blob/831a22c423fc0ab1918fba85fb667d18c31c1691/SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/PokemonFRLG_OverworldSim_Tests.cpp#L250),
   cp0007 m6f and r15, console B, November 1. Start `ViridianForest (5,20)`
   north; native goal is north gate `(7,9)`. Holding north crosses encounter
   terrain into cave warp `(5,9)`, arriving on the gate's directional mat
   `(7,10)` facing north, then walking north one tile. A 900 ms post-hold
   watch took the fade for encounter flashes; black below the mat looked like
   a battle text box. **Executable reduction:** `forest-north-gate` starts at
   the final source tile `(5,10)`. Fade alone confirms neither battle nor map;
   a battle observation without HP evidence remains unknown. Require stable
   destination map/tile evidence and drained input before continuing.

2. **Battle before the forest warp.** Same native source injects a late-seen
   battle on grass step 1 or 2, leaving `(5,19)` or `(5,18)`. Its console
   analogue is November 3, `00.13`, Mt. Moon 1F: battle wipe mistaken for a
   ladder fade, player one tile short of ladder. **Executable:**
   `forest-battle-before-warp` keeps both forest tiles after escape. It does
   not claim gate arrival. The source-map belief must be localized/recovered;
   missing fade on the resumed warp leg is an explicit native failure.

3. **Forest drift by two tiles.** Ledger r16, build `frlg-m21 (35cb58756)`,
   `00.07 / forest_exit` (checkpoint numbering before the forest save split):
   west 6 ended two tiles short at column 9, with no detected interruption.
   A later south-23 recovery assumed column 5 and hit TRAINER TIPS `(9,29)`
   six times. Exact preceding tile/row, facing and flags are **not recorded**;
   do not invent a complete deterministic replay. r17 `frlg-m22` also lost
   position after replanning and ended at “no fade”; blackout was another
   attempt, not evidence of the same pose. Native
   [re-anchor tests](https://github.com/dayfine/Arduino-Source/blob/891b8f97e2e1399011431942c18079c532a19b5d/SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/PokemonFRLG_OverworldReanchor_Tests.cpp#L123)
   use forest `(29,61)` to north gate `(7,8)` and test every grass-leg stop.
   **Inventory + guards:** retain partial/missed-input positions; reject a hold
   that meets an object or reaches different wall endpoints. Raw screen-change
   wall taps were diagnostic only; native comments say bumps and steps were
   not reliably distinguished. Full r16 replay awaits the missing trace.

4. **Route 2 south gate and forest mat.** Ledger cp0007-i succeeded from
   Viridian `(20,6)` to forest `(29,61)`. r12 failed earlier because the
   post-tutorial old man blocked east; a north step to `(20,5)` fixed that
   dynamic-object issue. **Executable derived link checks:**
   `route2-south-gate` enters Route2 cave `(5,51)` from `(5,52)`, arriving
   south gate `(7,10)`. Gate cave `(7,1)` leads to forest `(29,62)`; entering
   this south-facing mat does not warp, but pressing south from it does.
   Arrival back at the gate cave walks out to `(7,2)`, facing south.
   `forest-queued-exit` is explicitly a **synthetic queue diagnostic** on
   this real geometry, not a claimed captured input sequence. Undrained input
   can still cross the exit; early tile observation cannot authorize resuming.

5. **Cerulean / Nugget Bridge connection shortfall.** Native
   [simulation tests](https://github.com/dayfine/Arduino-Source/blob/360701b053f294cae5e652e2bcfb60fd25608306/SerialPrograms/Source/VideoGames/PokemonFRLG/Programs/AutoStory/PokemonFRLG_AutoStorySimulation_Tests.cpp#L599)
   and #219 description report November 3 `00.20` twice: the north hold
   crossed a connection and ended one tile short, e.g. `(11,16)`; west then
   hit bridge posts. #216 `00.16` had Cale `no_battle` twice; bounded north
   approaches fixed it. **Executable diagnostic slice:**
   `cerulean-connection-short` uses actual edge `(22,0)` to Route24 `(10,39)`,
   with explicit offset 12 and `FLAG_HIDE_CERULEAN_RIVAL`. Three completed
   input opportunities may end at `(10,37)` or `(10,38)` when one crossing
   opportunity stalls. These are derived slice endpoints, **not** the reported
   full-leg stopping tiles. Knowing `Route24` alone cannot choose a tile.
   Trainer-approach/dialogue execution remains native.

6. **Capture leaves either pacing tile.** #219 test
   `test_oddish_battle_on_far_step`, `00.20 / catch_oddish`, run m61:
   capture finished on `(3,19)` while return planned from `(4,19)`, causing a
   collision with a beaten Lass and later no Center fade. Both pacing tiles
   must survive into localization. **Inventory:** native changes trainer
   locations after encounters; Python currently tests pose sets and static
   convergence, not those dynamic NPC-world alternatives.

7. **Bill blocks the mat approach.** #219 `test_out_of_bill_cottage`,
   November 3 `00.18`: player `(6,6)`, Bill moved to `(7,6)` from static
   `(7,5)`. East bumped Bill, south stayed on column 6 and ended `(6,9)` beside
   actual mat `(7,9)`, so no warp. Native route goes around to `(7,8)`, then
   exits to Route25 `(51,5)`. **Inventory:** needs an exported post-scene
   object/warp-state update; do not change baseline terrain or assume the
   adjacent mat is equivalent. General recovery tests reject NPC anchors.

8. **BDSP Logan r55.** Native
   [Test_OpenLegKnownTrainer](https://github.com/dayfine/Arduino-Source/blob/f8bdd62b9df4dbf285f93853147295e0552a0367/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_PlannedRoute_Tests.cpp#L320),
   `00.04d / north_to_jubilife`: west from `(30,5)` toward `(24,5)`, Logan
   `(26,4)` south. Tap-count position `(27,5)` and sight interception `(26,5)`
   both remain possible. **Executable:** `logan-r55-localization` uses those
   two tiles, tutorial-disarmed assumption `VAR_ROUTE_202_STATE=1`, facing
   west. A common east clip reaches `(30,5)` from both without entering Logan's
   spawn. Python's four-press candidate matches the native recovery direction;
   it needs a later stable pose observation. Trainer motion/battle is not replayed.

9. **Mine B1F ↔ B2F boundary.** Native
   [old_mine_hall_south_20 / south_19 / north_20](https://github.com/dayfine/Arduino-Source/blob/f8bdd62b9df4dbf285f93853147295e0552a0367/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_StorySim_Tests.cpp#L832),
   `01.03`: hall arrival `(12,1)` south; native exit warp `(12,21)` enters
   coal room `OreburghMine (15,2)`. Nineteen ordinary south taps stop at row
   20; the next south input is a transition, not an ordinary counted tile.
   Return arrives hall `(11,21)` north and exits via `(11,1)` toward city
   `(45,59)` (native arrival allows `(45,58)` too). Exact original run IDs are
   absent from these test comments. **Executable gap:** `mine-pack-gap` shows
   our pinned hall has floor at row 21, an unlinked door at row 22, and no
   cross-floor link metadata. It fails unresolved, rather than applying #226's
   pending row-21 fix. Full mine replay is blocked on reviewed data/contracts.

10. **Mine south clip after a wild battle — new user report.** November 5
    pasted Gemini report says `01.03 / below_roark`, `EAST 14 moved 4`, ending
    `(19,15)` east beside Machop `(20,15)` and Worker 7 `(21,15)`, instead of
    crossing row 17 after `SOUTH 5`. Run ID, deployed revision and preceding
    per-tap trace are **unavailable**; its causal claim is unverified. Fetched
    [WalkUntil](https://github.com/dayfine/Arduino-Source/blob/f8bdd62b9df4dbf285f93853147295e0552a0367/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Utils/PokemonBDSP_AutoStory_Walk.cpp#L360)
    credits `moved_chunks` after escape, but elapsed chunk budget advances
    independently. Removing credit does not itself retry movement.
    **Executable diagnostic:** `mine-south-clip-after-battle` starts with
    column 15, rows 15/16/17. All converge south to `(15,17)` against wall
    row 18, on the existing published terrain. The cave is explicitly marked
    encounter-capable. A battle leaves the clip unconfirmed; after escape and
    drained inputs, repeat the clip within the shared retry budget. An advancing
    overworld view that is still under south input localizes the static belief;
    frozen video does not. Tests reject clipping east into Machop, different
    columns ending at different wall tiles, and exhausted retries. The full
    inbound corridor also differs in the pending pack, so this is not a full
    `below_roark` reproduction or approval of its other proposed wall holds.

11. **BDSP house and delayed/missed exit judgments.** Native
    [bedroom_to_lakefront / out_of_the_house_again](https://github.com/dayfine/Arduino-Source/blob/f8bdd62b9df4dbf285f93853147295e0552a0367/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_StoryTable.cpp#L247),
    `00.01 / 00.03`, r27: `(6,9)` south onto house door `(6,10)` arrives
    Twinleaf `(20,22)` south. **Executable:** `bdsp-player-house-exit` supplies
    an evidenced arrival contract for the existing one-way link. Variables
    `VAR_PLAYER_HOUSE_STATE=0`, `CONSOLE_MOMS_CALL=1` explicitly assume both
    door scenes spent; their numeric values are fixture assumptions.
    Reverse entrance, side-entered stairs, Barry's knockback `(9,13)`, and
    post-heal Mom displacement require further exported scene/link contracts.
    Ledger BDSP v3 r9/r11/r12 additionally reports evening tint causing a false
    indoor judgment, a false “arrived after 800ms” while still indoors, and a
    later exit overshooting south three rows. Those are detector/timing leads,
    not independently reproduced images here.

12. **Banner/fade arrives after movement overshoots.** #226 native
    [Test_StorySimExit](https://github.com/dayfine/Arduino-Source/blob/f8bdd62b9df4dbf285f93853147295e0552a0367/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_StorySim_Tests.cpp#L695):
    r75, `01.05 / out_of_oreburgh_gate`, expected Route203 `(55,9)` west;
    late banner left x49–54/y6–13 near pond. r81, `01.09 /
    out_of_the_ravaged_path`, missed fade; expected Route204North `(20,26)`
    south, ended `(20,27..30)`. **Inventory:** require arrival validation or
    stop in the transition step; a map banner is not tile evidence. These maps
    are outside our 22-map BDSP pack, so Python does not pretend to replay them.

## Shared contract and remaining gaps

`RuntimeWorld` reuses `LocalMap` and the shared router. FRLG resolves explicit
named warps and local edge offsets, honors door/cave/directional/step-on modes,
arrival displacement, facing and elevation. Unknown/unloaded exits remain
unresolved. BDSP arrival rules must be explicit evidenced contracts attached to
existing links; coordinate overlap never creates a connection. Scene exclusions,
flags, closed sides and NPC areas remain enforced.

`Session` distinguishes attempted inputs from possible completed movement,
including a bounded missed-press budget, optional connection stall and queued
prefixes. `can_resume` means a unique stable pose is available **for replanning**;
it does not mean a story goal or battle was completed. A contradictory observation
latches failure. The initial belief is an asserted precondition, not localized
by construction.

Two recovery choices are provided: bounded search for common actions on static
non-encounter floor, or an explicit one-direction clip whose every candidate
reaches the same known wall. Clips can allow encounter interruptions only under
an explicit recovery policy. Recovery/clip actions share a per-session attempt
budget (default three). No search result confirms execution. Inputs must drain,
the overworld must be observed, and position/stop evidence must narrow the belief.
A still observation needs advancing video; native detector thresholds and how to
establish that evidence stay in Arduino.

FRLG's current native implementation already uses this architecture more fully:
[after_stop/rejoin/replan](https://github.com/dayfine/Arduino-Source/blob/51c0ce6128e5981da56b370a770874b96a1e129f/SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/PokemonFRLG_OverworldRecovery.cpp#L305)
turns an interrupted leg into candidate positions, prepends safe wall holds,
plans back to the leg endpoint, then resumes. Existing wall holds can be
repeated after a late interruption. For unobserved open-leg shortfalls, `OPEN_LEG_SHORTFALL=2` considers the
planned endpoint and one/two tiles short; the next wall hold is reused when
it converges from all three. Native re-anchoring allows three holds and the
route stops after eight interruptions. Candidates are not necessarily just two;
trainer-world alternatives and late detection can widen them. Python does not
claim native cost, timing, trainer-world or route-leg parity.

Remaining work: producer-exported native semantic logs; complete BDSP links and
arrival/scene contracts after map review; moving/approaching NPC alternatives;
trainer sight missing from BDSP map metadata; native leg costs and stopping
policies; detector ambiguity; encounter escape outcomes; route cursor/save
semantics. Caller-supplied forbidden tiles supplement declared trainer rays;
missing hazards are not proven safe. Cave encounter maps are explicit state,
not inferred from a '.' glyph. Synthetic guards are labeled in tests and JSON.
Native controller/detector regressions remain in Arduino; no console, save or
active Arduino worktree was changed by this work.

## Exact cross-repository fixtures after #45

[CONFORMANCE.md](CONFORMANCE.md) adds eight shared exact spatial fixtures and
native game consumers. This is a first subset, not replacement of this richer
uncertainty/observation inventory or proof of full native planner parity. Its
fixture and map-byte checks are separate from transition confirmation. Pending
mine/house map differences and native interrupted-walk event replay remain open.

## Exact encounter-recovery diagnostics after #46

[ENCOUNTER_RECOVERY.md](ENCOUNTER_RECOVERY.md) documents four additional injected
cases and complete expected-state checkpoints, including every map/tile/facing
hypothesis, queue/awaiting state, retries and latched failures. They use the same
unchanged pinned maps. Native interruption/event replay is still pending; do not
count these as extra native conformance fixtures.

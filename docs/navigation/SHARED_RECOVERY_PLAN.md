# Share native recovery through nav-core, preserving FRLG before fixing BDSP

Status: first offline native slice published as fork drafts, November 5, 2026.
No consoles, saves or other agents' active branches were changed. The Python
semantic slice in Simulation #45 supplies independent scenarios; native C++
tests below validate the actual game consumers. The larger acceptance matrix
remains open where explicitly noted.

## Implementation checkpoint

Review in this order:

1. [Arduino #227](https://github.com/dayfine/Arduino-Source/pull/227): pure wall
   convergence search extracted to nav-core, with 9 portable native tests.
2. [Arduino #228](https://github.com/dayfine/Arduino-Source/pull/228): FRLG adapter.
   Original #224 and migrated versions pass the same 57 focused native tests.
   Full Clang runs pass the same 83 Overworld and 30 AutoStorySimulation tests;
   both jobs fail on the same 69 missing-image FileException cases.
3. [Arduino #229](https://github.com/dayfine/Arduino-Source/pull/229): BDSP
   interruption outcomes, safe common-wall recovery and real mine story-step
   regressions. 47 focused native tests pass, including 9 consumer cases.
   Original execution fails 6 of the initial 8 cases. Full patched Linux CI
   passes all 90 BDSP AutoStory tests; its only 26 failures match the baseline
   missing-image cases. Windows compiles the new files but is blocked by
   initializer warnings in unchanged baseline StorySim tests.

These are isolated owner handoffs based on pinned game stacks, not direct
changes to the owning branches. Shared core macOS and Windows Clang full CI
pass. The [native run record](https://github.com/dayfine/Arduino-Source/blob/nav/recovery-run-records/autostory/navigation/shared-recovery-2026-11-05.md)
contains exact revisions, CI links, merge order and fidelity limits.
Changes reach #226 through explicit parent merges, not automatically: #227
lands in #114; BDSP adapter/walker/story/simulator pieces from #229 land with
their owning PRs (#127/#129/#128/#167/#226), then merge forward through the
existing stack. Nav-core alone does not activate the BDSP fix.

The BDSP tests use real maps, planner, story table, StoryWalkSteps and RouteWalker.
They inject normalized cleared encounter outcomes; they do not emulate detector
pixels, controller queue timing or sub-tile motion. Unknown first-input/late
origins fail explicitly. Outbound mine, house transitions, full r55 replay and
the generic LegInterrupt same-pose contract remain follow-ups. The ordered gates
below retain their full scope; this checkpoint does not mark that whole matrix
complete.

## Where the current implementation lives

The FRLG recovery is **present in #224 because that PR inherits the stack**.
It is not a fix introduced by #224. Read-only history at the following heads
shows the initial implementation in the squashed #213, with subsequent recovery
changes in #215 and #219. Preserve the combined behavior, not just #213's copy.

| Layer / owning PR | Inspected branch and revision | Responsibility |
|---|---|---|
| [#114](https://github.com/dayfine/Arduino-Source/pull/114) | `nav/shared` @ `acf85aa2411a125ea1088908e66d4eff93351f1f` | Shared Grid, MapData, LegPlanner, LegWalker and route logging. Target owner for reusable recovery mechanics. |
| [#122](https://github.com/dayfine/Arduino-Source/pull/122) | `nav/story-steps` @ `24444f0fc38c819440b1112fcafc292bce2e0b53` | Story steps and checkpoint retry policy; consumes navigation. |
| [#213](https://github.com/dayfine/Arduino-Source/pull/213) | `frlg/stage1-core` @ `891b8f97e2e1399011431942c18079c532a19b5d` | Introduces FRLG OverworldReanchor / OverworldRecovery and their native tests. |
| [#215](https://github.com/dayfine/Arduino-Source/pull/215) | `frlg/stage3-mtmoon` @ `5b9b65a752dc124403501f30cf281d4c7f9cd29c` | Later FRLG recovery changes, including late battle behavior; baseline must include these. |
| [#219](https://github.com/dayfine/Arduino-Source/pull/219) | `frlg/stage5-bill` @ `360701b053f294cae5e652e2bcfb60fd25608306` | Later pacing/connection changes; history includes `51eb5de14` (both pacing tiles) and `00a207707` (warp slack after a connection). |
| [#224](https://github.com/dayfine/Arduino-Source/pull/224) | `frlg/stage7-celadon` @ `51c0ce6128e5981da56b370a770874b96a1e129f` | Aggregate FRLG baseline inspected for current behavior. |
| [#127](https://github.com/dayfine/Arduino-Source/pull/127), [#129](https://github.com/dayfine/Arduino-Source/pull/129) | `bdsp/nav-v4` @ `e531694c589464510d7720f4b571073aade2c118`; `bdsp/walk-v4` @ `b22e9471c35fb171daada221b6d467c1dc043387` | BDSP planning and native walker adapter owners. |
| [#167](https://github.com/dayfine/Arduino-Source/pull/167), [#226](https://github.com/dayfine/Arduino-Source/pull/226) | `bdsp/sim` @ `df6b1e47472f2448861eb72f4c432ead1d7c408c`; `bdsp/autostory-mine-floaroma-wip` @ `f8bdd62b9df4dbf285f93853147295e0552a0367` | BDSP simulator and mine/story integration regressions. |

Refresh heads and file ownership before implementation. Coordinate changes with
the owning PR agents; prepare patches/handoffs rather than pushing over their
branches. Move shared changes to their owner and merge them forward through the
stack. Never merge the FRLG aggregate into nav-core or create a dependency from
nav-core on a game or on #122's story types. Use fork drafts only, merge parents
rather than rebase/force-push, and leave upstream publication to the user.

## Intended boundary

| Shared native navigation | Game adapter / native execution | AutoStory consumer |
|---|---|---|
| Candidate pose sets; interruption/recovery outcomes; bounded search for convergent wall holds; route rejoin and recovery budgets. | Legal movement, elevation, warp/edge entry and arrival, trainer/object-world alternatives, timing, detector observations, input cancellation/draining and encounter clearing. | Goals/waypoints, story flags, declared route constraints, scene updates, checkpoint/save policy. |

Reuse existing shared types and seams before adding new ones. Candidate
uncertainty must cover map, tile and facing where needed. Keep policy parameters
explicit: FRLG's observed two-tile shortfall is not a universal BDSP error bound.
Likewise, timing estimates are not proof of movement or arrival.

One existing assumption needs an explicit audit: #114's `LegInterrupt::clear()`
contract says it leaves the same tile and facing. Trainer approach, delayed
movement or unflushed input may violate that promise. Adapt the outcome contract
or make adapter preconditions explicit and tested; do not merely rename the
FRLG code and preserve an invalid shared assumption.

## Ordered implementation and acceptance gates

Each stage ends with a reviewable commit/PR-owned patch and recorded test
results. Stop at a failing gate. Keep extraction, behavior changes and map-data
changes separate so a reviewer can identify the cause of any regression.

### 0. Pin ownership and the complete FRLG baseline

- [ ] Refresh the heads above and trace all changes to `OverworldReanchor`,
  `OverworldRecovery`, `OverworldRecoveryWalk`, `OverworldRoute`, `OverworldWalk`
  and the shared `LegWalker` since their owning PRs.
- [ ] Record baseline source SHA, map pin, test binary/CI run, registered suite
  names and results. Use the latest combined FRLG behavior as the reference.
- [ ] Identify which pure recovery functions can move to #114 and which need
  adapter hooks. Keep story retry semantics in #122 and game details outside core.
- [ ] Agree file ownership and merge sequence with the current owners before
  editing their branches. Keep unrelated work and existing lab saves intact.

**Gate:** a concrete extraction list, dependency diagram and passing native FRLG
baseline. The currently reported Python tests are not evidence of this gate.

### 1. Strengthen FRLG characterization before moving code

- [ ] Retain the existing native `OverworldReanchor`, `OverworldRecovery`,
  `OverworldMaps`, `OverworldWalk`, `OverworldSim` and AutoStory Simulation suites.
  Confirm test registration so passing compilation cannot hide missing suites.
- [ ] Fill missing regressions first using the matrix below. A new behavioral
  fix must have a red native regression before its fix; characterization of
  already-working behavior must pass on the pinned baseline.
- [ ] Assert candidate sets, chosen wall holds, convergence tile/facing,
  route-back endpoint, remaining route and failure reason—not just final success.
- [ ] Keep exact run/checkpoint evidence in test comments; label synthetic
  diagnostics and unavailable starting-pose/trace fields honestly.

**Gate:** baseline behavior is characterized, including later #215/#219 fixes.
Record failures requiring a separate fix rather than hiding them in extraction.

### 2. Extract the pure mechanism into nav-core

- [ ] Add the reusable candidate/convergence/rejoin machinery and portable
  native tests in #114, using movement/world hooks supplied by the adapter.
- [ ] Move generic tests with their implementation; keep real FRLG scenario
  integration tests in FRLG. Register shared tests/CMake sources on supported
  platforms and prove shared tests run without FRLG/BDSP AutoStory dependencies.
- [ ] Expose separate attempted-input, completed-movement and observed-stop
  outcomes. Unknown movement remains unknown; clearing an encounter alone
  establishes neither the intended endpoint nor an arrival map.
- [ ] Preserve FRLG behavior and policy initially: shortfall candidates at
  endpoint/one short/two short, up to three re-anchor holds, eight route stops,
  existing trainer hypotheses and late-interruption handling.
- [ ] Audit the existing `LegWalker`/interrupt seams for required outcome changes.
  Keep controller/detector implementation in adapters. Do not introduce a second
  competing walker or copy one recovery algorithm into each game.

**Gate:** shared native tests and applicable cross-platform CI/code-health pass.
No intentional route, threshold, count-credit or map behavior changes yet.

### 3. Switch FRLG to the shared implementation first

- [ ] Merge the owning shared changes forward through dependencies. Replace
  FRLG's pure implementation with a thin adapter; do not maintain two active
  copies of the algorithm. Keep game movement, maps, trainer worlds and detectors.
- [ ] Compare baseline and migrated native traces on the same inputs: candidate
  positions, holds, convergence, facing, route-back and remaining legs. Any
  intentional difference needs a separate red regression and behavioral change.
- [ ] Run the full FRLG matrix below, existing FRLG AutoStory suites, shared
  navigation suites, and applicable native CI/code-health checks.
- [ ] Preserve failure behavior: no safe common anchor means stop, not an
  optimistic endpoint, checkpoint advance or save.

**Gate:** FRLG consumes the shared implementation and all required native
regressions pass. Do not proceed to BDSP while FRLG parity is unresolved.

### 4. Specify BDSP interruption evidence, then integrate the adapter

- [ ] Add red native BDSP regressions for the mine report and r55 before changing
  count accounting or story legs. Pin source/map revisions and leave missing
  run evidence explicit; the November 5 Gemini diagnosis is a hypothesis.
- [ ] Carry possible positions after interrupted taps, late detection, partial
  holds and queued input. Distinguish time/input budget consumption from actual
  movement. Do not unconditionally remove `moved_chunks++` or retry every tap.
- [ ] Route BDSP planner/walker recovery through the shared core in their owning
  #127/#129 layers. Keep native scroll/still/battle/transition observations and
  encounter handling in BDSP, not in the story table or generic core.
- [ ] For column 15 and possible rows 15/16/17, prove a south wall hold converges
  at `(15,17)` against row 18 before the east leg. After a battle, drain input,
  confirm the overworld and repeat/replan within budget. A still view must not
  be accepted as a wall when caused by an NPC, menu or stalled capture.
- [ ] If columns or maps are also uncertain, find holds safe from every candidate
  or stop. Do not assume the mine's south clip solves arbitrary uncertainty.
- [ ] Treat any mine route change as a constraint/policy request, not a duplicate
  recovery implementation. Test proposed east/south anchors individually.

**Gate:** the BDSP native matrix passes through the shared mechanism. Re-run
FRLG and shared suites after every shared behavior change made for BDSP.

### 5. Validate end-to-end consumers and publish evidence

- [ ] Merge dependencies forward in their owning branches. Re-run shared, full
  FRLG and full BDSP native simulator suites against those combined heads.
- [ ] Test mine entry and exit independently, and separately validate checkpoint
  advancement only after established arrival. Missing pack links remain explicit
  failures until reviewed map/adapter contracts exist.
- [ ] Run the Simulation semantic scenarios as an independent check. Compare
  normalized states/outcomes; do not call them native planner/timing parity.
- [ ] Record CI links, binary/source/map pins, passing suites, unsupported cases
  and any fixture/resource failures. Do not waive new failures as pre-existing.
- [ ] Prepare a handoff for separately authorized console validation by its owner
  on matching FRLG/BDSP checkpoints/saves. Record observed results separately
  from simulator results. No console work is authorized by this plan-writing task.

**Gate:** both consumers use the common mechanism, native tests are green at
combined revisions, and remaining hardware/data limitations are explicit.

## Required native regression matrix

| Area | Cases and assertions |
|---|---|
| Shared recovery | One/two/many candidates; a common hold; multiple holds; no common endpoint; different maps/columns; exact convergence and route rejoin; depth/stop budgets exhausted. |
| Obstructions | NPC/wander area is not a wall anchor; approached trainer alternatives; ledge in jump direction; unknown terrain; warp on blocked glyph; unresolved map edge/door cannot anchor. |
| Input/observations | Interruption before/after a step; detection delayed until next leg; unknown facing; queued requests cancelled/drained; stale/still frame versus real collision; repeated interruptions. |
| FRLG Route 1 | Mart→Oak and reverse; late battle leaves a tile/whole leg short; re-anchor safely and retain the unexecuted route. |
| FRLG forest | Entry `(29,62)` and exit mats; every grass-leg stop; r16/r17 drift leads; endpoint/one/two-short candidates; next wall hold already converges versus needs inserted holds; gate fade versus battle/HP evidence. |
| FRLG Mt. Moon | Step-on ladder arrival/departure; missed battle flash before warp; late battle belongs to previous leg, not next; no fade leaves source pose uncertain. |
| FRLG later routes | Cerulean/Nugget Bridge connection delay and warp slack; pacing/capture leaves either tile; Bill moved beside the exit approach; trainer-world changes; bounded trainer approach remains game-specific. |
| BDSP r55 | Route202 post-dialogue `(27,5)`/`(26,5)` belief; do not walk into Logan; common east hold and replan from its established endpoint. |
| BDSP mine inbound | `below_roark` south leg interrupted with movement completed/not completed and detected late; rows 15/16/17 converge south; east at row15 hits Machop and must not count as wall localization; retry exhaustion fails. |
| BDSP mine outbound | Coal-room corridor and B1F stair/door boundaries; distinguish ordinary movement from step-into transition; missed fade/banner, arrival position/facing and premature counted-leg termination. |
| BDSP houses/exits | Door versus directional mat/stairs; reverse entrance and post-scene displacement; false indoor/outdoor judgment; queue overshoot; known map with unknown tile cannot advance checkpoint. |

The [scenario inventory](TRANSITION_SCENARIOS.md) contains source revisions,
checkpoints and known evidence gaps. Some BDSP mine maps/links differ between
our published pack and pending #226. Review corrections in PokemonSimulation
first; do not change terrain merely to make a native route pass or silently
advance the data pin during recovery extraction.

## PR sequence and ownership

1. **#114 owner:** shared extraction and portable tests, behavior preserving.
2. **FRLG owners (#213 and later delta owners):** consume shared code, preserve
   the combined baseline and remove duplicate pure implementation. Carry later
   fixes through their owners without importing the whole AutoStory stack into core.
3. **BDSP planner/walker owners (#127/#129):** integrate the shared outcome and
   recovery contract; generic additions go back to #114 and are merged forward.
4. **BDSP simulator/story owners (#167/#226):** real mine/house/r55 integration
   regressions and any declared story-route constraints. Story-specific tests
   remain here; reusable mechanism tests remain in nav-core.

Separate follow-up behavioral fixes from the extraction and re-run both games
when shared behavior changes. If stack restructuring becomes necessary, agree
it with the owning agents first and preserve review history.

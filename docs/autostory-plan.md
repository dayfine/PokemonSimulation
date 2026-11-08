# AutoStory offline integration plan

Track the work here, one milestone at a time. AutoStory owns the route/story
plan and hardware execution; PokemonSimulation owns map preparation, generic
planning and offline evaluation. FRLG and BDSP share contracts where the
semantics match and keep game-specific adapters where they differ.

## Next small unifications (2026-11-06)

The ordered [map/resources/story-data work](maps/UNIFICATION_STEPS.md) covers:
typed NPC/item/sign arrays and compact coordinate pairs; current FRLG/BDSP parity evidence; pinned external
Packages resources before removing native map copies/authoring; and **actions /
story events as data**, not merely route paths. It updates the older vendored-map
distribution choice. Published maps now use the v2 coordinate codec; historical
native replay pins retain their original data. The [FRLG resource handoff
checkpoint](maps/UNIFICATION_STEPS.md#frlg-resource-handoff-checkpoint-2026-11-06)
records prepared native #238, its published tool/data pins and validation gates.
FRLG #238 has merged into its story chain. All 22 BDSP maps now match #226
at the reviewed November 7 snapshot; the BDSP publication adds resolved pickup
metadata. BDSP resource adoption and actual native checkpoint exports remain
pending; see the current reconciliation and resource handoff notes.
The [story-event draft](story/STORY_PLAN_DRAFT.md) now records the FRLG/BDSP
semantic differences and complete hand-transcribed checkpoint examples; these
are review inputs, not native exports or executable plans.
The [execution follow-up](story/EXECUTION_PLAN.md) adds full FRLG main-story
coverage, program handoff/takeover (including RNG), and binding the shared event
data to the existing common engine with game-specific executors. First prove
the two exported checkpoints; then expand authored and executable coverage
without conflating them.
[Staged pickup enrichment](maps/item-identities.md) resolves 45 fixed pickups
and distinguishes three FRLG starter-choice interactions without changing active
map/replay pins.

## 1. Map ownership — current milestone

- [x] Import all 53 FRLG and 22 BDSP maps from the active aggregate branches,
  including BDSP consumer changes beyond its map-owner branch.
- [x] Import the generators and decoder dependencies with colocated tests.
- [x] Preserve the consumer schema, terrain patches, trigger extensions,
  flags, elevations, warp entry modes and unknown destinations.
- [x] Record source/target games, coordinate crops, checksums, console
  corrections, object overrides, unresolved provenance and scenario conditions.
- [x] Validate and export consumer-compatible JSON without an Arduino checkout.
- [x] Specify the [map change and consumer process](maps/consumer-process.md):
  pinned exports, remote-manifest hash verification and map corrections here.
- [ ] Recover exact pret revisions for BDSP inputs recorded as default branch;
  archive/pin inputs before refreshing them.
- [x] Implement pinned consumer lock/update/check commands, a reusable CI action
  and regression coverage. See [the integration](../integrations/arduino-source/README.md).
- [ ] Adopt the check in owning Arduino PRs and configure its required status.
  Resolve pending map differences first, remove duplicate offline authoring
  there and preserve native controller/detector tests.
- [ ] Consolidate the older eight `pokenav-map/1` fixtures only after explicit
  frame conversion and parity checks; do not overwrite them with cropped maps.

Inventory, commands and caveats: [maps/runtime-maps.md](maps/runtime-maps.md).

## 2. Generic route planning and drawing

- [x] First slice: [local routes on pinned runtime maps](navigation/RUNTIME_ROUTES.md),
  using the shared router and renderer, with state/metadata-aware movement,
  PNG/ASCII output and route/provenance JSON. Transitions remain excluded.

- [ ] Adapt the imported map contract to existing routing with explicit
  treatment of closed sides, Gen 3 elevations, entry modes and unresolved warps.
- [ ] Consolidate route generation/drawing tools here; accept waypoints,
  constraints and story state, and draw the planned route with frame labels.
- [ ] Export route legs plus their preconditions; test against the current
  Arduino plans before replacing their offline planner copies.
- [ ] Close the [native AutoStory route parity gap](navigation/AUTOSTORY_ROUTE_COMPARISON.md):
  align exported checkpoint state/goals/facing and native leg/open-stop costs,
  then compare traces including battle interruptions and replanning. Current
  diagrams are Python candidates for sourced goals, not native planner replays.

## 3. Shared simulation and recovery

This takes priority over moving the production walkers. A walker port is
optional until the simulation needs it.

- [ ] Define a versioned semantic event/state/trace contract. Share map identity,
  pose belief, route cursor/checkpoints, actions, observations, interruptions,
  outcomes and bounded retry budgets. Reuse the battle replay contract below.
- [x] First [transition/regression slice](navigation/TRANSITION_SCENARIOS.md):
  source-grounded inventory and semantic inputs; explicit FRLG cross-map
  predictions, pose beliefs/observations, queued/missed input, evidenced BDSP
  house arrival and bounded localization/clipping candidates. Mine south-wall
  clipping survives interrupted inputs without crediting a completed tile.
  Native plan import, dynamic trainer worlds and full replay remain pending.
- [ ] FRLG adapter: tile-locked movement, elevation, edge/warp entry and arrival,
  story flags and transitions. BDSP adapter: drift, collision/clipping,
  uncertain pose, arrival behavior and scene triggers.
- [ ] Complete native-exported regression replay beyond the reduced fixtures:
  FRLG Cerulean/Nugget Bridge transition; BDSP mine
  B1F/B2F stairs and house entrance/exit, with console trace IDs as evidence.
- [ ] Wild encounter recovery: interruption mid-leg, partial/queued movement,
  determine map and possible positions, relocalize, then resume from a proven
  checkpoint. Clipping must avoid doors, unsafe edges and unintended triggers.
- [ ] Test ambiguous landmarks, moving NPCs, repeated interruptions, exhausted
  retry budgets and unknown transitions. Assert safe failure as well as success.

The ordered native migration is tracked in [the shared recovery plan](navigation/SHARED_RECOVERY_PLAN.md):
characterize the combined FRLG baseline, extract into nav-core #114, prove FRLG
parity, then integrate and re-test BDSP. #224 inherits the recovery from #213
and later fixes; it is not the original owning PR.

Keep hardware timing/detector integration tests in Arduino. Shared semantic
fixtures should be data, not Python tests extracting C++ source strings.

## 4. Replay AutoStory plans and evaluate quality

- [x] First shared record codec and native/Python conformance vectors; see
  [checkpoint contract](story/CHECKPOINT_CONTRACT.md). Policy/envelope binding
  and evaluated game-table exports remain pending.
- [ ] AutoStory exports its route/story events as versioned JSON; replay here
  yields state changes and battle histories with complete preconditions.
- [ ] Validate both FRLG and BDSP plans through the same orchestration layer;
  report unsupported events and uncertainty explicitly.
- [ ] Extend [the battle replay interface](battles/autostory-replay-interface.md)
  to consume generated histories, evaluate strategy/preparation and report
  route quality. Minimum win rates (e.g. 60/70%) and reliability quotas remain
  configurable proposals, not selected defaults or exact-100% claims.
- [ ] Preserve party, captures/training/evolution, EXP/EV, moves, HP/PP,
  inventory/purchases and flags so future fire/grass teams with supporters
  can be evaluated without hardcoding Pokeguy's route.
- [ ] Add a Butter adapter after locating its actual format and examples;
  normalize supported steps, retain source locations and reject unsupported
  instructions rather than silently skipping them.

Start with a minimal common JSON event representation needed for replay.
Game-specific events carry explicit game payloads/handlers. Native FRLG/BDSP
story-type unification can follow proven semantics; it is not a prerequisite
for importing either format. Full production walker relocation is deferred.

## 5. Repeat the full-run analysis for BDSP and Let's Go Pikachu/Eevee

Recorded follow-up; no new game implementation starts with this note. Repeat
the FRLG exercise for **Brilliant Diamond/Shining Pearl (BDSP)** and
**Let's Go Pikachu/Let's Go Eevee (LGPE)**, using each game's actual plan and
data sources. The shared replay/evaluation interface should support these
adapters without requiring a pret decompilation or FRLG-shaped inputs.

- [ ] Identify and pin suitable map, trainer/team, species, move, item and
  mechanics sources for each game/version. Record source provenance, coverage
  and uncertainty; distinguish remake baselines from verified target-game data.
  Do not assume DP data fully describes BDSP or FRLG data describes LGPE.
- [ ] Reconstruct the full battle sequence and entering conditions from the
  chosen run/AutoStory plan: party, progression/stats, moves/PP, HP/status,
  inventory, purchases/pickups, healing and relevant game state. Reconcile
  progression and observed stats against run evidence using game-specific rules.
- [ ] Validate each game's battle mechanics and NPC AI adapter against known
  cases before publishing win rates. Select the engine/data adapter per game;
  sharing the orchestration does not imply reusing the Gen 3 battle engine.
- [ ] Simulate every battle with adaptive sampling and confidence intervals;
  rank the hardest fights and classify the required player policy complexity
  using A/B/C where applicable: attacks, recovery, setup/team planning.
- [ ] Compare observed-run entries with deliberate preparation variants and
  report required healing, consumables and PP logistics. Carry unsupported
  mechanics or uncertain inputs as explicit limits on the conclusions.
- [ ] Publish one conditions/strategy/win-rate handoff per game/run, analogous
  to [the FRLG battle reference](battles/pokeguy-conditions.md), and evaluate
  exported plans against the shared configurable quality criteria.

## Navigation conformance checkpoint after #45

The next slice is [shared exact navigation fixtures](navigation/CONFORMANCE.md):
eight pinned real-map spatial cases, with independent Python and native FRLG /
BDSP evaluation. It found and fixes Python's omitted-grid FRLG elevation default
(ground 3). Fixtures include exact maps, initial hypotheses, flags/variables,
typed input legs and complete arrival traces/anchor expectations.

- [x] Define the first strict versioned data pack and exact Python replay.
- [x] Prepare native registered consumers using real production movement APIs,
  with byte checks and deliberate drift rejection (64 FRLG / 54 BDSP focused
  tests locally). Native draft pins remain previews until publisher merge.
- [x] Provide immutable export/check tooling; map approval remains mandatory.
- [x] Promote native fixture copies to merged #46 main revision; prepare the
  native fixture-pin workflow and verify its command locally.
- [ ] Publish the native branches and run/merge their prepared workflow (initial
  push gate approval remains pending).
- [ ] Extend the same contract to uncertain encounter outcomes, bounded wall
  recovery and route rejoin, then to matching-policy route/leg expectations.
- [ ] Resolve mine/house map-version differences before shared BDSP cases.

Arduino #227/#228/#229 and Simulation #45 are merged; earlier historical run
counts in the recovery plan are retained as historical measurements, not the
latest case totals. The conformance document records the new focused run scope.

### Encounter-recovery oracle after #46

[The next slice](navigation/ENCOUNTER_RECOVERY.md) strengthens Python assertions
from candidate counts to complete state records. Four injected real-map cases
cover interrupted/queued movement, lost facing, drained-input gating, advancing
wall confirmation, retry exhaustion, NPC rejection and a Forest warp boundary.
It also fixes an import error exposed by actual Forest trainer-sight metadata.

- [x] Specify exact state checkpoints and verify the Python semantic oracle.
- [ ] Export equivalent native walker reports and compare these checkpoints in
  FRLG/BDSP. Existing native spatial fixtures remain the eight #46 cases.
- [ ] Verify native automatic route rejoin/cursor semantics; the current Python
  diagnostic supplies its post-anchor continuation leg explicitly.

### First native recovery replay after #47

- [x] Export seven actual registered BDSP Route202 walker/GridSim cases, with
  pinned source/map identities, physical displacement and native plan logs.
- [x] Replay the supplied native legs in Python, compare full interrupted tile
  sets, reject credit-as-displacement, and verify native recovery/rejoin outcomes.
- [x] Record the native per-wall retry policy separately from Python's global
  Session budget; keep unreported native facing/queue/video state unverified.
- [ ] Publish the native exporter and run native GitHub CI (approval pending).
- [x] Add actual FRLG walker exports for the first Forest shortfall checkpoint.
- [ ] Bridge the remaining full-state fields for both games.

See [the native BDSP checkpoint](navigation/ENCOUNTER_RECOVERY.md#first-actual-native-replay-bdsp-route-202).

### FRLG native Forest replay (stacked after #49)

- [x] Capture actual `run_route()` / `OverworldSimWalker` repair and route rejoin
  for the r16 Forest one/two-tile shortfalls; preserve TRUST negative controls.
- [x] Verify that an already-converging next wall needs no inserted repair.
- [x] Publish readable checked traces and side-by-side collision-map diagrams;
  keep runtime candidate storage, video/queue/timing evidence unverified.
- [x] Reject vertical FRLG sign interactions as Python wall anchors.
- [ ] Publish the locally committed native exporter and run native CI (same
  pending initial-push approval as the preceding native adapters).
- [ ] Export actual candidate/facing/queued-input observations and compare
  complete #47 state snapshots, rather than reconstructed geometry alone.

See [the Forest results and exact limits](../data/navigation/native-recovery/FRLG_FOREST.md)
and [the implementation checkpoint](navigation/ENCOUNTER_RECOVERY.md#native-frlg-forest-shortfall-replay).

### PLZA story-event design probe

- [x] Draft [intro + Main Missions 01–03](story/PLZA_OPENING_DRAFT.md) as reviewable
  event data alongside the FRLG/BDSP transcriptions.
- [ ] Review the common envelope and game profiles using all three shapes.
- [ ] Bind native exports/observations and replay parity; the PLZA example has no
  maps, ruleset, executor or simulator binding and provides no win rates.

This is a format exercise, not PLZA battle expansion. Native resource adoption
and FRLG/BDSP evaluated story exports remain the implementation sequence.

Exchange-format JSON Schemas now cover common story records, current v2 runtime maps and FRLG battle cases/full reports; see [schemas](../schemas/README.md). Semantic validators and native reader parity remain required.

### Evaluated story capture progress

- [x] Export FRLG Parcel `00.05` from its actual compiled native table and check
  the clean CI capture here with its source revision and artifact provenance;
  see [native exports](story/NATIVE_EXPORTS.md). Native bookkeeping remains
  distinct from observed entry state; runtime/policy/execution inputs are unbound.
- [ ] Export BDSP mine/Roark `01.03` through its evaluated native table adapter.
- [ ] Bind effective shared requirements/state/save/retry policy and establish
  native/Python execution parity before replacing C++ authoring tables.

- [ ] Import the complete pinned FRLG map catalog (425 distinct source maps;
  currently 53 published), with explicit unsupported/stateful geometry gaps,
  reviewed publication and native consumer-pin adoption.
- [ ] Write the full Pokeguy LeafGreen story-event draft through Champion,
  reusing existing battle/progression evidence and adding source-backed
  overworld actions. Track authored, bound and replay-validated coverage
  separately; see [execution plan](story/EXECUTION_PLAN.md#full-frlg-world-and-pokeguy-plan-expansion).

### Authored checkpoint pilot update (2026-11-08)

- FRLG Parcel `00.05` is data-authored in Arduino #260 / Simulation #73. Native Linux, Windows and macOS tests and same-file Python replay pass. The lean authored contract replaces the export snapshot as the production definition; snapshots remain migration fixtures only.
- The next slice is [BDSP mine/Roark `01.03`](../data/story/bdsp-mine-pilot/README.md), preserving current #226 revision `0738cd55b` (15 events), with explicit save-card/failure policy, multi-tile arrivals and wall/door variants. Nine Python scenarios and Python CI pass in Simulation #74; Arduino #263 is published with full native execution/paired CI running. No new map edits are included.
- Then add the starter RNG handoff/resume example, before full FRLG expansion. The [execution plan](story/EXECUTION_PLAN.md) records the revised two-gate migration sequence and remaining parity limits.

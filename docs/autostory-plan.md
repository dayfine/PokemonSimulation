# AutoStory offline integration plan

Track the work here, one milestone at a time. AutoStory owns the route/story
plan and hardware execution; PokemonSimulation owns map preparation, generic
planning and offline evaluation. FRLG and BDSP share contracts where the
semantics match and keep game-specific adapters where they differ.

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

Keep hardware timing/detector integration tests in Arduino. Shared semantic
fixtures should be data, not Python tests extracting C++ source strings.

## 4. Replay AutoStory plans and evaluate quality

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

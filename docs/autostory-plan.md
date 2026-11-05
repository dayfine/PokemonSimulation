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
- [ ] Recover exact pret revisions for BDSP inputs recorded as default branch;
  archive/pin inputs before refreshing them.
- [ ] Consumer handoff: agree how Arduino obtains these packs, switch builds
  to that resource and remove duplicate offline generation there. Preserve
  native controller/detector tests in Arduino. Coordinate with map owners.
- [ ] Consolidate the older eight `pokenav-map/1` fixtures only after explicit
  frame conversion and parity checks; do not overwrite them with cropped maps.

Inventory, commands and caveats: [maps/runtime-maps.md](maps/runtime-maps.md).

## 2. Generic route planning and drawing

- [ ] Adapt the imported map contract to existing routing with explicit
  treatment of closed sides, Gen 3 elevations, entry modes and unresolved warps.
- [ ] Consolidate route generation/drawing tools here; accept waypoints,
  constraints and story state, and draw the planned route with frame labels.
- [ ] Export route legs plus their preconditions; test against the current
  Arduino plans before replacing their offline planner copies.

## 3. Shared simulation and recovery

This takes priority over moving the production walkers. A walker port is
optional until the simulation needs it.

- [ ] Define a versioned semantic event/state/trace contract. Share map identity,
  pose belief, route cursor/checkpoints, actions, observations, interruptions,
  outcomes and bounded retry budgets. Reuse the battle replay contract below.
- [ ] FRLG adapter: tile-locked movement, elevation, edge/warp entry and arrival,
  story flags and transitions. BDSP adapter: drift, collision/clipping,
  uncertain pose, arrival behavior and scene triggers.
- [ ] Regression scenarios: FRLG Cerulean/Nugget Bridge transition; BDSP mine
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

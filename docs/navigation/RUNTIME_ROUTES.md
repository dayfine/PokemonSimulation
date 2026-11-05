# Local routes on pinned runtime maps

The first step of the generic-planner migration connects the imported FRLG
and BDSP maps to the existing Dijkstra search and PNG renderer. It plans
**inside one map**. Cross-map planning and story replay remain future work.

`pokesim.maps.local_routing.LocalMap` keeps the complete source JSON alongside
its effective patched grid. Its `World.try_step` adapter handles runtime
movement metadata without converting it to the older reference-file schema.
Ordinary `World` instances continue using the existing grid movement rules.

## Run

From the repository root with a full-history PokemonSimulation checkout:

```sh
PYTHONPATH=src python3 -m pokesim.cli.route \
  --game frlg --map PalletTown --start 6,8 --goal oaks_lab_front \
  --png /tmp/pallet-route.png --json /tmp/pallet-route.json

PYTHONPATH=src python3 -m pokesim.cli.route \
  --game bdsp --map Route201 --start 44,3 --goal 53,3 \
  --png /tmp/route201-route.png --json /tmp/route201-route.json
```

Start/goal can be local `x,y` or a named point from that runtime map. A trainer
point occupied by an NPC is not a walking destination; choose an adjacent
interaction tile. Coordinates belong to the runtime crop, not the older
snake-case BDSP reference files.

Default input is the cached `origin/main` publishing commit. `--source` selects
another full-history cache; `--revision` selects a full immutable commit. This
offline command reads verified Git objects, checks approval against cached main
and verifies the entire game pack's inventory/hashes before loading the map.
It does not fetch; update the trusted cache separately when newer data is wanted.

The JSON output records the publishing revision, manifest/map hashes, crop
origin/dimensions, source-game provenance and unresolved source revision status,
entry assumptions, supplied flags/variables, costs, moves and limitations.
Retain the JSON alongside the drawing when sharing a route.

## State and movement

| Input/feature | Current handling |
|---|---|
| Terrain patches | Applied before search; original JSON and evidence remain available. |
| `8/2/4/6` | Closed north/south/west/east side, tested on both entry and exit. They never cause forced movement. |
| Encounter terrain | Grass cost, including closed-side tiles in the `wild` region; no battle/recovery simulation. |
| FRLG elevations | Transition and bridge rules from the existing Gen 3 movement model. A bridge start requires explicit `--elevation`. |
| Objects | Occupied tiles excluded; a wandering NPC's entire declared rectangle is excluded. |
| Hide flags | Pass repeatable `--flag FLAG_NAME`; absent flags are treated as unset. No story scripts run. |
| Scene variables | Pass repeatable `--var NAME=INTEGER`. Unknown or active coord-event boxes are excluded; a known disarmed box can be crossed. |
| Map-state assumptions | Maps with manifest preconditions, such as the opened Vermilion Gym, require `--acknowledge-map-state`. This asserts the documented state; it does not establish it on console. |
| Directional warps | Their trigger fires when pressing the matching direction while standing on the mat. Merely entering the mat does not trigger them. |
| Other warps | Stepping into/on them ends local movement; the search never traverses a transition. |
| Map edges | Unresolved boundaries; they are not wall anchors. |

`--grass-cost` changes the grass penalty (finite and nonnegative). Tile, turn
and warp costs remain the shared router's defaults. Exit status is 0 for a
route, 2 for an unreachable local goal, and 1 for invalid inputs or conditions.
The CLI writes no report or image for an unreachable goal.

ASCII uses the runtime glyphs plus `@` start, `X` goal, `*` route, `O` object
occupancy and `?` active/unknown scene areas. PNGs show the computed route in
red, excluded object/scene areas in blue and closed tile sides as black lines.

## Limits and next work

This is a conditional static route, not an AutoStory plan-quality judgment.
Trainer sight, omitted NPCs, actual NPC motion, battle interruptions, controller
timing, active scene effects and recovery are not simulated. In particular,
source pack omissions of wandering BDSP NPCs are not proof that those tiles
are clear in the game. Generic story triggers with unevaluated semantics are
rejected instead of silently ignored.

Next in step 2: connect maps using explicit edge/warp metadata, model entry and
arrival behavior, and export route legs with constraints suitable for the
consumer. BDSP rectangles alone do not establish that two maps connect;
different interior matrices can reuse the same coordinate origin. Actual
story-event execution and interruption/recovery tests belong to step 3.

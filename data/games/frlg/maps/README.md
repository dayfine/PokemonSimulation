# FRLG map set

Each FRLG map has up to three files (see [OVERLAYS.md](../../../../docs/maps/OVERLAYS.md)):

| Directory | Content | Owner |
|---|---|---|
| `base/` | The map as generated from `pret/pokefirered@ce6406d8`: every source warp and connection linked by name, water as `w`, elevation grids, spinner/hole/button glyphs. | The generator; `--check` reproduces every file byte for byte. Never edited by hand. |
| `overlays/` | Ordered authored operations over the base (`tile`, `link`, `object`, `trigger`, `point`), each with `why`, `when`, `evidence` and `status` ([schema](../../../../schemas/map-overlay.schema.json)). | Reviewed PRs, one operation per map fix. |
| `runtime/` | The effective map, base + overlays at story state `complete` (every `when` passed), for consumers that do not apply overlays yet. A map without an overlay publishes its base bytes. | Derived by `map_overlays write`; `map_overlays check` fails on any difference. |

Each map's **status** lives in its entry in
[`data/maps/runtime-manifest.json`](../../../maps/runtime-manifest.json), with
the runtime file's hash and `base` / `overlay` references (file and sha256):

| Status | Meaning | Count |
|---|---|---:|
| `verified` | Reviewed content. `verified.basis` is `approved-runtime-pack` (in the approved pack before this set existed; no per-map run was recorded) or `console-run` (`run`, `date`, `checkpoint`, optional `consumer_revision`). | 57 |
| `candidate` | Generated, unreviewed. | 99 |

Every entry also records its `source` (pret file and commit), the same object
as the runtime file's `source`. The status is kept out of the map bytes, so
promoting a map changes only the manifest.

`runtime/` is the directory the published manifest and the Arduino-Source
resource pin read (`data/games/frlg/maps/runtime/<Name>.json`). "Runtime" names
the published map format, not approval.

## Overlays

Overlays today:

| Map | Operation | why | when |
|---|---|---|---|
| `VermilionCity_Gym` | `tile` (4..6, 6..7) to `.`: the electric beams are off | `story_state` | `FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES`, after checkpoint 00.23 |
| `PokemonMansion_1F`, `_2F`, `_3F`, `_B1F` | `gate` open or closed: one operation per barrier (13 in all). The base and runtime tiles show each barrier as `G` (the base is the blockdata, the switch-off state); the effective map has it as the new game leaves it until the switch flag is set | `story_state` | `FLAG_POKEMON_MANSION_SWITCH_STATE`, set when a statue switch is pressed (a second press clears it) |
| `VictoryRoad_1F`, `_2F`, `_3F` | `gate` open: one operation per barrier half (2 per barrier, 8 in all). The base and runtime tiles show the barrier as `G` (the base is the blockdata, the open state); the effective map has it closed (the OnLoad script's new-game state) until a boulder has been pushed onto the switch's button. | `story_state` | `VAR_MAP_SCENE_VICTORY_ROAD_*` (a VAR, set to 100 by the switch) |
| `SilphCo_2F` to `SilphCo_11F` | `gate` open: one operation per Card Key door (20 in all). The base and runtime tiles show the door as `G` and the map's `gates` table names it; the effective map has it closed (the OnLoad script's new-game state) until the flag is set. Evidence lists the opening script | `story_state` | `FLAG_SILPH_<n>F_DOOR[_<m>]`, set when the door is opened with the Card Key |

## Gates and story state

`G` marks a **gate**: a barrier that the story opens (or closes). Every `G` tile
is in an entry of the map's `gates` table (`tiles`, `open_glyph`, `new_game`,
and what moves it). A consumer that does not read the table treats `G` as a
wall. The base and runtime files keep `G`; `map_overlays.effective_map(name,
state)` draws each gate open or closed for a story state (gate operations in
the overlay say when), and the runtime files are not resolved, so a consumer
infers the gate states itself from the story state it records:

| Gate kind | Table entry | Story state a consumer records | Open when |
|---|---|---|---|
| Silph Co. Card Key door | `{"opens_by": "card_key_face_a", "flag": "FLAG_SILPH_5F_DOOR_1", "new_game": "closed"}` | the set of `FLAG_SILPH_<n>F_DOOR[_<m>]` flags: each is set the moment that door is opened with the Card Key | its flag is set |

The Mansion's gates belong to one **switch**, `mansion` (the `switches` table:
the flag, `toggle`, the four `floors` that share it, and each statue's tile and
the tile and direction to face it from). A consumer records one boolean, the
switch state (`FLAG_POKEMON_MANSION_SWITCH_STATE`, off at a new game; every
statue press asks yes/no and on yes flips it, and each floor redraws its gates
when it loads), and infers every gate from it (`open_when` in the gates table).
Gates open per switch state (tiles `x,y`; all other tiles never change):

| Floor | Statue (stand on, face north) | Open with the switch OFF (closed with it ON) | Open with the switch ON (closed with it OFF) |
|---|---|---|---|
| `PokemonMansion_1F` | (5, 5) from (5, 6) | `barrier_2` (31..33, 18..19) | `barrier_1` (22..24, 10..11), `barrier_3` (27..29, 25..26), `barrier_4` (32..34, 25..26) |
| `PokemonMansion_2F` | (2, 16) from (2, 17) | `barrier_1` (12, 6..8) | `barrier_2` (24..26, 14..15), `barrier_3` (10, 30..32) |
| `PokemonMansion_3F` | (12, 5) from (12, 6) | `barrier_1` (21, 6..8) | `barrier_2` (17..19, 11..12) |
| `PokemonMansion_B1F` | (24, 29) from (24, 30) and (27, 5) from (27, 6) | `barrier_2` (33..35, 20..21), `barrier_4` (16, 28..30) | `barrier_1` (12, 10..12), `barrier_3` (20..22, 22..23) |

The runtime files are not resolved: they keep `G`. `map_overlays.effective_map`
at `COMPLETE` (every `when` passed) is the switch-on state, which the story does
not stay in, so use a recorded switch state (`StoryState(flags=...)`), not
`COMPLETE`, for a Mansion route.

## Victory Road boulder switches

A Strength boulder pushed onto a button tile (`B`, `MB_STRENGTH_BUTTON`) runs that tile's coord event
(`src/field_player_avatar.c` `DoBoulderFinish`, then `HandleBoulderActivateVictoryRoadSwitch` in
`src/field_control_avatar.c`); the player stepping on it does nothing. The script redraws a rock barrier
open and sets a scene VAR to 100 (`data/maps/VictoryRoad_<f>/scripts.inc`, `FloorSwitch*`); each floor's
OnLoad draws the barrier closed while the VAR is not 100. These are VARs, not flags, so the switch's
`flag` names a `VAR_` and carries `set_value` (100), `toggle: false`, `pressed_by: strength_boulder` and
its `buttons`; a consumer records the VAR as set once the boulder is on the button. Nothing unpresses a
switch except `Route23_OnTransition` (`data/maps/Route23/scripts.inc`), which sets all four VARs back
to 0 every time Route 23 loads, so a consumer clears them on entering Route 23. A barrier is two
metatiles that open to different glyphs (`8`, a floor tile with its north side closed, over `~`), so
each barrier is two gates, `barrier_<n>_top` and `barrier_<n>_bottom`, moved by `floor_switch_<n>`.

| Floor | Button (switch) | VAR | Barrier |
|---|---|---|---|
| `VictoryRoad_1F` | (20, 16) `floor_switch_1` | `VAR_MAP_SCENE_VICTORY_ROAD_1F` | (12, 14), (12, 15) |
| `VictoryRoad_2F` | (2, 19) `floor_switch_1` | `VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER1` | (13, 10), (13, 11) |
| `VictoryRoad_2F` | (14, 19) `floor_switch_2` | `VAR_MAP_SCENE_VICTORY_ROAD_2F_BOULDER2` | (33, 16), (33, 17) |
| `VictoryRoad_3F` | (7, 7) `floor_switch_1` | `VAR_MAP_SCENE_VICTORY_ROAD_3F` | (12, 12), (12, 13) |

The boulders themselves (Strength objects) are **not modelled**: the map format has no movable object,
so the pack carries neither them nor where they can be pushed. Their start tiles in the decomp
(`object_events`, `OBJ_EVENT_GFX_PUSHABLE_BOULDER`):
1F (7, 18), (4, 12), (16, 3); 2F (8, 7), (6, 17), (33, 19) hidden until a 3F boulder falls
(`FLAG_HIDE_VICTORY_ROAD_2F_BOULDER`); 3F (19, 15), (33, 18) hidden by `FLAG_HIDE_VICTORY_ROAD_3F_BOULDER`,
(35, 13), (32, 5). A boulder pushed onto the hole `H` at 3F (34, 18) falls and reveals 2F's (33, 19)
(`HandleBoulderFallThroughHole`). `Route23_OnTransition` also resets both hide flags (shows the 3F boulder, hides the 2F one).

## One-way warps

A hole (tile `H`, decomp behavior `MB_FALL_WARP`) is a warp with `"one_way": true`:
you fall to the warp event it names and the landing has no way back up. In the
pack: `PokemonMansion_3F` (18..20, 18) and (23..24, 18), and `VictoryRoad_3F`
(34, 18). The generator sets it on every warp on an `H` tile, and the validator
requires it. Seafoam Islands (1F to B3F) and the Six Island Dotted Hole floors
also have holes but are outside the pack's scope; they get it when added.

List a map's differences from its base, or see it at a story state:

```sh
PYTHONPATH=src python3 -m pokesim.maps.map_overlays audit VermilionCity_Gym
PYTHONPATH=src python3 -m pokesim.maps.map_overlays audit --all
PYTHONPATH=src python3 -m pokesim.maps.map_overlays effective VermilionCity_Gym --checkpoint 00.23
```

In Python, `map_overlays.effective_map(name, StoryState(checkpoint=..., flags=...))`
returns base + the operations in effect; `StoryState()` is a new game and
`COMPLETE` is past every `when`.

## Workflow

1. **Pull candidates into a run.** Bumping Arduino-Source's
   `devtools/maps/map-resources.lock.json` to a newer main commit publishes every
   map, candidates included, into `Packages/Resources/Pokemon/Maps/frlg`. AutoStory
   parses only the maps named in its own map list, so a candidate is used once
   it is added there.
2. **Promote on a console pass.** After a run walks a candidate map, record it:

   ```sh
   PYTHONPATH=src python3 -m pokesim.maps.frlg_map_set promote Route11 \
     --run <run record> --date 2026-11-10 --checkpoint 00.14 \
     --consumer-revision <Arduino-Source commit>
   ```
3. **Publish the status.** Merge the manifest change to main and bump the
   consumer lock to that commit (`manifest_sha256` changes; map bytes do not).

A map **fix** adds one overlay operation with its evidence (the output of
Arduino-Source's map-fix-evidence skill), then runs `map_overlays write`. It
needs the usual review. Never edit `base/` or `runtime/` by hand.

A **generator change** regenerates every base: generate into an empty
directory, replace `base/` with it, run `map_overlays write` (a stale overlay
operation, one that no longer changes anything, fails here), then
`frlg_map_set sync-candidates` for new maps.

## Scope

[`pokeguy-map-scope.json`](pokeguy-map-scope.json) lists the 281 catalog maps
the generator does **not** publish as candidates (425-map catalog):

| Excluded group | Maps |
|---|---:|
| Sevii, event islands and island Trainer Tower | 164 |
| Multiplayer facilities | 5 |
| Optional mainland caves, routes and legendary destinations | 13 |
| Unused interiors, cabins and upper floors | 73 |
| Mainland Pokemon Centers and elevators (scripted in AutoStory) | 26 |

**Pokemon Centers and elevators are scripted in AutoStory, not mapped.** The
Centers are mostly identical and the elevators are small, so a per-building map
costs more than a script. `IndigoPlateau_PokemonCenter_1F` stays a candidate
because it is the Elite Four lobby. Eight Center 1F maps were verified before
this decision and stay in the set with their status.

Verified maps may lie outside the scope: those 8 Centers, `CeruleanCave_1F`,
`CeruleanCave_2F`, `CeruleanCave_B1F`, `PalletTown_RivalsHouse` and
`PewterCity_Museum_1F`. Every candidate must be in scope and every in-scope
map must be present.

This is a conservative first-Champion scope, not a visited-map ledger. The ship
healing cabin is **SSAnne_1F_Room6** (pinned source heal script). Tea, Fly,
Bill, Safari Surf and Warden reward rooms are retained. LeafGreen-specific
version conditions still need review.

## Checks

```sh
PYTHONPATH=src python3 -m pokesim.maps.frlg_map_set check
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_pack
PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --all \
  --scope data/games/frlg/maps/pokeguy-map-scope.json --item-identities \
  --out data/games/frlg/maps/base --manifest data/maps/runtime-manifest.json --check
PYTHONPATH=src python3 -m pokesim.maps.map_overlays check
python3 -m pip install -r schemas/requirements.txt
PYTHONPATH=src python3 -m pokesim.maps.frlg_import_audit data/games/frlg/maps/runtime \
  --schema --manifest data/maps/runtime-manifest.json \
  --scope data/games/frlg/maps/pokeguy-map-scope.json --out /tmp/frlg-import-audit.json
```

The generator `--check` regenerates every manifest map's base, verified maps
outside the scope included, and requires each to match byte for byte. The pack
audit allows one kind of unresolved link, a **boundary**: the destination is
scope-excluded and absent, so the link is a dead end, never a successful
transition (100 warps, 2 connections across the set; a link into a scripted
Center or elevator keeps its target name). Since verified maps are generated
bases too, every warp into a map of the set finds its return point: the 31
pending relinks of #81 are gone.

## Candidate gaps

| Gap | Count |
|---|---:|
| Cells with unsupported non-collision behavior | 0 |
| Dynamic warp destinations | 0 |
| Pickups without a pinned identity catalog entry | 79 |

70 candidates omit their elevation grid with an `elevation_omitted` reason in
`source`: every walkable cell is then default ground (3). 25 keep their grids
(water, bridges, stairs, multi-level terrain). A map with water always keeps
its grid: a missing grid reads as ground everywhere, and water's level is what
stops a walking player in Arduino's FRLG walker. Glyphs beyond the original set are
documented in [tile-legend.json](tile-legend.json): spin tiles `u d l r o`
(RocketHideout_B2F/B3F, ViridianCity_Gym), holes `H` (PokemonMansion_3F,
VictoryRoad_3F) and Strength buttons `B` (VictoryRoad_1F/2F/3F). Arduino's
native decoder needs those glyphs before those maps join its map list.
A collision-free `MB_COUNTER` (PewterCity_Museum_1F (11, 5)) is floor: the
counter only lets the player talk across it.

NPCs and pickups keep source event, script and optional local-ID provenance.
A person who wanders or walks back and forth has a `wander` box: their start
tile +- the pret movement range, kept inside the map
(`IsCoordOutsideObjectEventMovementRange()`). Back-and-forth walkers and
`*_UP_AND_DOWN`/`*_LEFT_AND_RIGHT` wanderers keep to their axis.
A person who walks a sequence of directions (`MOVEMENT_TYPE_WALK_SEQUENCE_*`)
has a `path` instead: `tiles`, the tiles they step through in order from their
start tile, and `loop`, the index in `tiles` they go on from after the last
one. The generator walks pret's rule on the map's collision, behavior and
elevation grids (`MoveNextDirectionInSequence()` and
`MovementType_WalkSequence*_Step1()` in `src/event_object_movement.c`): at the
edge of their range they turn to the next direction; any other collision (a
wall, ground at another elevation, a person who stands still) makes them walk
in place for good, which a path shows as a last tile that loops to itself.
E.g. Route 11's Dave walks down 4 and right 8 and back the same way. Every
FRLG sequence walker loops back to its start tile (`loop` 0).
`source_event` is a zero-based source array index, not an in-game object ID.
An item ball's `item` and `quantity` come from the pinned catalog
(`data/maps/item-identities.json`) or, for a map it doesn't list, from the
ball's own `finditem` script in `data/scripts/item_ball_scripts.inc` (hash
pinned in `data/maps/item-source-inputs.json`); a scripted ball (the Eevee
ball, Silph Scope, Lift Key) stays `pickup: unresolved`. Item balls are
objects and block movement. Hidden items (`bg_events` of type `hidden_item`)
are `hidden_items` records (`coord`, `item`, `quantity`, `flag`,
`source_bg_event`, optional `underfoot`): data only, they never block.
Scripted geometry, flags, other background interactions, coordinate triggers
and game-version differences still need review. Structural validity does not
establish story traversability.

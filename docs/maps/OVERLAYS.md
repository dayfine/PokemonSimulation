# Map overlays: generated base plus authored changes

Status: accepted design, 2026-11-09. Migration in progress (steps 1 and 2 done; see the end).

## Why

Until now an authored change to a map could live in four places:

1. Inline in a map's JSON: BDSP's `patches` (repeated in the manifest), and
   FRLG edits baked into runtime files (water drawn as `#`, Vermilion Gym's
   opened gate, warps and connections left unlinked when the target map was
   not in the pack).
2. Python tables in `bdsp_decomp_map_builder.py`: `PATCHES`, `OBJECTS`,
   `COORD_EVENTS`, `WARP_DOORS`, `WARPS`, `POINTS`.
3. Story-specific omissions mixed into world data (the Route 201 Potion giver
   left off the map because she moves).
4. Route anchors with prose proof (`POTION_GIVER_TALK_FROM`), and in AutoStory
   code, scripted interiors.

So a map could not be regenerated without losing edits, nobody could list
every way a map differs from its decomp, and approving a map fix meant
reviewing a whole JSON diff. On 2026-11-09 this showed up as 31 FRLG warps
and connections that verified maps never linked, which blocked routing into
the new candidate maps.

## Design

### 1. Base layer: generated only

Each map's base comes from the pinned decomp and is never edited by hand.
The generator's `--check` reproduces it byte for byte. Generator gaps are
fixed in the generator, not patched afterwards: water vs wall, elevation,
spinner/hole/button glyphs, every warp and connection the source defines.

### 2. One overlay file per map

`data/games/<game>/maps/overlays/<Map>.json` holds an ordered list of
operations. Each operation has:

| Field | Meaning |
|---|---|
| `op` | `tile` (coord, glyph), `link` (warp or connection), `object` (add, remove, move), `trigger` (add, remove), `point` (only for world facts; see 3) |
| `why` | `console_measured`, `remake_delta`, `story_state`, `generator_gap` |
| `when` | for `story_state`: the flag or checkpoint after which it applies (e.g. Vermilion Gym's gate is open after 00.23; an NPC hidden by a flag) |
| `evidence` | for `console_measured`: run, date, screenshot path, what was seen; for `remake_delta`: the observation; for `generator_gap`: the generator issue it waits on |
| `status` | `candidate` or `verified`, as for maps |

`generator_gap` operations are temporary: each one names the generator fix
that removes it.

### 3. Route hints belong to the story, not the map

Anchors such as "the tile to talk to the Potion giver from" describe our
route, not the world. They move to the checkpoint data next to the steps
that use them. Map `point`s stay only for world facts (a warp's return point,
a sign's tile).

### 4. One resolver

`effective_map(name, story_state)` = base + the overlay operations that apply
at that point in the story. PokemonSimulation's sims and Arduino-Source's
walker use the same function (Python here, a small C++ port in Arduino-Source
with shared test vectors). The published pack ships base and overlays
separately, so a consumer can always see what is authored.

### 5. Scripted, not mapped

Pokemon Centers, elevators and other repeated interiors are listed in the
scope file as scripted in AutoStory (2026-11-09 decision). They get no maps
or overlays.

### 6. Review and status

- A map fix is a PR that adds one overlay operation with its evidence: the
  output of Arduino-Source's map-fix-evidence skill. The user approves these.
- `audit <Map>` lists every difference from the base, grouped by `why`.
- A console pass promotes a map's status and the status of the operations it
  exercised (`frlg_map_set promote`). As MAPPING_PROTOCOL.md says, a pass does
  not verify tiles the run never touched; the promotion records the run so
  that limit stays visible.

## Step 1 as built (FRLG)

### Layout and format

- `data/games/frlg/maps/base/<Map>.json`: all 152 maps, `pokesim-runtime-map/2`
  in the contract format. `frlg_decomp_map_builder --all --scope ... --manifest
  ... --out data/games/frlg/maps/base --check` reproduces every one; with
  `--manifest`, verified maps outside the scope (8 Centers, Cerulean Cave,
  RivalsHouse, Museum) get bases too.
- `data/games/frlg/maps/overlays/<Map>.json`: `pokesim-map-overlay/1`
  (`schemas/map-overlay.schema.json`): `{format, map, operations}`. A `tile`
  operation takes `coords` (a list, so one fix such as a gate is one
  operation) and `glyph`; `when` is `{flag, after_checkpoint}` (either or both)
  and is required for `story_state` and only there; a `generator_gap` names
  its `evidence.generator_fix`. An operation that changes nothing fails, so a
  generator fix cannot leave a stale operation behind.
- `data/games/frlg/maps/runtime/<Map>.json`: unchanged path and format. It is
  now derived: the base bytes for a map without an overlay, else base +
  overlays at story state `complete` (every `when` passed), with
  `source.overlay = {file, story_state}`.
- Manifest: each FRLG entry keeps `file`/`sha256` (the runtime file) and adds
  `base: {file, sha256}` and, when present, `overlay: {file, sha256}`.

`pokesim.maps.map_overlays` implements `effective_map(name, story_state)`
(`StoryState(checkpoint, flags)`, `NEW_GAME`, `COMPLETE`; an operation applies
once its flag is set or once the state's checkpoint is later than
`after_checkpoint`), `audit <Map>` / `audit --all`, `effective <Map>`,
`check` and `write`.

### What the verified maps' hand edits became

Every difference between the 57 verified files and their regenerated bases:

| Difference | Maps | Became |
|---|---:|---|
| Vermilion Gym's beams open, (4..6, 6..7) | 1 | Overlay: `tile`, `story_state`, when `FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES` / after 00.23 (was `OPENED_TILES`). |
| Water behind collision drawn as `#` (SSAnne_Exterior 602 tiles, VermilionCity 156) | 2 | Dropped, no overlay: consumers do not need it. Python routing blocks `w`; Arduino's walker blocks water by elevation and AutoStory's `story_route_costs()` forbids Surf. Both maps keep their elevation grids. |
| Warps and connections into maps the v1 pack lacked (59 warps, 7 connections) and their arrival points | 21 | Generator output (the 31 pending relinks and the one-way connections are gone). |
| Object provenance, pickup identities, starter interactions | 53 | Generator output (`source_event`, `source_script`, `source_local_id`, `item`, `quantity`, `interaction`). |
| Elevation grid left out where every walkable tile is ground | 5 | Generator output with `source.elevation_omitted` (CeruleanCity_Mart, PewterCity_Mart, ViridianCity_Mart, SSAnne_1F_Corridor, VermilionCity_Gym). |

`src/pokesim/maps/testdata/frlg-v1-to-base-delta.json` records the generated
differences per map; the publication test undoes exactly those and still
reproduces the reviewed v1 digests, so nothing else changed.

Generator fixes in this step: every manifest map gets a base; the omission of
an elevation grid is limited to lossless cases (never with water, never on a
map with nowhere to search from); a collision-free `MB_COUNTER` is floor; and
`OPENED_TILES` left the generator. 14 candidates gain their elevation grids.

### Consumer (Arduino-Source)

**Recommended interim:** keep reading `runtime/` (the pre-resolved effective
maps at story state `complete`) and switch to base + overlays in step 4. The
export layout, file names and count are unchanged (152 FRLG maps; the export
copies `runtime/` only), so adopting this revision needs only:

1. `devtools/maps/map-resources.lock.json`: `games.frlg.revision` to the merge
   commit on main and `manifest_sha256` to that manifest's hash (`consumer_sync
   update --layout resources`). 71 FRLG files change bytes (all 57 verified, 14
   candidates); BDSP is untouched.
2. Re-run the FRLG overworld map and route tests: verified maps now link the
   gates, houses and connections they used to leave open, so a route may use
   a newly linked map when both are loaded. Links into unloaded maps stay dead
   ends (`take_warp`/`cross_edge` return nothing).
3. `devtools/runtime-map-tests/prepare_parity.py` stays pinned to its v1
   fixture revision. If it is moved to this revision, expect 348 pairs
   (2 x (152 FRLG + 22 BDSP), not 150), and skip the `enrich_map` variant for
   FRLG: the item catalog's FRLG map-content pins describe the v1 maps (FRLG
   identities are generator-owned now; the pins retire with step 2's catalog
   republish, which also touches BDSP).
4. `Pokemon_MapData.cpp`'s glyph table still lacks `u d l r o H B`. None of
   AutoStory's current maps contain them; add them before
   RocketHideout_B2F/B3F, ViridianCity_Gym, PokemonMansion_3F or
   VictoryRoad_1F-3F join its map list.

**Step 4 (later):** read `base/` and `overlays/`, port `effective_map` to C++
with shared test vectors from `test_map_overlays.py`, pass the checkpoint and
flags AutoStory knows, and extend the export (`consumer_sync`) with the two
directories.

## Step 2 as built (BDSP)

`data/games/bdsp/maps/{base,overlays,runtime}/`, the same three layers
([README](../../data/games/bdsp/maps/README.md)). `bdsp_decomp_map_builder`
writes the base: its tables `PATCHES`, `OBJECTS`, `COORD_EVENTS`, `WARP_DOORS`
and `WARPS` are gone, and so are the manifest's `generation_overrides`,
`terrain_corrections` and `bdsp_differences` copies of them (their notes are the
operations' evidence). `POINTS` stays: route anchors, step 3. Generator
defaults: objects hidden by a story flag are left out, warp tiles are `.`, coord
events are `coord_event_<index>`.

The runtime files are byte-identical to the published ones: `git diff
data/games/bdsp/maps/runtime` is empty and every manifest runtime `sha256` is
unchanged; only the manifest's metadata and the new `base`/`overlay` references
changed.

What the 45 operations (18 maps) are:

| Was | Became | Count |
|---|---|---:|
| `PATCHES` (22 tiles) | `tile`, `console_measured`; published as the map's `patches` (run and date from the evidence) | 7 |
| `WARP_DOORS` (17 tiles) | `tile` to `D`, `generator_gap` (waits on decoding door versus step-on) | 5 |
| `WARPS` | `link` (warp add), `generator_gap` (the builder emits no warps) | 3 |
| `OBJECTS` `show` (+ `range`, `name`) | `object` add with its wander box, `story_scope` | 13 |
| `OBJECTS` `add` | `object` add, `console_measured` | 2 |
| `OBJECTS` `hide` | `object` remove: `console_measured` (3: Route203, Sandgem), `story_scope` (1: Route201's Potion lady) | 4 |
| `OBJECTS` `at`/`still`/`name` | `object` update (`to`, `set`), `console_measured` | 1 |
| `COORD_EVENTS` names | `trigger` update (`set` the name), `story_scope` | 9 |
| `COORD_EVENTS` `add` | `trigger` add, `console_measured` | 1 |

New in the format for this: `why: story_scope` (below); `object` `update`
(`to`, `set`: a value sets a field, `null` removes it) and an `index` on `object`
add (position among the objects of the kind, since people keep the events
file's order); `trigger` add, remove and update; `link` warp `add`. The
resolver's `game` selects the publication conventions: BDSP publishes a
`console_measured` tile as a `patch` over the raw tiles (the loader and the
Arduino reader apply them), keeps every record key where the builder had it,
writes the readable map format and carries no `source.overlay` stamp.

`story_scope` is the fifth `why`: a choice about which people and labels the
static map carries for our story (a person the decomp hides by flag but the
story meets, one it walks to instead of routing around, a trigger's name). The
Jubilife clowns' wander ranges (the point of #89 and #90) are the `object` add
operations in `overlays/JubilifeCity.json`, with the capture and the limit of
the measurement in their evidence. It has no `when`: several of these people
are there only for a window of the story (00.05's clowns, Rowan at 00.03), but
the resolver only has "from here on" (`story_state`), so they are present at
every state until it learns windows.

Left for later: `POINTS` (step 3); `story_scope` presence windows; the older
snake-case `pokenav-map/1` fixtures under `data/games/bdsp/maps/*.json`, whose
object lists are a second hand-kept copy; FRLG's runtime files, which predate
key-order preservation and the patch convention.

## Migration

Each step is its own PR; the existing tests must show no behaviour change
except where a step says otherwise.

1. FRLG generator fixes: emit every source warp and connection (this replaces
   the 31 pending relinks), water as `w`, elevation, and the spinner (`u d l r o`),
   hole (`H`) and Strength button (`B`) glyphs. Hand edits in the verified
   FRLG maps become overlay operations (Vermilion Gym's gate as `story_state`).
2. BDSP: move `PATCHES`, `OBJECTS`, `COORD_EVENTS`, `WARP_DOORS`, `WARPS` and
   inline `patches` into overlay files, keeping their evidence. Done
   2026-11-12 (above).
3. Move route anchors from map `points` into the checkpoint data.
4. Resolver in both repos; Arduino-Source reads base + overlays instead of
   pre-baked files.

## Log

- 2026-11-09: design written after the FRLG single-map-set change (#81);
  step 1 started.
- 2026-11-09: step 1 (FRLG): one generator mode for all 152 bases (every
  warp and connection linked, water kept as water with its elevation grid,
  OPENED_TILES removed); Vermilion Gym's beams are the only overlay
  (`story_state`); water-as-wall dropped; `map_overlays` with
  `effective_map`, `audit`, `check`, `write`; overlay schema; runtime files
  pre-resolved at story state `complete` as the consumer's interim.
- 2026-11-11: generator: item balls on maps outside the pinned item catalog
  get their item from their `finditem` script, and hidden items are published
  as non-blocking `hidden_items`; Celadon Mansion 2F, 3F, Roof and RoofRoom
  join the scope (156 maps). Objects only: no tile changes.
- 2026-11-12: step 2 (BDSP): the builder writes a pure base; `PATCHES`,
  `OBJECTS`, `COORD_EVENTS`, `WARP_DOORS` and `WARPS` are 45 overlay operations
  in 18 files with their evidence; `map_overlays` covers both games, adds the
  `object` update, `trigger` and warp-add operations and `story_scope`; the
  manifest drops the copies of the tables. The runtime files did not change a
  byte. From #90: the Poketch Company clown's row-18 range is the
  `clown_poketch_company` operation, not a table edit.
- 2026-11-12: FRLG Victory Road's three boulder switches and their rock barriers are
  gates (8 gate operations, `when` a `VAR_`); the switches table gains the Strength-button kind.
  The boulders are not modelled (no movable object in the format).

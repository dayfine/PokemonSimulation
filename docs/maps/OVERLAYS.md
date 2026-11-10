# Map overlays: generated base plus authored changes

Status: accepted design, 2026-11-09. Migration in progress (see the end).

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

## Migration

Each step is its own PR; the existing tests must show no behaviour change
except where a step says otherwise.

1. FRLG generator fixes: emit every source warp and connection (this replaces
   the 31 pending relinks), water as `w`, elevation, and the spinner (`u d l r o`),
   hole (`H`) and Strength button (`B`) glyphs. Hand edits in the verified
   FRLG maps become overlay operations (Vermilion Gym's gate as `story_state`).
2. BDSP: move `PATCHES`, `OBJECTS`, `COORD_EVENTS`, `WARP_DOORS`, `WARPS` and
   inline `patches` into overlay files, keeping their evidence.
3. Move route anchors from map `points` into the checkpoint data.
4. Resolver in both repos; Arduino-Source reads base + overlays instead of
   pre-baked files.

## Log

- 2026-11-09: design written after the FRLG single-map-set change (#81);
  step 1 started.

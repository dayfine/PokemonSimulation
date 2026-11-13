# Runtime map ownership

PokemonSimulation owns the imported map packs, generation tables, corrections
and offline checks. Arduino remains the consumer of generated JSON. Consumer
branches have not been changed or had their generators deleted by this import.
The staged work is tracked in [the integration plan](../autostory-plan.md).
The [consumer process](consumer-process.md) specifies pinned exports and hash
checks so future map corrections are authored here. The
[check/update tools and CI action](../../integrations/arduino-source/README.md)
are implemented; Arduino adoption and required status settings are pending.

## Inventory and provenance

| Pack | Maps | Arduino snapshot |
|---|---:|---|
| `data/games/frlg/maps/runtime/` | 152 (57 verified, 95 candidate) | `frlg/stage7-celadon`, `51c0ce6128e5981da56b370a770874b96a1e129f` (first 53) |
| `data/games/bdsp/maps/runtime/` | 22 | `bdsp/autostory-v4`, `040693c62486439b4b473732860b0d4c6632dc2a` |

FRLG is one map set with a per-map `status` (`verified` or `candidate`) in the
manifest; see [its README](../../data/games/frlg/maps/README.md) for the
statuses, scope and promotion workflow.

[The manifest](../../data/maps/runtime-manifest.json) lists every file,
its SHA-256, original path and revision, target/source game, crop origin,
source revision certainty, terrain patches, generator overrides and special
preconditions. The BDSP consumer snapshot adds `OreburghMineB1F` and revises
`OreburghCity` beyond the map owner branch `bdsp/maps-v4` at
`20b518e5a23388683c151ba32e3acd5623d9994b`; its generator is imported too.

FRLG generation uses `pret/pokefirered` at
`ce6406d8c2eaf46d543c8a2606de0c3cb1951982`. The target pack is FRLG;
its decomp source is FireRed, not an independent LeafGreen map audit.
BDSP uses Diamond as its default baseline and Platinum for selected interiors
and Ravaged Path. Some interiors record Platinum `c6689696d5fb` and are explicitly
unverified on console. Many other BDSP maps record only `default branch` and a
read date. Their exact pret commit is **unresolved**. Successful regeneration
from the original cache proves parity with this import, not reproducibility
from an arbitrary current pret checkout. Recover/pin these inputs before
refreshing that cache or claiming reproducible BDSP source generation.

Imported Python and map JSON retain their Arduino lineage; the original MIT
copyright notice is retained in the root [LICENSE](../../LICENSE).

See [OVERLAYS.md](OVERLAYS.md) for the base + overlay design that replaces inline patches and builder tables.

## Runtime schema and frames

The published pack uses `pokesim-runtime-map/2`, explicitly marked in every map
and the manifest. [The publication record](V2_PUBLICATION.md) describes the
conversion and native prerequisites. Historical unmarked/v1 packs remain
readable. The original runtime contract comes from Arduino's `Pokemon_MapData.h/.cpp` at the pinned
snapshots; [runtime_map_schema.py](../../src/pokesim/maps/runtime_map_schema.py) validates geometry
and navigation fields and preserves unknown extensions.

| Field | Meaning |
|---|---|
| `name`, `source`, `tiles` | Required identity, source (`decomp_file`, `revision`, `date`), rectangular row strings. |
| `world` | Optional shared world name and crop origin `x,y`. BDSP crop origins are in the manifest even when JSON omits this field. |
| `elevation` | Optional matching grid of hexadecimal Gen 3 elevations, default zero. |
| `allow_running` | Optional boolean, default true. |
| `points`, `regions` | Named `[x,y]` tiles and named lists of tiles. BDSP also encodes regions as numbered points. |
| `warps` | `coord: [x,y]`, optional `enter` (default `walk_into`), paired `to_map,to_point` when resolved, optional `one_way: true` for a drop (a hole, tile `H`: the landing has no warp back; required on every warp on an `H` tile). |
| `connections` | `side,to_map,offset` for connected map edges. |
| `npcs`, `items`, `signs`, `interactables` | Typed arrays of `name,coord` (identified pickups may derive `name` from `source_event` and default `quantity` to 1), optional facing, inclusive `wander` box (`min`, `max`), trainer sight/looks and hide flag. Section supplies kind; non-item interactions use `interactables` when enriched. |
| `triggers`, `flag_sets` | Named story trigger boxes/conditions; named sets of game flags. Preserve game semantics. |
| `coord_events` | BDSP extension: named `coord,width,length,var,value,source` scene triggers. |
| `gates`, `switches` | FRLG story barriers. `gates`: id -> `tiles`, `open_glyph` (`.` or `~`), `new_game` (`open`/`closed`) and what moves it: a Card Key door has `opens_by: card_key_face_a` and `flag`; a switch gate has `switch` (id in `switches`) and `open_when` (`on`/`off`). `switches`: id -> shared `flag`, `toggle`, `floors` (maps that share the state), `statues` (`coord`, `face_from`, `facing`). A Strength-button switch (Victory Road) has `toggle: false`, a `VAR_` as `flag`, `set_value`, `pressed_by: strength_boulder` and `buttons` (`coord`, tile `B`); `open_glyph` may also be `2/4/6/8`. See the FRLG map README. |
| `patches` | Ordered `coord,glyph,measured_by` overrides, applied by the loader over raw tiles. |

Tiles: `#` blocked, `.` open, `~` encounter terrain (including cave floor),
`w` water, `^v<>` directional ledges, `D` door/warp entrance, `S` sign,
space outside; FRLG adds spin tiles `u d l r` (forced north/south/west/east)
and `o` (stop spinning), `H` hole (fall warp), `B` Strength button and `G` gate (closed unless the consumer resolves the map's `gates` table from its story state). The
canonical table is `data/games/frlg/maps/tile-legend.json` (with
`runtime_symbols.SYMBOLS` and the runtime-map schema's tile pattern). **`8/2/4/6` close the north/south/west/east side of a tile**;
they are not the forced-movement glyphs of the older `pokenav-map/1` schema.
Some closed-side encounter tiles additionally appear in FRLG's `wild`
region. Preserve elevation and region semantics when adapting these maps.

Warp entry modes: `walk_into`, `step_on`, `cave_entrance` (arrival steps south),
and `walk_north/south/west/east`. An unresolved warp remains an entrance whose
destination is unknown; it is not a wall or a safely traversable normal tile.
`effective_map()` applies terrain patches to a copy and retains the raw
evidence; it does not execute flags, NPC motion, triggers or transitions.

The eight older snake-case BDSP files immediately under `data/games/bdsp/maps/`
remain `pokenav-map/1` reference fixtures used by the existing grid tests.
Their coordinates must not be mixed with this pack. For example, old Route
201 has origin `(96,832)`, size `64×32`; imported Route201 has `(96,839)`,
size `64×25`. That seven-row difference is a crop, not a BDSP terrain patch.

## BDSP differences and scenario assumptions

There are 22 measured terrain patches across Route201, Route202,
Route204North and PlayerHouse1F. Since the overlay migration they are `tile`
operations in `data/games/bdsp/maps/overlays/` with their run, date and
observation as evidence; the runtime JSON keeps the baseline tiles intact and
publishes them as `patches` with `measured_by`. A measured discrepancy is
an applied navigation correction, not automatically proof of a remake change:
baseline decoding and measurement error remain possible explanations.

`bdsp_decomp_map_builder.py` writes the base (`data/games/bdsp/maps/base/`) and
keeps only `MAPS` (source game/header, world crop and verification limits) and
`POINTS` (route anchors; step 3 of [OVERLAYS.md](OVERLAYS.md) moves them). The
other former tables (`PATCHES`, `OBJECTS`, `COORD_EVENTS`, `WARP_DOORS`,
`WARPS`) are overlay operations; the
[BDSP README](../../data/games/bdsp/maps/README.md) says which became what.
Examples of explicit BDSP differences include a wandering NPC in Sandgem
and added Floaroma people.

The overlays include **story-specific choices** (`why: story_scope`), not just remake deltas.
For example, the Route201 Potion giver is omitted from static planning because
she moves and her interaction is approached separately. Hidden wandering
NPCs still exist on console: future generic simulation must model their
occupancy/recovery rather than assume the omitted cells are always clear.
Do not promote a `show`/`still` assumption or an unverified interior into a
confirmed BDSP fact. Older fixtures' pending offsets remain unresolved;
they have not been silently applied to the new coordinate frames.

FRLG also has scenario assumptions: Vermilion Gym's barriers are open in the
published runtime file, through the `story_state` overlay operation that
applies after `FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES` (checkpoint 00.23); its
base keeps them closed ([OVERLAYS.md](OVERLAYS.md)). The manifest labels this
entry precondition. Story flag sets and NPC hide flags must eventually be
replayed by the game adapter.

## Parser and builder modules

All map modules live directly in `src/pokesim/maps/`; they can serve any
planner or simulator, independent of AutoStory.

| Module | Responsibility |
|---|---|
| `dppt_map_decomp_parser.py` | Parse Diamond/Platinum source headers, matrices, land data and events. These are BDSP baselines, not BDSP-native files. |
| `bdsp_decomp_map_builder.py` | Build the BDSP base maps from those parsed sources and crops; corrections and story assumptions are overlays. |
| `frlg_decomp_map_builder.py` | Read pinned FireRed source maps/metatiles and build the FRLG base maps. |
| `map_overlays.py` | Apply authored overlay operations to a base (`effective_map(name, story_state)`), audit them and derive the FRLG and BDSP runtime files. |
| `runtime_map_schema.py` | Validate the shared runtime format's structural and coordinate invariants. |
| `runtime_map_pack.py` | Audit, apply patches to copies, and export packs. |

## Generate, validate and export

Run from the repository root; Python stdlib only:

```sh
PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder --all \
  --scope data/games/frlg/maps/pokeguy-map-scope.json --item-identities \
  --out data/games/frlg/maps/base --manifest data/maps/runtime-manifest.json --check
PYTHONPATH=src python3 -m pokesim.maps.map_overlays check
PYTHONPATH=src python3 -m pokesim.maps.frlg_map_set check
PYTHONPATH=src python3 -m pokesim.maps.bdsp_decomp_map_builder --check
PYTHONPATH=src python3 -m pokesim.maps.map_overlays --game bdsp check
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_pack
PYTHONPATH=src python3 -m unittest discover -s src/pokesim/maps -t src
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_pack --export-game frlg --out /tmp/frlg-map-export
```

FRLG fetches pinned raw files into `~/.cache/pokefirered/<commit>/` on cache
misses; `--cache` changes the cache root. BDSP never fetches: `--cache` defaults
to `~/.cache/maps/decomp`, containing paths `<pret/repo>/<source path>`.
Use an archived original cache for parity checks; unknown original commits
prevent a trustworthy fresh-cache recipe today. Unit tests use synthetic
Diamond/Platinum input and do not need the network or caches.

Omit `--check` to regenerate; review output and the manifest together. If a
map changes, update its manifest checksum/source/corrections and record the
new input revision/evidence; retain the original import lineage. Never just
refresh checksums to suppress an unexplained difference. Both generators'
`--out` can target a scratch directory. FRLG generates the named maps plus
the maps already in that directory, so supply the full desired pack when
generating a fresh export to retain graph links.

Exports validate inventory, checksums and resolved graph edges first, copy
JSON byte-for-byte and require an empty destination to avoid stale maps.
The export is suitable for the current Arduino paths; removing its copies
and generators requires a separate consumer PR and an agreed resource-fetch
mechanism. No runtime package download or Arduino build changes are implied
by this migration.

## Published compact-coordinate format

[The ordered unification plan](UNIFICATION_STEPS.md) specifies runtime-map v2:
`npcs`/`items`/`signs` arrays without repeated `kind` fields,
`coord: [x, y]`, inclusive wander `min`/`max` coordinate pairs, and short records
kept inline. `runtime_map_format` produces readable exports; Python loaders
normalize either representation for routing/recovery. Both generators now emit
v2. Native consumers must gain the v2 reader before adopting this pack.
Manifest/map format consistency is checked in both directions.

[Staged item enrichment](item-identities.md) adds resolved item IDs/counts and
source-event/collection references, and separates starter-choice interactions
from pickups. Use `runtime_map_format --game frlg|bdsp` to request it explicitly.

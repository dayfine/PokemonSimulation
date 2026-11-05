# AutoStory map ownership

PokemonSimulation owns the imported map packs, generation tables, corrections
and offline checks. Arduino remains the consumer of generated JSON. Consumer
branches have not been changed or had their generators deleted by this import.
The staged work is tracked in [the integration plan](../autostory-plan.md).

## Inventory and provenance

| Pack | Maps | Arduino snapshot |
|---|---:|---|
| `data/games/frlg/maps/autostory/` | 53 | `frlg/stage7-celadon`, `51c0ce6128e5981da56b370a770874b96a1e129f` |
| `data/games/bdsp/maps/autostory/` | 22 | `bdsp/autostory-v4`, `040693c62486439b4b473732860b0d4c6632dc2a` |

[The manifest](../../data/maps/autostory-manifest.json) lists every file,
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
notice is in [ARDUINO-LICENSE.txt](ARDUINO-LICENSE.txt).

## Runtime schema and frames

The pack is called `autostory-map/1` by this repository. That identifier is
external metadata: no new field was injected into consumer JSON. The imported
runtime contract comes from Arduino's `Pokemon_MapData.h/.cpp` at the pinned
snapshots; [schema.py](../../src/pokesim/maps/autostory/schema.py) validates geometry
and navigation fields and preserves unknown extensions.

| Field | Meaning |
|---|---|
| `name`, `source`, `tiles` | Required identity, source (`decomp_file`, `revision`, `date`), rectangular row strings. |
| `world` | Optional shared world name and crop origin `x,y`. BDSP crop origins are in the manifest even when JSON omits this field. |
| `elevation` | Optional matching grid of hexadecimal Gen 3 elevations, default zero. |
| `allow_running` | Optional boolean, default true. |
| `points`, `regions` | Named `[x,y]` tiles and named lists of tiles. BDSP also encodes regions as numbered points. |
| `warps` | `x,y`, optional `enter` (default `walk_into`), paired `to_map,to_point` when resolved. |
| `connections` | `side,to_map,offset` for connected map edges. |
| `objects` | `name,kind,x,y`, optional facing, inclusive `wander` box (`x0,y0,x1,y1`), trainer sight/looks and hide flag. |
| `triggers`, `flag_sets` | Named story trigger boxes/conditions; named sets of game flags. Preserve game semantics. |
| `coord_events` | BDSP extension: named `x,y,width,length,var,value,source` scene triggers. |
| `patches` | Ordered `x,y,glyph,measured_by` overrides, applied by the loader over raw tiles. |

Tiles: `#` blocked, `.` open, `~` encounter terrain (including cave floor),
`w` water, `^v<>` directional ledges, `D` door/warp entrance, `S` sign,
space outside. **`8/2/4/6` close the north/south/west/east side of a tile**;
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
Route204North and PlayerHouse1F. JSON keeps the baseline tiles intact;
`patches` carry console run/date evidence. The manifest repeats these separately
from object/trigger/door interpretation overrides. A measured discrepancy is
an applied navigation correction, not automatically proof of a remake change:
baseline decoding and measurement error remain possible explanations.

`bdsp.py` keeps the authored tables and explanatory evidence:

- `MAPS`: source game/header, world crop and verification limits.
- `PATCHES`: console terrain corrections.
- `OBJECTS`: source object index, position changes, stationary assumptions,
  additions and omissions. Examples of explicit BDSP differences include
  wandering NPCs on Route203/Sandgem and added Floaroma people.
- `COORD_EVENTS`: source trigger names and console-only trigger additions.
- `WARP_DOORS`, `WARPS`, `POINTS`: navigation interpretation and route anchors.

These tables include **story-specific omissions**, not just remake deltas.
For example, the Route201 Potion giver is omitted from static planning because
she moves and her interaction is approached separately. Hidden wandering
NPCs still exist on console: future generic simulation must model their
occupancy/recovery rather than assume the omitted cells are always clear.
Do not promote a `show`/`still` assumption or an unverified interior into a
confirmed BDSP fact. Older fixtures' pending offsets remain unresolved;
they have not been silently applied to the new coordinate frames.

FRLG also has scenario assumptions: Vermilion Gym's barriers are baked open
by `OPENED_TILES` after `FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES`. The manifest
labels this entry precondition. It is not an initial-state gym map. Story
flag sets and NPC hide flags must eventually be replayed by the game adapter.

## Generate, validate and export

Run from the repository root; Python stdlib only:

```sh
PYTHONPATH=src python3 -m pokesim.maps.autostory.frlg --out data/games/frlg/maps/autostory --check
PYTHONPATH=src python3 -m pokesim.maps.autostory.bdsp --check
PYTHONPATH=src python3 -m pokesim.maps.autostory.pack
PYTHONPATH=src python3 -m unittest discover -s src/pokesim/maps -t src
PYTHONPATH=src python3 -m pokesim.maps.autostory.pack --export-game frlg --out /tmp/frlg-map-export
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

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
| `candidate` | Generated, unreviewed. | 95 |

Every entry also records its `source` (pret file and commit), the same object
as the runtime file's `source`. The status is kept out of the map bytes, so
promoting a map changes only the manifest.

`runtime/` is the directory the published manifest and the Arduino-Source
resource pin read (`data/games/frlg/maps/runtime/<Name>.json`). "Runtime" names
the published map format, not approval.

## Overlays

There is one overlay today:

| Map | Operation | why | when |
|---|---|---|---|
| `VermilionCity_Gym` | `tile` (4..6, 6..7) to `.`: the electric beams are off | `story_state` | `FLAG_FOUND_BOTH_VERMILION_GYM_SWITCHES`, after checkpoint 00.23 |

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

[`pokeguy-map-scope.json`](pokeguy-map-scope.json) lists the 285 catalog maps
the generator does **not** publish as candidates (425-map catalog):

| Excluded group | Maps |
|---|---:|
| Sevii, event islands and island Trainer Tower | 164 |
| Multiplayer facilities | 5 |
| Optional mainland caves, routes and legendary destinations | 13 |
| Unused interiors, cabins and upper floors | 77 |
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
`source_event` is a zero-based source array index, not an in-game object ID.
Scripted geometry, flags, hidden/background interactions, coordinate triggers
and game-version differences still need review. Structural validity does not
establish story traversability.

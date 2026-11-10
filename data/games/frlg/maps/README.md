# FRLG map set

One copy of each FRLG map, in `runtime/`. Each map's **status** lives in its
entry in [`data/maps/runtime-manifest.json`](../../../maps/runtime-manifest.json):

| Status | Meaning | Count |
|---|---|---:|
| `verified` | Reviewed content. `verified.basis` is `approved-runtime-pack` (in the approved pack before this set existed; no per-map run was recorded) or `console-run` (`run`, `date`, `checkpoint`, optional `consumer_revision`). | 57 |
| `candidate` | Generated from `pret/pokefirered@ce6406d8`, unreviewed. Bytes are owned by the generator. | 95 |

Every entry also records its `source` (pret file and commit), the same object
as the map file's `source`. The status is kept out of the map bytes, so
promoting a map changes only the manifest: map hashes stay the same.

`runtime/` is the directory the published manifest and the Arduino-Source
resource pin read (`data/games/frlg/maps/runtime/<Name>.json`). "Runtime" names
the published map format, not approval. There is no other FRLG map directory.

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

A map **fix** is a separate change. It edits the map, updates its manifest
hash/corrections with evidence, and needs the usual review. Do not substitute a
candidate's bytes for a verified map to make a route pass. To regenerate
candidates after a generator change, generate into an empty directory, copy only
`candidate` maps into `runtime/`, then run `frlg_map_set sync-candidates`.
That command rewrites candidate entries from the files and never touches verified ones.

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
  --out data/games/frlg/maps/runtime --manifest data/maps/runtime-manifest.json --check
python3 -m pip install -r schemas/requirements.txt
PYTHONPATH=src python3 -m pokesim.maps.frlg_import_audit data/games/frlg/maps/runtime \
  --schema --manifest data/maps/runtime-manifest.json \
  --scope data/games/frlg/maps/pokeguy-map-scope.json --out /tmp/frlg-import-audit.json
```

The generator `--check` regenerates the in-scope catalog. It requires every
candidate to match byte for byte and skips verified maps (reviewed content may
legitimately differ from the generator). The pack audit allows exactly two
kinds of unresolved link:

- **Boundary**: the destination is scope-excluded and absent, so the link is a dead end, never a successful transition (59 warps, 2 connections).
- **Pending relink**: a candidate warps into a verified map that has no return point yet (31 warps). Verified maps were built while their neighbors were absent, so their warps toward candidates carry no destination, and some candidate connections are one-way. Relinking edits reviewed maps and needs approval with evidence.

Pending relinks by verified map: CeruleanCity (CeruleanCity_House1),
LavenderTown (LavenderTown_Mart, LavenderTown_VolunteerPokemonHouse,
PokemonTower_1F), Route2 (Route2_EastBuilding), Route22 (Route22_NorthEntrance),
Route5 (Route5_SouthEntrance), Route6 (Route6_NorthEntrance),
SSAnne_1F_Corridor (SSAnne_1F_Room6), VermilionCity (VermilionCity_Mart),
ViridianCity (ViridianCity_Gym). One-way connections into verified maps come from
Route21_North, Route12, Route23, Route8, SaffronCity_Connection, Route11 and
SaffronCity.

## Candidate gaps

| Gap | Count |
|---|---:|
| Cells with unsupported non-collision behavior | 0 |
| Dynamic warp destinations | 0 |
| Pickups without a pinned identity catalog entry | 79 |

84 candidates omit their elevation grid with an `elevation_omitted` reason in
`source`. Every relevant walkable cell is then default ground (3). 11 keep their
grids (bridges, stairs, multi-level terrain). Glyphs beyond the original set are
documented in [tile-legend.json](tile-legend.json): spin tiles `u d l r o`
(RocketHideout_B2F/B3F, ViridianCity_Gym), holes `H` (PokemonMansion_3F,
VictoryRoad_3F) and Strength buttons `B` (VictoryRoad_1F/2F/3F). Arduino's
native decoder needs those glyphs before those maps join its map list.

NPCs and pickups keep source event, script and optional local-ID provenance.
`source_event` is a zero-based source array index, not an in-game object ID.
Scripted geometry, flags, hidden/background interactions, coordinate triggers
and game-version differences still need review. Structural validity does not
establish story traversability.

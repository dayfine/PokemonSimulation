# PokeGuy FRLG source-map candidate

140 maps retained from the 425-map catalog at
`pret/pokefirered@ce6406d8c2eaf46d543c8a2606de0c3cb1951982`.
The explicit exclusions and review basis live in
[../pokeguy-map-scope.json](../pokeguy-map-scope.json):

| Excluded group | Maps |
|---|---:|
| Sevii, event islands and island Trainer Tower | 164 |
| Multiplayer facilities | 5 |
| Optional mainland caves, routes and legendary destinations | 13 |
| Unused interiors, cabins and upper floors | 103 |

This is a conservative first-Champion review scope, not a verified visited-map
ledger. Uncertain transit floors (notably Silph) and mainland outdoor routes
remain until the complete event draft establishes their exact use. Restore
excluded Centers if an alternative plan adds healing there. The ship healing
cabin is **SSAnne_1F_Room6**, confirmed by its pinned source heal script; Tea,
Fly, Bill, Safari Surf and Warden reward rooms are also retained.

These are **unreviewed candidates**, separate from the 53 approved maps in
`../runtime`. Approved maps, manifests and native resource pins are unchanged.
This is a FireRed source baseline; LeafGreen-specific version conditions still
need review for PokeGuy's plan.

## Reproduce and audit

Use an empty directory for generation; `--check` verifies without rewriting:

```sh
PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder \
  --all --scope data/games/frlg/maps/pokeguy-map-scope.json \
  --item-identities --out /tmp/frlg-pokeguy-candidate
PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder \
  --all --scope data/games/frlg/maps/pokeguy-map-scope.json \
  --item-identities --out data/games/frlg/maps/source-candidate --check
python3 -m pip install -r schemas/requirements.txt
PYTHONPATH=src python3 -m pokesim.maps.frlg_import_audit \
  data/games/frlg/maps/source-candidate --schema \
  --scope data/games/frlg/maps/pokeguy-map-scope.json \
  --out /tmp/frlg-import-audit.json
```

`--all` without `--scope` can still regenerate the entire pinned source catalog
outside the repository. Scoped generation reads full source headers so it
preserves destinations into excluded maps. The audit accepts these **103 boundary
warps** only with the explicit exclusion inventory. Their missing destination
resources cannot be routed/executed successfully; they are not deleted doors or
successful no-op transitions. Unexpected missing destinations fail the audit.
CI reproduces the selected files from the full pinned source catalog.

## Elevation and remaining gaps

126 retained maps omit their elevation grids with an explicit `elevation_omitted`
reason recorded in `source`: every relevant walkable cell uses the loader's
default ground level (3). The other 14 keep their grids (bridges with level `f`
or `4`, stairs, or multi-level terrain like Route 12, Safari Zone, Victory Road,
Silph 8F/9F, etc.). A flat-looking room is not enough to erase these semantics.
Regression tests cover these distinctions, flat water, unreachable/counter tiles,
and irrelevant wall heights. Elevation omission is derived from source data rather
than a manually maintained map-name list; no new lossy omission was added.

All 140 maps pass geometry/schema checks. Included fixed destinations resolve;
excluded destinations remain explicit boundaries. Current unresolved support:

| Gap | Count |
|---|---:|
| Cells with unsupported non-collision behavior | 0 |
| Dynamic warp destinations | 0 |
| Pickups without a pinned identity catalog entry | 84 |
| Identified fixed pickups | 22 |
| Known late-story geometry patch left unapplied | 1 |

All metatile behaviors encountered in the 140 candidate maps are resolved into
canonical glyphs. Full metadata and glyph specifications are documented in
[../tile-legend.json](../tile-legend.json):
- Forced spin mazes (`u, d, l, r` for `MB_SPIN_*` and `o` for `MB_STOP_SPINNING`) in Rocket Hideout and Viridian Gym.
- Floor pit holes (`H` for `MB_FALL_WARP`) with `step_on` entry in Pokémon Mansion and Victory Road.
- Boulder pressure switches (`B` for `MB_STRENGTH_BUTTON`) in Victory Road.
- Step-on teleport pads (`MB_REGULAR_WARP`) in Saffron Gym and Silph Co are mapped to floor with `step_on` entry.
- Sand, cave sand, mountain top and ice cosmetic floors (`MB_SAND`, `MB_SAND_CAVE`, `MB_MOUNTAIN_TOP`, `MB_ICE`) map to walkable open floor (`.` or cave encounter `~`).

Dynamic warps preserve source tokens rather than inventing a fixed destination.
NPCs and pickups retain source event, script and optional local-ID provenance;
`source_event` is a zero-based source array index, not an in-game object ID. Unidentified pickups remain unresolved.

Vermilion Gym retains its decomp baseline instead of the legacy builder's
late-story OPENED_TILES patch. Scripted geometry, flags, hidden/background
interactions, coordinate triggers and game-version differences still require
review. Structural validity does not establish story traversability.

## Promotion gate

Complete movement/stateful-geometry and source identity audits, review against
the corrected runtime pack, then publish an approved resource revision through
the normal manifest and consumer-pin process. Do not substitute this candidate
for corrected runtime resources merely to make a route pass.

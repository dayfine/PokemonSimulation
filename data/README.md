# Reference data

- `games/bdsp/maps/`: maps derived from pret/pokediamond with explicit console
  checks and corrections in their metadata.
- `games/bdsp/wall_hits.json`: measured walks used to validate the BDSP maps.
- `games/frlg/battles/`: four benchmark cases and a pinned pret trainer/AI snapshot.
- `games/frlg/routes/`: route fixtures for the FRLG planner.
- `measurements/`: raw console measurements for future model fitting.
- `runs/pokeguy-leafgreen-15934/`: full-run battle ledger, video-note evidence,
  and pinned pret trainer/species EXP data. See the
  [EXP audit](../docs/progression/README.md).

Game-specific Python rules and loaders live in `src/pokesim/games/`.
Upstream decomp checkouts belong in `external/` and are not committed.
Map files retain the `pokenav-map/1` format identifier for compatibility.

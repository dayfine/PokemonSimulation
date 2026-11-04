# Roadmap

PokemonSimulation is expanding from navigation into offline simulation and
planning for Pokémon automation. This refactor establishes naming and layout;
the integrations below are future work.

## Existing foundation

- Tile geometry, map schemas, text grids, and rendering.
- Movement rules, elevation, connected maps, warps, and NPC obstacles.
- Shortest paths, movement legs, belief planning, scoring, and localization.
- Movement uncertainty models.
- Map imports from local pret/pokefirered, pret/pokediamond, and
  pret/pokeplatinum checkouts.
- BDSP reference maps and console measurements; FRLG route fixtures.

The navigation design started in
[issue #7](https://github.com/dayfine/PokemonSimulation/issues/7).
Details of the existing models live in [navigation/](navigation/).

## Battle simulation

Choose a public battle simulation library and build a Python interface for
our first workload. Evaluate generation support, trainer AI, items, state
representation, reproducibility, and how closely it models FireRed battles.
Reuse an existing engine rather than growing another mechanics implementation.
No engine or runtime dependency has been selected yet.

## pret map data

Use pret decompilations as upstream map data sources, building on the existing
importers in `pokesim.decomp`. Keep local source checkouts in `external/`,
record revisions in derived data, and keep console corrections explicit.
Broader map coverage and reproducible source setup are follow-up work.

## Offload AutoStory work

Review [Arduino-Source PR #213](https://github.com/dayfine/Arduino-Source/pull/213)
workload by workload. Candidates include its map and battle-data generators,
battle simulations and win-chance estimates, and route or strategy evaluation.
For each project, define the input state, the offline result, and how the
console program consumes it before moving code.

## Movement simulation and measurements

Extend the existing movement and uncertainty models into repeated route
simulations. Capture console traces and fit physics parameters from raw
measurements in `data/measurements/`. Validate predictions against console
runs and, where useful, an emulator.

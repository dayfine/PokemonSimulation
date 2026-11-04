# Roadmap

PokemonSimulation is expanding from navigation into offline simulation and
planning for Pokémon automation. The first battle benchmark milestone is
implemented; broader integrations remain future work.

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

The [first milestone](battles/README.md) runs Misty, the Cerulean rival,
the S.S. Anne rival, and Lt. Surge. Python owns policies and repeated seeded
trials; a pinned local Showdown adapter owns Gen 3 mechanics, with Smogon's
calculator for decision previews. The imported pret trainer parties and
scoring scripts are revision-stamped.

Reports include confidence intervals, item consumption, conditions at loss,
and example traces. This is an approximation of FRLG trainer behavior:
AI damage helpers differ from pret, voluntary switching is omitted, and
some source-fixture stats are assumed. Validate against console runs before
using these estimates as a readiness gate. Next work depends on the outcome
of that validation; do not expand to other games yet.

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

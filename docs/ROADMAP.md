# Roadmap

The active cross-game migration is tracked in the
[AutoStory offline integration plan](autostory-plan.md), starting with map
ownership. The [imported map packs](maps/runtime-maps.md) contain the current
FRLG and BDSP AutoStory maps and generators.

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

The [full trainer benchmark](battles/pokeguy-benchmark.md) now runs all 69
trainer fights in Pokeguy’s reviewed route, using recorded entry states, live
progression, setup-item actions, and adaptive sampling. The original
[four-case milestone](battles/README.md) remains a separate experiment. Python owns policies and repeated seeded
trials; a pinned local Showdown adapter owns Gen 3 mechanics, with Smogon's
calculator for decision previews. The imported pret trainer parties and
scoring scripts are revision-stamped.

Reports include confidence intervals, item consumption, conditions at loss,
and example traces. This is an approximation of FRLG trainer behavior:
AI damage helpers differ from pret, voluntary switching is omitted, and
some source-fixture stats are assumed. Validate against console runs before
using these estimates as a readiness gate. Next work depends on the outcome
of that validation; do not expand to other games yet.

## Future team-composition comparison

Follow-up requested: repeat the battle-by-battle win-rate and player-action
complexity analysis for **Charmander/fire-starter** and **Bulbasaur/grass-starter**
teams with supporters. This is a recorded follow-up, not work started in the
current Squirtle analysis.

Reconstruct each team's route, EXP/EV allocation, levels/stats, moves/PP and bag
before comparing results. Include supporter roles and both deliberate and forced
switches, then compare attack-only, recovery and setup/team policies with adaptive
sampling. Do not reuse Squirtle's recorded entry states as another team's inputs.

## Route progression

The [Pokeguy LeafGreen audit](progression/README.md) now logs the complete
reviewed battle sequence and computes EXP after each opponent and battle.
It compares a flee-all-random-wild route with the documented wild-win control,
preserving Rare Candies and reporting every discrepant observation. The
state ledger also reconstructs EVs, raw stats, HP/status, PP and consumables.
Conditional trainer win rates now run through the battle benchmark. Wild and
capture/escape objectives, input sensitivity, better NPC parity, and a simulation
carrying random outcomes across the whole route remain future work.

## Battle resource logistics

Use [League PP requirements](battles/league-pp-requirements.md) as a resource
contract for a separate pickup/purchase/timing process. The recorded plan reserves
one Elixir between Lance and Champion. Derive extra PP reserves from chained
stochastic battle outcomes before treating that observed plan as sufficient for C.

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

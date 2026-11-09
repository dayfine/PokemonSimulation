# PokemonSimulation

Offline simulation, data preparation, and planning for Pokémon automation.
This repo is where we can evaluate routes and battle strategies in Python
before spending time on a console run.

The existing library covers maps, tile movement, routing under uncertainty,
and movement physics for FireRed / LeafGreen and Brilliant Diamond /
Shining Pearl. The battle benchmark runs all 69 trainer encounters in Pokeguy’s FRLG route
with Python policies, pret data, and a local Pokémon Showdown engine.
See [the full trainer benchmark](docs/battles/pokeguy-benchmark.md) for inputs, limitations,
and [the complete results table](docs/battles/pokeguy-trainers.md).
The [preparation comparisons](docs/battles/pokeguy-preparation.md) test healthier
entries, recovery supplies, Dig and Speed thresholds outside the speedrun.
The [single-file FRLG AutoStory handoff](docs/battles/pokeguy-conditions.md) contains
all 69 fights, both entry variants and rates, opponent teams, strategy rules and
openings, required healing stops, and League PP requirements for another agent/repo.
The [proposed replay interface](docs/battles/autostory-replay-interface.md) defines
AutoStory plans as producers of battle histories and this repo as their evaluator,
with configurable minimum-win-rate and reliability-quota criteria.

The [AutoStory integration plan](docs/autostory-plan.md) tracks map ownership,
route planning and shared FRLG/BDSP simulation. The [imported map packs](docs/maps/runtime-maps.md)
include 53 FRLG and 22 BDSP maps, portable generators, corrections, provenance
and a byte-identical export for Arduino consumers.
The [local runtime-map planner](docs/navigation/RUNTIME_ROUTES.md) now computes
and draws routes inside a pinned FRLG or BDSP map, recording its inputs and state.
The [shared story and simulation guide](docs/story/README.md) explains which
data and regression scenarios both repositories share, what their separate
implementations verify, and the next story-execution parity gate.

The [SV Snacksworth plan](docs/sv/snacksworth-plan.md) describes proposed team
preparation, capture policies, recovery, and validation for automating all 25
treat encounters in either version. Its [route research](docs/sv/snacksworth-routes.md)
covers helper acquisition and flight anchors; console routes are not yet validated.

The [C-strategy comparison](docs/battles/pokeguy-c-comparison.md) reruns only
the 12 setup fights and combines them with the retained baseline for a new
risk ranking.

The [full-route EXP audit](docs/progression/README.md) logs Pokeguy's LeafGreen
battles, calculates the starter's level after each one, and compares it with
the video notes, including a route that flees all random wild encounters.
See the [trainer route guide](docs/progression/pokeguy-route.md) for the full
trainer sequence grouped by segment and the level targets before major battles.
The [starting-state ledger](docs/progression/pokeguy-states.md) adds HP/status,
raw stats, PP, held items, badges, and tracked consumables for every encounter.

The console programs live in
[Arduino-Source](https://github.com/PokemonAutomation/Arduino-Source).
Its [FRLG AutoStory PR #213](https://github.com/dayfine/Arduino-Source/pull/213)
is the starting point for identifying work to run offline here, such as data
generation, battle evaluation, and route validation.

## Layout

| Path | Purpose |
|---|---|
| `src/pokesim/games/frlg/battle/` | Python battle policies, pret import, engine client, and benchmark reports. |
| `src/pokesim/games/frlg/progression/` | EXP/EV/stat models, move and inventory ledgers, and video-route audits. |
| `engines/frlg-showdown/` | FireRed/LeafGreen (Gen 3) adapter using pinned Showdown and Smogon packages. |
| `src/pokesim/grid/` | Map models, movement rules, rendering, and route planning. |
| `src/pokesim/physics/` | Movement uncertainty models. |
| `src/pokesim/decomp/` | pret map importers: FRLG (`frlg`) and Sinnoh (`landdata`, `events`, `repos`, `generate`). |
| `src/pokesim/games/` | Game-specific rules and data loaders. |
| `src/pokesim/cli/` | Commands for importing, converting, and rendering maps. |
| `src/pokesim/**/test_*.py` | Python tests and synthetic decomp fixtures, beside the modules they exercise. |
| `data/games/<game>/` | Reference maps, route fixtures, and game data. |
| `data/measurements/` | Raw console measurements for fitting models. |
| `data/runs/` | Timestamped battle ledgers and pinned progression reference data. |
| `external/` | Ignored local checkouts of upstream data sources. |
| `docs/navigation/` | Map, movement, physics, and routing documentation. |
| `docs/examples/` | Small example inputs. |

## Develop

Python modules use Python 3.8+ and the standard library. Battle simulation
also requires Node 22+ and the pinned npm packages; navigation works without
them. From the repository root:

```sh
PYTHONPATH=src python3 -m unittest discover -s src -t src
PYTHONPATH=src python3 -m unittest pokesim.test_package
PYTHONPATH=src python3 -m pokesim.cli.textgrid show docs/examples/tiny_town.json
```

GitHub Actions runs the tests on Python 3.8 and 3.12. All commands currently
run from a source checkout; keep `PYTHONPATH=src` when running tools.

Tests against a real pret/pokefirered checkout run when `POKEFIRERED_DIR`
points at it:

```sh
POKEFIRERED_DIR="$PWD/external/pokefirered" PYTHONPATH=src python3 -m unittest discover -s src -t src
```

Run the full trainer benchmark:

```sh
npm ci --omit=optional --prefix engines/frlg-showdown
PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles --out /tmp/pokeguy-battles.json
```

See [external/README.md](external/README.md) for source checkout conventions,
[data/README.md](data/README.md) for reference data, and
[docs/navigation/MAPS.md](docs/navigation/MAPS.md) for importer commands.

## Migration from PokemonNavigation

- Python imports and commands use `pokesim` instead of `pokenav`.
- `python/pokenav/` moved to `src/pokesim/`; Python tests now live beside their source modules.
- `games/` and `measurements/` moved under `data/`.
- The FRLG importer moved from `pokenav.grid.maps.pret` to `pokesim.decomp.frlg`.
- The saved map format remains `pokenav-map/1`, so existing JSON maps still load.

## Conventions

- Keep Python `test_*.py` files beside the modules they exercise; discovery starts at `src/`.
- Put FRLG-specific simulation under `pokesim.games.frlg`; CLI names include `frlg`.
- Start modules and classes with a comment explaining their purpose.
- Give meaningful numbers a name and record their source.
- Keep functions short and flat.
- Document command-line tools with example input/output; include runnable commands in their module docstrings.
- Record source repositories, revisions, and measurements alongside derived data.

See [docs/ROADMAP.md](docs/ROADMAP.md) for current capabilities and next work.

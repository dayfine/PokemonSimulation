# PokemonSimulation

Offline simulation, data preparation, and planning for Pokémon automation.
This repo is where we can evaluate routes and battle strategies in Python
before spending time on a console run.

The existing library covers maps, tile movement, routing under uncertainty,
and movement physics for FireRed / LeafGreen and Brilliant Diamond /
Shining Pearl. The first battle milestone runs four FRLG trainer encounters
with Python policies, pret data, and a local Pokémon Showdown engine.
See [the battle benchmark guide](docs/battles/README.md) for inputs, limitations,
and reproducible results.

The console programs live in
[Arduino-Source](https://github.com/PokemonAutomation/Arduino-Source).
Its [FRLG AutoStory PR #213](https://github.com/dayfine/Arduino-Source/pull/213)
is the starting point for identifying work to run offline here, such as data
generation, battle evaluation, and route validation.

## Layout

| Path | Purpose |
|---|---|
| `src/pokesim/battle/` | Python battle policies, pret import, engine client, and benchmark reports. |
| `engines/frlg-showdown/` | FireRed/LeafGreen (Gen 3) adapter using pinned Showdown and Smogon packages. |
| `src/pokesim/grid/` | Map models, movement rules, rendering, and route planning. |
| `src/pokesim/physics/` | Movement uncertainty models. |
| `src/pokesim/decomp/` | pret map importers: FRLG (`frlg`) and Sinnoh (`landdata`, `events`, `repos`, `generate`). |
| `src/pokesim/games/` | Game-specific rules and data loaders. |
| `src/pokesim/cli/` | Commands for importing, converting, and rendering maps. |
| `tests/` | Python unit tests and synthetic decomp fixtures. |
| `data/games/<game>/` | Reference maps, route fixtures, and game data. |
| `data/measurements/` | Raw console measurements for fitting models. |
| `external/` | Ignored local checkouts of upstream data sources. |
| `docs/navigation/` | Map, movement, physics, and routing documentation. |
| `docs/examples/` | Small example inputs. |

## Develop

Python modules use Python 3.8+ and the standard library. Battle simulation
also requires Node 22+ and the pinned npm packages; navigation works without
them. From the repository root:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -t .
PYTHONPATH=src python3 -m unittest tests.test_package
PYTHONPATH=src python3 -m pokesim.cli.textgrid show docs/examples/tiny_town.json
```

GitHub Actions runs the tests on Python 3.8 and 3.12. All commands currently
run from a source checkout; keep `PYTHONPATH=src` when running tools.

Tests against a real pret/pokefirered checkout run when `POKEFIRERED_DIR`
points at it:

```sh
POKEFIRERED_DIR="$PWD/external/pokefirered" PYTHONPATH=src python3 -m unittest discover -s tests -t .
```

Run the battle milestone:

```sh
npm ci --omit=optional --prefix engines/frlg-showdown
PYTHONPATH=src python3 -m pokesim.cli.battle --battles 1000 --out /tmp/frlg.json
```

See [external/README.md](external/README.md) for source checkout conventions,
[data/README.md](data/README.md) for reference data, and
[docs/navigation/MAPS.md](docs/navigation/MAPS.md) for importer commands.

## Migration from PokemonNavigation

- Python imports and commands use `pokesim` instead of `pokenav`.
- `python/pokenav/` moved to `src/pokesim/`; `python/tests/` moved to `tests/`.
- `games/` and `measurements/` moved under `data/`.
- The FRLG importer moved from `pokenav.grid.maps.pret` to `pokesim.decomp.frlg`.
- The saved map format remains `pokenav-map/1`, so existing JSON maps still load.

## Conventions

- Start modules and classes with a comment explaining their purpose.
- Give meaningful numbers a name and record their source.
- Keep functions short and flat.
- Document command-line tools with an example input, output, and command.
- Record source repositories, revisions, and measurements alongside derived data.

See [docs/ROADMAP.md](docs/ROADMAP.md) for current capabilities and next work.

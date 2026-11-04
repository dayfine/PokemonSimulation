# FireRed / LeafGreen (Gen 3) Showdown adapter

This directory contains PokemonSimulation's **FireRed / LeafGreen adapter**.
Pokémon Showdown and Smogon's calculator are general-purpose dependencies;
the code here selects Gen 3 mechanics and adds FRLG story-battle behavior,
including badge boosts, bag turns, measured stats, and accuracy previews.
It is not a shared adapter for arbitrary games or generations.

| File | Responsibility |
|---|---|
| `engine.cjs` | FRLG battle setup and bag actions; Showdown `gen3` turns and state export. |
| `progression.cjs` | Live FRLG solo knockout EXP/EV awards, level-up stats/HP, and move learning. |
| `damage.cjs` | Smogon generation 3 damage previews and pret FRLG accuracy-stage table. |
| `runner.cjs` | JSON-lines subprocess entry point for this FRLG adapter. |
| `test/*.test.cjs` | FRLG adapter mechanics and full-route feature checks. |

Run from the repository root:

```sh
npm ci --omit=optional --prefix engines/frlg-showdown
npm test --prefix engines/frlg-showdown
PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles --out /tmp/pokeguy-battles.json
```

The Python client is `src/pokesim/games/frlg/battle/engine.py`; the experiment inputs and
NPC AI snapshots are under `data/games/frlg/battles/` (old fixtures) and
`data/runs/pokeguy-leafgreen-15934/` (full trainer route). See the
[battle guide](../../docs/battles/README.md) and
[gap review](../../docs/battles/GAPS.md) for supported behavior and limits.

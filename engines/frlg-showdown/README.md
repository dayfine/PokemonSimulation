# FireRed / LeafGreen (Gen 3) Showdown adapter

This directory contains PokemonSimulation's **FireRed / LeafGreen adapter**.
Pokémon Showdown and Smogon's calculator are general-purpose dependencies;
the code here selects Gen 3 mechanics and adds FRLG story-battle behavior,
including badge boosts, bag turns, measured stats, and accuracy previews.
It is not a shared adapter for arbitrary games or generations.

| File | Responsibility |
|---|---|
| `engine.cjs` | FRLG battle setup and bag actions; Showdown `gen3` turns and state export. |
| `damage.cjs` | Smogon generation 3 damage previews and pret FRLG accuracy-stage table. |
| `runner.cjs` | JSON-lines subprocess entry point for this FRLG adapter. |
| `test/engine.test.cjs` | FRLG adapter mechanics checks. |

Run from the repository root:

```sh
npm ci --omit=optional --prefix engines/frlg-showdown
npm test --prefix engines/frlg-showdown
PYTHONPATH=src python3 -m pokesim.cli.battle --battles 1000 --out /tmp/frlg.json
```

The Python client is `src/pokesim/battle/engine.py`; the experiment inputs and
NPC AI snapshot are under `data/games/frlg/battles/`. See the
[battle guide](../../docs/battles/README.md) and
[gap review](../../docs/battles/GAPS.md) for supported behavior and limits.

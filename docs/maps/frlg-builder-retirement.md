# Removing FRLG's duplicate map builder

The remaining native dependency was `devtools/maps/frlg_battle_data.py`: it
imported the map builder's pinned `COMMIT` and `Decomp` reader. Its exporter now
lives here as `pokesim.games.frlg.battle_data_export`, using the existing FireRed
reader. The parser/export logic is unchanged; its five JSON outputs reproduced
the checked-in native BattleData byte-for-byte in the cached-source check.

```sh
PYTHONPATH=src python3 -m pokesim.games.frlg.battle_data_export \
  --out /path/to/Arduino-Source/SerialPrograms/Source/VideoGames/PokemonFRLG/Programs/AutoStory/BattleData \
  --check
```

Like the map builder, it uses FireRed source pin
`ce6406d8c2eaf46d543c8a2606de0c3cb1951982` and `~/.cache/pokefirered` by default.
Cache misses use the existing pinned fetch path. This is a code-ownership move,
not a new audit of the source facts or a change to battle rules. The native
battle runtime still consumes its existing five generated files.

The native owning branch can now replace the old battle exporter with a thin
CLI forwarder requiring `PYTHONPATH=<pinned-tools>/src`, remove `frlg_maps.py`,
and remove its duplicate Python tests. Those cases already live beside
`frlg_decomp_map_builder.py` here. Keep native decoder, route, transition,
recovery and story tests in Arduino.

The generic Sinnoh decomp CLI is still used by `devtools.maps`; its removal is
a separate migration. Do not delete it as incidental FRLG cleanup. Likewise,
resource/tool pins can move only to approved publishing revisions on main.
The map publication/resource preparation from #55–#57 is now on main; this
catch-up brings #58's exporter there after it was merged into the old stacked
branch. Native exporter pins must wait for this catch-up to land.

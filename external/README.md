# External source checkouts

Keep local upstream source checkouts here, such as `pokefirered`,
`pokediamond`, or `pokeplatinum` from pret. Their contents are ignored by Git;
the battle benchmark pins its pokefirered source revision in
`data/games/frlg/battles/pret.json`. See `docs/battles/README.md` to reproduce it.

The map importers accept a checkout path (`--repo` for the Sinnoh importer,
a positional path for the FRLG importer). Real-checkout tests use
`POKEFIRERED_DIR`; see the root README for the command. Checkouts elsewhere
on disk work too.

Record the upstream repository and revision when generating reference data.
Do not commit ROMs or entire upstream checkouts here.

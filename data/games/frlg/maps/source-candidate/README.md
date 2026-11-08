# Full FRLG source-map candidate

425 distinct maps generated from the complete `group_order` catalog at
`pret/pokefirered@ce6406d8c2eaf46d543c8a2606de0c3cb1951982`.
This includes optional, link and postgame maps. It is a FireRed source baseline;
LeafGreen-specific version conditions still need review for Pokeguy's plan.

These files are **unreviewed candidates**, separate from the 53 approved maps
in `../runtime`. They are not in the runtime manifest, are not exported to
native consumers and do not change approved resource hashes or pins.

## Reproduce and audit

Use an empty directory for a fresh generation; `--check` verifies an existing
candidate without rewriting it:

```sh
PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder \
  --all --item-identities --out /tmp/frlg-world-candidate
PYTHONPATH=src python3 -m pokesim.maps.frlg_decomp_map_builder \
  --all --item-identities --out data/games/frlg/maps/source-candidate --check
python3 -m pip install -r schemas/requirements.txt
PYTHONPATH=src python3 -m pokesim.maps.frlg_import_audit \
  data/games/frlg/maps/source-candidate --schema --out /tmp/frlg-import-audit.json
```

All 425 pass geometry/schema validation and fixed warp/connection destination
checks. The pinned generator reproduces every file. The audit currently finds:

| Unresolved or partial support | Count |
|---|---:|
| Cells with unsupported non-collision behavior | 6,038 |
| Dynamic warp destinations | 19 |
| Pickups without a pinned identity catalog entry | 145 |
| Identified fixed pickups | 30 |
| Known late-story geometry patch left unapplied | 1 |

121 maps have at least one recorded gap. `unresolved_tiles` groups coordinates
by source behavior, including spinning tiles, ice, currents, cycling-road pull
and fall/regular warps. They remain blocked unknown cells (` `), or blocked
water (`w`), rather than ordinary traversable floor. Water remains water even
when the source collision bits block walking; Surf/current/Waterfall execution
is not implemented by this import.

Dynamic warps have no invented fixed destination. Their source map/warp tokens
remain in `source_destination`, with `unresolved: dynamic_destination`.
NPCs and pickups keep source event/script/local-ID provenance. `source_event`
is the zero-based source-array index, not an in-game local object ID. Named
local-ID constants are preserved separately when the source supplies them.
Unidentified pickups retain an explicit unresolved description; they are not assigned guessed item names or
quantities. The schema allows unresolved pickup metadata while still rejecting
it alongside a claimed fixed item identity.

The candidate keeps Vermilion Gym's decomp baseline instead of automatically
applying the legacy builder's late-story OPENED_TILES patch. Other scripted
terrain changes, flags, hidden/background interactions and coordinate-trigger
execution still require a source/adapter audit. The generator does not simulate
map scripts. Structural validity is not proof of full story traversability.

## Promotion gate

Audit and model unsupported movement/stateful geometry, complete item/script
identity coverage, check game-version differences, then review changes against
the corrected runtime pack. Only an approved publisher revision may regenerate
the runtime manifest and move native resource pins. Do not substitute these
files wholesale for the corrected runtime pack merely to make a route pass.

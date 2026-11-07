# Preparing pinned map resources

This adds a resource destination to the existing consumer verifier/export
transaction. Embedded exports remain the default for existing consumers.
Resource packs live at `Packages/Resources/Pokemon/Maps/{frlg,bdsp}`; their
separate checked-in lock is `devtools/maps/map-resources.lock.json` with format
`pokesim-map-resource-lock/1`. The lock retains an immutable publishing revision
and manifest hash per game. No native lock or game loader is changed by this
preparation-tooling PR.

Each prepared game directory contains exactly its map JSON, `LICENSE.txt` from
the pinned repository revision, and `PROVENANCE.txt` with repository, game, pin
and map-byte hashes. Metadata uses a `.txt` suffix so existing native `*.json`
embedding cannot mistake it for a map. Clone the publishing repository outside
the deployed Resources directory; materialize only the selected pack here.

## Prepare a development checkout

After this tooling lands, clone a full publishing cache and leave it on the
approved tools revision. Record the immutable tools SHA in the consumer CI
configuration too; code/tool version and each game's data pin are distinct.

```sh
git clone https://github.com/dayfine/PokemonSimulation.git /path/to/pokesim
cd /path/to/pokesim
# Choose and review a full commit already reachable from origin/main.
PYTHONPATH=src python3 -m pokesim.maps.consumer_sync update --layout resources \
  --source . --consumer /path/to/Arduino-Source --game frlg \
  --revision FULL_APPROVED_PUBLISHING_SHA
```

Commit the resource lock in the native owning branch. Ignore generated pack
directories there during fork development; do not delete unrelated existing
Packages resources. An existing embedded lock is independent and is not migrated
or removed by this command. Review differences against the owning game's
embedded map snapshot before replacing its input.

On a fresh consumer checkout with that lock:

```sh
PYTHONPATH=src python3 -m pokesim.maps.consumer_sync prepare --layout resources \
  --source . --consumer /path/to/Arduino-Source
PYTHONPATH=src python3 -m pokesim.maps.consumer_sync check --layout resources \
  --source . --consumer /path/to/Arduino-Source --offline
```

`prepare` reads all pins from the resource lock and cannot select a new revision.
It validates every source before writing. Missing/empty game directories can be
materialized; partial, modified, extra or symlinked entries fail without being
repaired. Repeating preparation on intact packs is safe. `update` deliberately
repins selected games only after existing exports verify cleanly. Other game
pins remain unchanged. Both operations stage complete directories and retain the
existing rollback behavior for ordinary I/O failures.

Commands fetch publishing `origin/main` by default for approval checks. Explicit
`--offline` trusts that cached ref's freshness; it is suitable after a CI checkout
with full history. Neither mode accepts an unpublished draft as approved data.
There is no fallback to a mutable branch or a locally patched terrain file.

## CMake and CI integration

Native builds can include `integrations/arduino-source/resource-maps.cmake` from
the pinned tools checkout and call:

```cmake
pa_pokesim_map_directory(MAPS frlg "${ARDUINO_ROOT}" "${POKESIM_SOURCE_CACHE}")
```

The helper verifies the **whole resource lock**, then returns that game's
absolute prepared directory. It adds the lock and resource files as configure
dependencies. Missing/unapproved/drifted resources fail configure with a prepare
instruction. Configuration never clones, downloads, rewrites a lock or repairs
resources. Python 3.8+ is a build-time requirement for this verification, not a
live console dependency.

To preserve the current runtime while changing map ownership first, a native
owning branch can embed JSON from this returned directory with its existing
`pa_embed_text_files()` call. That helper currently requires a path relative to
`CMAKE_CURRENT_SOURCE_DIR`, so first use `file(RELATIVE_PATH ...)`. This changes
the embedding **input** to prepared resources; it is not runtime filesystem
loading. A later runtime loader must separately preserve packaging and failure
behavior. Alternatively, use the verified directory in an explicitly tested
resource loader. Never retain an implicit fallback to old source maps.

The integration action accepts `layout: resources` and `operation: prepare` for
a fresh consumer with an existing lock (`operation: check` verifies an intact
pack). Reference an immutable approved action SHA after merge. CI tests this
path with real approved map history and a CMake configure smoke project; unit
tests cover drift, partial exports, approval, independent pins, license/provenance,
symlinks and configure failure. This is resource-tool validation, not proof that
native story execution has adopted it.

## Native adoption gates

1. Merge the v2 reader (#114) through each relevant game chain before selecting
   a v2 data pin. Publishing #56 must land before normal v2 adoption.
2. Compare each game's current map snapshot against the chosen publishing pin.
   FRLG's inspected pack matched; BDSP retains the three
   [held differences](BDSP_RECONCILIATION.md). This tool does not resolve them.
3. Prepare/check resources in CI before CMake, replace the game's source-map
   input, and run its native map, route, transition, recovery and story tests
   from a checkout with the old map directory absent.
4. After those pass, remove tracked map copies and duplicate builders/parsers
   in their owning native PRs. The [FRLG dependency move](frlg-builder-retirement.md)
   makes its map-builder removal possible without breaking battle-data generation. Audit dependent CLI imports first. Resource
   preparation deliberately permits old source files during this test stage;
   it is not an authoring-retirement gate.
5. At upstream handoff, submit the required resource data through the agreed
   resource repository/package process. A standard upstream checkout must not
   depend on an undocumented private clone or a draft publishing pin.

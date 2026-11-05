# Arduino map consumer integration

The implementation lives in `pokesim.maps.consumer_sync` and
`pokesim.maps.consumer_source`. Python 3.8+ and Git suffice; no Python packages
or battle engine are needed. This folder supplies the CI action and workflow
template. Installing it in the owning Arduino branches is still pending;
the template is not an active Arduino workflow.

## Run the tooling

From a PokemonSimulation checkout with these modules, set `PYTHONPATH=src`.
`--source` names a Git checkout of `dayfine/PokemonSimulation`; Git object reads
use the selected commit, never uncommitted source files. `--consumer` names an
Arduino checkout or an empty directory for a trial export.

```sh
# Read-only preflight before adopting a pin; select a full publishing SHA.
PYTHONPATH=src python3 -m pokesim.maps.consumer_sync compare \
  --source . --consumer /path/to/Arduino-Source \
  --game bdsp --revision FULL_PUBLISHING_COMMIT

# Initialize matching/empty exports, or advance previously clean locked packs.
PYTHONPATH=src python3 -m pokesim.maps.consumer_sync update \
  --source . --consumer /path/to/Arduino-Source \
  --game bdsp --revision FULL_PUBLISHING_COMMIT

# Check every locked game, without changing consumer files.
PYTHONPATH=src python3 -m pokesim.maps.consumer_sync check \
  --source . --consumer /path/to/Arduino-Source
```

Repeat `--game` to initialize both FRLG and BDSP together. All existing map
directories must be locked; removing a game from the lock does not exempt its
maps. Games can subsequently advance independently.

The default command refreshes source `origin/main` before verifying ancestry.
`--offline` explicitly trusts the cached `origin/main` ref and objects; it
does not establish their freshness or authenticate a manually fabricated cache.
The origin URL is restricted to PokemonSimulation. Shallow caches cannot be
refreshed by this tool; use a full-history checkout. An unmerged publishing
commit, mutable revision, missing object or unsupported format fails.

`check` fails on altered bytes, missing/extra maps, symlinks, lock/manifest
inconsistency, unlocked game directories and retired authoring modules.
`compare` diagnoses a proposed pin without creating a lock or changing exports;
it is not a substitute for the CI `check` command.

`update` validates the published source and current exports first. It will
not overwrite a pending local correction, drop an unknown file, or delete a
duplicate generator. Initial adoption accepts only empty directories or
byte-identical copies. For an existing lock, current packs must pass integrity
before an update can replace them. Files are staged as complete game directories;
ordinary swap errors roll back, and the lock is replaced last. A process kill
during swaps can require recovery; integrity fails rather than reporting success
under an inconsistent lock. Restore exports from the previous locked revision
before retrying. Review and commit exports and lock together.

## Activate in the owning consumer branches

1. Review pending map differences in PokemonSimulation first. In particular,
   `compare` against the #40 publishing baseline flags #226's five modified
   BDSP maps; this implementation does not approve or import those corrections.
   Do not erase them to obtain a passing check.
2. Remove the duplicate authoring modules in their owning Arduino PRs, after
   migrating dependent tools/tests. For BDSP these are `bdsp_maps.py` and
   `decomp.py`; for FRLG, `frlg_maps.py`. The legacy `devtools/maps/__main__.py`
   imports `decomp` and exposes its CLI, so update that dependency before
   removing the parser. Keep unrelated drawing helpers and native readers.
3. Use `update` to create `devtools/maps/map-packs.lock.json` and the exact
   selected packs. Consumer destinations are fixed to the existing CMake map
   paths. No C++ reader, embedding or build-network change is necessary.
4. Add these narrow rules to the consumer's `.gitattributes` before checking
   out/exporting on Windows; verify the resulting bytes with `check`:

   ```gitattributes
   SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Maps/*.json text eol=lf
   SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/Maps/*.json text eol=lf
   ```

5. Copy `map-pack-integrity.yml.example` to
   `.github/workflows/map-pack-integrity.yml`, replacing
   `IMPLEMENTATION_COMMIT` with the full merged PokemonSimulation commit that
   contains this action. The workflow runs for drafts too. Default PR checkout
   checks the merge result; the action obtains full approved publishing history
   independently and compares it to the consumer lock.
6. Run native reader/story tests against the selected exports and configure
   `map-pack-integrity` as a required check on the actual merge target branches.
   Apply the same gate to owning map PRs and their stacked story branches;
   merely adding a check on fork main does not protect another stack's target.
   Record this ownership policy in the Arduino agents instructions. Do not
   claim enforcement until the workflow and required status are both active.

The action runs the verifier from the pinned action commit and reads map data
from the independently checked-out publishing repository. Consumer-local
manifests or builder output are never its reference. Builds still use vendored
JSON and need no network access.

## Validation of the implementation

Colocated tests use real temporary Git repositories and cover drift in terrain,
points, NPCs, triggers, patches and metadata; inventory changes; forged local
manifest/hash; unmerged/mutable pins; symlinks; retired generators; independent
game updates; and rollback on a failed second directory swap. Simulation CI
also exercises the composite action with a complete real published export and
confirms that a subsequent local edit is rejected.

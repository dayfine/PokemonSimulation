# Arduino map consumer integration

The [new migration plan](../../docs/maps/UNIFICATION_STEPS.md) stages compact
coordinate arrays and a move to pinned external Packages resources. Commands
below still target the existing embedded source-map directories; resource-path
adoption and native v2 reader support remain pending. The current snapshot
comparison is also recorded in that plan.

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

## Initial rollout revisions

The merged tooling is available at
`d139398d48ee831da540b901e6700c6ba5dbb32c` on PokemonSimulation main.
The workflow template pins this exact action revision. The initial data pin
can use the same commit, with manifest SHA-256
`d2ee1c66222eee741103149c3a6db245ee51115ad6e87a79f7a3fe6e7a7b0176`.
Generate the consumer lock with `update`; do not substitute PR #42's
intermediate merge commit for a publishing commit verified on main.

Read-only preflight against these specific Arduino revisions:

| Consumer snapshot | Export status | Remaining adoption work |
|---|---|---|
| FRLG #224, `51c0ce6128e5981da56b370a770874b96a1e129f` | All 53 maps byte-identical; no missing/extra maps. | Retire `devtools/maps/frlg_maps.py` in its owning PR, then lock/export and install the check. |
| BDSP #226, `398b8518ba7c6a74e7fd3bfc1116bdcba161dab5` | 22 maps present; five differ. | Review corrections here before adoption; retire `bdsp_maps.py` and dependent `decomp.py` authoring uses in the owning PRs. |

BDSP differences are `JubilifeCity.json`, `OreburghMine.json`,
`OreburghMineB1F.json`, `PlayerHouse1F.json`, and `Route201.json`.
These observations neither import nor approve those changes. Re-run `compare`
after a consumer branch advances; this table records snapshots, not a promise
that a later head still matches. The Arduino workflow, required-status settings
and duplicate-builder removal have not been applied by this handoff.

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
   `.github/workflows/map-pack-integrity.yml`. The template already pins the
   merged implementation; review any future action revision update separately
   from the map-data pin. The workflow runs for drafts too. Default PR checkout
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

## Shared navigation fixture adoption

See [navigation conformance](../../docs/navigation/CONFORMANCE.md) for the
versioned exact-pose pack, registered native adapters and
`pokesim.maps.conformance_sync update/check` commands. Its preview flag applies
only to candidate fixtures; it cannot approve pending map data. Promote to the
merged publisher SHA before normal adoption. A separate native `Navigation fixture pin` workflow is prepared on the local
conformance branches and verifies the approved #46 pin. Native publication/CI
is pending; this existing action remains map-only.

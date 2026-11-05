# Map changes and consumer updates

Status: check/update tooling and a reusable CI action are implemented; adoption
in Arduino and its required status settings remain pending. See the
[integration commands and rollout](../../integrations/arduino-source/README.md).
No changes from PR #226 are imported, and consumer migration is not complete.

PokemonSimulation is the authoring repository for map data, source parsers,
builders, schemas and corrections. Arduino-Source consumes a pinned export.
Console testing can discover a map problem; that evidence belongs with a map
change here, rather than a second independently maintained map there.

## Ownership boundary

| Change | Authoritative repository |
|---|---|
| Terrain, collision, warp tiles/destinations/entry modes, connected edges, elevation, crop/world origin | PokemonSimulation |
| NPC positions/movement assumptions, named points/regions, scene triggers, patches, map-state preconditions | PokemonSimulation |
| Decomp parser/build rules, recorded source inputs and map schema | PokemonSimulation |
| Route choice, controller actions/timing, screen detectors, game execution | Arduino-Source; offline planner migration is a later milestone |
| Native JSON reader/embedding and controller regression tests | Arduino-Source; reader semantics must match the published map contract |

A map edit must not be disguised as a route fix. Conversely, do not change
terrain to make a mistaken movement sequence pass. Name the coordinate frame
and starting story state before deciding whether the map, route or walker is
wrong. A successful simulation shows internal consistency, not proof that the
map matches the game; console observations and decomp evidence remain necessary.

## Distribution choice: pinned, vendored JSON

Keep generated JSON committed in Arduino's existing map directories initially.
This preserves its current CMake embedding and offline builds. Those files are
an export cache, not an authoring surface. Remove the duplicate map builders and
parsers when the consumer switches; retain only a small fetch/copy/check tool.
Audit dependent CLI wrappers before removing their decoder imports. Route
drawing/planning tools are a separate migration; do not delete all of
`devtools/maps` just because builders move.

Use one consumer lock file,
`devtools/maps/map-packs.lock.json`. Each selected game pins a full
PokemonSimulation commit, the manifest path and its SHA-256. The update command
writes this shape; this example uses placeholders rather than a real lock:

```json
{
  "format": "pokesim-map-lock/1",
  "repository": "dayfine/PokemonSimulation",
  "games": {
    "bdsp": {
      "revision": "<full 40-character PokemonSimulation commit>",
      "manifest_path": "data/maps/runtime-manifest.json",
      "manifest_sha256": "<SHA-256 of that manifest's exact bytes>"
    },
    "frlg": {
      "revision": "<full 40-character PokemonSimulation commit>",
      "manifest_path": "data/maps/runtime-manifest.json",
      "manifest_sha256": "<SHA-256 of that manifest's exact bytes>"
    }
  }
}
```

Games may advance independently. Pin PokemonSimulation's publishing commit,
not the manifest's `upstream_revision`: the latter records historical Arduino
import lineage. Keep consumer destination paths in the verifier's fixed game
configuration, rather than accepting arbitrary write paths from the lock.
The existing per-map SHA-256 values cover JSON bytes, including objects,
points, triggers, metadata and patches. No second aggregate hash is needed:
the pinned manifest authenticates the inventory and those file hashes.

## Consumer check

Run a required `map-pack-integrity` check on every Arduino PR, including drafts.
Check the merge result as well as the branch so a parent update cannot change
the pack underneath a green child. The check must:

1. Read the lock and reject unknown repositories, games, formats or mutable
   revisions such as `main`. Resolve the exact commit from PokemonSimulation.
   Normal mergeable consumer updates must pin a commit reachable from that
   repository's `main`; fail if the check cannot establish this.
2. Read the manifest from that commit's Git object, not from Arduino's local
   working tree. Compare its exact SHA-256 with the lock. Verify the runtime
   format is supported by the consumer.
3. For every map in each selected game, verify the published JSON against its
   manifest SHA-256, then compare the vendored JSON's bytes with it. Require
   exact inventory equality: no missing, extra or duplicate maps/names. Reject
   unsafe or unexpected manifest paths rather than following them blindly.
4. Reject the retired authoring generators/parsers reappearing in Arduino.
   Require review for changes to the verifier, its workflow or ownership rules.
5. Report per-file missing/extra/modified status and the pinned revision. A
   mismatch fails; it must never regenerate files, rewrite the lock, silently
   update hashes, or fall back to another revision.

Use UTF-8/LF export bytes, with narrow `.gitattributes` rules for the vendored
JSON directories so Windows checkout does not change the build inputs. Do not
normalize JSON or line endings inside the checker: formatting changes should
also require a fresh export. A semantic diff can explain a failure to reviewers,
but is not the acceptance criterion.

Builds use the checked-in JSON and do not fetch the network. CI obtains its
reference from the pinned repository; an offline developer check may use a
previously verified checkout/cache of that exact commit. A cache miss is an
explicit failure, not permission to trust the local copies.

Hash checks detect drift; they do not prove a map is correct or enforce review
by themselves. Configure the check as required in branch protection and assign
maintainer review for map-lock/checker changes. Verify those hosting settings during rollout; adding a workflow alone does
not block a merge.

## Correcting a map

1. The console/AutoStory agent records the failure, map/pack revision, coordinate
   frame, story flags, intended movement, observed stop/transition and evidence
   (run/date/trace or capture). It identifies a proposed map discrepancy or an
   unresolved hypothesis; it does not directly fix the vendored map.
2. Open the correction in PokemonSimulation. Fix the source parser when decoding
   is wrong; otherwise add an evidenced game-specific correction or explicit
   scenario overlay/precondition. Keep decomp baseline, BDSP differences and
   uncertain observations distinguishable. Named anchors and generator door
   tables are map changes too.
3. Add a focused regression against the observed behavior, regenerate affected
   output and review the semantic diff. Test bounds, warp/point links and the
   effects on affected routes; retain native controller tests in Arduino.
4. Regenerate the manifest's hashes **here**, together with the corresponding
   source/correction metadata. Generator output parity must pass; updating a
   checksum alone is not an acceptable correction.
5. Merge the map PR here. Run the consumer's explicit update tool with that
   immutable revision. It verifies the published manifest, copies the complete
   selected game pack and writes the lock together. It must not preserve local
   edits or choose different files from different revisions of one game pack.
6. The Arduino PR contains the lock/export bump and any dependent route/walker
   changes, with a link to the map PR. Run integrity plus native reader and
   affected story tests. The map correction remains authored and reviewed here.

Cross-repo candidate testing can use a separate, clearly experimental workflow
with an explicit unmerged source commit. It cannot satisfy the normal required
check or become the default pack. Merge the map correction first, then update
the consumer lock. Do not introduce a generic CI bypass or a quiet local overlay.

The eventual replay/simulation history should carry the publishing commit and
manifest hash used by the game plan. Reports must use the same pack, rather
than evaluating against whichever maps happen to be latest.

## What #226 illustrates

Inspected [Arduino PR #226](https://github.com/dayfine/Arduino-Source/pull/226)
at `e572a3036fb270f4cc0fbd6b66442872b0c0bd1a`, relative to its stated base
`df6b1e47472f2448861eb72f4c432ead1d7c408c`:

| File | Semantic change requiring map ownership |
|---|---|
| `JubilifeCity.json` | Objects and named points. |
| `OreburghMine.json` | Terrain rows 9–12, plus formatting changes. |
| `OreburghMineB1F.json` | Warp/door glyphs on row 21. |
| `PlayerHouse1F.json` | Scene trigger location and evidence. |
| `Route201.json` | Console correction patches. |
| `devtools/maps/bdsp_maps.py` | B1F door interpretation table. |

These are candidates to review here, not findings that this document accepts
as correct. In particular, a raw terrain edit must have a corresponding
generator/correction change and evidence. The required consumer check would
reject all five edited JSON files under the old pin, even if Arduino's local
simulations passed. Changing the local lock hash alone would still fail against
the manifest fetched from the pinned source. None of these changes is imported
by this implementation.

## Rollout and remaining milestone 1 work

1. Implemented: source audit in CI, pinned lock/check/update commands,
   consumer CI action and regression tests. Reproducible source generation in
   CI and consumer adoption remain pending.
2. Archive the exact BDSP source inputs used for current output with their file
   hashes. Recover pret commits where possible; if not recoverable, label the
   snapshot's original commit unresolved and pin its archived bytes. Do not
   replace unknown history with a guessed current pret revision. Run generation
   against these fixed inputs, without a mutable global cache.
3. Resolve the initial consumer baseline against active branches, including
   reviewing #226-style differences in separate map PRs. A new integrity gate
   must start from an intentional baseline, not silently discard pending fixes.
4. In the owning Arduino PRs, add locks/update/check tooling and required CI,
   align CMake inputs with the export, remove authoring duplicates and update
   agent instructions to point here. Preserve native parser/controller tests.
   Add checker cases for changed terrain/points/triggers, extra/missing files,
   a changed local manifest/hash, wrong revision and a valid complete update.
5. Move the old eight reference fixtures into an explicitly separate reference
   namespace after frame/parity checks; carry their measurements with them.
   Do not overwrite them with runtime crops or let consumer exports include them.

Only then mark map ownership complete. The core tooling implements the process
decision; source-input pinning and Arduino adoption above remain open.

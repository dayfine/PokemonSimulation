# Map and story-data unification: small steps

The two repos should consume one map dataset and one serialized action/story
plan, while retaining game-specific execution. This document supersedes the
initial vendored-map distribution choice in `consumer-process.md`: the desired
end state is pinned external map resources during fork development, with any
upstream resource submission handled explicitly at handoff.

## Current evidence

November 7 update: FRLG resource handoff #238 merged into its AutoStory chain.
All 22 BDSP maps at #226 `fc56a720b9c0b1f4d945dbef382d61b0a6382b97` match
Simulation `f12af546d98f453e005c3116442423dcbdcda347` byte-for-byte. The held
terrain/NPC differences below are resolved by consumer alignment, not new map
corrections. The BDSP pack now publishes the 15 resolved pickup identities;
consumer resource adoption must select the approved publishing revision after
merge. [Current reconciliation](BDSP_RECONCILIATION.md).

The older snapshots below are retained as historical evidence.


Compared against PokemonSimulation `b49fe94` using immutable Git blobs:

| Game / Arduino head | Inventory | Byte-identical | Outstanding content |
|---|---|---|---|
| FRLG #224, `4f40579b61dd6558a0da410cccef106e06733483` | 53 / 53 | 53 | None at this snapshot. |
| BDSP #226, `01e6659116f520b51c35ee956aa6a222dfa864f8` | 22 / 22 | 17 | Five maps, listed below. |

| BDSP map | Actual differing fields |
|---|---|
| JubilifeCity | `npcs` (legacy `objects`), `points` |
| OreburghMine | `tiles`, rows 9–12 (zero-based) |
| OreburghMineB1F | `tiles`, row 21 |
| PlayerHouse1F | `coord_events` |
| Route201 | `patches` |

This table records the initial audit. The [subsequent review](BDSP_RECONCILIATION.md)
adopts two changes and retains three explicit evidence gaps.

Formatting alone explains none of these five differences. The comparison does
not approve either version's terrain, NPC assumptions or triggers. Bring the
correction and its decomp/console evidence here for review; do not overwrite
pending native corrections to make a hash check green.

Reproduce without checking out or changing either Arduino branch:

```sh
PYTHONPATH=src python3 -m pokesim.maps.map_parity \
  --arduino-source /path/to/Arduino-Source --game bdsp \
  --revision 01e6659116f520b51c35ee956aa6a222dfa864f8
PYTHONPATH=src python3 -m pokesim.maps.map_parity \
  --arduino-source /path/to/Arduino-Source --game frlg \
  --revision 4f40579b61dd6558a0da410cccef106e06733483
```

`format-only` means decoded map values match, including coordinate conversion;
it is a diagnostic, not a substitute for byte/hash integrity acceptance.

## 1. Compact coordinates, then activate the schema

- [x] Stage the versioned `pokesim-runtime-map/2` codec and readable formatter.
  Validate both representations; normalize for existing Python routing/recovery.
  Round-trip all 75 checked-in maps without altering any geometry or extension.
- [x] Keep short NPC/warp/patch records on one line; coordinate pairs remain
  inline where they fit. Preserve zero/false and all unknown extensions.
- [x] Add v2 reading to the shared native `Pokemon_MapData` owner, with native
  cases for coordinates, inclusive wander bounds, malformed/mixed versions and
  v1 compatibility. Merge that prerequisite into both story chains.
- [x] Review the five BDSP data differences here with recorded evidence.
  [Reconciliation decisions](BDSP_RECONCILIATION.md): adopt two; hold Route 201, the mine
  corridor and president edits pending anchored BDSP evidence. Parity improves
  to 19/22 against the same #226 snapshot; native adoption remains pending.
- [x] Convert all published maps and generator output together; bump the
  manifest's runtime format, update checksums and consumer format capability.
  Re-run every map audit, native reader test, route golden and recovery replay.

Wire representation:

```json
{
  "format": "pokesim-runtime-map/2",
  "points": {"roark": [18, 28]},
  "npcs": [
    {"name": "roark", "coord": [18, 28], "facing": "east"},
    {"name": "machop_8", "coord": [12, 28], "wander": {"min": [11, 28], "max": [13, 28]}}
  ],
  "items": [{"coord": [4, 28], "source_event": 3, "item": "escape_rope"}]
}
```

The fragment illustrates formatting, not a complete valid map. V2 replaces
`objects` with `npcs`, `items`, `signs` and non-item `interactables`; the section carries the kind, so each
record omits `kind`. Empty sections are omitted. Records remain arrays because
names are not unique in existing FRLG maps. Preserve record order within each
kind; cross-kind interleaving is not part of the v2 contract. Native migration
must validate that grouping does not alter routing, interaction or trainer
behavior. The Python tests check real-map occupancy and trainer hazards.

`coord` replaces
`x`/`y` for NPCs/items/signs, warps, terrain patches and coordinate events. Wander `min`
and `max` replace `x0`/`y0` and `x1`/`y1` with the same inclusive bounds. Named
points/regions already use pairs. Trigger `width`/`length` are extents, not tile
coordinates, and remain named dimensions. Decomp source coordinates and
provenance/generation overrides retain their source representation; this is a
runtime wire-format change, not a rewrite of pret data or Python Tile objects.

Preview a complete map now:

```sh
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_format \
  --input data/games/bdsp/maps/runtime/OreburghMine.json \
  --out /tmp/OreburghMine.coord.json
```

The [published pack now uses v2](V2_PUBLICATION.md); both generators and the
consumer verifier support it. The formatter refuses in-place overwrites.
Existing consumer pins/exports remain unchanged: native chains must first pick
up the #114 reader, then explicitly adopt an approved publishing revision.

### Native decoder preparation after #53

The native decoder is now folded into [Arduino nav-core #114](https://github.com/dayfine/Arduino-Source/pull/114),
`nav/shared` commit `bd9a6669dda2b92884fa377fb402f03d466c4a20` (native CI pending).
`Pokemon_RuntimeMap.{h,cpp}` supplies wire normalization inside the existing
`parse_map()` API, so both games gain v1/v2 support by merging nav-core. No loader
call-site changes or separate native decoder PR are needed.

Local evidence: 26 new native schema cases and all eight existing MapData cases
pass, including legacy diagnostics, embedded test maps, mixed-version
rejection, coordinate bounds, inclusive wander boxes and full metadata retention.
A GUI-free native target also compares 150 complete records from immutable
Simulation `40717c7c809c415c751fd7a348dfc1895f7ec3d7`: all 75 maps, both plain
and with staged pickup/interaction enrichment. Expected normalized JSON comes
from that pinned Python codec; comparisons and production parsing run in C++.
This establishes decoder parity, not matching route choices or live execution.

The remaining sequence is:

1. Finish #114 CI, propagate `nav/shared` through the FRLG/BDSP story chains,
   and run native route/story/recovery tests before activating v2. The original
   `parse_map()` entry point now performs versioned normalization automatically.
2. Reconcile the five BDSP content differences against current immutable heads
   and their evidence here. Publish one reviewed normalized pack, then prepare
   pinned external Resources and remove native authoring/copies after adoption.
3. Export complete story-event checkpoints for BDSP mine/Roark and FRLG Parcel
   as shared data, including actions and entering conditions, rather than only
   movement routes. Use the existing native story engine and per-game executors.

No published maps, native consumer pins, terrain corrections or captured replay
facts were changed by this checkpoint. The initial separate-branch push hit inherited hook findings. Folding the
change into #114 used the correct existing PR base, passed code health and
pushed normally, without a hook bypass.

## 2. Enforce parity, rather than maintaining copies

- [ ] Record one immutable PokemonSimulation commit plus manifest SHA-256 per
  game in Arduino's resource lock, preserving independent FRLG/BDSP pins.
- [ ] Require complete inventory/byte/hash checks against that publishing commit,
  including draft PRs and merge results. A missing map, unexpected file, local
  patch or unsupported schema fails without fetching a mutable fallback.
- [ ] Route all map corrections through PokemonSimulation; new console evidence
  may originate in Arduino, but its accepted data change and provenance live here.

The existing `consumer_sync` implementation already provides the pinned/vendored
integrity mechanism. Its destination paths are fixed to embedded source maps;
the [resource layout and preparation protocol](resource-packs.md) now extend
and test that boundary without repinning or changing native loaders.

## 3. External map resources in the native story chains

Proposed destination: `Packages/Resources/Pokemon/Maps/{frlg,bdsp}` (not yet wired
into native builds). Clone PokemonSimulation into an external source cache,
checkout/verify the locked publishing SHA, and materialize only its selected map
pack into Resources. Do not clone the entire simulation repo into the deployed
Resources tree. Preserve license/provenance and ship only the needed data.

- [x] Add resource prepare/check commands, clone/pin instructions and the tested
  CMake fail-closed helper; [details](resource-packs.md). Simulation CI exercises
  locked preparation and configure.
- [ ] Adopt that preparation/helper in the owning native game builds and CI.
- [ ] Replace the CMake source-directory embedding inputs. At #226's inspected
  head, `EmbedTextFiles.cmake` and `pa_embed_text_files(...AutoStory/Maps...)`
  still compile source JSON into the app; changing README alone cannot remove it.
- [ ] Update resource-path loading/packaging, and prove fresh-checkout native map,
  story, route and recovery tests work using only the prepared resources.
- [ ] Then remove tracked map copies and duplicate Python builders/decomp parsers
  from their owning native PRs, propagating those changes through the chains.
- [ ] Upstream handoff: explicitly submit any needed data to the appropriate
  resource repository/packaging path; ensure a normal upstream checkout builds
  and tests. Do not merge an upstream PR requiring an undocumented private clone.

**Keep one shared native runtime JSON decoder** in navigation. It converts
resource data to `MapData`; both games need that reader. What leaves AutoStory
is duplicated map authoring/decomp parsing and embedded map copies, not the
ability of the executable to load map resources. Controller/detector tests stay
native. Network and Python never enter the live console execution path.

### FRLG resource handoff checkpoint (2026-11-06)

[Arduino #238](https://github.com/dayfine/Arduino-Source/pull/238) now prepares
53 FRLG maps from published Simulation main
`906956e94fc912ae9adb0e44845da780f3bc7e4c`, manifest
`856e07a265da0b273172a7aa97a2aa335c90ea0a39162d50912b55fb60a86bc7`.
It removes the native map copies and duplicate FRLG builder, while retaining
native parsing, planning and controller execution. CMake embeds the verified
Resources JSON through the existing API; this is not a runtime filesystem-loader
migration. The battle-data forwarder reproduces all five native outputs.

All 53 maps match the old v1 content after canonical v2 conversion: coordinates,
typed grouping and omitted empty sections change; geometry, metadata, triggers
and order within each kind do not. Native decoder parity covers 150 complete
plain/enriched records from this publishing pin. Its fixture tool normalizes
v2 before enrichment and requires a clean checkout of an immutable supplied SHA.
The default historical v1 fixture pin remains supported.

This remains a **prepared fork handoff**, not adoption across the entire native
chain or an upstream resource submission. #238 includes nav-core #114 directly.
Linux/Windows schema and parity checks passed at `f3b7d5836`; full native
build/test validation and macOS checks are tracked in #238. Missing image
fixtures do not justify calling the full suite green. Test-only GCC portability
fixes live in their owning #222/#224 branches and are merged into the handoff.

BDSP stays on its existing source maps until the three held differences in
[the reconciliation](BDSP_RECONCILIATION.md) are resolved against anchored
evidence. Do not import the old #226 terrain edits merely to get parity.

After reviewing/landing the resource handoff, implement the evaluated native
checkpoint exports below. [PLZA's guide-authored example](../story/PLZA_OPENING_DRAFT.md)
is now available on Simulation main via #62; it remains a design probe without
map/executor/battle bindings, not a native-export prerequisite.

## 4. Actions/story events as shared data

[Early format draft and complete authored-row examples](../story/STORY_PLAN_DRAFT.md)
compare FRLG Parcel and BDSP mine/Roark without claiming native export or replay.
The native exporter and execution bindings below remain pending.

The [execution and FRLG coverage plan](../story/EXECUTION_PLAN.md) records the
next milestones after the first checkpoint parity tests: shared native execution
of the serialized events, explicit RNG-program handoff/resume, and a full FRLG
main-story draft in the readable style used for PLZA. Authored, bound and
replay-validated coverage remain separate milestones.

This means the **action/story-event sequence**, not just paths or generated walk
legs. Both current chains already use shared `StoryStep`, `StoryCheckpoint` and
`StoryStepExecutor` types (`Pokemon_StorySteps.h`); their tables are constructed
in C++. Start by serializing that existing contract, rather than designing a
second engine or scraping C++ with Python.

- [ ] Specify `pokesim-story-plan/1`: game/version, plan revision, map/schema/data
  pins, checkpoint IDs/start beliefs, ordered event IDs, requirements, actions,
  expectations, skip conditions, interrupt policy and bounded recovery.
- [ ] Export actual evaluated native tables through an offline C++ entry point
  or native test. Encode polymorphic `Pose.where` as a tagged pose (e.g. tile set,
  row/column belief or unknown), retaining facing and coordinate-frame identity.
  Convert executor callbacks/variants into symbolic action/condition references;
  do not serialize function addresses or infer successful observations.
- [ ] First fixtures: BDSP `01.03` mine/Roark and FRLG `00.05` Oak's Parcel.
  Export all events for each selected checkpoint, not only its route events.
  Compare exported/imported records with the native table before replacing it.
- [ ] Add JSON decoding/binding to the existing native executors and a Python
  replay adapter. Common actions retain kinds such as `route`, `step`, `talk`,
  `answer`, `battle`, `train`, `heal`, `shop`, `save` and `ready`. Game actions use
  an explicit game/action tag plus a versioned payload. Unknown kinds, conditions
  or payload versions fail as unsupported, rather than being skipped.
- [ ] Move those checkpoints' authored tables to JSON once round-trip/native
  parity is proven. Then expand checkpoint by checkpoint and remove their C++
  authoring tables. Arduino owns plan authoring and live execution;
  PokemonSimulation consumes the same pinned event data and owns offline replay.
- [ ] Replay emits planned movement, uncertain transitions/recovery and battle
  histories. A battle history needs party/stats/HP/PP/status, inventory, level,
  EXP/EV, moves, strategy and trainer/ruleset pins. Missing state is an explicit
  unmet input, never an invented full-health/default-bag assumption or win rate.

A `route` event contains a movement goal/preconditions; routing derives its walk
legs. A `legs` event may intentionally preserve fixed movements, with its own
preconditions and recovery. Neither replaces interactions, purchases, trainer
battles, starter selection or other game-specific story actions. Preserve
`assumed` versus observed scene arrivals from the native tables.

Acceptance: feed the **same serialized checkpoint** into the native scripted
executor and Python replay; compare ordered actions, pre/post-state, interruptions
and failure/recovery results on a shared scenario, then separately validate real
controller/detector behavior in Arduino. A Python route candidate alone is not
proof of native story execution or battle readiness.

## Item identities — implemented as staged enrichment

[Pickup identity implementation and commands](item-identities.md) now cover all
48 existing item-ball records: 45 fixed pickups and three starter-choice
interactions. Both builders retain source event metadata and optionally enrich
it. V2 previews use real item identifiers/quantities; Oak's balls go into
`interactables`, not `items`. Source scripts/IDs and collection flags are retained
in a pinned catalog with compact per-record references.

Published map bytes now use v2; historical native replay pins remain unchanged.
Unknown/conditional rewards remain unresolved, and Diamond/Platinum identities
are labeled as BDSP baselines rather than claimed BDSP verification. CI checks
reproduction against the 28 pinned source inputs. The map/resource/story-event
resource/story-event migration above is still pending.

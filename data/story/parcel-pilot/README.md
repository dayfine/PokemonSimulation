# FRLG Parcel load-and-replay pilot

This Python diagnostic loads the actual evaluated `00.05` native capture,
binds its route/step/scene events to explicit offline capabilities, and produces
an evidence-labeled trace. It uses five approved runtime maps with exact hashes;
it does not use the unreviewed full-world candidate maps.

```sh
PYTHONPATH=src python3 -m pokesim.story.parcel_replay \
  data/story/parcel-pilot/cases.json --case complete --summary \
  --out /tmp/parcel-trace.json
PYTHONPATH=src python3 -m unittest pokesim.story.test_parcel_replay
```

The readable summary is:

```text
00.05: model_complete (offline diagnostic; native parity not established)
below_mart_door -> ViridianCity [36, 20] north, elevation 3 [model-prediction]
mart_door -> ViridianCity_Mart [4, 7] north, elevation 3 [model-prediction]
parcel_from_clerk -> ViridianCity_Mart [4, 3] west, elevation 3 [scripted-observation]
Save: never; retry: none (synthetic policy).
```

`binding.json` pins the capture bytes/source revision, approved map bytes/revision,
registered capabilities and Python route costs. Capture and map hash drift,
unknown bindings, unsupported policies and malformed inputs fail. Execution
uses local data only. Structural schemas accompany the semantic readers.

`cases.json` is one input/expectation table. Every entry/scene observation and
interruption is **synthetic**, even though the checkpoint and maps come from
real native/source data. It covers:

| Case | Expected outcome |
|---|---|
| `complete` | Three events complete, with a separately supplied Parcel receipt and scene pose. |
| `entry-not-overworld` | No actions; start pose alone is insufficient. |
| `missing-scene-evidence` | Stop; the authored `declared_after` cannot establish arrival or receipt. |
| `missing-parcel-receipt` | Stop despite the matching scene pose. |
| `wrong-scene-arrival` | Stop despite a Parcel receipt. |
| `unconfirmed-mart-transition` | Invalidate pose and stop before the clerk event. |
| `interrupted-route1-grass` | Stop with `(12,39)` / `(12,38)` as candidates, facing unknown; no nominal movement credit. |

The grass interruption is anchored to the north input from Route 1 `(12,39)`
into grass at `(12,38)` (press 26 for this Python profile). It is not tied to
a shared press ordinal: a changed route that misses the physical injection
point fails rather than silently skipping it. It is not a recorded console failure or a claim that these
are the only possible outcomes for every encounter. Recovery/rejoin is not
implemented in this pilot; the bounded safe policy is to stop. Existing lower
level [recovery tests](../../../docs/navigation/ENCOUNTER_RECOVERY.md) remain
separate until their observations can be bound here.

The full JSON trace retains all modeled presses (120 for this Python cost
profile), the final in-place facing adjustment, event boundaries and evidence
basis. `--summary` gives the small event-level view. A stopped run returns exit
status 1 and can still write its diagnostic report with `--out`.

## Explicit limits and native parity work

The offline policy is one attempt, no saving and stop on failure. These are
**chosen diagnostic settings**, not exported native run options. Native runtime
configuration and effective save/retry policy remain unbound in every report.
Native FRLG attaches an end-of-checkpoint save; this diagnostic does not model
or claim that save. No HP, party, bag or other bookkeeping defaults become
observed state. `received` contains only the scripted scene receipt, not a
reconstructed full inventory.

At capture revision `b170b7d2103e887ded825c37fdbdc19fd654fca8`:

- Native `build_story_checkpoint()` inserts a `from_save` initializer before
  the three authored events. Python instead checks the supplied scripted entry
  pose/screen; it does not execute that initializer or prove a save was loaded.
- Native `StoryExecutor::step()` uses `take_step()` to report a nominal same-map
  tile. Python's runtime map model instead resolves the door warp to the Mart
  entry mat `(4,7)`. These intermediate results are deliberately not claimed
  equivalent.
- Native `StoryExecutor::mash()` waits for overworld and returns no pose. The
  shared engine subsequently installs the authored scene pose. This pilot
  requires a separate scripted observation and receipt; it does not upgrade
  native fallback declarations to evidence.
- Native uses `default_route_costs()` and its production walker. Python uses
  explicitly pinned Dijkstra weights and an abstract in-place final turn.
  Its press trace is not a controller-timing or native planner-leg oracle.

These behaviors were inspected in the pinned
[`PokemonFRLG_AutoStoryEvents.cpp`](https://github.com/dayfine/Arduino-Source/blob/b170b7d2103e887ded825c37fdbdc19fd654fca8/SerialPrograms/Source/VideoGames/PokemonFRLG/Programs/AutoStory/PokemonFRLG_AutoStoryEvents.cpp)
and shared
[`Pokemon_StoryEvents.cpp`](https://github.com/dayfine/Arduino-Source/blob/b170b7d2103e887ded825c37fdbdc19fd654fca8/SerialPrograms/Source/Pokemon/AutoStory/Pokemon_StoryEvents.cpp),
not established by running native tests in this PR.

Next, add a native consumer of the same scenario inputs using the existing
engine and production planner/walker seams. Export actual intermediate outcomes
and resolved runtime/save/retry settings; compare like-for-like fields, keeping
native declarations, modeled predictions and independent observations distinct.
Keep initializer/save operations visible in native traces rather than deleting
them to force matching event counts.
Any change to native fallback/step behavior needs its own regression and review.
Then add supported encounter recovery/rejoin, end-save verification and the
BDSP `01.03` capture. The native authoring table remains in place until parity
passes. This pilot does not implement a generic executable story-plan envelope,
handoff/resume, battles or full PokeGuy story execution.

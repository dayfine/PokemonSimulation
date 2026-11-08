# FRLG Parcel load-and-replay example

**Start with [the readable scenarios](CASES.md).** Each shows starting state,
supplied observations/interruptions, expected outcome and (where enabled) the
complete expected action table. It is generated from `cases.json`, not replay
output, and checked for drift in tests.

The reusable checkpoint runner loads captured story events and dispatches
registered handlers. FRLG routing/stepping lives in the game adapter; the
Parcel-specific receipt requirement lives in `binding.json`. There is no
checkpoint-ID guard or hardcoded Parcel item in the runner. A synthetic second
checkpoint exercises the same loader/runner with a different ID, scene-first
ordering, repeated steps and another receipt. Currently supported capabilities
are FRLG route/step and scripted scene observation; other kinds/games stop at
binding until their adapters exist.

```sh
PYTHONPATH=src python3 -m pokesim.story.checkpoint_replay \
  data/story/parcel-pilot/cases.json --case parcel-all-events --summary \
  --out /tmp/parcel-trace.json
PYTHONPATH=src python3 -m unittest pokesim.story.test_checkpoint_replay \
  pokesim.games.frlg.test_story_replay
PYTHONPATH=src python3 -m pokesim.story.replay_cases \
  data/story/parcel-pilot/cases.json --check-doc data/story/parcel-pilot/CASES.md
```

## What check_actions verifies

`input.check_actions: true` requires `expectation.actions`: the **entire ordered
sequence** of actual modeled requests. Missing/extra/reordered actions, different
directions or different tile distances fail even if the final status says complete.
`false` (or omission) checks outcomes only and must omit `expectation.actions`.
The switch never changes execution. The CLI and tests use the same checker;
the CLI records `case_check.actions` as `matched` or `not-checked`.

The selected success case is called `parcel-all-events`, rather than `complete`.
It checks 23 semantic actions: straight-line walks totaling 117 tiles, three
route map transitions, the final facing change, the Mart entrance transition,
and the scene request. For example, exiting the lab is a southward walk for four
tiles followed by a separate door warp. Hops remain separate from walking.
No expected action counts button presses or depends on input timings.

Actions describe **requested intent**, not confirmed displacement. In the grass
interruption case the requested leg remains `walk north for 7 tiles`; the
result instead retains two candidate tiles and unknown facing. It must not
credit all seven tiles, or rewrite the original request as the one interrupted
movement. The per-move diagnostic state trace remains available separately.

The entry failure checks an empty action list. The failed Mart transition checks
that entry was requested but the scene never was. The grass interruption checks
the exact prefix through the interrupted walk request; later actions must be absent.
Other cases deliberately check outcomes without locking down a route.

**This checks all currently modeled requests for the three authored events.**
It does not simulate the clerk's dialogue/animation or independently implement
the game's Parcel-grant script. The scene result is still supplied by a fake
observation, visibly labeled synthetic. Exact action checking does not establish
native execution parity or turn this into a complete console simulation.

`binding.json` pins the actual evaluated `00.05` capture/source revision, five
approved runtime maps, capabilities, receipt requirement and Python route costs.
It does not use the unreviewed full-world candidate maps. Hash drift, unknown
bindings, unsupported policy and malformed inputs fail before execution.

The grass interruption is anchored to a north input from Route 1 `(12,39)` into
`(12,38)` (model move 26 under this profile). A changed route that misses this physical
point fails rather than silently omitting the interruption. It is not recorded
console evidence or a claim that every encounter has exactly these outcomes.
Recovery/rejoin remains unbound: this diagnostic safely stops with two candidates
and unknown facing. Existing lower-level [recovery tests](../../../docs/navigation/ENCOUNTER_RECOVERY.md)
remain separate. A stopped run exits 1; `--out` retains its report, including
actual actions if an expectation check fails.

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
  Its movement trace is not a controller-timing or native planner-leg oracle.

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

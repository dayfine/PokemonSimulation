# BDSP mine/Roark authored checkpoint

Arduino-Source owns the authored plan. `source.json` pins its repository revision, path and hash; consume that committed file with the command below. The checked-in [15-event snapshot](bdsp-mine-01.03.plan.json) is retained only as a frozen offline regression fixture.

Start with [the 15 reference events](bdsp-mine-01.03.plan.json) and [the readable cases](CASES.md). The native story table loads the same JSON. The old hand-transcribed BDSP draft had 16 events; it is not the source of this pilot.

Source: [Arduino-Source #226](https://github.com/dayfine/Arduino-Source/pull/226), exact revision `0738cd55b562d1dd685cdea289663a015a1cbe59`, `SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_StoryTable.cpp`, `oreburgh_mine_to_roark()`. Barry and the first heal now belong to `01.02b`. This file preserves the current inbound/outbound legs, two-tile Center/exit beliefs, `counted_wall` and `to_wall` variants, failure policy, and save-card guard.

The native companion is [Arduino #263](https://github.com/dayfine/Arduino-Source/pull/263), branch `bdsp/checkpoint-json`, based on that exact #226 head. Python implementation: [PokemonSimulation #74](https://github.com/dayfine/PokemonSimulation/pull/74). Game executors remain unchanged. Its adjacent tests load the actual table, execute `01.03` through the existing engine/fake-game simulator, and stop before healing when the exit fails through all three attempts. This is integration coverage; that fake is not a detector/timing oracle.

## Run the Python check

```sh
# Authoritative plan from an explicitly fetched Arduino checkout:
PYTHONPATH=src python3 -m pokesim.story.native_plan \
  data/story/bdsp-mine-pilot/source.json --checkout ../Arduino-Source

# Frozen historical regression snapshot (no external checkout required):
PYTHONPATH=src python3 -m pokesim.story.checkpoint_replay \
  data/story/bdsp-mine-pilot/cases.json --case mine-all-events \
  --binding data/story/bdsp-mine-pilot/binding.json --summary
PYTHONPATH=src python3 -m unittest pokesim.games.test_bdsp_story_replay
```

Nine scenarios cover all 15 events, wrong entry, unconfirmed mine arrival/exit, wild interruption before Roark, missing conversation/departure evidence, the wandering Hiker, and an unconfirmed heal. The full success, wrong-entry, missing-arrival and interrupted cases assert every ordered semantic action. Expectations do not drive execution. Shortened legs cannot be repaired by assigning `declared_after`.

## What the model proves

- Local routes and legs use the existing runtime world/movement/planner and the approved map bytes pinned at `4de7742a764d27293b4525d6ad2a6fc8a95f3e3a`. No terrain, corrections or resource pins are changed.
- BDSP `STEP` traverses its source corridor to a doorway; it is not treated as one tile. B1F arrivals can stand on a cave mat, then move away from it toward the interior.
- Complete mine destination links are absent from the published maps. Arrival is therefore a separate **scripted observation**, checked against the authored alternatives, rather than a predicted or confirmed warp. Without it the run stops.
- `to_wall` must actually reach a terrain wall within its bound; an NPC/unknown/transition is not a wall. `counted_wall` computes both native declared starts: 37 and 38 tiles north converge at city `(46,21)`. The requested count 37 must lie within those bounds. The observed/model physical pose and native fallback belief remain separate.
- Roark's conversation needs adjacency, a facing change where necessary, and a scripted dialogue observation. The scene needs a separate departure result. Healing needs a receipt; neither action becomes successful merely because it was requested.
- Wandering NPC regions remain hazards. A test may explicitly script a collision-free movement window for a named NPC; absent that window the model stops before entering its range. It does not treat the Hiker as a permanent wall or invent live waiting behavior.
- A battle during a counted leg retains the requested distance, invalidates the pose, and exposes the before/after candidate tiles with unknown facing. Recovery/rejoin is not silently assumed.

## What remains unproved

The Python path uses its pinned cost profile; it does not reproduce native robust planner costs or select identical legs. Observations, clearance windows and scene/heal results are synthetic. Controller queues, analog movement, actual NPC trajectories, banner/fade/dialogue detectors and scene timing are not simulated here. The native executor's declared-arrival fallback remains unchanged.

The authored native policy is save-at-start with `reload_and_retry` guarded by the `Oreburgh City` save card. Python uses the existing explicit one-attempt stop/no-save diagnostic binding; a Python pass is not native retry/save parity. Battle outcomes and post-heal stats are not fabricated.

## Existing run evidence behind this route

These are references preserved from #226's comments at `0738cd55b`, not new console runs performed for this PR:

- Lab-B, 2026-11-07: a counted south-three approach below Roark moved only two tiles. The current route clips the room’s south wall before moving west to talk.
- Lab-B, 2026-11-08 11:55: wild-battle recovery replanned only to open tile `(15,16)`; a later south-five leg overshot a row and the remaining taps ran under Roark’s rocks. The current source groups the inbound legs through the corner. This pilot’s interruption case stops with uncertainty; it does not claim recovery/rejoin is proved.
- Lab-B, 2026-11-08 09:46, 10:39 and 12:03: the B1F exit came out on city column 46, east of the sign at `(45,56)`, so walking north did not stop at that sign. The current route instead clips the wall beside the Center.
- Lab-B, 2026-11-08 13:50: a north tap/east wall hold matched the map only from column 46; east from `(48,57)` was blocked although the map showed `(49,57)` open. The current route avoids that street. The pilot does not change terrain to explain this unresolved discrepancy.

Entry assumes the native preceding `01.02b` Barry/heal setup. The pilot does not invent party levels, HP, item counts, or quest-flag observations to turn that assumption into a verified precondition.

Arduino CI replays its current plan against pinned simulator code and independent cases; it does not compare plan bytes between repositories. Route changes can legitimately require revised scenario expectations, but they do not require mirroring JSON or updating a simulator pin merely for whitespace or authoring changes. Update `source.json` when choosing a new native revision for offline analysis; after a draft native PR is squash-merged, repin to the merge commit on its target branch before retiring the source branch. Native literal Center/Roark anchors are checked against map-derived points, and the live route rationale stays beside the authoritative native JSON.

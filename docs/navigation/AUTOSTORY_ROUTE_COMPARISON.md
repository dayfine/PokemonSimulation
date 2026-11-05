# Comparison with the native AutoStory routes

The original #44 goldens were handpicked planner exercises. They were not
checked against the AutoStory tasks, so they should not have been presented
as representative routes. This comparison fixes the reference inputs and
keeps the remaining planner differences explicit.

| Case | Old golden | Native contract now used |
|---|---|---|
| Pallet Town | `(6,8)` to lab front `(16,14)` | FRLG `00.03 / below_oaks_trigger`: `(6,8)` to `(12,2)`, face north. Oak's scene starts on the next north step. |
| Fan Club | `(5,9)` to `(5,3)` above the chairman | FRLG `00.26 / beside_chairman`: local arrival `(5,10)` to `(4,4)`, face east toward chairman `(5,4)`. |
| Route202 | Training grass `(19,27)` directly to later save `(30,24)`, including an unknown-tutorial variant | BDSP `00.04d / north_to_jubilife`: saved position `(30,24)` to the `jubilife_exit` region, after tutorial/healing/shopping. |

Sources, inspected at fixed revisions:

- [FRLG #224, `oaks_trigger()`](https://github.com/dayfine/Arduino-Source/blob/51c0ce6128e5981da56b370a770874b96a1e129f/SerialPrograms/Source/VideoGames/PokemonFRLG/Programs/AutoStory/PokemonFRLG_AutoStoryTable.cpp).
- [FRLG #224, `bike_voucher()` and its chairman interaction](https://github.com/dayfine/Arduino-Source/blob/51c0ce6128e5981da56b370a770874b96a1e129f/SerialPrograms/Source/VideoGames/PokemonFRLG/Programs/AutoStory/PokemonFRLG_AutoStoryTableCeladon.cpp).
- [FRLG arrival rules](https://github.com/dayfine/Arduino-Source/blob/51c0ce6128e5981da56b370a770874b96a1e129f/SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/PokemonFRLG_OverworldMap.cpp) and [Fan Club destination warp](https://github.com/dayfine/Arduino-Source/blob/51c0ce6128e5981da56b370a770874b96a1e129f/SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/Maps/VermilionCity_PokemonFanClub.json): `warp_1` is `(5,10)`, a directional mat, so the local arrival is not automatically displaced north or south. This is a derived local slice of a longer native route.
- [BDSP #226, `to_jubilife()` and preceding tutorial/heal sequence](https://github.com/dayfine/Arduino-Source/blob/4fc851b4783cbad6a50437056d56d658d8585335/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/PokemonBDSP_AutoStory_StoryTable.cpp).

All three selected map JSON files match the native snapshots byte-for-byte.
No map correction from #226 was imported for this comparison. These failures
came from selecting unrelated endpoints/state and from poor presentation,
rather than a crop difference in these three maps.

The old pictures also colored large NPC occupancy rectangles blue, like water,
and omitted axes, endpoints, checkpoint labels and legends. The corrected
[gallery](../../src/pokesim/maps/goldens/README.md) uses annotated SVGs as the
primary review view, with distinguishable object/scene overlays and PNGs for
raster regression tests.

## What still differs from native AutoStory

These are Python candidates for native **goals**, not native planner replays.

- [FRLG's native costs](https://github.com/dayfine/Arduino-Source/blob/51c0ce6128e5981da56b370a770874b96a1e129f/SerialPrograms/Source/VideoGames/PokemonFRLG/Overworld/PokemonFRLG_OverworldRoute.cpp)
  include grass cost 20 and open-stop penalties (including a larger penalty
  for stopping in encounter terrain). Python currently uses tile/turn/grass
  costs without those leg-stop terms. Matching endpoints does not establish
  that the selected paths are identical.
- [BDSP uses robust leg costs](https://github.com/dayfine/Arduino-Source/blob/4fc851b4783cbad6a50437056d56d658d8585335/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Data/PokemonBDSP_AutoStory_PlanCosts.cpp),
  possible-position sets, trainer interruptions and replanning. The local
  Python model does not yet reproduce those policies or carry battle outcomes.
- The Route202 case uses `VAR_ROUTE_202_STATE=1` as an explicit disarmed-state
  assumption. The native row order establishes that the tutorial is over;
  the numeric value is not asserted to have been extracted from that row.
- The Fan Club entry pose is derived from map/arrival metadata. Cross-map
  movement into the building is still excluded from the Python route.

Next parity work should compare movement legs, stopping conditions, state and
cost policy on the same exported task. A matching golden only locks down
the current candidate; it does not validate the full game plan.


The next [transition/localization slice](TRANSITION_SCENARIOS.md) now tests
FRLG warp/edge arrival and reduced semantic interruption scenarios, including
a BDSP mine south clip. These are not native planner replays: leg costs,
dynamic trainer worlds, hardware observations and complete story execution
remain open. No pending #226 map refinement was imported.

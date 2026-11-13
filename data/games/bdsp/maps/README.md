# BDSP map set

The 22 BDSP maps AutoStory walks (Twinleaf to Floaroma, plus the Oreburgh mine
and gym) are published in three layers, as for FRLG
([OVERLAYS.md](../../../../docs/maps/OVERLAYS.md)):

| Directory | Content | Owner |
|---|---|---|
| `base/` | The map as the generator reads it from the pinned Diamond (or, for the interiors and the Ravaged Path, Platinum) decompilation: terrain, the people the events file shows, its coord events, and the named `points` (route anchors, until step 3 moves them to the checkpoint data). Nothing authored by hand. | `bdsp_decomp_map_builder`; `--check` reproduces every file byte for byte. |
| `overlays/` | Every correction BDSP needs, as ordered operations with `why`, `evidence` and `status` ([schema](../../../../schemas/map-overlay.schema.json)). 18 maps have one. | Reviewed PRs; one operation per map fix. |
| `runtime/` | What consumers read (Arduino-Source's resource pin): base + overlays, in the pack's readable format. A map without an overlay publishes its base bytes. | Derived by `map_overlays write`; `map_overlays check` fails on any difference. |

The eight snake-case files in this folder (`route_201.json`, ...) are the older
`pokenav-map/1` reference fixtures of the grid tests; their coordinates are not
the pack's (see [runtime-maps.md](../../../../docs/maps/runtime-maps.md)).

## What the overlays hold

45 operations in 18 files. All are `candidate`: the manifest says BDSP is
"mixed; not blanket verified", and a console pass promotes status.

| Operation | Count | why | What it is |
|---|---:|---|---|
| `tile` (a measured tile) | 7 (22 tiles) | `console_measured` | Route201, Route202, Route204North, PlayerHouse1F. Published as the runtime map's `patches` over the base's raw tiles, with `measured_by` = evidence `run` + `date`. |
| `tile` to `D` | 5 (17 tiles) | `generator_gap` | Warp tiles a route enters by walking into the door; the base writes every warp tile `.`. Waits on decoding door versus step-on from the remake. |
| `object` add | 15 | `story_scope` (13), `console_measured` (2) | A person the decomp hides by a story flag but the story meets (Jubilife's clowns and president, Roark, Rowan, Barry, the Lake Verity actors, Floaroma's grunts), and the two Floaroma people the console found. The Jubilife clowns' wander boxes are here. |
| `object` remove | 4 | `console_measured` (3), `story_scope` (1) | People who wander in BDSP but stand still in Diamond (Route203, Sandgem), and Route201's Potion lady, whom the story walks to. |
| `object` update | 1 | `console_measured` | Route204North's Brandon: still, on (20, 12). |
| `trigger` update | 9 | `story_scope` | The names AutoStory's coord-event table uses (`coord_event_<index>` in the base). |
| `trigger` add | 1 | `console_measured` | Mom's call on the door mat (PlayerHouse1F), not in the decomp. |
| `link` add (warp) | 3 | `generator_gap` | The door mats of the two Twinleaf houses and the Lab; the builder emits no warps. |

`story_scope` is a choice about which people and labels the static map carries
for our story; it has no `when` yet, so the effective map holds them at every
story state.

## Commands

```sh
PYTHONPATH=src python3 -m pokesim.maps.bdsp_decomp_map_builder --check
PYTHONPATH=src python3 -m pokesim.maps.map_overlays --game bdsp audit JubilifeCity
PYTHONPATH=src python3 -m pokesim.maps.map_overlays --game bdsp check
PYTHONPATH=src python3 -m pokesim.maps.map_overlays --game bdsp write
```

A map fix is one overlay operation with its evidence, then `map_overlays write`.
Never edit `base/` or `runtime/` by hand; a generator change regenerates
`base/` and `write` refuses any operation that no longer changes anything.

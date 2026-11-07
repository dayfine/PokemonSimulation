# BDSP map reconciliation

## Current review — November 7, 2026

Compared all 22 maps at Simulation `f12af546d98f453e005c3116442423dcbdcda347`
with Arduino #226 `fc56a720b9c0b1f4d945dbef382d61b0a6382b97`. Every map was
byte-identical, including objects, points, patches, triggers, warp metadata and
source annotations. The three previously held changes below have been removed
on the consumer side; no new terrain or NPC correction is adopted here.
This establishes repository parity, not new console verification.

The subsequent BDSP pickup publication adds the pinned catalog identities,
quantities, collection flags and provenance to 15 items across seven maps.
Stable object names, positions, geometry, NPCs, triggers and warps stay fixed.
`item_3` remains an object ID; `item: escape_rope` describes its reward.
The source is explicitly a Diamond/Platinum remake baseline, not verified BDSP
item data. Source-map copies can now be replaced by pinned prepared resources
after this publishing commit lands on main and native adoption checks pass.

Reproduce the pre-enrichment comparison from the immutable Simulation revision:

```sh
PYTHONPATH=src python3 -m pokesim.maps.map_parity \
  --arduino-source /path/to/Arduino-Source --game bdsp \
  --revision fc56a720b9c0b1f4d945dbef382d61b0a6382b97
```

Run from a checkout of `f12af546d98f453e005c3116442423dcbdcda347`. The enriched
pack intentionally differs in pickup metadata and its checksums.

## Historical review — November 6, 2026

Review date: 2026-11-06. Compared PokemonSimulation base
`40717c7c809c415c751fd7a348dfc1895f7ec3d7` with Arduino-Source
[#226 at `01e6659116f520b51c35ee956aa6a222dfa864f8`](https://github.com/dayfine/Arduino-Source/tree/01e6659116f520b51c35ee956aa6a222dfa864f8/SerialPrograms/Source/PokemonBDSP/Programs/AutoStory/Maps).
All five differences were reviewed: two adopted, three held. With this change,
19/22 BDSP maps match that native snapshot byte-for-byte (previously 17/22).
FRLG maps are unchanged. This is an offline review; no new console run occurred.

| Map | Decision | Evidence / limitation |
|---|---|---|
| OreburghMineB1F | Adopt step-on warp row | Diamond events and land behavior agree with #226. Destination arrival/facing remains unresolved. |
| PlayerHouse1F | Adopt reported post-heal trigger | Native checkpoint `00.04` and r45/r46 attribution agree on the door mat. Original captures were not independently replayed. |
| Route201 | Hold pending anchored evidence | Source confirms sign location, but new collision patches predate shared recovery; existing sign overrides also need reconciliation. |
| OreburghMine (B2F) | Hold seven corridor edits | They conflict with the decoded source; no per-tile target-game evidence accompanies them. |
| JubilifeCity | Hold fixed president relocation | Source spawn and story phases do not support a permanent `(46,36)` position. |

Coordinates below are zero-based local `(x,y)` tiles. They are not screenshot
pixels or global decomp `(x,z)` coordinates. Reviewed decisions are linked from
`data/maps/runtime-manifest.json`; original import lineage remains intact.

## Adopted changes

**Mine hall:** Diamond events `narc_0196` lists B2F warps at `(11,21)`,
`(12,21)`, `(13,21)`. Land data `narc_0313` has behavior `0x6f` at all three.
The builder previously converted these warp glyphs to ordinary floor, despite
retaining the row-22 cave mouths. Registering row 21 in `WARP_DOORS` makes a
south step from row 20 report an unresolved warp immediately. This agrees with
#226's StorySim expectation `warped at (12,21)`. A route cannot clip through
these stairs to a wall or assume it reached B2F. Arrival coordinates/facing need
a separate transition contract and evidence.

**Mom's post-heal call:** move the added `moms_call` trigger from `(6,9)` to
`(6,10)`, width/length 1. #226 checkpoint `00.04` explicitly approaches `(6,9)`
in `around_mom`, then steps south in `to_moms_call`. The map attributes this to
console r45/r46 (2026-11-01); the local r47 summary also reports the checkpoint
passing. The original r45/r46 captures were not located in this review.

`CONSOLE_MOMS_CALL == 0` activates this synthetic trigger; value 1 disarms it.
It is distinct from the existing Platinum `moms_warning` trigger, whose variable
is `VAR_PLAYER_HOUSE_STATE`. Local routing blocks an active/unknown scene rather
than executing it. When disarmed, the mat remains an unresolved house warp.
This is a reported BDSP story contract layered over Platinum geometry, not a
source-derived BDSP script or blanket verification of the interior.

## Held changes and evidence needed

Use the [mapping protocol](MAPPING_PROTOCOL.md) to establish positions from
independent directions, preserve interruption uncertainty, and record evidence.

**Chronology matters:** all five map deltas entered #226 in WIP commit
[`e572a3036`](https://github.com/dayfine/Arduino-Source/commit/e572a3036fb270f4cc0fbd6b66442872b0c0bd1a)
on November 4 at 21:18 Pacific. Shared wall recovery entered its history through
#229 merge `8c6acefa34253d8d67a13d1fb51f2f1a7433eb` on November 5. The current
#226 head contains both, but no later map revalidation was found. These edits
could reflect incorrect localization before recovery, rather than terrain.
Commit dates alone do not establish that explanation, either.

**Route 201:** hold the native patch changes. They report 20 extra blocked
tiles: columns 36–39 on rows 9–12, plus columns 32–35 on row 12, attributed to
`r6, 2026-11-04`. All are floor in the decoded baseline. Original anchored
probe/r6 captures were not located/replayed. Do not import these walls based on
an attributed run label alone, especially when recovery had not landed yet.

There is also a known source/override discrepancy: Diamond event object 3 is
`ARROW_SIGNPOST` at global `(109,856)`, minus crop `(96,839)` = local `(13,17)`.
The current pack overrides that source sign to floor and puts a sign at
`(13,18)` (r16). Native #226 instead preserves the source sign and patches
`(13,18)` to trees (`probe-r201-sign, 2026-11-03`). The source corroborates the
sign's spawn, but does not prove BDSP's collision at `(13,18)`. Keep this map
unchanged for now, explicitly unresolved. Verify sign/trees from a known tile
and facing, independently of interrupted movement, before reconciling both.

**Mine corridor:** #226's broad WIP edit changes these seven tiles without
updating its generator or adding per-tile measurement evidence:

| Tile | Retained source | Native WIP |
|---|---|---|
| `(16,9)` | floor | wall |
| `(17,9)` | floor | wall |
| `(15,10)` | wall | floor |
| `(13,11)` | wall | floor |
| `(14,11)` | wall | floor |
| `(15,11)` | floor | wall |
| `(16,12)` | wall | floor |

Independent decoding of Diamond land `narc_0314` gives `0x0008` for those floor
tiles and `0x8000` for those walls. Keep the source baseline. A BDSP difference
is possible, but adopting it needs an anchored initial pose, scene/flags, action
and collision observations, and a verified coordinate frame. A successful tap
sequence alone does not establish terrain when localization could be wrong.

**President:** retain point/object spawn `(46,35)`, rather than WIP `(46,36)`.
Diamond events `narc_0002` object 24 is global `(174,771)`, local `(46,35)`.
#226's StoryTable describes walking to `(46,39)` during the introductory scene
and returning to `(46,35)` after the coupon interaction. A local November 2 note
reports approximately `(46,39)` after a scene; that does not establish `(46,36)`.
The static spawn does not prove the current NPC pose. A scene-specific override
needs checkpoint/flags and an anchored observation; do not move the permanent
spawn to compensate for route drift.

## Source checks and reproduction

The following cached source blobs were matched to GitHub at pret/pokediamond
commit `b623abef1b4dfe204ca50aab42447ac00c134290` using Git blob IDs. These are
individual source checks, not a resolved revision claim for the entire pack.
Paths are relative to `files/fielddata/`.

| Source | Git blob | SHA-256 |
|---|---|---|
| `eventdata/zone_event_release/narc_0196.bin` | `abb5b22e809daf47fec74ff560062fa4992dc2ee` | `fec75b45d815d678eff659c06b6f6ec9c531a724f1f3a2d25e16c3d586248f70` |
| `eventdata/zone_event_release/narc_0327.bin` | `5ca757fe28afb2039d055f4e6691dbe49361f8ab` | `20e193fabb4489ff5cae7faa6f2420ee45a08f6f45f6f6945036459be321f750` |
| `land_data/land_data_release/narc_0314.bin` | `9e903035f4c90337deb71eb08e24a711971fb9d5` | `1e8f4c1626072afeb9c04fc45894f18a31a88f3ac79675b7cabd29aafa5b4500` |

```sh
# Uses the existing decomp cache; does not fetch or run a console.
PYTHONPATH=src python3 -m pokesim.maps.bdsp_decomp_map_builder --check
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_pack
PYTHONPATH=src python3 -m unittest pokesim.maps.test_bdsp_map_reconciliation -v
PYTHONPATH=src python3 -m pokesim.maps.item_identity \
  --cache /path/to/pinned-item-sources --check
PYTHONPATH=src python3 -m pokesim.maps.map_parity \
  --arduino-source /path/to/Arduino-Source --game bdsp \
  --revision 01e6659116f520b51c35ee956aa6a222dfa864f8
```

The B1F geometry/content digest in the item catalog is deliberately refreshed;
item identities, rewards, source pins and collection flags remain unchanged.
Historical native replay fixtures retain their original publishing pins.

## Native adoption

Do not silently overwrite #226 or declare it in parity. Its owner must reconcile
the three held differences: use this canonical baseline, or supply the anchored
BDSP evidence above for a new reviewed correction. After that, adopt one immutable
publishing commit and manifest hash through the resource lock. Re-run native
route/story tests against that exact pack before removing source-map copies.
The initial reconciliation used v1 maps. The subsequent
[compact-format publication](V2_PUBLICATION.md) changes their representation,
without accepting any held corrections; native resource adoption remains pending.

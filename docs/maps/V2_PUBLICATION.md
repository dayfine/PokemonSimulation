# Compact runtime-map publication

All 75 published maps (53 FRLG, 22 BDSP) and both generators now emit
`pokesim-runtime-map/2`. Every file carries the marker; the manifest advertises
the same version and updated byte hashes. This is a representation change on
top of #55's reviewed data, not further acceptance of its held BDSP corrections.

Records use `coord: [x,y]`; NPC wander boxes use inclusive `min`/`max` pairs.
`npcs`, `items`, `signs` and `interactables` supply the object kind. Short records
stay inline. Source metadata, generation overrides and terrain-correction
provenance in the manifest keep their original source coordinate vocabulary.
Zero/false values and unknown extensions are preserved. Empty object sections
are omitted; order within each kind is preserved. Cross-kind ordering is not a
runtime identity: use names/coordinates/source-event references, not array indices.

Item identities remain opt-in enrichment. This migration changes no item
catalog facts/content bindings: their canonical digest already uses compact
coordinates. No terrain, object position, warp contract, flag, trigger or
trainer behavior is deliberately changed by this conversion.

## Validation and historical evidence

`test_runtime_map_publication.py` compares canonical value digests recorded
from immutable v1 parent `4a16ca2b12c02b965136bcc2f347c342d900613b` and checks
formatter stability. `data/maps/v2-value-baseline.json` retains those 75 digests
so the check survives parent-branch deletion or squash merging; it is a test
oracle, not a second map-authoring surface.
The four route goldens retain identical paths, costs, SVG bytes and PNG pixels;
only their map-byte hashes are refreshed.

Historical transition/native-recovery fixtures keep their original revisions,
checksums and observations. `pinned_runtime_map` first checks current bytes;
when they differ, it reads the exact recorded Git revision locally and verifies
the checksum before decoding. It never fetches, changes a pin or substitutes
current geometry for missing history. A shallow clone must supply full history
(e.g. `git fetch --unshallow origin`); CI explicitly checks out history.

Separately, all shared transition cases and captured FRLG/BDSP recovery cases
are replayed in Python against the current v2 maps and compared with their
expectations/historical results. These checks are not fresh native captures.
The existing focused native executable from nav-core #114 also passes 150
complete production-reader comparisons using this pack: every map plain and
with optional item enrichment, plus the native schema contract cases. This is
decoder validation; game-specific native story execution remains an adoption gate.

## Native adoption and the next step

The v2 reader is integrated into shared `parse_map()` on Arduino nav-core #114
(inspected head `7225e71e4b3d8728cb18a8c928d6ac7a837105ba`). Merge it through both
game chains before selecting a v2 publishing pin. This publication PR is stacked
on #55; neither draft revision is automatically approved by consumer tooling.
An immutable revision must be on publishing `origin/main` before normal adoption.

The consumer verifier accepts both versions, enforces marker/manifest agreement,
and retains independent game pins, complete inventory/byte checks and approval
checks. It does not negotiate capabilities with an old native binary. Existing
native pins and resource paths are unchanged. Never repin an old reader to v2.

Next: prepare pinned map packs in `Packages/Resources/Pokemon/Maps/{frlg,bdsp}`,
wire native loading/build/CI to those prepared resources, validate the owning
game routes, then remove embedded source copies and duplicate authoring tools.
See [the ordered plan](UNIFICATION_STEPS.md).

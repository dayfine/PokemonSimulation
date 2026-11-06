# Confirming map locations and corrections

Use this protocol for a disputed tile, object, trigger or transition. Start with
a pinned source map; confirm only the facts actually measured. Passing a story
checkpoint does not verify every tile on its route. This document specifies
future console measurements; the examples below are not new run evidence.

## 1. Establish the starting state

Record game/version, native build SHA, map-pack commit/hash, checkpoint, story
flags, object visibility, movement mode and coordinate frame. For BDSP distinguish
local `(x,y)` from decomp world `(x,z)` and record the crop origin. Keep NPC
spawn coordinates separate from their current scene-dependent positions.

Start from an independently proven anchor: an identified doorway with a verified
arrival contract, a known sign, or a corner formed by two established boundaries.
Record the player's tile/belief and facing, and explain how each was established.
A single wall constrains one axis; it does not identify your position along that
wall. If multiple tiles remain possible, retain them until observations separate
them. Do not anchor using the very wall or arrival location being investigated.

A loaded save is an anchor only when its recorded pose and story state are known.
Do not reload a different checkpoint or overwrite a save just to finish a probe.

## 2. Probe one fact at a time

Use bounded, movement-aware walks with an observation after each leg. Separate
turning from translation: a turn-only press is not a tile moved. Record actual
movement/stops, not inferred distance from hold duration. Screenshots help retain
evidence but camera perspective and decorative art do not establish tile rows.

For a disputed destination tile, approach from a known adjacent tile and record
the **directed edge**: source tile, direction, destination candidate and result.
A stop alone is insufficient: confirm that the game is responsive, input has
finished, the player faces the intended direction, and no menu, battle, dialogue
or moving actor explains the stop. Camera stillness alone does not prove a wall.

For a sign/NPC, record adjacent traversable tiles, approach direction, facing,
and the interaction response/identity. Check the faces that the game permits;
failed interaction from an unsupported side is not proof of a misplaced object.
A wandering or scene-controlled NPC is not a permanent terrain boundary.

## 3. Cross-check from independent directions

Before accepting a disputed location, obtain at least two independently anchored
approaches, preferably perpendicular (for example, from west and north). Reset
or re-anchor between them; repeating the same uncertain walk twice adds little
positional evidence. Measure from opposite sides too when safely accessible.
A return trip to another known anchor checks distance and accumulated drift.

For example, a hypothetical obstacle at `(4,3)` can be probed east from proven
`(3,3)` and south from independently proven `(4,2)`. These are **synthetic
coordinates**, not a proposed route through an existing map. Both blocked edges
support the obstacle's location only if both starting tiles are established.
They do not prove all four edges or the obstacle's identity.

Record which sides were tested and which were inaccessible/unsafe. A one-sided
result remains provisional unless other independent evidence establishes the
claim; do not invent an unsafe approach to satisfy a count. One-way ledges,
elevation, directional mats and doors can legitimately behave differently by
direction. Model that asymmetry rather than forcing agreement with a wall glyph.

## 4. Invalidate interrupted measurements

If a wild battle, dialogue, transition, partial movement or queued input occurs,
stop the measurement. Retain the possible poses; do not credit an attempted step
as completed. Cancel/drain input through the native executor, observe the game
state, and use bounded safe localization to recover an established anchor before
repeating the probe. If that is impossible, end the probe as unresolved.

A wall recovery is valid only when every candidate pose can safely reach the
same verified anchor without crossing a transition, scene or other hazard.
Reaching a newly hypothesized wall cannot validate that same hypothesis.
Do not change map terrain to make an interrupted route or its recovery succeed.

For a transition, record the last confirmed source tile/facing, triggering input,
observed map change, first arrival pose/belief and facing, and any automatic
walk-out separately. Confirm the destination from its own anchors. Test the
reverse direction where available; do not assume transitions are reciprocal or
infer arrival from overlapping map crops. Stop before an unverified transition
unless that transition itself is the authorized, bounded measurement.

## 5. Keep an evidence record and publish the smallest correction

Use one record per claim, with a row per approach. This illustrative record is
synthetic and deliberately remains unresolved:

```yaml
claim: obstacle at local [4, 3]
status: unresolved
pins: {game: required, build: required, map_pack: required, frame: required}
state: {checkpoint: required, flags: required, movement_mode: required}
probes:
  - anchor: required independent anchor and proof
    start: {tile: [3, 3], facing: east}
    action: one east step
    expected: blocked toward [4, 3]
    observed: not measured
    evidence: required run / step / log / capture references
  - anchor: required second anchor and proof
    start: {tile: [4, 2], facing: south}
    action: one south step
    expected: blocked toward [4, 3]
    observed: not measured
    evidence: required run / step / log / capture references
interruptions: required, including recovery or explicit failure
conclusion: required tested edges, untested sides, and confidence/limits
```

Separate source facts, planned probes, observations and conclusions. Disagreement
between approaches calls for checking pose, facing, flags and direction-specific
behavior before editing the map. A run label alone is not reproducible evidence.

Submit the record with the correction here: update the generator/override,
map, manifest/hash and affected content bindings together. Add a regression for
the measured behavior; run route/recovery tests against the corrected map. Keep
historical replay fixtures pinned to their original data. Only then should the
native consumer adopt the new publishing commit and revalidate its routes.

## Apply this to the held BDSP differences

- **Mine corridor:** test the seven disputed cells in
  [the reconciliation](BDSP_RECONCILIATION.md) from established adjacent tiles
  on multiple axes. Record collisions and interruptions separately.
- **Route 201:** verify the sign's identity and readable face(s), then adjacent
  tree/barrier edges from independent anchors. The sign observation does not
  validate all 20 reported tree tiles.
- **Jubilife president:** record checkpoint/scene flags and NPC interaction
  position before/after the scene. Do not replace a spawn with a scene pose.

## Earlier AutoStory guidance

This extends the existing instructions rather than treating old run labels as
verification:

- [Map tools README at #226's inspected head](https://github.com/dayfine/Arduino-Source/blob/01e6659116f520b51c35ee956aa6a222dfa864f8/devtools/maps/README.md#measuring-a-map): decomp first, anchor measurements, sign reads, map/route/walker distinction.
- [Lab navigation notes at the reviewed agents revision](https://github.com/dayfine/Arduino-Source/blob/a44e0f85cd75b43017590194dba1b2e94607bb0e/autostory/LAB_NAVIGATION.md): start from a proven anchor; timed holds and screenshot row estimates produced mistakes.

Their general statements about DP/BDSP layout agreement do not verify a new
remake correction. The extra acceptance requirements here are independent
multi-direction checks, interruption handling, and explicit untested boundaries.

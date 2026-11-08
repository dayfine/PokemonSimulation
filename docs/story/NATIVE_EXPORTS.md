# Evaluated native checkpoint captures

The first native adapter is [Arduino fork #251](https://github.com/dayfine/Arduino-Source/pull/251),
stacked on FRLG stage 1. Its `StoryCheckpointExport` executable calls the actual
`story_checkpoints()` table, then the shared checkpoint codec and FRLG extension
serializer. It does not extract C++ source strings or construct a console runner.

Build/capture instructions are in that branch's `devtools/story-export/README.md`.
The Linux full-build workflow uploads Parcel `00.05` as an artifact named
`frlg-checkpoint-<os>-<compiler>`. A canonical capture comes from a clean CI build;
its `source_revision` names the clean revision used when configuring that target.
Reconfigure after switching revisions. Match it against the workflow run's head.

Import and compact the captured data here:

```sh
python3 -m pip install -r schemas/requirements.txt
PYTHONPATH=src python3 -m pokesim.story.native_export frlg-parcel.native.json \
  --expected-revision COMMIT_SHA --out /tmp/frlg-parcel.capture.json
```

The schema registry resolves the shared checkpoint reference locally. Common
reader semantics still reject duplicate event IDs. A source-revision mismatch,
unknown native field, missing extension field or incorrectly claimed observation
fails instead of silently discarding data. Source revision is an identity check,
not cryptographic authentication of a caller-provided document.

The [checked-in Parcel capture](../../data/story/native/frlg-parcel-00.05.json)
was produced by the compiled native table. Its [provenance](../../data/story/native/README.md)
records the CI revision, run, artifact and original file hash. Python checks its
schema, source identity, actual event order and key poses; it is no longer just
a synthetic format test.

## What this capture means

This `pokesim-native-checkpoint-export/1` record is an evaluated authored-table
capture, not the proposed `pokesim-story-plan/1` executable envelope. It preserves
shared actions/poses and every FRLG stage-1 extension: menu and supplies, including
party moves/PP, optional stats and foe bookkeeping. Other revisions with added
fields need a matching adapter/schema; game name alone is not a capability pin.

`state_basis: native-table-bookkeeping` explicitly limits every supplies value.
A value-initialized full HP bar, empty item count or lead member does not prove
an observation, entry requirement or battle input. Runtime configuration, map
pins, executor bindings, entry evidence and effective save/retry policy remain
listed as `unbound`. No executable plan or successful replay is inferred.

## Next parity gate

- Parcel capture/import validation is implemented; keep its native revision and provenance pinned.
- Add BDSP mine/Roark `01.03` through its own evaluated native table adapter.
- Resolve shared requirements/state/evidence and effective save/failure policy
  from actual run options and executor behavior, without guessed defaults.
- Bind the same serialized records to the existing native engine and Python
  replay. Compare ordered actions, effects, interruptions and failures before
  replacing native authoring tables or expanding full FRLG coverage.

Synthetic boundary tests remain labeled synthetic; a captured authored row does
not prove console execution or timing. Native tests stay next to native sources,
Python tests next to their reader. Shared format tests are not controller tests.

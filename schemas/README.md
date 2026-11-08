# Exchange format schemas

JSON Schema 2020-12 describes the structural contract. Install the development
validator and check current published data:

```sh
python3 -m pip install -r schemas/requirements.txt
PYTHONPATH=src python3 -m pokesim.formats.json_schema --check-published
PYTHONPATH=src python3 -m pokesim.formats.json_schema story-checkpoint checkpoint.json
PYTHONPATH=src python3 -m pokesim.formats.json_schema frlg-battle-report report.json
```

| Schema | Scope |
|---|---|
| `story-checkpoint` | Common native checkpoint, step and tile-pose records from #66. Policy/state envelope is still proposed, not covered here. |
| `runtime-map-v2` | Current published FRLG/BDSP runtime maps with coordinate pairs and typed NPC/item/sign/interactable arrays. Historical v1 and older grid formats remain handled by their existing readers. |
| `frlg-battle-cases` | Existing Gen 3 solo-battle experiment inputs. This does not imply support for another generation or arbitrary teams. |
| `frlg-battle-report` | Existing full benchmark output (`pokesim-frlg-report/1`), including probability/count shapes. Run summaries and other result formats are not covered yet. |

`$id` identifies each schema; validation loads it from the local checkout and
does not fetch it. Consumers should pin the publisher revision alongside data
and fixtures. CI checks schema validity, all published runtime maps, checked-in
FRLG cases, common story conformance vectors and synthetic malformed records.
The report schema has synthetic boundary tests; full reports are generated
artifacts, not checked-in fixtures in this repository.

Story records reject unknown fields, matching the codec. Maps and battle
records retain existing extension fields; known fields are checked, and compact
map records reject conflicting legacy coordinate aliases/redundant kinds.
We do not insert defaults or rewrite published data. Existing map hashes and
resource pins remain unchanged. A missing pickup quantity still means one in
the runtime decoder, not in the schema validator.

## Formatting

Small definitions and short arrays stay inline within a soft 120-column width;
large containers expand with two-space indentation. Reproduce or check it with:

```sh
PYTHONPATH=src python3 -m pokesim.formats.contract_format
PYTHONPATH=src python3 -m pokesim.formats.contract_format --check
PYTHONPATH=src python3 -m pokesim.formats.contract_format path/to/authored.json
```

With no paths, this command touches schemas and the shared story conformance fixture only; explicit paths format other authored JSON. It preserves all values and key order.
CI checks the formatting.

## Structural validation is one layer

Keep existing semantic validators and runtime readers:

- Maps: equal row widths, bounds, region/warp geometry, wander ordering,
  connectivity, destination references and flag semantics.
- Story: unique event IDs, game bindings, preconditions, observations and safe
  execution. Declared arrival is not proof of observed arrival.
- Battles: trainer/move/item lookup against pinned rules, HP versus maximum HP,
  PP versus move limits, EXP/EV consistency and supported mechanics. Reports
  still need wins <= trials, consistent probabilities/outcome counts and
  statistical coverage checks.

JSON Schema's `integer` accepts mathematically integral JSON numbers such as
`1.0`. Native readers can impose the stricter integer-token requirement; schema
validation does not replace those readers. Likewise, unique IDs across objects
are checked by code, not `uniqueItems` (which compares whole objects).

Changes should update the schema, reader and common fixtures together. The
existing native codec CI pins #66's vectors; it does not yet consume these schema
files. Pin/adopt this revision in native authoring validation after review.

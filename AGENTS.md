# Repository conventions

## JSON formatting

For new or edited repository-authored JSON, use the shared compact formatter:

```sh
PYTHONPATH=src python3 -m pokesim.formats.contract_format path/to/file.json
PYTHONPATH=src python3 -m pokesim.formats.contract_format --check path/to/file.json
```

Keep short objects, definitions, coordinate pairs and arrays inline within a
soft 120-column width; expand larger structures with two-space indentation.
Preserve every value (including zero/false), key order and array order. Use
`pokesim.formats.contract_format.json_text` in new or updated JSON writers.

Do not bulk-reformat unrelated existing files. Published map/resource bytes are
hash-pinned: formatting changes require the normal publisher regeneration,
manifest update and consumer-pin adoption process. Keep externally generated
lockfiles and vendored/source snapshots in their owning tool's format.

With no paths, the formatter checks/formats schemas and shared story fixtures;
CI enforces those files. Apply the same convention when working on other JSON.

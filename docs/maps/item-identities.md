# Pickup identities and non-item interactions

The current map pack has 48 objects drawn with an item-ball sprite. The staged
identity catalog resolves **45 fixed pickups** (30 FRLG, 15 BDSP baseline) and
**3 FRLG starter-choice interactions**. It is generated from pinned source
instructions, not inferred from `item_3`, `item_ball`, sprite names or label
suffixes. [The catalog](../../data/maps/item-identities.json) preserves full event
IDs/indices, scripts, collection flags and resolved rewards.

The existing v1 map files, hashes and captured native replay fixtures remain
unchanged. Enrichment is available in staged exports and opt-in map generation;
activating it in the published pack follows native data/reader adoption.

## Use an enriched preview

```sh
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_format --game bdsp \
  --input data/games/bdsp/maps/runtime/OreburghMine.json \
  --out /tmp/OreburghMine.items.json
PYTHONPATH=src python3 -m pokesim.maps.runtime_map_format --game frlg \
  --input data/games/frlg/maps/runtime/PalletTown_ProfessorOaksLab.json \
  --out /tmp/OaksLab.interactions.json
```

Example typed item record (field order/line wrapping is formatting):

```json
{"name": "item_3", "coord": [4, 28], "item": "escape_rope", "quantity": 1, "source_event": 3, "hide_flag": "flag 993"}
```

`name` retains the old map-local label for native compatibility. **`item` is the
actual item identifier.** `source_event` is a compact index into the source map's
event list; the catalog stores the full local ID and script once rather than
repeating long script names in every runtime record. The map's
`source.item_identities` records the source pin/event digest, catalog path/hash
and verification level. The catalog/input manifest binds the exact input map
content, preventing a known map name from attaching old rewards to edited data.
Always enrich from the unchanged v1 input, rather than re-enriching a preview.

Oak's balls are emitted in the v2 `interactables` array, for example:

```json
{"name": "item_ball", "coord": [9, 4], "interaction": {"kind": "starter_choice", "species": "squirtle"}, "source_event": 5}
```

The Squirtle choice is source event index 5 at the pinned FRLG revision.
These records contain no item/quantity and do not grant a Pokémon: confirmation,
scene state and the actual gift remain game-executor actions. V1 decoding keeps
the historical item-sprite kind for native compatibility; v2 separates semantics.

## Source/version boundaries

| Source | Pin | Resolution |
|---|---|---|
| pret/pokefirered | `ce6406d8c2eaf46d543c8a2606de0c3cb1951982` | Fixed `finditem` operands and its declared default amount; lab scripts identify starter choice. |
| pret/pokediamond | `b623abef1b4dfe204ca50aab42447ac00c134290` | Visible-item archive 370, 7000-based entries, fixed SetVar item/count and shared tail; numeric item constants. |
| pret/pokeplatinum | `c6689696d5fb51a644239702cb556eb52012a46a` | Its own visible-item ScriptEntry list and fixed operands, used for the imported RavagedPath baseline. |

Diamond script 7012 is Escape Rope; Platinum script 7012 is Luck Incense. The
same numeric script ID is not portable across games. BDSP's imported maps use
Diamond/Platinum baselines: resolved identities are explicitly labeled as such,
**not as verification against BDSP's own item data**. Metadata also exposes
`source_game`, `target_game` and `target_game_relation` (`native_decomp` or
`remake_baseline`) for machine readers. Mine event 3/script 7012
resolves to Escape Rope x1; event 4/script 7013 resolves to Potion x1.

Conditional or variable reward scripts outside the supported fixed forms remain
`pickup.status = "unresolved"`, without guessed item IDs or quantities. Hidden
items, NPC gifts and additional maps are outside this visible-item pass. Finding
an item on a map is not a replay inventory gain: reachability, collection flags,
bag capacity and confirmed collection must be handled by the story executor.

## Reproduce and check

[Reviewed input pins/hashes](../../data/maps/item-source-inputs.json) cover 28
files. Cache files are ignored/external; no ROM or upstream checkout is committed.

```sh
# Fetch only missing inputs at exact public source pins, verify, then compare.
PYTHONPATH=src python3 -m pokesim.maps.item_identity \
  --cache /path/to/item-sources --fetch --check
# After reviewing intentional source/input changes, regenerate the catalog only.
PYTHONPATH=src python3 -m pokesim.maps.item_identity \
  --cache /path/to/item-sources --write
```

On the lab's framework Python 3.8, prefix fetch commands with
`SSL_CERT_FILE=/etc/ssl/cert.pem` to use the system CA bundle if its Python
default CA file is missing. The fresh-cache check was verified with that setting.

Cached drift is an error, including with `--fetch`; the tool never silently
replaces it. Each file is verified with SHA-256 and its recorded Git blob ID.
CI reproduces the catalog from pinned public inputs. Runtime provenance hashes
identify catalog bytes; `inputs_sha256` hashes `json.dumps(inputs, sort_keys=True)`.

Both map builders accept `--item-identities` for deliberate enriched generation
into a separate output directory. Their default output remains compatible with
the existing v1 pack. The decomp parser now retains event ID, index and script,
and enrichment rejects changed source-event digests/references rather than
attaching a stale catalog entry. Review the five pending BDSP map corrections
separately; this feature changes no terrain or native console execution.

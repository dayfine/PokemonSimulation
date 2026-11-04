# Pokeguy's LeafGreen route and EXP audit

The [trainer route and level targets](pokeguy-route.md) groups all 69 trainer
battles into 17 route segments, with entry levels for every rival, Gym Leader,
and League battle. It includes the two early wild wins, all seven Rare Candies,
and evolution checkpoints.

The [complete battle log](pokeguy-exp.md) calculates the starter's cumulative
EXP and level after every battle from Oak's lab through the Champion. It
contains 69 trainer fights / 199 trainer Pokémon, seven Rare Candies, and the
documented wild encounters. This is the battle sequence on Pokeguy's route,
not a list of every available trainer in the game.

The inputs are [events.json](../../data/runs/pokeguy-leafgreen-15934/events.json)
and [reference.json](../../data/runs/pokeguy-leafgreen-15934/reference.json).
The first is a curated transcription of the existing
[video notes](https://github.com/dayfine/Arduino-Source/blob/11cbf77e0271e97b3639f9d5d419d0549ebec0bf/pokemon_sv/FRLG_POKEGUY_15934_VIDEO_NOTES.md),
including source lines, timestamp ranges, level/EXP observations, defeated
Pokémon order, and events that award no EXP. The second independently
resolves trainer IDs, complete parties, species EXP yields, and the Squirtle
family's growth curve from pinned pret data. Parties must match as multisets;
the runner's defeat order can differ from their stored party order.

## Result

Including the two documented wild wins reproduces **69/69 explicit level
statements in the notes**, **57/57 additional continuity checkpoints**, and
**33/33 recorded EXP awards**. Continuity checkpoints carry a level forward
from the notes, including unchanged maximum HP; they are not additional direct
video readings. Repeated before/after levels are not independent observations. Matching them is
an audit against the existing notes, not a new continuous video verification
or proof that no unrecorded event occurred.

When we flee every random wild encounter, the model omits 24 EXP from a
Lv3 Rattata and 15 from a Lv2 Pidgey. It matches 112/126 total level checkpoints
(59/69 explicit statements):

| After battle | Flee all random wilds | Observed-wild control / video notes |
|---|---:|---:|
| Sammy | 7 | 8 |
| Liam | 10 | 11 |
| Brock | 12 | 13 |
| Colton | 13 | 14 |
| Greg | 15 | 15 |
| Misty | 21 | 21 |
| Cerulean rival | 22 | 22 |
| S.S. Anne rival | 28 | 28 |
| Lt. Surge | 28 | 28 |
| Champion | 57 | 57 |

The routes still differ by 39 EXP after Greg despite sharing a level. The
first Rare Candy, before Misty, sets both to exactly Lv19 / 4,575 EXP;
their EXP totals then agree throughout the rest of the run. Both finish at
Lv57 / 181,418 EXP. We retain the observed Candy schedule in both calculations.

A focused review of the video at 1:31:00–1:31:41 confirmed the Silph grunt's
order: Cubone (595 EXP), Marowak (849 EXP, then Lv46), Drowzee (699 EXP).
This corrected the transcription's initial use of stored party order;
the source notes and arithmetic were consistent. Details are recorded in
that event's `video_review` metadata.

## Reproduce

Only Python 3.8+ and the standard library are needed. No ROM, Node dependency,
engine simulation, or network access is used to calculate progression:

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_progression --out /tmp/pokeguy-exp
```

The command writes a readable `report.md` plus `report.json` with every foe's
base yield, awarded EXP, cumulative EXP, level before/after, included/excluded
status, and all observation comparisons. Outputs contain input fingerprints
and source revisions; no timestamps or random seeds affect the calculation.
Use `--route` and `--reference` for alternate inputs with the same format.

Regenerate the reference snapshot from the recorded pret revision:

```sh
git clone https://github.com/pret/pokefirered external/pokefirered
git -C external/pokefirered checkout ce6406d8c2eaf46d543c8a2606de0c3cb1951982
PYTHONPATH=src python3 -m pokesim.games.frlg.progression.pret \
  --repo external/pokefirered \
  --route data/runs/pokeguy-leafgreen-15934/events.json \
  --out /tmp/pokeguy-reference.json
```

The importer records hashes of the trainer, party, species, growth-curve,
EXP/item implementation, and Tower script sources. It rejects unsupported
trainer structures and a changed growth formula. It does not build C/C++.

```sh
POKEFIRERED_DIR="$PWD/external/pokefirered" PYTHONPATH=src \
  python3 -m unittest pokesim.games.frlg.progression.test_progression
```

## Calculation and limits

The starter begins at the Lv5 Medium Slow threshold, 135 EXP. For a native
solo participant without Exp. Share or Lucky Egg, trainer EXP is
`floor(floor(base_yield * foe_level / 7) * 150 / 100)`. Floors follow
[pret's EXP implementation](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/battle_script_commands.c#L3113).
Multiple level increases from one award are supported, including reaching
Lv11 exactly at 742 EXP after Liam's Sandshrew in the control.

Rare Candies set total EXP to the next level's threshold, discarding progress
within the current level. Evolution preserves EXP and the family's growth
curve. Captures, escapes, and the old man's demonstration award no starter
EXP. The scripted Tower Marowak defeat awards EXP in both modes; "flee all
wilds" means random encounters, not omitting that required fight.

Every listed fight is assumed won by the starter alone. This audit calculates
progression conditional on those wins; it does not establish that the lower
early levels can win the same battles. It does not calculate EVs, full stats,
move availability, battle win probabilities, money, or item inventory. Those
can build on the ledger once this EXP baseline is accepted. Observed levels
are assertions to compare against and never inputs used to reset EXP.

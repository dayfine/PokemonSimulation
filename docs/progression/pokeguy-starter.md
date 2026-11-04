# Pokeguy's starter: nature and IV reconstruction notes

The independent EXP/EV reconciliation fits **Mild (+Sp. Atk, -Defense)** as
the only nature consistent with the three full in-game stat readings below.
This uses the recorded run's two wild wins and all trainer/scripted defeats,
zero initial EVs, no vitamins, no Pokérus, no Macho Brace, and solo participation.
EVs are awarded per defeated species; they are not divided by the EXP share.
Captures and fleeing give no EVs in FRLG.

Stat order here is **HP / Attack / Defense / Sp. Atk / Sp. Def / Speed**.

| In-game reading | Recorded stats | Accumulated EVs at that knockout |
|---|---|---|
| Wartortle Lv22, after Cerulean rival's Abra | 64 / 38 / 39 / 44 / 44 / 37 | 5 / 0 / 11 / 3 / 0 / 16 |
| Blastoise Lv50, after Route 22 rival's Pidgeot | 156 / 105 / 107 / 121 / 122 / 105 | 29 / 40 / 53 / 37 / 12 / 70 |
| Blastoise Lv54, after Agatha's Arbok | 168 / 114 / 116 / 130 / 131 / 113 | 31 / 50 / 60 / 47 / 17 / 72 |

All three readings are level-up stat displays, so the newly earned EVs have
been included in the stat recalculation. The final cumulative EVs after the
Champion are **31 / 65 / 60 / 57 / 18 / 77** (308 total). Rare Candies add no EVs.

Searching every nature and each IV from 0 through 31 independently per stat,
using all three readings, leaves these IV candidates:

| Stat | IV candidates |
|---|---|
| HP | 28 |
| Attack | 24 or 25 |
| Defense | 16 |
| Sp. Atk | 31 |
| Sp. Def | 21 |
| Speed | 27 |

For HP, `floor((2*base + IV + floor(EV/4))*level/100) + level + 10`.
For other stats, add 5 instead of `level + 10`, then apply the nature's
110/100, 90/100, or 100/100 multiplier with integer truncation.
Use raw summary stats, without battle stages or badge boosts. The yields,
base stats, nature table, and integer order come from the pinned
[species data](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/data/pokemon/species_info.h)
and [`MonGainEVs` / `CalculateMonStats`](https://github.com/pret/pokefirered/blob/ce6406d8c2eaf46d543c8a2606de0c3cb1951982/src/pokemon.c).

A focused inspection of the full video frame at
[2:45](https://www.youtube.com/watch?v=CbfjWuRWH10&t=165) also reads the
overlay as **Mild, 28 / 25 / 16 / 31 / 21 / 27**. This is a separate overlay
claim, not a Summary-screen reading or an input to the candidate search.
It is consistent with the independent result and chooses Attack 25 from the
remaining pair; the three gameplay stat readings alone do not distinguish it.

These are investigation results under the stated route assumptions. The
current progression CLI audits EXP and move membership; it does not yet
provide an EV/IV solver or feed reconstructed stats into live battles.

# Pokeguy FRLG: fight preconditions and two variants

The recorded variant uses the sourced speedrun entry. The prepared variant requires a full rest before six named fights; all other entries remain identical to recorded. These are independent battle contracts, not a newly reconciled continuous route.

A full rest means maximum HP, clear status, and maximum PP on all known moves. It does not add battle items or change level, EXP, IVs, EVs, moves, held items, badges, or strategy. Shopping/pickup planning and propagation of changed outcomes into later entries remain separate work.

Both variants use the latest measured C2 policy for the twelve setup fights. That implementation is pinned to [PR #37](https://github.com/dayfine/PokemonSimulation/pull/37) at `df4fece87aec6d3089a8802e4b6840bd47220549`. Other measurements retain their stated policy and seed. Recorded entry does not mean a replay of Pokeguy's button presses.

Speed-EV diagnostics and Dig substitutions are excluded from these rankings. In particular, Surge retains raw Speed 47. Later C healing candidates retain their tested HP until rerun.

Intervals are recomputed at 95% simultaneous coverage over all 112 measured candidate arms and all sampling looks. Some intervals exceed the original precision target after combining experiments. Close point-estimate ranks are not established differences. All-win samples do not establish a 100% true win probability.

## Required healing stops

| Fight | Recorded HP → prepared HP | Requirement before entry |
|---|---:|---|
| forest-sammy | 16 → 25/25 | Full HP + full PP + clear status. Restore HP and PP before the Forest trainer; a Viridian Center backtrack is allowed. |
| pewter-liam | 5 → 27/27 | Full HP + full PP + clear status. Pewter Center before entering the Gym. |
| brock | 11 → 33/33 | Full HP + full PP + clear status. Pewter Center after Liam and before Brock. |
| mtmoon-josh | 10 → 42/42 | Full HP + full PP + clear status. Route 4 Center before entering Mt. Moon; flee intervening wild encounters. |
| cerulean-rival | 32 → 61/61 | Full HP + full PP + clear status. Cerulean Center after Misty and before the bridge rival. |
| ssanne-rival | 37 → 76/76 | Full HP + full PP + clear status. Accept the 1F Room 6 cabin rest before the rival. |

## Top ten: prepared variant

| Rank | Fight | Tier | Entry HP | Preparation | Win rate | Simultaneous interval |
|---:|---|---|---:|---|---:|---:|
| 1 | surge | B | 79/79 | Recorded entry | 56.2% | 50.9%–61.5% |
| 2 | koga | C | 34/122 | Recorded entry | 70.1% | 64.5%–75.2% |
| 3 | cerulean-rival | B | 61/61 | Full HP + PP | 75.5% | 70.0%–80.6% |
| 4 | ssanne-rival | B | 76/76 | Full HP + PP | 75.7% | 70.2%–80.8% |
| 5 | tower-rival | C | 38/114 | Recorded entry | 90.0% | 83.8%–94.5% |
| 6 | erika | C | 35/137 | Recorded entry | 91.5% | 85.2%–95.8% |
| 7 | lorelei | C | 159/159 | Recorded entry | 94.3% | 87.7%–98.1% |
| 8 | agatha | C | 45/165 | Recorded entry | 95.3% | 88.2%–98.8% |
| 9 | route22-rival | C | 153/153 | Recorded entry | 95.6% | 88.4%–99.0% |
| 10 | champion | C | 171/171 | Recorded entry | 95.6% | 88.4%–99.0% |

## Top ten: recorded variant

| Rank | Fight | Tier | Entry HP | Preparation | Win rate | Simultaneous interval |
|---:|---|---|---:|---|---:|---:|
| 1 | cerulean-rival | B | 32/61 | Recorded entry | 45.2% | 40.0%–50.6% |
| 2 | ssanne-rival | B | 37/76 | Recorded entry | 49.3% | 44.0%–54.6% |
| 3 | brock | A | 11/33 | Recorded entry | 53.8% | 48.5%–59.1% |
| 4 | surge | B | 79/79 | Recorded entry | 56.2% | 50.9%–61.5% |
| 5 | pewter-liam | A | 5/27 | Recorded entry | 65.2% | 59.7%–70.3% |
| 6 | koga | C | 34/122 | Recorded entry | 70.1% | 64.5%–75.2% |
| 7 | mtmoon-josh | B | 10/42 | Recorded entry | 83.5% | 77.8%–88.4% |
| 8 | forest-sammy | B | 16/25 | Recorded entry | 86.5% | 80.6%–91.1% |
| 9 | tower-rival | C | 38/114 | Recorded entry | 90.0% | 83.8%–94.5% |
| 10 | erika | C | 35/137 | Recorded entry | 91.5% | 85.2%–95.8% |

## Contract for every fight

Stats are raw summary stats, before badge boosts, in HP/Atk/Def/SpA/SpD/Spe order. EVs are earned totals; the recorded summary stats remain authoritative until live recalculation. Each trainer ID resolves its full party, moves, items and AI flags in `data/runs/pokeguy-leafgreen-15934/battle-reference.json`. Solo lead, no player switching, and the NPC/engine approximations of the benchmark still apply.

Each entry starts a fresh battle with zero stat stages, no existing volatile conditions or field effects, and the opposing party at full HP and PP. Badge boosts and Torrent are applied by the engine. EXP/EV awards and level-up learning occur after actual knockouts. The lab rival also enables the modeled tutorial behavior.

Shared starter profile: Mild, IVs HP28/Atk25/Def16/SpA31/SpD21/Spe27, male, Torrent. Every bag below is the complete supported battle-consumable bag, not a minimum shopping list. Unlisted battle items are unavailable; no items are silently replenished by resting.

### lab-rival

Opponent: `TRAINER_RIVAL_OAKS_LAB_BULBASAUR` — BULBASAUR Lv5.

SQUIRTLE Lv5; EXP 135; raw stats 20/11/10/12/12/10; earned EVs 0/0/0/0/0/0; status clear; held item none; badges none.

Battle bag: none.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 20/20 | TACKLE: 35, TAIL_WHIP: 30 | 345/360 (95.8%) |
| prepared | 20/20 | TACKLE: 35, TAIL_WHIP: 30 | 345/360 (95.8%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### forest-sammy

Opponent: `TRAINER_BUG_CATCHER_SAMMY` — WEEDLE Lv9.

SQUIRTLE Lv7; EXP 241; raw stats 25/13/13/15/15/12; earned EVs 0/0/0/1/0/2; status clear; held item none; badges none.

Battle bag: antidote ×1.

Player strategy: B. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 16/25 | TACKLE: 28, TAIL_WHIP: 30, BUBBLE: 29 | 830/960 (86.5%) |
| prepared | 25/25 | TACKLE: 35, TAIL_WHIP: 30, BUBBLE: 30 | 158/160 (98.8%) |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 12.

### pewter-liam

Opponent: `TRAINER_CAMPER_LIAM` — GEODUDE Lv10, SANDSHREW Lv11.

SQUIRTLE Lv8; EXP 340; raw stats 27/14/14/16/16/14; earned EVs 0/0/0/1/0/3; status clear; held item none; badges none.

Battle bag: antidote ×1.

Player strategy: A. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 5/27 | TACKLE: 28, TAIL_WHIP: 30, BUBBLE: 25 | 1225/1880 (65.2%) |
| prepared | 27/27 | TACKLE: 35, TAIL_WHIP: 30, BUBBLE: 30 | 120/120 (100.0%) |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 12.

### brock

Opponent: `TRAINER_LEADER_BROCK` — GEODUDE Lv12, ONIX Lv14.

SQUIRTLE Lv11; EXP 742; raw stats 33/18/18/20/21/17; earned EVs 0/0/2/1/0/3; status clear; held item none; badges none.

Battle bag: antidote ×1.

Player strategy: A. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 11/33 | TACKLE: 26, TAIL_WHIP: 30, BUBBLE: 22, WITHDRAW: 40 | 1109/2060 (53.8%) |
| prepared | 33/33 | TACKLE: 35, TAIL_WHIP: 30, BUBBLE: 30, WITHDRAW: 40 | 120/120 (100.0%) |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 12.

### route3-colton

Opponent: `TRAINER_BUG_CATCHER_COLTON` — CATERPIE Lv10, WEEDLE Lv10, CATERPIE Lv10.

SQUIRTLE Lv13; EXP 1286; raw stats 38/20/21/24/24/19; earned EVs 0/0/4/1/0/3; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 6/38 | TACKLE: 26, BUBBLE: 20, WITHDRAW: 40, WATER_GUN: 25 | 100/100 (100.0%) |
| prepared | 6/38 | TACKLE: 26, BUBBLE: 20, WITHDRAW: 40, WATER_GUN: 25 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route3-greg

Opponent: `TRAINER_BUG_CATCHER_GREG` — WEEDLE Lv9, KAKUNA Lv9, CATERPIE Lv9, METAPOD Lv9.

SQUIRTLE Lv14; EXP 1621; raw stats 40/21/22/25/25/20; earned EVs 2/0/4/1/0/4; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 8/40 | TACKLE: 26, BUBBLE: 20, WITHDRAW: 40, WATER_GUN: 22 | 100/100 (100.0%) |
| prepared | 8/40 | TACKLE: 26, BUBBLE: 20, WITHDRAW: 40, WATER_GUN: 22 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route3-james

Opponent: `TRAINER_BUG_CATCHER_JAMES` — CATERPIE Lv11, METAPOD Lv11.

SQUIRTLE Lv15; EXP 2096; raw stats 42/23/24/26/27/22; earned EVs 3/0/8/1/0/5; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 10/42 | TACKLE: 26, BUBBLE: 20, WITHDRAW: 40, WATER_GUN: 18 | 100/100 (100.0%) |
| prepared | 10/42 | TACKLE: 26, BUBBLE: 20, WITHDRAW: 40, WATER_GUN: 18 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### mtmoon-josh

Opponent: `TRAINER_YOUNGSTER_JOSH` — RATTATA Lv10, RATTATA Lv10, ZUBAT Lv10.

SQUIRTLE Lv15; EXP 2389; raw stats 42/23/24/26/27/22; earned EVs 4/0/10/1/0/5; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: B. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 10/42 | TACKLE: 26, BUBBLE: 19, WITHDRAW: 40, WATER_GUN: 16 | 919/1100 (83.5%) |
| prepared | 42/42 | TACKLE: 35, BUBBLE: 30, WITHDRAW: 40, WATER_GUN: 25 | 100/100 (100.0%) |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 11.

### mtmoon-rocket

Opponent: `TRAINER_TEAM_ROCKET_GRUNT` — RATTATA Lv13, ZUBAT Lv13.

WARTORTLE Lv16; EXP 2746; raw stats 49/29/29/33/33/28; earned EVs 4/0/10/1/0/8; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 10/49 | TACKLE: 26, BUBBLE: 19, WITHDRAW: 40, WATER_GUN: 12 | 158/160 (98.8%) |
| prepared | 10/49 | TACKLE: 26, BUBBLE: 19, WITHDRAW: 40, WATER_GUN: 12 | 158/160 (98.8%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### mtmoon-miguel

Opponent: `TRAINER_SUPER_NERD_MIGUEL` — GRIMER Lv12, VOLTORB Lv12, KOFFING Lv12.

WARTORTLE Lv16; EXP 3053; raw stats 49/29/29/33/33/28; earned EVs 4/0/10/1/0/10; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 10/49 | TACKLE: 26, BUBBLE: 19, WITHDRAW: 40, WATER_GUN: 10 | 100/100 (100.0%) |
| prepared | 10/49 | TACKLE: 26, BUBBLE: 19, WITHDRAW: 40, WATER_GUN: 10 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### misty

Opponent: `TRAINER_LEADER_MISTY` — STARYU Lv18, STARMIE Lv21.

WARTORTLE Lv20; EXP 5460; raw stats 59/35/36/40/41/34; earned EVs 5/0/11/1/0/11; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×7.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 54/59 | TACKLE: 26, WATER_GUN: 5, MEGA_KICK: 5, BITE: 25 | 177/180 (98.3%) |
| prepared | 54/59 | TACKLE: 26, WATER_GUN: 5, MEGA_KICK: 5, BITE: 25 | 177/180 (98.3%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### cerulean-rival

Opponent: `TRAINER_RIVAL_CERULEAN_BULBASAUR` — PIDGEOTTO Lv17, ABRA Lv16, RATTATA Lv15, BULBASAUR Lv18.

WARTORTLE Lv21; EXP 6799; raw stats 61/36/37/41/43/35; earned EVs 5/0/11/1/0/14; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: B. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 32/61 | WATER_GUN: 5, MEGA_KICK: 5, BITE: 22, WATER_PULSE: 20 | 932/2060 (45.2%) |
| prepared | 61/61 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 20 | 1148/1520 (75.5%) |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 11.

### bridge-cale

Opponent: `TRAINER_BUG_CATCHER_CALE` — CATERPIE Lv10, WEEDLE Lv10, METAPOD Lv10, KAKUNA Lv10.

WARTORTLE Lv22; EXP 7888; raw stats 64/38/39/44/44/37; earned EVs 5/0/11/3/0/17; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 22/64 | WATER_GUN: 5, MEGA_KICK: 4, BITE: 20, WATER_PULSE: 17 | 100/100 (100.0%) |
| prepared | 22/64 | WATER_GUN: 5, MEGA_KICK: 4, BITE: 20, WATER_PULSE: 17 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-ali

Opponent: `TRAINER_LASS_ALI` — PIDGEY Lv12, ODDISH Lv12, BELLSPROUT Lv12.

WARTORTLE Lv22; EXP 8415; raw stats 64/38/39/44/44/37; earned EVs 6/0/15/3/0/18; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 22/64 | WATER_GUN: 5, MEGA_KICK: 4, BITE: 16, WATER_PULSE: 17 | 100/100 (100.0%) |
| prepared | 22/64 | WATER_GUN: 5, MEGA_KICK: 4, BITE: 16, WATER_PULSE: 17 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-timmy

Opponent: `TRAINER_YOUNGSTER_TIMMY` — SANDSHREW Lv14, EKANS Lv14.

WARTORTLE Lv23; EXP 8971; raw stats 66/39/41/46/46/38; earned EVs 6/1/15/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 14, WATER_PULSE: 17 | 100/100 (100.0%) |
| prepared | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 14, WATER_PULSE: 17 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-reli

Opponent: `TRAINER_LASS_RELI` — NIDORAN_M Lv16, NIDORAN_F Lv16.

WARTORTLE Lv23; EXP 9436; raw stats 66/39/41/46/46/38; earned EVs 6/2/16/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 16 | 100/100 (100.0%) |
| prepared | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 16 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-ethan

Opponent: `TRAINER_CAMPER_ETHAN` — MANKEY Lv18.

WARTORTLE Lv23; EXP 9842; raw stats 66/39/41/46/46/38; earned EVs 7/3/16/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 14 | 100/100 (100.0%) |
| prepared | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 14 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-rocket

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_6` — EKANS Lv15, ZUBAT Lv15.

WARTORTLE Lv23; EXP 10127; raw stats 66/39/41/46/46/38; earned EVs 7/4/16/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 13 | 100/100 (100.0%) |
| prepared | 24/66 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 13 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-wayne

Opponent: `TRAINER_HIKER_WAYNE` — ONIX Lv17.

WARTORTLE Lv24; EXP 10497; raw stats 69/41/43/47/48/40; earned EVs 7/5/16/4/0/20; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 11 | 100/100 (100.0%) |
| prepared | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 11 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-kelsey

Opponent: `TRAINER_PICNICKER_KELSEY` — NIDORAN_M Lv15, NIDORAN_F Lv15.

WARTORTLE Lv24; EXP 10890; raw stats 69/41/43/47/48/40; earned EVs 7/5/17/4/0/20; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 10 | 100/100 (100.0%) |
| prepared | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 10 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-flint

Opponent: `TRAINER_CAMPER_FLINT` — RATTATA Lv14, EKANS Lv14.

WARTORTLE Lv24; EXP 11271; raw stats 69/41/43/47/48/40; earned EVs 8/6/17/4/0/20; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 8 | 100/100 (100.0%) |
| prepared | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 8 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-haley

Opponent: `TRAINER_LASS_HALEY` — ODDISH Lv13, PIDGEY Lv13, ODDISH Lv13.

WARTORTLE Lv24; EXP 11628; raw stats 69/41/43/47/48/40; earned EVs 8/7/17/4/0/21; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, potion ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 6 | 100/100 (100.0%) |
| prepared | 27/69 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 13, WATER_PULSE: 6 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### cerulean-dig-rocket

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_5` — MACHOP Lv17, DROWZEE Lv17.

WARTORTLE Lv25; EXP 12213; raw stats 72/43/45/49/50/42; earned EVs 8/7/17/6/0/22; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, potion ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/72 | WATER_GUN: 5, MEGA_KICK: 5, BITE: 12, WATER_PULSE: 6 | 100/100 (100.0%) |
| prepared | 27/72 | WATER_GUN: 5, MEGA_KICK: 5, BITE: 12, WATER_PULSE: 6 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route6-jeff

Opponent: `TRAINER_CAMPER_JEFF` — SPEAROW Lv16, RATICATE Lv16.

WARTORTLE Lv25; EXP 12902; raw stats 72/43/45/49/50/42; earned EVs 8/8/17/6/1/22; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 21/72 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 12, WATER_PULSE: 5 | 100/100 (100.0%) |
| prepared | 21/72 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 12, WATER_PULSE: 5 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### ssanne-rival

Opponent: `TRAINER_RIVAL_SS_ANNE_BULBASAUR` — PIDGEOTTO Lv19, RATICATE Lv16, KADABRA Lv18, IVYSAUR Lv20.

WARTORTLE Lv27; EXP 15244; raw stats 76/46/47/52/53/45; earned EVs 8/8/17/6/1/25; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 37/76 | WATER_GUN: 5, MEGA_KICK: 3, BITE: 12, WATER_PULSE: 3 | 1025/2080 (49.3%) |
| prepared | 76/76 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 20 | 1136/1500 (75.7%) |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 11.

### vermilion-tucker

Opponent: `TRAINER_GENTLEMAN_TUCKER` — PIKACHU Lv23.

WARTORTLE Lv28; EXP 17261; raw stats 79/47/49/55/55/47; earned EVs 8/8/17/9/2/29; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 79/79 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 20 | 100/100 (100.0%) |
| prepared | 79/79 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 20 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### surge

Opponent: `TRAINER_LEADER_LT_SURGE` — VOLTORB Lv21, PIKACHU Lv18, RAICHU Lv24.

WARTORTLE Lv28; EXP 17664; raw stats 79/47/49/55/55/47; earned EVs 8/8/17/9/2/31; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `B:solo-recovery/1`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 79/79 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 19 | 1147/2040 (56.2%) |
| prepared | 79/79 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 19 | 1147/2040 (56.2%) |

Result source: recorded — preparation control, seed 11; prepared — preparation control, seed 11.

### route9-alicia

Opponent: `TRAINER_PICNICKER_ALICIA` — ODDISH Lv18, BELLSPROUT Lv18, ODDISH Lv18, BELLSPROUT Lv18.

WARTORTLE Lv28; EXP 19069; raw stats 79/47/49/55/55/47; earned EVs 8/8/17/9/2/37; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 43/79 | WATER_GUN: 25, MEGA_KICK: 4, BITE: 25, WATER_PULSE: 16 | 100/100 (100.0%) |
| prepared | 43/79 | WATER_GUN: 25, MEGA_KICK: 4, BITE: 25, WATER_PULSE: 16 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route9-conner

Opponent: `TRAINER_BUG_CATCHER_CONNER` — CATERPIE Lv20, WEEDLE Lv20, VENONAT Lv20.

WARTORTLE Lv29; EXP 20317; raw stats 81/49/51/57/57/49; earned EVs 8/10/17/11/2/37; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 45/81 | WATER_GUN: 25, MEGA_KICK: 2, BITE: 23, WATER_PULSE: 16 | 100/100 (100.0%) |
| prepared | 45/81 | WATER_GUN: 25, MEGA_KICK: 2, BITE: 23, WATER_PULSE: 16 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-ashton

Opponent: `TRAINER_POKEMANIAC_ASHTON` — CUBONE Lv23, SLOWPOKE Lv23.

WARTORTLE Lv29; EXP 21086; raw stats 81/49/51/57/57/49; earned EVs 9/10/17/11/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 45/81 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 20 | 100/100 (100.0%) |
| prepared | 45/81 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 25, WATER_PULSE: 20 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-winston

Opponent: `TRAINER_POKEMANIAC_WINSTON` — SLOWPOKE Lv25.

WARTORTLE Lv30; EXP 22000; raw stats 84/50/53/58/59/50; earned EVs 10/10/18/11/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 42/84 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 23, WATER_PULSE: 19 | 100/100 (100.0%) |
| prepared | 42/84 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 23, WATER_PULSE: 19 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-martha

Opponent: `TRAINER_PICNICKER_MARTHA` — ODDISH Lv22, BULBASAUR Lv22.

WARTORTLE Lv30; EXP 22529; raw stats 84/50/53/58/59/50; earned EVs 11/10/18/11/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 39/84 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 21, WATER_PULSE: 19 | 215/220 (97.7%) |
| prepared | 39/84 | WATER_GUN: 25, MEGA_KICK: 5, BITE: 21, WATER_PULSE: 19 | 215/220 (97.7%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-allen

Opponent: `TRAINER_HIKER_ALLEN` — GEODUDE Lv25.

WARTORTLE Lv30; EXP 23197; raw stats 84/50/53/58/59/50; earned EVs 11/10/18/13/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 39/84 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 21, WATER_PULSE: 19 | 100/100 (100.0%) |
| prepared | 39/84 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 21, WATER_PULSE: 19 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-oliver

Opponent: `TRAINER_HIKER_OLIVER` — ONIX Lv20, ONIX Lv20, GEODUDE Lv20.

WARTORTLE Lv30; EXP 23657; raw stats 84/50/53/58/59/50; earned EVs 11/10/19/13/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 39/84 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 21, WATER_PULSE: 18 | 100/100 (100.0%) |
| prepared | 39/84 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 21, WATER_PULSE: 18 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-sofia

Opponent: `TRAINER_PICNICKER_SOFIA` — JIGGLYPUFF Lv21, PIDGEY Lv21, MEOWTH Lv21.

WARTORTLE Lv31; EXP 24948; raw stats 86/52/54/60/61/52; earned EVs 11/10/22/13/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 41/86 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 18, WATER_PULSE: 17 | 100/100 (100.0%) |
| prepared | 41/86 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 18, WATER_PULSE: 17 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-dudley

Opponent: `TRAINER_HIKER_DUDLEY` — GEODUDE Lv21, GEODUDE Lv21, GRAVELER Lv21.

WARTORTLE Lv31; EXP 25847; raw stats 86/52/54/60/61/52; earned EVs 13/10/22/13/3/40; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 41/86 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 18, WATER_PULSE: 14 | 100/100 (100.0%) |
| prepared | 41/86 | WATER_GUN: 25, MEGA_KICK: 3, BITE: 18, WATER_PULSE: 14 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-dana

Opponent: `TRAINER_PICNICKER_DANA` — MEOWTH Lv20, ODDISH Lv20, PIDGEY Lv20.

WARTORTLE Lv32; EXP 27224; raw stats 89/53/56/62/62/53; earned EVs 13/10/26/13/3/40; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 44/89 | WATER_GUN: 24, MEGA_KICK: 3, BITE: 16, WATER_PULSE: 14 | 100/100 (100.0%) |
| prepared | 44/89 | WATER_GUN: 24, MEGA_KICK: 3, BITE: 16, WATER_PULSE: 14 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route8-rich

Opponent: `TRAINER_GAMER_RICH` — GROWLITHE Lv24, VULPIX Lv24.

WARTORTLE Lv32; EXP 28087; raw stats 89/53/56/62/62/53; earned EVs 13/10/26/14/3/42; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 39/89 | WATER_GUN: 24, MEGA_KICK: 2, BITE: 14, WATER_PULSE: 14 | 100/100 (100.0%) |
| prepared | 39/89 | WATER_GUN: 24, MEGA_KICK: 2, BITE: 14, WATER_PULSE: 14 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-poster-guard

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_7` — RATICATE Lv20, ZUBAT Lv20.

WARTORTLE Lv32; EXP 28879; raw stats 89/53/56/62/62/53; earned EVs 13/11/26/14/3/43; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 39/89 | WATER_GUN: 22, MEGA_KICK: 2, BITE: 14, WATER_PULSE: 14 | 100/100 (100.0%) |
| prepared | 39/89 | WATER_GUN: 22, MEGA_KICK: 2, BITE: 14, WATER_PULSE: 14 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-key-grunt

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_18` — KOFFING Lv21, ZUBAT Lv21.

WARTORTLE Lv32; EXP 29606; raw stats 89/53/56/62/62/53; earned EVs 13/11/26/14/3/46; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 39/89 | WATER_GUN: 22, MEGA_KICK: 1, BITE: 14, WATER_PULSE: 13 | 100/100 (100.0%) |
| prepared | 39/89 | WATER_GUN: 22, MEGA_KICK: 1, BITE: 14, WATER_PULSE: 13 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-left-guard

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_16` — SANDSHREW Lv23, EKANS Lv23, SANDSLASH Lv23.

WARTORTLE Lv33; EXP 30362; raw stats 92/55/58/64/64/55; earned EVs 13/11/27/14/3/47; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 42/92 | WATER_GUN: 22, MEGA_KICK: 1, BITE: 14, WATER_PULSE: 11 | 100/100 (100.0%) |
| prepared | 42/92 | WATER_GUN: 22, MEGA_KICK: 1, BITE: 14, WATER_PULSE: 11 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-right-guard

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_17` — EKANS Lv23, SANDSHREW Lv23, ARBOK Lv23.

WARTORTLE Lv33; EXP 31925; raw stats 92/55/58/64/64/55; earned EVs 13/12/30/14/3/47; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 42/92 | WATER_GUN: 21, MEGA_KICK: 1, BITE: 13, WATER_PULSE: 10 | 100/100 (100.0%) |
| prepared | 42/92 | WATER_GUN: 21, MEGA_KICK: 1, BITE: 13, WATER_PULSE: 10 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-giovanni

Opponent: `TRAINER_BOSS_GIOVANNI` — ONIX Lv25, RHYHORN Lv24, KANGASKHAN Lv29.

BLASTOISE Lv36; EXP 40007; raw stats 114/74/76/85/88/74; earned EVs 13/15/31/14/3/47; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 38/114 | WATER_GUN: 20, MEGA_KICK: 1, BITE: 12, WATER_PULSE: 8 | 100/100 (100.0%) |
| prepared | 38/114 | WATER_GUN: 20, MEGA_KICK: 1, BITE: 12, WATER_PULSE: 8 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rival

Opponent: `TRAINER_RIVAL_POKEMON_TOWER_BULBASAUR` — PIDGEOTTO Lv25, GYARADOS Lv23, GROWLITHE Lv22, KADABRA Lv20, IVYSAUR Lv25.

BLASTOISE Lv36; EXP 42364; raw stats 114/74/76/85/88/74; earned EVs 15/15/33/14/3/47; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×21, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false, "torrent_power": true}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 38/114 | WATER_GUN: 18, MEGA_KICK: 1, BITE: 12, WATER_PULSE: 6 | 630/700 (90.0%) |
| prepared | 38/114 | WATER_GUN: 18, MEGA_KICK: 1, BITE: 12, WATER_PULSE: 6 | 630/700 (90.0%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### tower-tammy

Opponent: `TRAINER_CHANNELER_TAMMY` — HAUNTER Lv23.

BLASTOISE Lv37; EXP 45826; raw stats 116/77/78/88/90/77; earned EVs 15/18/33/17/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/116 | WATER_GUN: 16, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 5 | 100/100 (100.0%) |
| prepared | 24/116 | WATER_GUN: 16, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 5 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-jennifer

Opponent: `TRAINER_CHANNELER_JENNIFER` — GASTLY Lv24.

BLASTOISE Lv37; EXP 46447; raw stats 116/77/78/88/90/77; earned EVs 15/18/33/19/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/116 | WATER_GUN: 15, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 5 | 100/100 (100.0%) |
| prepared | 24/116 | WATER_GUN: 15, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 5 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-emilia

Opponent: `TRAINER_CHANNELER_EMILIA` — GASTLY Lv24.

BLASTOISE Lv37; EXP 46934; raw stats 116/77/78/88/90/77; earned EVs 15/18/33/20/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/116 | WATER_GUN: 14, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 5 | 100/100 (100.0%) |
| prepared | 24/116 | WATER_GUN: 14, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 5 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rocket1

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_19` — ZUBAT Lv25, ZUBAT Lv25, GOLBAT Lv25.

BLASTOISE Lv38; EXP 47952; raw stats 119/79/81/91/93/79; earned EVs 15/18/35/21/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/119 | WATER_GUN: 13, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 4 | 100/100 (100.0%) |
| prepared | 27/119 | WATER_GUN: 13, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 4 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rocket2

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_20` — KOFFING Lv26, DROWZEE Lv26.

BLASTOISE Lv38; EXP 49443; raw stats 119/79/81/91/93/79; earned EVs 15/18/35/21/4/53; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/119 | WATER_GUN: 11, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 3 | 100/100 (100.0%) |
| prepared | 27/119 | WATER_GUN: 11, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 3 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rocket3

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_21` — ZUBAT Lv23, RATTATA Lv23, RATICATE Lv23, ZUBAT Lv23.

BLASTOISE Lv38; EXP 50644; raw stats 119/79/81/91/93/79; earned EVs 15/18/36/21/5/53; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 27/119 | WATER_GUN: 10, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 2 | 100/100 (100.0%) |
| prepared | 27/119 | WATER_GUN: 10, MEGA_KICK: 1, BITE: 9, WATER_PULSE: 2 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### fuchsia-kirk

Opponent: `TRAINER_JUGGLER_KIRK` — DROWZEE Lv31, DROWZEE Lv31, KADABRA Lv31, DROWZEE Lv31.

BLASTOISE Lv38; EXP 52025; raw stats 119/79/81/91/93/79; earned EVs 15/18/36/21/5/58; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 31/119 | MEGA_KICK: 1, BITE: 6, WATER_PULSE: 2, SURF: 15 | 100/100 (100.0%) |
| prepared | 31/119 | MEGA_KICK: 1, BITE: 6, WATER_PULSE: 2, SURF: 15 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### koga

Opponent: `TRAINER_LEADER_KOGA` — KOFFING Lv37, MUK Lv39, KOFFING Lv37, WEEZING Lv43.

BLASTOISE Lv39; EXP 55016; raw stats 122/81/82/93/95/81; earned EVs 15/18/36/23/8/58; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": false, "outspeed": true, "spa": 1, "target_torrent": false}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 34/122 | MEGA_KICK: 1, BITE: 6, WATER_PULSE: 2, SURF: 11 | 1191/1700 (70.1%) |
| prepared | 34/122 | MEGA_KICK: 1, BITE: 6, WATER_PULSE: 2, SURF: 11 | 1191/1700 (70.1%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### blaine

Opponent: `TRAINER_LEADER_BLAINE` — GROWLITHE Lv42, PONYTA Lv40, RAPIDASH Lv42, ARCANINE Lv47.

BLASTOISE Lv40; EXP 59726; raw stats 126/83/85/95/98/83; earned EVs 16/19/40/23/8/58; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 24/126 | MEGA_KICK: 1, BITE: 5, WATER_PULSE: 2, SURF: 5 | 100/100 (100.0%) |
| prepared | 24/126 | MEGA_KICK: 1, BITE: 5, WATER_PULSE: 2, SURF: 5 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### celadon-tamia

Opponent: `TRAINER_BEAUTY_TAMIA` — BELLSPROUT Lv24, BELLSPROUT Lv24.

BLASTOISE Lv41; EXP 65720; raw stats 128/85/87/97/100/85; earned EVs 16/22/40/23/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 26/128 | MEGA_KICK: 1, BITE: 5, WATER_PULSE: 2, SURF: 1 | 100/100 (100.0%) |
| prepared | 26/128 | MEGA_KICK: 1, BITE: 5, WATER_PULSE: 2, SURF: 1 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### celadon-lori

Opponent: `TRAINER_BEAUTY_LORI` — EXEGGCUTE Lv24.

BLASTOISE Lv44; EXP 77440; raw stats 137/91/93/104/107/92; earned EVs 16/24/40/23/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 35/137 | BITE: 3, WATER_PULSE: 2, SURF: 1, BLIZZARD: 5 | 100/100 (100.0%) |
| prepared | 35/137 | BITE: 3, WATER_PULSE: 2, SURF: 1, BLIZZARD: 5 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### erika

Opponent: `TRAINER_LEADER_ERIKA` — VICTREEBEL Lv29, TANGELA Lv24, VILEPLUME Lv29.

BLASTOISE Lv44; EXP 77944; raw stats 137/91/93/104/107/92; earned EVs 16/24/41/23/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 1, "target_torrent": false}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 35/137 | BITE: 2, WATER_PULSE: 2, SURF: 1, BLIZZARD: 5 | 567/620 (91.5%) |
| prepared | 35/137 | BITE: 2, WATER_PULSE: 2, SURF: 1, BLIZZARD: 5 | 567/620 (91.5%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### silph-rival

Opponent: `TRAINER_RIVAL_SILPH_BULBASAUR` — PIDGEOT Lv37, GYARADOS Lv38, GROWLITHE Lv35, ALAKAZAM Lv35, VENUSAUR Lv40.

BLASTOISE Lv44; EXP 81126; raw stats 137/91/93/104/107/92; earned EVs 16/27/42/26/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 85/137 | BITE: 25, WATER_PULSE: 20, SURF: 15, BLIZZARD: 5 | 289/300 (96.3%) |
| prepared | 85/137 | BITE: 25, WATER_PULSE: 20, SURF: 15, BLIZZARD: 5 | 289/300 (96.3%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### silph-boardroom-grunt

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_41` — CUBONE Lv32, DROWZEE Lv32, MAROWAK Lv32.

BLASTOISE Lv45; EXP 88089; raw stats 140/93/95/107/109/94; earned EVs 16/30/42/31/9/64; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 30/140 | BITE: 24, WATER_PULSE: 19, SURF: 14, BLIZZARD: 3 | 100/100 (100.0%) |
| prepared | 30/140 | BITE: 24, WATER_PULSE: 19, SURF: 14, BLIZZARD: 3 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### silph-giovanni

Opponent: `TRAINER_BOSS_GIOVANNI_2` — NIDORINO Lv37, KANGASKHAN Lv35, RHYHORN Lv37, NIDOQUEEN Lv41.

BLASTOISE Lv46; EXP 90232; raw stats 143/96/98/110/112/96; earned EVs 16/30/45/31/10/64; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 1, "target_torrent": false}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 33/143 | BITE: 23, WATER_PULSE: 17, SURF: 14, BLIZZARD: 3 | 100/100 (100.0%) |
| prepared | 33/143 | BITE: 23, WATER_PULSE: 17, SURF: 14, BLIZZARD: 3 | 100/100 (100.0%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### sabrina

Opponent: `TRAINER_LEADER_SABRINA` — KADABRA Lv38, MR_MIME Lv37, VENOMOTH Lv38, ALAKAZAM Lv43.

BLASTOISE Lv46; EXP 95251; raw stats 143/96/98/110/112/96; earned EVs 21/32/46/31/10/64; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 0, "target_torrent": false}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 33/143 | BITE: 23, WATER_PULSE: 16, SURF: 11, BLIZZARD: 3 | 177/180 (98.3%) |
| prepared | 33/143 | BITE: 23, WATER_PULSE: 16, SURF: 11, BLIZZARD: 3 | 177/180 (98.3%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### viridian-takashi

Opponent: `TRAINER_BLACK_BELT_TAKASHI` — MACHOKE Lv38, MACHOP Lv38, MACHOKE Lv38.

BLASTOISE Lv47; EXP 100344; raw stats 146/98/99/113/114/98; earned EVs 21/32/46/37/12/65; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 25/146 | BITE: 23, WATER_PULSE: 16, SURF: 7, BLIZZARD: 3 | 139/140 (99.3%) |
| prepared | 25/146 | BITE: 23, WATER_PULSE: 16, SURF: 7, BLIZZARD: 3 | 139/140 (99.3%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### viridian-warren

Opponent: `TRAINER_COOLTRAINER_WARREN` — MAROWAK Lv37, MAROWAK Lv37, RHYHORN Lv38, NIDORINA Lv39, NIDOQUEEN Lv39.

BLASTOISE Lv48; EXP 103435; raw stats 149/101/101/115/117/100; earned EVs 21/37/46/37/12/65; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 28/149 | BITE: 23, WATER_PULSE: 16, SURF: 4, BLIZZARD: 3 | 100/100 (100.0%) |
| prepared | 28/149 | BITE: 23, WATER_PULSE: 16, SURF: 4, BLIZZARD: 3 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### giovanni-gym

Opponent: `TRAINER_LEADER_GIOVANNI` — RHYHORN Lv45, DUGTRIO Lv42, NIDOQUEEN Lv44, NIDOKING Lv45, RHYHORN Lv50.

BLASTOISE Lv48; EXP 109093; raw stats 149/101/101/115/117/100; earned EVs 26/37/51/37/12/65; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 28/149 | BITE: 23, WATER_PULSE: 11, SURF: 4, BLIZZARD: 3 | 100/100 (100.0%) |
| prepared | 28/149 | BITE: 23, WATER_PULSE: 11, SURF: 4, BLIZZARD: 3 | 100/100 (100.0%) |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route22-rival

Opponent: `TRAINER_RIVAL_ROUTE22_LATE_BULBASAUR` — PIDGEOT Lv47, RHYHORN Lv45, GYARADOS Lv45, GROWLITHE Lv45, ALAKAZAM Lv47, VENUSAUR Lv53.

BLASTOISE Lv49; EXP 116923; raw stats 153/103/105/117/119/102; earned EVs 29/40/53/37/12/67; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false}`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 153/153 | BITE: 23, WATER_PULSE: 6, SURF: 4, BLIZZARD: 3 | 325/340 (95.6%) |
| prepared | 153/153 | BITE: 23, WATER_PULSE: 6, SURF: 4, BLIZZARD: 3 | 325/340 (95.6%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### lorelei

Opponent: `TRAINER_ELITE_FOUR_LORELEI` — DEWGONG Lv52, CLOYSTER Lv51, SLOWBRO Lv52, JYNX Lv54, LAPRAS Lv54.

BLASTOISE Lv51; EXP 127126; raw stats 159/107/108/123/124/107; earned EVs 29/43/54/42/13/70; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×13, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×15, xspeed ×4.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 4, "target_torrent": false}`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 159/159 | BITE: 25, SURF: 15, BLIZZARD: 5, STRENGTH: 15 | 415/440 (94.3%) |
| prepared | 159/159 | BITE: 25, SURF: 15, BLIZZARD: 5, STRENGTH: 15 | 415/440 (94.3%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### bruno

Opponent: `TRAINER_ELITE_FOUR_BRUNO` — ONIX Lv51, HITMONCHAN Lv53, HITMONLEE Lv53, ONIX Lv54, MACHAMP Lv56.

BLASTOISE Lv52; EXP 137248; raw stats 162/109/111/126/126/109; earned EVs 31/43/58/44/15/70; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×12, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×11, xspeed ×4.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": true}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 130/162 | BITE: 19, SURF: 14, BLIZZARD: 5, STRENGTH: 15 | 307/320 (95.9%) |
| prepared | 130/162 | BITE: 19, SURF: 14, BLIZZARD: 5, STRENGTH: 15 | 307/320 (95.9%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### agatha

Opponent: `TRAINER_ELITE_FOUR_AGATHA` — GENGAR Lv54, GOLBAT Lv54, HAUNTER Lv53, ARBOK Lv56, GENGAR Lv58.

BLASTOISE Lv53; EXP 145160; raw stats 165/112/113/128/129/111; earned EVs 31/48/60/44/17/70; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×12, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×9, xspeed ×3.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 1, "target_torrent": false, "torrent_power": true}`.
Full-heal comparison pending: retain this tested HP/setup condition for both variants.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 45/165 | BITE: 19, SURF: 9, BLIZZARD: 5, STRENGTH: 15 | 343/360 (95.3%) |
| prepared | 45/165 | BITE: 19, SURF: 9, BLIZZARD: 5, STRENGTH: 15 | 343/360 (95.3%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### lance

Opponent: `TRAINER_ELITE_FOUR_LANCE` — GYARADOS Lv56, DRAGONAIR Lv54, DRAGONAIR Lv54, AERODACTYL Lv58, DRAGONITE Lv60.

BLASTOISE Lv54; EXP 154891; raw stats 168/114/116/130/131/113; earned EVs 31/50/60/52/17/72; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×11, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×8, xspeed ×2.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 3, "target_torrent": false}`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 168/168 | BITE: 19, SURF: 4, BLIZZARD: 5, STRENGTH: 15 | 119/120 (99.2%) |
| prepared | 168/168 | BITE: 19, SURF: 4, BLIZZARD: 5, STRENGTH: 15 | 119/120 (99.2%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### champion

Opponent: `TRAINER_CHAMPION_FIRST_BULBASAUR` — PIDGEOT Lv59, ALAKAZAM Lv57, RHYDON Lv59, GYARADOS Lv59, ARCANINE Lv61, VENUSAUR Lv63.

BLASTOISE Lv55; EXP 166100; raw stats 171/117/118/134/134/115; earned EVs 31/59/60/52/17/74; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, fullrestore ×9, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×2, xspecial ×7, xspeed ×2.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.
Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false}`.

| Variant | Entry HP | Exact moves and remaining PP | Win sample |
|---|---:|---|---:|
| recorded | 171/171 | BITE: 25, SURF: 13, BLIZZARD: 5, STRENGTH: 15 | 325/340 (95.6%) |
| prepared | 171/171 | BITE: 25, SURF: 13, BLIZZARD: 5, STRENGTH: 15 | 325/340 (95.6%) |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

## Reproduce

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_conditions
```

The preparation plan contains pinned C2 and supplemental rest counters. The latter used seed 12: Sammy 158/160, Liam 120/120, Brock 120/120. No top-ten reordering is presented as new simulation. The other results come from the existing original and preparation benchmark reports.

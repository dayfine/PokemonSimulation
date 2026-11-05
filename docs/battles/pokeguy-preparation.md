# FRLG: preparation outside the speedrun

Pokeguy's recorded low-HP entries are the speedrun case. These experiments keep
that case and add alternatives for a run that can spend time healing, buying
supplies, or teaching Dig. They do not replace the recorded-entry rankings.

## What changes in each experiment

The player uses the same B recovery policy throughout; it has no X-item setup.
Without recovery items, its choices reduce to attacks. NPC AI, starter profile,
level, EXP, and other inputs remain fixed except for the named intervention.

- `recorded`: the original entry HP, PP, and bag, with a fresh seed.
- `full-hp`: restore HP only; retain recorded PP and bag.
- `carry-potion`: add one Potion, leaving entry HP unchanged.
- `pre-potion`: spend one extra Potion before entering; restore at most 20 HP,
  without adding a Potion to the battle bag.
- `full-hp-carry-potion`: restore HP and add one carried Potion.
- `full-rest`: restore HP, status and all known moves' PP, as at a Center.
- `dig`: replace Water Gun with a fresh 10-PP Dig; retain Mega Kick and Bite.
- `speed`: change only Speed EVs and resulting raw Speed at fixed EXP. This is
  a diagnostic of the threshold, **not a planned legal training route**.
- `dig-speed`: combine those two interventions.

HP changes automatically affect Torrent in the battle engine. Full-HP Brock
therefore does not retain the low-HP damage bonus. Dig uses Gen 3 mechanics,
including its two turns. The controller chooses attacks using expected turns
to KO; this is not an optimized move-by-move battle plan.

## Results

Adaptive sampling used seed 11, 30340 trials over 28 variants, and a maximum of 3,000 trials each. Every case met the total interval-width target of 10 percentage points; none reached the cap or turn limit. The intervals have 95% simultaneous coverage over this experiment and all sampling looks, conditional on the model. They do not cover the earlier benchmark or model inaccuracies.

A result of 100/100 means no observed loss, with an interval of 91.2%–100%; it does not prove certainty. Fresh recorded controls differ from the historical point estimates because this is a new seed. Full rest changes PP as well as HP.

[Machine-readable results](pokeguy-preparation.json).

### Pewter preparation

| Fight | Variant | HP | Speed | Wins/trials | Win rate | Interval |
|---|---|---:|---:|---:|---:|---:|
| Liam | recorded | 5/27 | 14 | 1225/1880 | 65.2% | 60.1%–70.0% |
| Liam | full-hp | 27/27 | 14 | 100/100 | 100.0% | 91.2%–100.0% |
| Liam | carry-potion | 5/27 | 14 | 158/160 | 98.8% | 90.9%–100.0% |
| Liam | pre-potion | 25/27 | 14 | 177/180 | 98.3% | 90.7%–100.0% |
| Liam | full-hp-carry-potion | 27/27 | 14 | 100/100 | 100.0% | 91.2%–100.0% |
| Brock | recorded | 11/33 | 17 | 1109/2060 | 53.8% | 48.8%–58.8% |
| Brock | full-hp | 33/33 | 17 | 100/100 | 100.0% | 91.2%–100.0% |
| Brock | carry-potion | 11/33 | 17 | 100/100 | 100.0% | 91.2%–100.0% |
| Brock | pre-potion | 31/33 | 17 | 100/100 | 100.0% | 91.2%–100.0% |
| Brock | full-hp-carry-potion | 33/33 | 17 | 100/100 | 100.0% | 91.2%–100.0% |

### Rival and Surge alternatives

| Fight | Variant | HP | Speed | Wins/trials | Win rate | Interval |
|---|---|---:|---:|---:|---:|---:|
| Cerulean rival | recorded | 32/61 | 35 | 932/2060 | 45.2% | 40.3%–50.3% |
| Cerulean rival | full-rest | 61/61 | 35 | 1148/1520 | 75.5% | 70.3%–80.3% |
| S.S. Anne rival | recorded | 37/76 | 45 | 1025/2080 | 49.3% | 44.3%–54.3% |
| S.S. Anne rival | full-hp | 76/76 | 45 | 1178/1600 | 73.6% | 68.5%–78.4% |
| S.S. Anne rival | full-rest | 76/76 | 45 | 1136/1500 | 75.7% | 70.5%–80.5% |
| S.S. Anne rival | dig | 37/76 | 45 | 1085/2060 | 52.7% | 47.7%–57.6% |
| S.S. Anne rival | speed | 37/76 | 48 | 1081/2060 | 52.5% | 47.5%–57.5% |
| S.S. Anne rival | dig-speed | 37/76 | 48 | 1144/2040 | 56.1% | 51.0%–61.0% |
| Surge | recorded | 79/79 | 47 | 1147/2040 | 56.2% | 51.2%–61.2% |
| Surge | dig | 79/79 | 47 | 1098/2060 | 53.3% | 48.3%–58.3% |
| Surge | speed | 79/79 | 54 | 1127/1480 | 76.1% | 70.9%–80.9% |
| Surge | dig-speed | 79/79 | 54 | 1178/1620 | 72.7% | 67.5%–77.5% |

### Forest and Mt. Moon preparation

| Fight | Variant | HP | Speed | Wins/trials | Win rate | Interval |
|---|---|---:|---:|---:|---:|---:|
| Forest Sammy | recorded | 16/25 | 12 | 830/960 | 86.5% | 81.0%–90.9% |
| Forest Sammy | full-hp | 25/25 | 12 | 177/180 | 98.3% | 90.7%–100.0% |
| Forest Sammy | carry-potion | 16/25 | 12 | 119/120 | 99.2% | 90.1%–100.0% |
| Forest Sammy | speed | 16/25 | 15 | 769/880 | 87.4% | 81.8%–91.8% |
| Mt. Moon Josh | recorded | 10/42 | 22 | 919/1100 | 83.5% | 78.1%–88.1% |
| Mt. Moon Josh | full-rest | 42/42 | 22 | 100/100 | 100.0% | 91.2%–100.0% |

For Liam and Brock, full HP had no observed losses without a Potion. With full HP and a backup Potion, Brock never used it; Liam used it in 35% of trials, without a demonstrated improvement over full HP alone. At their recorded low HP, the carry-potion variants used one Potion in every trial.

Healing or a full rest produced substantial improvements in the tested early fights. Surge benefited from the Speed diagnostic. Dig alone did not demonstrate an improvement with this policy; its intervals overlap the recorded controls. In Gen 3 Dig has 60 power, takes two turns, and leaves Wartortle Water-type. A policy that plans around the underground turn may behave differently.


## Where healing is sensible on a slower route

The reconciled ledger has **62 of 69 fights starting below maximum HP**.
That alone does not establish that all 62 need intervention. The recorded
states, including later bosses, remain available in the
[complete starting-state ledger](../progression/pokeguy-states.md).

The first priorities are Forest Sammy (16/25), Liam (5/27), Brock (11/33),
Mt. Moon Josh (10/42), Cerulean rival (32/61), and S.S. Anne rival (37/76).
The table above measures preparation alternatives for these fights. Surge
already starts at 79/79 HP, so entry healing cannot solve its difficulty.

For subsequent full-HP tests, prioritize these bosses. Their listed HP comes
from the recorded ledger; **full-HP win rates have not yet been measured**.

| Fight | Recorded HP | Practical healing opportunity |
|---|---:|---|
| Pokémon Tower rival | 38/114 | Lavender Center before entering the Tower |
| Koga | 34/122 | Fuchsia Center before the Gym |
| Erika | 35/137 | Celadon Center before the Gym |
| Silph rival | 85/137 | Saffron Center before the Silph sequence |
| Silph Giovanni | 33/143 | Leave and heal, or separately plan a Silph healing stop |
| Sabrina | 33/143 | Saffron Center before the Gym |
| Blaine | 24/126 | Cinnabar Center before the Gym |
| Viridian Gym Giovanni | 28/149 | Viridian Center before the Gym |

Several of these starts activate Torrent. A healthier entry can improve setup
survival while also losing a damage threshold, so the C plan must be retested
together with HP. Any healing before Bruno (130/162) and Agatha (45/165) must
come from the bag inside the League; evaluate that alongside setup and PP requirements.
Do not replace those states with full HP and reuse their old win rates.

Many ordinary Route 3, Nugget Bridge, Route 25, Tower, and Viridian Gym trainers
already had all-win baseline samples despite low entry HP. They are lower
priorities than the measured risky fights; an all-win sample is not a guarantee.
Healing at a route boundary changes subsequent HP and PP, so these independent
experiments also do not establish a new continuous-route completion probability.

## Availability and remaining policy limits

Potions are available before Brock: the starting PC contains one, the Route 1
Mart clerk gives one, and Viridian/Pewter Marts sell them. They were absent
from these recorded early battle bags. A Pewter Center stop can restore HP
without consuming a Potion. A single pre-battle Potion leaves Liam at 25/27
and Brock at 31/33; neither is identical to a full heal.

The S.S. Anne woman in 1F Room 6 offers a free full-party rest before the rival.
Pokeguy used that rest after the rival. Cerulean Center is also accessible
before the bridge rival. TM28 comes from the Cerulean Rocket after the rival
sequence, making Dig an option for S.S. Anne and Surge, not that first rival.

Mega Kick and Bite are already included in the recorded Cerulean, S.S. Anne,
and Surge movesets. Dig was not taught in the recorded run. Mega Kick's misses,
Bite's Gen 3 special damage/flinches, and enemy Quick Attack priority are
represented in the engine. The current greedy controller does not explicitly
optimize for the future benefit of flinches or Dig's invulnerable turn.

The B controller's finishing-hit shortcut also ignores opposing priority when
deciding to skip healing. Thus passing an ordinary Speed threshold does not
make a finishing attack safe against Quick Attack. These experiments preserve
that policy; fixing it should be a separately measured B-policy change.

| Fight | Current raw Speed | Ordinary-move threshold |
|---|---:|---|
| Forest Sammy | 12 | 15 beats Weedle's 14, before String Shot drops |
| Cerulean rival | 35 | Already above the entire team; Abra is fastest at 34 |
| S.S. Anne rival | 45 | 48 beats Kadabra's 47 |
| Surge | 47 | 54 beats Raichu's 53; currently ties Voltorb's 47 |

At the same levels and starter profile, the isolated diagnostics require Speed
EVs of 120 instead of 2 (Forest), 68 instead of 25 (S.S. Anne), and 128 instead
of 31 (Surge). Earning those EVs would normally also earn EXP. Holding existing
EVs fixed instead, levels 9, 29, and 33 reach the respective thresholds, but
actual training also changes other stats and must be evaluated separately.

On the recorded route, X Special shopping occurs later, at Celadon Department
Store 5F. These early B fights lack it, but HP, PP, typing, accuracy, statuses,
priority and policy decisions also contribute. The absence of X Special is
not a sufficient explanation by itself.

Source checks use the pinned pret checkout from the battle reference:
`src/player_pc.c`, `data/maps/Route1/scripts.inc`,
`data/maps/ViridianCity_Mart/scripts.inc`, `data/maps/PewterCity_Mart/scripts.inc`,
`data/maps/SSAnne_1F_Room6/scripts.inc`, `data/maps/CeruleanCity/scripts.inc`,
and `data/maps/CeladonCity_DepartmentStore_5F/scripts.inc`.

## Reproduce

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_preparation --out /tmp/frlg-preparation.json
```

Requires the pinned Node engine dependencies. The full JSON retains exact
scenarios and seeded example traces. The adjacent `.summary.json` contains
the compact comparison, source hashes and stopping results.

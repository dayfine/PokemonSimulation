# Mail Glitch grind (mg-04): where to level CH'DING and MIMIEN

Model: `src/pokesim/games/frlg/progression/grind.py` (Monte Carlo, 200 runs per row, seed 1).
Data: `data/games/frlg/progression/mail-glitch-grind-pret.json` from pret/pokefirered
(`grind_pret.py`) and the mg-03 party read from the lab save with `save_party.py`
(`mail-glitch-mg03-party.json`; the save itself is not committed).

The mg-03 save already has **CH'DING (Farfetch'd) at Lv 22 with Knock Off**, so its
grind is skipped. Only **MIMIEN (Mr. Mime) Lv 9 → 33 (Recycle)** needs EXP: 35,208 points.
The sweeper is the saved Lv 57 Blastoise (Surf, Bite, Blizzard, Strength).

| Strategy | MIMIEN EXP/hour | Battles | Heal trips | Blastoise faints / 1000 battles | Total time, both grinders |
|---|---:|---:|---:|---:|---:|
| Tower 5F, switch trick (today's plan) | 17,100 | 217 | 145 (heal pad) | 3.3 (+7.7 Awakenings used) | 124 min |
| Tower 5F, MIMIEN alone when it outspeeds and surely one-hits | 26,000 | 217 | 7 | 0 | 81 min |
| Victory Road 1F, switch trick | 38,900 | 84 | 10 | 0.2 | 55 min |
| **Victory Road 2F, switch trick** | **40,600** | **77** | **11** | **0.1** | **53 min** |
| VS Seeker rematches, Route 8 (singles) | 51,400 | 27 trainers | 4 | 55 | 42 min |

Recommended default: **Victory Road 2F with the switch trick.** Fallback: **Tower 5F with
MIMIEN fighting alone when it outspeeds and its lowest roll KOs** (otherwise switch), healing
on the PurifiedZone pad. No grinder fainted in any row: switching goes before the foe's
move, so the grinder is never hit.

Why the others lose:
- Tower switch trick: Gastly's Hypnosis then Curse (Blastoise loses 1/4 HP per turn
  while asleep) kills Blastoise about 1 battle in 300, even from full HP and with an
  Awakening used whenever both land (7.7 Awakenings per grind; the save has one).
- VS Seeker: the save has no VS Seeker (key items read from the save). Lass Megan's final
  rematch team (Lv 46-48, Raichu last) wears Blastoise down without in-battle healing.
  The rate also depends on an assumed 3 trainers in range per use.
- Cerulean Cave is closed until the Sevii Islands story is done, so it is not compared.
- Sevault Canyon needs the Rainbow Pass; the save has neither the Tri-Pass nor the
  Rainbow Pass, so it is unavailable.

## Read from data vs. assumed

From pret: encounter tables and slot rates, the FRLG step-encounter test, running allowed
per map (no running in Pokémon Tower), species stats and EXP yields, growth curves,
learnsets and wild movesets, move data, type chart, natures, final VS Seeker rematch
parties, the 70% rematch answer rate. From the save: levels, EXP, IVs, EVs, natures,
stats, moves and PP, traded flags, bag.

Assumed: eight badges (all badge boosts, Victory Road open); every duration in `TIMING`
(Fast text, battle scenes off); Victory Road heal round trip 90 s and Route 8 → Lavender
40 s; pacing on one tile type (no 60% behaviour-change roll); stat-changing moves,
abilities other than Levitate, held items and in-battle healing are ignored; Blastoise
heals below 50% HP (Tower: below 100%, since the pad is two tiles away); level-up moves
other than Recycle are declined once MIMIEN has four moves.

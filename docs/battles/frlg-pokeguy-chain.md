# PokeGuy's League setup as one chain

`python3 -m pokesim.cli.frlg_league_pokeguy` plays PokeGuy's setup from Lorelei to the Champion with
HP, PP and bag carried over (500 chains, seed `f1`, the engine and table of `frlg_league_plan eval`).
Full tables: `~/BDSPLab/notes/e4-sim/pokeguy-chain/tables.txt`.

| Scenario | League |
|---|---:|
| Each fight alone from his recorded entry (C2 + his goals) | 71.8% all five (per fight 90-96%) |
| A: his Blastoise, bag and between-fight healing, C2 + his goals | 23.2% |
| B: his Blastoise and bag, our planned policy | 13.2% |
| C: our Blastoise Lv54 and bag, no held item, C2 + his goals | 7.6% |
| E: C + Black Glasses | 15.8% |
| P: our Blastoise Lv54 and bag, no held item, planned policy | 23.0% |
| D: P + Black Glasses (= #111's planned Lv54 result) | 21.2% |

Why ~95% per fight becomes ~23% as a chain:

- The per-fight numbers start every fight from his recorded entry, bag included. Even played in one seed,
  the five isolated fights all win only 72-77% of the time.
- Items: C2 spends ~2.9 X Accuracy at Agatha chasing Gengar's Double Team (he spent none on video), so
  Lance and the Champion get ~0 of the 3 and 2 his recorded bags gave them; the Champion falls from 95% to
  36%. His on-video setup (policy `video`) keeps them (Champion 61%) but loses more at Bruno (63%).
- Full Restores: Lance alone takes ~5 in the chain. In our item sweep, Full Restore +5 is worth +19pp.
- PP: Surf runs out at Lance (Elixir 0.6 per Lance), so the Champion gets less Elixir help.

The League cases carry his Black Glasses (`held_item`), so every earlier chain on our Blastoise held them
too; `run_chain(..., held_item='')` now models our console Blastoise. The engine's Gen 3 Black Glasses is
1.1x Sp. Atk on Dark moves (Showdown's gen3 mod; Bite on Dewgong 28.2 -> 30.9 mean), and the policy's
`@smogon/calc` previews see it too.

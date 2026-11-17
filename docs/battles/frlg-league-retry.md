# FRLG League worked backwards: retry each fight from a save

`python3 -m pokesim.cli.frlg_league_retry --runs 500 --seed r1 --out-dir DIR` retries each League fight from a save
until it wins within its Full Restore budget k (a loss does not save; the game saves between rooms). Setup P of
#113: our Blastoise Lv54, BAG_NOW, no held item, policy `planned`. Full tables:
`~/BDSPLab/notes/e4-sim/retry/tables.txt`.

| Fight | Choice | Accept rule | P(accept) | Tries |
|---|---|---|---:|---:|
| Lorelei | X Sp +6 on Dewgong | FR <= 1 | 73% | 1.4 |
| Bruno | plan | FR <= 2 | 48% | 2.1 |
| Agatha | plan | FR = 0 | 90% | 1.1 |
| Lance | heal only when the mean hit KOs | FR <= 2 | 58% | 1.7 |
| Champion | plan setup, 3 FR left | win | 46% | 2.2 |

About 8.5 expected tries for the whole League (played forward with these rules), against 23% for one unbroken chain.
The Champion with 4 Full Restores wins 61% per try from a real Lance win (70% with the whole non-FR bag); it
saturates at ~71% from 6. Stacking setup on Pidgeot loses to Whirlwind (0%), and +2 X Special on Bruno's Onix drops
Bruno to 18%.

Bruno played PokeGuy's way (+2 Sp. Atk, Surf only, heal only on a sure KO) wins 60% per try against the plan's 82%;
never healing wins 20%. Roar/Whirlwind count as a soft reset (one failed try) at Bruno and the Champion, but pret's AI
only picks them once one of our stats is at +3 or more, so the +2 plans never see them, while the long Champion
setup (X Sp +4) is reset 93-100% of the time.

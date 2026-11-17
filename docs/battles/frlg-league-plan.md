# FRLG League plan (policy `planned`)

The League policy is data plus a short override table, so the simulator and the
AutoStory program can run the same decisions. The data is a per-fight plan
(`src/pokesim/games/frlg/league/plan.json`). The override table holds the rows
for facts a plan can't know in advance. Code:
`src/pokesim/games/frlg/league/planned.py`. Search and tables:
`python3 -m pokesim.cli.frlg_league_plan {eval,search,champion}`.

## The plan by hand: what to have at each door

One row per boundary. An **Enter** row is what you must have after the heal,
standing at the door. An **Exit** row is what a passing win leaves at least.
Item counts are hard. A win that ends below its Exit row spent more than the
fight's caps, so it does not pass: don't save, reset and fight again. HP and
Surf are only a guide. They show what the sim's passing runs had (median, and
the point 1 in 10 runs fall below). Max HP is 171 (Blastoise Lv54).

| Boundary | HP | Surf/Blizzard PP | Full Restore | X Special | X Speed | X Accuracy | Guard Spec | Super Potion | Elixir | Max Elixir |
|---|---|---|---|---|---|---|---|---|---|---|
| Enter Lorelei | 171 (always) | >= 15 / >= 5 | 8 | 15 | 5 | 3 | 2 | 6 | 1 | 1 |
| Exit Lorelei | median 107, 1 in 10 below 36 | 15 (low 12) / >= 5 | 7 | 9 | 5 | 3 | 2 | 6 | 1 | 1 |
| Enter Bruno | 171 (always) | 12 (sim low) / >= 5 | 6 | 9 | 5 | 3 | 2 | 5 | 1 | 1 |
| Exit Bruno | median 51, 1 in 10 below 32 | 10 (low 5) / >= 5 | 5 | 7 | 2 | 3 | 2 | 5 | 1 | 1 |
| Enter Agatha | median 104, 1 in 10 below 85 | 5 (sim low) / >= 5 | 5 | 7 | 2 | 3 | 2 | 4 | 1 | 1 |
| Exit Agatha | median 84, 1 in 10 below 47 | 7 (low 3) / >= 5 | 5 | 4 | 1 | 3 | 2 | 4 | 1 | 1 |
| Enter Lance | 171 (always) | 3 (sim low) / >= 5 | 4 | 4 | 1 | 3 | 2 | 2 | 1 | 1 |
| Exit Lance | median 86, 1 in 10 below 62 | 5 (low 1) / any | 3 | 2 | 1 | 3 | 2 | 2 | 1 | 1 |
| Enter Champion | 171 (always) | >= 8 / >= 4 | 2 | 2 | 1 | 3 | 2 | 0 | 0 | 1 |
| Exit Champion | median 39, 1 in 10 below 3 | 11 (low 6) / any | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |

**Between two fights: one heal, nothing else.**

1. Fix a status with its cure or a Full Heal. If you have neither, use a Full
   Restore, and that is the heal.
2. Missing 50 HP or less: 1 Super Potion.
3. Missing 100 HP or less, with two Super Potions to spare: 2 Super Potions.
4. Otherwise: 1 Full Restore.
5. Before the Champion only: the Elixir, if Surf is below 8 or Blizzard is
   below 4.

"To spare" means above what the Exit row of the next fight still has to keep.
The heal comes out of the next fight's caps, so each Enter row is the previous
Exit row less the most the heal can take. There is no PP item before an E4
fight, so its Surf is whatever the last fight left.

- Lorelei. Goal: Win with <= 1 Full Restore: 6 X Special on Dewgong (+6), Bite/Surf through, Lapras Strength -> Bite -> Bite. Pass: a win using at most 1 Full Restore, 6 X Special (the heal before it included). Pass rate 73% per try (about 1.36 tries); 95% of 10-try checks see at least 5 pass(es); reset budget 5 tries.
- Bruno. Goal: Win with <= 2 Full Restores: 2 X Special and up to 3 X Speed on Onix #1, Surf through; reset on Roar or a lost Speed race. Pass: a win using at most 2 Full Restores, 2 X Special, 3 X Speed, 1 Super Potion (the heal before it included); a Roar or Whirlwind that lands is a reset. Pass rate 37% per try (about 2.70 tries); 95% of 10-try checks see at least 1 pass(es); reset budget 9 tries.  LOW: a 10-try check cannot tell bad luck from a broken plan.
- Agatha. Goal: Win with no Full Restore: 3 X Special and 1 X Speed on Gengar #1 (+3), Bite/Surf through. Pass: a win using at most 3 X Special, 1 X Speed, 1 Super Potion (the heal before it included). Pass rate 72% per try (about 1.39 tries); 95% of 10-try checks see at least 5 pass(es); reset budget 5 tries.
- Lance. Goal: Win with <= 2 Full Restores: 2 X Special on Gyarados, Blizzard the dragons, keep the Max Elixir. Pass: a win using at most 2 Full Restores, 2 X Special, 2 Super Potions (the heal before it included). Pass rate 44% per try (about 2.26 tries); 95% of 10-try checks see at least 2 pass(es); reset budget 7 tries.  LOW: a 10-try check cannot tell bad luck from a broken plan.
- Champion. Goal: Win with the 3 Full Restores left: Guard Spec, +2 X Special, +2 X Accuracy, +1 X Speed on Pidgeot; stay at +2 (Whirlwind at +3); reset on Whirlwind. Pass: a win using at most 3 Full Restores, 2 X Special, 1 X Speed, 2 X Accuracy, 1 Guard Spec, 2 Super Potions, 1 Max Elixir, 1 Elixir (the heal before it included); a Roar or Whirlwind that lands is a reset. Pass rate 40% per try (about 2.53 tries); 95% of 10-try checks see at least 2 pass(es); reset budget 8 tries.  LOW: a 10-try check cannot tell bad luck from a broken plan.

**Margin.** Expected tries along the chain: 10.25 (2000 runs per fight). Three
fights are under the bar for a 10-try console check (pass rate under 40%, or
at most 2 passes in 10): Bruno (37%, 1 in 10), Lance (44%, 2 in 10) and the
Champion (40%, 2 in 10). Three passes in 10 needs about 51% per try. Until
these improve, check them with 20 tries: 95% of 20-try batches see at least 4
(Bruno), 5 (Lance) and 4 (Champion) passes. What would raise them (Full
Restores are sold at the Indigo Plateau Mart):

- Champion: a 9th Full Restore, capped at 4. The chain gives 47% per try and
  9.87 tries in total (1000 runs).
- Bruno: a 3rd Full Restore cap. The cap search (200 runs per cell) puts it
  near 54%, which is 3 in 10. About 22% of Bruno's tries are early resets
  after Onix #1, which cost little but still count as fails.
- Lance: a 3rd Full Restore cap puts it near 70% in the cap search; a 3rd
  Super Potion only gets it to about 50%.

The chain hasn't checked the Bruno or Lance changes. The cap search's own pick
(Full Restores 1/0/0/3/4, Super Potions 0/0/2/2/2) has a slightly lower sum of
tries per fight, but in the chain Bruno passed only 22% of tries, so the plan
keeps the old Full Restore split.

`plan.json` holds these rows as each fight's `contract`. Print the table with
`python3 -m pokesim.games.frlg.league.contracts [--markdown]`.
`test_plan_contracts.py` checks the arithmetic. The bag covers Enter Lorelei.
Each Enter row less what the fight may still spend covers its Exit row, and
each Exit row less the next heal covers the next Enter row. The heal rule never
spends more than its budget or more than one heal. The items add up to the bag,
and the pass figures follow the binomial. The caps, HP figures and pass rates
come from `frlg_league_final --cap-search --runs 2000`, which searches the Full
Restore x Super Potion caps and then runs the chain forward. Each fight starts
from the previous fight's passing wins. `contracts --fill boundaries.json`
writes the result into `plan.json`.

## Plan schema (`frlg-league-plan/1`)

One JSON file for the whole League:

```json
{"format": "frlg-league-plan/1",
 "fights": {
   "<fight>": {                                // lorelei, bruno, agatha, lance, champion
     "foes": [                                 // by the trainer's party slot
       {"species": "dewgong",
        "moves": ["bite", "surf"],             // ranking: the first with PP above the reserve
        "setup": [                             // goals in order; each serves a move
          {"item": "xspecial", "stage": 4, "serves": "bite"},
          {"item": "guardspec", "stage": 1}]}],
     "between": {"hp": 0.8, "pp": {"surf": 8}},  // before this fight: HP fraction, PP floors
     "reserve": {"pp": {"blizzard": 5},          // PP this fight must not spend
                 "items": {"fullrestore": 6, "maxelixir": 1}}}}}  // bag counts it must leave
```

Optional per-foe keys (format stays `/1`; a reader that doesn't know them can ignore them):

```json
{"species": "machamp", "moves": ["surf"],
 "heal": {"below": 80, "heal_at_least": 50,      // HP < 80: the smallest spendable heal restoring >= 50 HP
          "heal_when_can_ko": false,             // false (default): a sure KO this turn comes first
          "ko_rule": true},                      // true (default): the KO-risk heal row still applies
 "sequence": ["strength", "bite", "bite"],       // our n-th attack on this foe; then `moves`
 "kill_order": true}                             // false: skip the kill_order row for this foe
```

- `heal.below` is HP points (not a fraction). Items are tried Super Potion, Hyper Potion, Max Potion, Full Restore;
  one is taken only if its spendable count is above the fight's reserve (so a Full Restore budget still holds).
  Two heal turns in a row with the foe's HP unchanged stop the block (the KO-risk row's streak rule).
- A foe with a `sequence` skips the `kill_order` row.

Optional per-fight keys:

```json
{"goal": "Win with <= 1 Full Restore: ...",            // the fight's goal in words
 "caps": {"fullrestore": 1, "xspecial": 6, "superpotion": 1},  // what an accepted win may spend (top-ups included)
 "reset": {"roar": true,                               // a Roar / Whirlwind that lands: soft reset
           "after_foe": {"index": 0, "speed_below": 0, "items_used": {"xspeed": 3}}}}
                                                       // when slot 0 falls: reset if Speed < 0 with 3 X Speed spent
```

- `between: {"heal": "one"}` is the one-heal rule above (`planned._one_heal`). The old form
  `{"hp": 0.8, "pp": {...}}` (Super Potions up to an HP fraction) still works for other plans.
- `contract` (`topup`, `entry`, `exit`, `pass`) is the per-fight bookkeeping in the table at the top. `topup` is
  the most the heal before the fight may take. `entry.items` is the previous exit less `topup`, and `exit.items`
  is the bag less every cap so far. HP and Surf figures are informative, taken from the chain's passing wins.
  `pass` holds `expected_pass` (P(win within the caps) per try), `min_pass` (the most passes k of 10 that 95% of
  10-try batches reach: P(K <= k-1) < 5%) and `reset_budget` (ceil(3 / expected_pass) tries, about a 95% chance
  of at least one pass).
- `caps` is the accept rule: a win counts only if no item's use exceeds its cap. `reserve.items` must equal
  the later fights' caps (`planned.reserves_from_caps`), so a fight can spend its cap and never a later
  fight's; `test_plan_budget.py` checks that and that Full Restores, X Special, X Speed and the Max Elixir
  caps add up to the whole bag. `python3 -m pokesim.cli.frlg_league_final` searches the Super Potion caps
  and runs the chain forward under these accept rules.

- A foe that isn't found at its slot is looked up by species.
- A setup goal whose `serves` move has no PP above the reserve is skipped.
  Guard Spec's goal is met while Mist is up.
- `reserve.items` is the count to leave in the bag. Only the KO-risk heal may go
  below it, for a Full Restore when nothing else survives the hit (losing here
  loses the League).
- `reserve.pp` keeps a move's PP for later fights. A sure KO may still use it
  when we are at KO risk.
- The Elixir and the Max Elixir are hard reserves through Lance (both are capped at the Champion), so Blizzard
  has PP for Venusaur.
- `planned.build(spec, bag)` expands the compact spec in `league/specs.py`. It
  works out each fight's item reserve from the later fights' setup goals and
  Full Restore allowances.

## Override table (first match wins; the chain logs the row as `why`)

| row | when | action |
|---|---|---|
| `locked` | two-turn / recharge / Outrage turn | the forced move |
| `sure_ko` | a move's lowest roll KOs (accuracy with both stat stages, evasion included; foe HP after its trainer's Full Restore) and we move first (speed with stages and paralysis); not while this is the plan's setup foe and we are safe | the cheapest such move (Strength, Bite, Surf, Blizzard) |
| `sleep_cure` | asleep / frozen with a cure | Full Restore at KO risk, else Awakening, Full Heal |
| `status_ko` | a status and HP <= D | Full Restore |
| `foe_heal` | the foe's `heal` block: HP < `below` (before `sure_ko` when `heal_when_can_ko`) | the smallest spendable heal restoring >= `heal_at_least` |
| `ko_heal` | HP <= D < max HP, where D is the foe's worst normal hit now, against our current Def/Sp. Def stages. D is 0 while the foe recharges, sleeps, uses an item, or has a charge move it isn't holding | the smallest heal that clears D with a mean hit to spare. After two medicine turns with the foe's HP unchanged: Full Restore. D >= max HP: attack |
| `cure` | paralysis or poison, no KO risk, no medicine streak | its cure, Full Heal |
| `kill_order` | the trainer has an open item slot and the planned hit can leave the foe at 1-24% | a hit leaving it at 25% or more, after which the finisher's lowest roll KOs; else the strongest hit that stays at 25% or more |
| `pp_restore` | every planned move is out of PP | an Elixir not held in reserve |
| `plan:setup` | the first unmet goal; HP >= min(75%, D + (turns - 1) x mean), or the foe uses its item this turn (a free turn) | the X item; otherwise a heal (`plan:setup_heal`) |
| `plan:move` | otherwise | the first planned move with PP above the reserve |

Trainer items follow pret `ShouldUseItem`: a Full Restore below 1/4 HP. Item
slot `i > 0` stays closed while more than `4 - i + 1` of the trainer's Pokémon
are alive. E4 members carry 2 Full Restores and the Champion carries 4.

Phazing: our HM users sit on the bench, so Roar and Whirlwind succeed and reset
our stat stages. pret's `AI_CV_Roar` favours phazing only once one of our
stats is above +2. Setup goals therefore stop at +2 Sp. Atk against Pidgeot
and the first Onix.

## What the C++ port must change

- Read `plan.json` in place of `LEAGUE_FIGHTS` budgets and `foe_threats` rows.
  Budgets become reserves: the count to leave for later fights.
- Compute D live from the current foe and our current stat stages, Rock Tomb
  and Scary Face drops included. This needs a Gen 3 damage formula with badge
  boosts, or rows indexed by our Def/Sp. Def stage. A per-foe row computed at
  +0 gives the wrong answer after drops.
- Compute speed with stat stages and paralysis for "we move first". Compute
  accuracy with our accuracy stage and the foe's evasion (Double Team) for
  "sure KO".
- Track the trainer's Full Restore slots (count used, alive count) and treat a
  foe under 1/4 as full HP when one is open. A foe under 1/4 with an open slot
  uses its turn on the item: that turn has no KO risk, so it goes to setup.
- Add the `kill_order` row.
- Gate setup goals on the served move's PP above its reserve. Cap Sp. Atk at +2
  against Roar/Whirlwind users.
- Handle being dragged out by Roar or Whirlwind (switch Blastoise back in).
- Between fights: a cure, Super Potions to the plan's HP target, PP items to
  the plan's PP floor, and never the Max Elixir before the Champion. After a
  PP item, check the PP read. On 2026-11-16 the read after the Max Elixir still
  said Blizzard 0/5.
- Log each decision's row name, so `frlg_league_policycheck` can compare the
  console's choices with the sim's.

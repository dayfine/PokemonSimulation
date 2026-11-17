# FRLG League plan (policy `planned`)

The League policy is data plus a short override table, so the simulator and the
AutoStory program can run the same decisions. The data is a per-fight plan
(`src/pokesim/games/frlg/league/plan.json`). The override table holds the rows
for facts a plan can't know in advance. Code:
`src/pokesim/games/frlg/league/planned.py`. Search and tables:
`python3 -m pokesim.cli.frlg_league_plan {eval,search,champion}`.

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
- The Max Elixir is a hard reserve through Lance, so Blizzard has PP for Venusaur.
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

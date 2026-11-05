# FRLG AutoStory battle handoff: Pokeguy Squirtle route

This is the single file to give another agent or repository. It contains all 69 trainer fights in route order, both entry variants and win rates, full player and opponent conditions, the strategy to run for each fight, healing requirements, League PP requirements and the limits of the estimates. Prefer the prepared variant for the six designated rests; elsewhere it preserves the tested recorded state.

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

## All fights in route order

| # | Fight | Tier | Level | Recorded HP | Prepared HP | Recorded win rate | Prepared win rate |
|---:|---|:---:|---:|---:|---:|---:|---:|
| 1 | [lab-rival](#lab-rival) | A | 5 | 20/20 | 20/20 | 95.8% | 95.8% |
| 2 | [forest-sammy](#forest-sammy) | B | 7 | 16/25 | 25/25 | 86.5% | 98.8% |
| 3 | [pewter-liam](#pewter-liam) | A | 8 | 5/27 | 27/27 | 65.2% | 100.0% |
| 4 | [brock](#brock) | A | 11 | 11/33 | 33/33 | 53.8% | 100.0% |
| 5 | [route3-colton](#route3-colton) | A | 13 | 6/38 | 6/38 | 100.0% | 100.0% |
| 6 | [route3-greg](#route3-greg) | A | 14 | 8/40 | 8/40 | 100.0% | 100.0% |
| 7 | [route3-james](#route3-james) | A | 15 | 10/42 | 10/42 | 100.0% | 100.0% |
| 8 | [mtmoon-josh](#mtmoon-josh) | B | 15 | 10/42 | 42/42 | 83.5% | 100.0% |
| 9 | [mtmoon-rocket](#mtmoon-rocket) | A | 16 | 10/49 | 10/49 | 98.8% | 98.8% |
| 10 | [mtmoon-miguel](#mtmoon-miguel) | B | 16 | 10/49 | 10/49 | 100.0% | 100.0% |
| 11 | [misty](#misty) | B | 20 | 54/59 | 54/59 | 98.3% | 98.3% |
| 12 | [cerulean-rival](#cerulean-rival) | B | 21 | 32/61 | 61/61 | 45.2% | 75.5% |
| 13 | [bridge-cale](#bridge-cale) | A | 22 | 22/64 | 22/64 | 100.0% | 100.0% |
| 14 | [bridge-ali](#bridge-ali) | B | 22 | 22/64 | 22/64 | 100.0% | 100.0% |
| 15 | [bridge-timmy](#bridge-timmy) | A | 23 | 24/66 | 24/66 | 100.0% | 100.0% |
| 16 | [bridge-reli](#bridge-reli) | A | 23 | 24/66 | 24/66 | 100.0% | 100.0% |
| 17 | [bridge-ethan](#bridge-ethan) | A | 23 | 24/66 | 24/66 | 100.0% | 100.0% |
| 18 | [bridge-rocket](#bridge-rocket) | A | 23 | 24/66 | 24/66 | 100.0% | 100.0% |
| 19 | [route25-wayne](#route25-wayne) | A | 24 | 27/69 | 27/69 | 100.0% | 100.0% |
| 20 | [route25-kelsey](#route25-kelsey) | A | 24 | 27/69 | 27/69 | 100.0% | 100.0% |
| 21 | [route25-flint](#route25-flint) | A | 24 | 27/69 | 27/69 | 100.0% | 100.0% |
| 22 | [route25-haley](#route25-haley) | B | 24 | 27/69 | 27/69 | 100.0% | 100.0% |
| 23 | [cerulean-dig-rocket](#cerulean-dig-rocket) | B | 25 | 27/72 | 27/72 | 100.0% | 100.0% |
| 24 | [route6-jeff](#route6-jeff) | A | 25 | 21/72 | 21/72 | 100.0% | 100.0% |
| 25 | [ssanne-rival](#ssanne-rival) | B | 27 | 37/76 | 76/76 | 49.3% | 75.7% |
| 26 | [vermilion-tucker](#vermilion-tucker) | A | 28 | 79/79 | 79/79 | 100.0% | 100.0% |
| 27 | [surge](#surge) | B | 28 | 79/79 | 79/79 | 56.2% | 56.2% |
| 28 | [route9-alicia](#route9-alicia) | B | 28 | 43/79 | 43/79 | 100.0% | 100.0% |
| 29 | [route9-conner](#route9-conner) | B | 29 | 45/81 | 45/81 | 100.0% | 100.0% |
| 30 | [rocktunnel-ashton](#rocktunnel-ashton) | B | 29 | 45/81 | 45/81 | 100.0% | 100.0% |
| 31 | [rocktunnel-winston](#rocktunnel-winston) | B | 30 | 42/84 | 42/84 | 100.0% | 100.0% |
| 32 | [rocktunnel-martha](#rocktunnel-martha) | B | 30 | 39/84 | 39/84 | 97.7% | 97.7% |
| 33 | [rocktunnel-allen](#rocktunnel-allen) | A | 30 | 39/84 | 39/84 | 100.0% | 100.0% |
| 34 | [rocktunnel-oliver](#rocktunnel-oliver) | A | 30 | 39/84 | 39/84 | 100.0% | 100.0% |
| 35 | [rocktunnel-sofia](#rocktunnel-sofia) | B | 31 | 41/86 | 41/86 | 100.0% | 100.0% |
| 36 | [rocktunnel-dudley](#rocktunnel-dudley) | A | 31 | 41/86 | 41/86 | 100.0% | 100.0% |
| 37 | [rocktunnel-dana](#rocktunnel-dana) | B | 32 | 44/89 | 44/89 | 100.0% | 100.0% |
| 38 | [route8-rich](#route8-rich) | A | 32 | 39/89 | 39/89 | 100.0% | 100.0% |
| 39 | [hideout-poster-guard](#hideout-poster-guard) | B | 32 | 39/89 | 39/89 | 100.0% | 100.0% |
| 40 | [hideout-key-grunt](#hideout-key-grunt) | A | 32 | 39/89 | 39/89 | 100.0% | 100.0% |
| 41 | [hideout-left-guard](#hideout-left-guard) | A | 33 | 42/92 | 42/92 | 100.0% | 100.0% |
| 42 | [hideout-right-guard](#hideout-right-guard) | B | 33 | 42/92 | 42/92 | 100.0% | 100.0% |
| 43 | [hideout-giovanni](#hideout-giovanni) | B | 36 | 38/114 | 38/114 | 100.0% | 100.0% |
| 44 | [tower-rival](#tower-rival) | C | 36 | 38/114 | 38/114 | 90.0% | 90.0% |
| 45 | [tower-tammy](#tower-tammy) | A | 37 | 24/116 | 24/116 | 100.0% | 100.0% |
| 46 | [tower-jennifer](#tower-jennifer) | A | 37 | 24/116 | 24/116 | 100.0% | 100.0% |
| 47 | [tower-emilia](#tower-emilia) | A | 37 | 24/116 | 24/116 | 100.0% | 100.0% |
| 48 | [tower-rocket1](#tower-rocket1) | A | 38 | 27/119 | 27/119 | 100.0% | 100.0% |
| 49 | [tower-rocket2](#tower-rocket2) | A | 38 | 27/119 | 27/119 | 100.0% | 100.0% |
| 50 | [tower-rocket3](#tower-rocket3) | A | 38 | 27/119 | 27/119 | 100.0% | 100.0% |
| 51 | [fuchsia-kirk](#fuchsia-kirk) | A | 38 | 31/119 | 31/119 | 100.0% | 100.0% |
| 52 | [koga](#koga) | C | 39 | 34/122 | 34/122 | 70.1% | 70.1% |
| 53 | [blaine](#blaine) | B | 40 | 24/126 | 24/126 | 100.0% | 100.0% |
| 54 | [celadon-tamia](#celadon-tamia) | A | 41 | 26/128 | 26/128 | 100.0% | 100.0% |
| 55 | [celadon-lori](#celadon-lori) | A | 44 | 35/137 | 35/137 | 100.0% | 100.0% |
| 56 | [erika](#erika) | C | 44 | 35/137 | 35/137 | 91.5% | 91.5% |
| 57 | [silph-rival](#silph-rival) | C | 44 | 85/137 | 85/137 | 96.3% | 96.3% |
| 58 | [silph-boardroom-grunt](#silph-boardroom-grunt) | B | 45 | 30/140 | 30/140 | 100.0% | 100.0% |
| 59 | [silph-giovanni](#silph-giovanni) | C | 46 | 33/143 | 33/143 | 100.0% | 100.0% |
| 60 | [sabrina](#sabrina) | C | 46 | 33/143 | 33/143 | 98.3% | 98.3% |
| 61 | [viridian-takashi](#viridian-takashi) | B | 47 | 25/146 | 25/146 | 99.3% | 99.3% |
| 62 | [viridian-warren](#viridian-warren) | A | 48 | 28/149 | 28/149 | 100.0% | 100.0% |
| 63 | [giovanni-gym](#giovanni-gym) | A | 48 | 28/149 | 28/149 | 100.0% | 100.0% |
| 64 | [route22-rival](#route22-rival) | C | 49 | 153/153 | 153/153 | 95.6% | 95.6% |
| 65 | [lorelei](#lorelei) | C | 51 | 159/159 | 159/159 | 94.3% | 94.3% |
| 66 | [bruno](#bruno) | C | 52 | 130/162 | 130/162 | 95.9% | 95.9% |
| 67 | [agatha](#agatha) | C | 53 | 45/165 | 45/165 | 95.3% | 95.3% |
| 68 | [lance](#lance) | C | 54 | 168/168 | 168/168 | 99.2% | 99.2% |
| 69 | [champion](#champion) | C | 55 | 171/171 | 171/171 | 95.6% | 95.6% |

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

## Strategy rules to implement in the consuming repo

The tier describes observed action complexity, not a separate difficulty scale.
**B is the default runtime even for fights labeled A.** Set
`enable_complex_planning=true` only for the twelve C fights. No measured policy
switches the player's Pokémon. A fainted lead loses.

### Attack selector used by A, B and C

Honor forced/locked moves, including the second turn of Dig and recharge.
Among usable, non-disabled moves with PP, estimate damage against the current
foe, accounting for Gen 3 typing, stats, stages, accuracy, status, ability,
held item and field effects. For each damaging move compute:

```text
expected_damage_per_turn = mean(noncritical_damage_rolls) * hit_probability
if two_turn_move: expected_damage_per_turn /= 2
expected_KO_turns = ceil(foe_HP / expected_damage_per_turn)
if every roll KOs and hit_probability == 1:
    expected_KO_turns = 2 for a two-turn move, otherwise 1
choose the smallest tuple:
    (expected_KO_turns, -hit_probability, base_power, -remaining_PP, move_slot)
```

If no move has positive expected damage, use the first usable move; if none
is usable, the engine supplies Struggle. C first prefers a safe guaranteed
KO over an equal-turn PP-saving choice. This controller does not optimize
the future value of Bite flinches or confusion, or Dig's underground turn.

### B: attack plus recovery, evaluated again every turn

Compute an NPC threat estimate by sampling its move-scoring policy 32 times
with a separate fixed RNG seeded 0. Combine move-selection frequencies,
accuracy, a 1/16 critical chance, damage rolls, paralysis and sleep. Add
`floor(max_HP/8)` for each of existing poison/toxic and Leech Seed. The
heuristic treats toxic as a flat residual; actual turns use the engine's
status mechanics. Let `L` be the 80th-percentile next-turn HP loss, `M` its
mean, and `W` its maximum positive-weight loss.

1. Honor a forced move. Select an attack. B calls it a finishing hit when it
   is strictly faster (or has positive priority), has 100% hit probability,
   always KOs, is not two-turn, sleep/paralysis/freeze/confusion cannot stop
   it, and the NPC will not use a medicine. In that case, check PP recovery
   only and otherwise attack.
2. Otherwise, when current HP is greater than `L`, cure the current status:
   prefer its dedicated cure, then Full Heal, then Full Restore. For
   confusion alone, try Full Heal then Full Restore. These do not clear
   Leech Seed; the solo policy has no switch remedy for it.
3. If HP is at most `max(max_HP/2, W)`, choose the smallest HP medicine in
   stock whose actual gain exceeds `L`. Capacity ties prefer Max Potion
   before Full Restore. A Full Restore also cures status.
4. Otherwise use an Oran Berry if at least 10 HP is missing, HP is at most
   half, and `10 > L`.
5. Check PP medicine only if HP is greater than `2*L` and the player is not
   asleep/frozen. At least two damaging moves must be empty, or no usable
   move must do damage. Prefer Elixir, then Max Elixir; otherwise Ether,
   then Max Ether on the empty damaging move with highest base power.
6. Otherwise attack.

**Known B limitation:** its finishing-hit shortcut ignores opposing priority
when comparing Speed. Quick Attack can still interrupt an apparent finish.
Do not silently fix this and attribute the existing rates to the new policy.

### C2: conditional setup layered over B

Use the exact per-fight targets below. In Gen 3 each X item grants one stage;
items are not free turns. Preserve boosts across opponents within a fight.
The Sp. Atk multiplier at a nonnegative stage `s` is `(2+s)/2`. Torrent
multiplies Water damage by 1.5 when `3*HP <= max_HP`.

1. Honor forced actions. A safe finish also checks lethal higher-priority
   opposing moves (including critical damage) and residual survival. Take
   it when setup/Torrent activation is complete or only the last foe is
   left. Also take it instead of setting up against Self-Destruct/Explosion
   or an ordinary hit capable of KOing the player even at full HP.
2. Cure status using the B cure rule. While asleep/frozen/confused, fall
   back to B rather than planning setup turns.
3. Budget all pending setup actions. Let `N` be at least one, counting
   affordable Sp. Atk/accuracy deficits, one needed X Speed and a pending
   Guard Spec. Let `D` be the largest ordinary damage roll of any usable
   enemy move plus the same residual estimate. A foe locked into recharge
   or asleep for more than one turn contributes only residual damage.
4. Target HP reserve `R = min(0.75*max_HP, D + (N-1)*M)`. If HP exceeds `D`
   and reaches `R`, do not heal. Otherwise consider medicines with positive
   gain and post-heal HP above `D`. Let `E = post_heal_HP - M`; if current
   HP already exceeds `D`, reject candidates with `E <= current_HP`.
   Prefer the smallest restoration with `E >= R`; otherwise maximize `E`.
   This is why C can choose a larger medicine than B or heal before half HP.
5. If HP still cannot exceed `D`, attack instead of spending a setup turn.
   Otherwise check B's PP-recovery rule.
6. For pending setup, use Guard Spec first only when configured and an
   active foe still has Sand Attack, Smokescreen, Flash, Kinesis, Octazooka
   or Mud-Slap PP, with Mist absent. Then choose X Special, X Speed,
   X Accuracy in that order when their current targets are unmet.
7. `torrent_power=true` raises the Sp. Atk target while Torrent is off to
   replace its 1.5 multiplier. `target_torrent=true` instead permits an
   opening activation window while multiple foes remain: use an additional
   X Special/X Speed below stage +6, or the weakest damaging move that
   cannot KO the setup foe. Stop stalling once Torrent or equivalent
   Sp. Atk power is achieved. Safety healing can still override this.
8. Otherwise attack. Re-evaluate after every action and opponent change.

These rules are a bounded heuristic with full roster knowledge, not optimal
play or a literal replay of the video's buttons. The openings below are
deterministic previews under the current policy and exact entry variant;
they are **not** a fixed script for subsequent turns.

## Medicine, badges and move semantics

| Item code | Effect in this Gen 3 model |
|---|---|
| potion / superpotion / hyperpotion | Restore 20 / 50 / 200 HP |
| maxpotion / fullrestore | Restore full HP; Full Restore also clears status/confusion |
| awakening / antidote / parlyzheal / burnheal / iceheal | Cure sleep / poison / paralysis / burn / freeze |
| fullheal | Cure major status or confusion |
| oranberry | Restore 10 HP as a bag action |
| ether / maxether | Restore 10 / all PP of one selected move |
| elixir / maxelixir | Restore 10 / all PP of every move |
| xspecial / xspeed / xaccuracy / xattack / xdefend | Raise the named stat one stage, capped at +6 |
| guardspec | Five-turn Mist protection from opposing stat reductions; does not undo existing drops |
| direhit | Focus Energy effect; supported but not selected by this policy |

X Attack, X Defend and Dire Hit are engine capabilities, not actions selected
by this C2 planner. C2 chooses only X Special, X Speed, X Accuracy and Guard
Spec for setup.

Bag use consumes a turn with priority above moves; the foe may still act.
It does not consume move PP or trigger the player's move-only sleep,
paralysis or confusion checks. A locked two-turn move cannot be interrupted
with a bag item. Resting never restocks the battle bag.

Apply badge boosts to raw stats before battle stages, rounding down:
Boulder Atk ×1.1; Thunder Speed ×1.1; Soul Def ×1.1; Volcano Sp. Atk and
Sp. Def ×1.1. Cascade/Rainbow/Marsh/Earth add none of these stat boosts.
Gen 3 uses type-based physical/special categories: Bite is special; Mega
Kick, Strength and Dig are physical. Use Gen 3 move powers and PP, with
no PP Ups. Misses consume PP; prevented attacks do not.

Black Glasses uses the Gen 3 ×1.1 Sp. Atk modifier for Dark moves, rather
than a modern-generation item bonus. NPC Sitrus Berries restore a fixed 30
HP. All listed opponents have zero EVs; their individual IV/nature/ability
and resulting stats are embedded below. Move names identify actions:
the table order is not a verified in-game controller menu-slot mapping.


## Move-learning and evolution decisions

Keep the per-fight moves and PP exactly as listed. Level-up choices below apply whenever the stated level is reached, including during a battle; the event is the observed timing, not a guarantee under a different outcome. New moves start at base PP. Allow the normal Wartortle/Blastoise evolutions at levels 16/36 on this route. Starting species, EXP and stats in each fight remain the entry contract.

| Move | Action | Replace | Acquisition | Observed timing |
|---|---|---|---|---|
| BUBBLE | learn | empty slot / no replacement | Level 7 | route1-pidgey-defeated: after foe 1 |
| WITHDRAW | learn | empty slot / no replacement | Level 10 | pewter-liam: after foe 2 |
| WATER_GUN | learn | TAIL_WHIP | Level 13 | brock: after foe 2 |
| MEGA_KICK | learn | WITHDRAW | tutor | Rare Candy preparation before Misty: before |
| BITE | learn | BUBBLE | Level 19 | Rare Candy preparation before Misty: after |
| WATER_PULSE | learn | TACKLE | TM03 | cerulean-rival: before |
| RAPID_SPIN | decline | empty slot / no replacement | Level 25 | route25-haley: after foe 1 |
| PROTECT | decline | empty slot / no replacement | Level 31 | rocktunnel-oliver: after foe 2 |
| SURF | learn | WATER_GUN | HM03 | fuchsia-kirk: before |
| RAIN_DANCE | decline | empty slot / no replacement | Level 42 | celadon-tamia: after foe 2 |
| BLIZZARD | learn | MEGA_KICK | TM14 | celadon-lori: before |
| STRENGTH | learn | WATER_PULSE | HM04 | lorelei: before |
| SKULL_BASH | decline | empty slot / no replacement | Level 55 | lance: after foe 3 |

Do not teach Dig in these adopted variants. Mega Kick and Bite are already included before Misty; Water Pulse replaces Tackle before Cerulean rival. Surf, Blizzard and Strength replace Water Gun, Mega Kick and Water Pulse at the points above. Decline Rapid Spin, Protect, Rain Dance and Skull Bash.


## Contract and strategy for every fight

Stats are raw summary stats, before badge boosts, in HP/Atk/Def/SpA/SpD/Spe order. EVs are earned totals; the recorded summary stats remain authoritative until live recalculation. The opponent tables below embed the party, moves, IV/nature/ability, stats and held items; NPC medicine slots and AI flags are included for each fight. Solo lead, no player switching, and the NPC/engine approximations of the benchmark still apply.

Each entry starts a fresh battle with zero stat stages before switch-in ability effects, no existing volatile conditions or field effects, and the opposing party at full HP and PP. Badge boosts and Torrent are applied by the engine. EXP/EV awards and level-up learning occur after actual knockouts. The lab rival also enables the modeled tutorial behavior.

Shared starter profile: Mild, IVs HP28/Atk25/Def16/SpA31/SpD21/Spe27, male, Torrent. Every bag below is the complete supported battle-consumable bag, not a minimum shopping list. Unlisted battle items are unavailable; no items are silently replenished by resting.

### lab-rival

Opponent: `TRAINER_RIVAL_OAKS_LAB_BULBASAUR` — BULBASAUR Lv5.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| BULBASAUR (Grass/Poison) Lv5 | Impish; all IVs 0; M; overgrow | 19/9/9/9/11/9 | TACKLE (35), GROWL (40) | none |

SQUIRTLE Lv5; EXP 135; raw stats 20/11/10/12/12/10; earned EVs 0/0/0/0/0/0; status clear; held item none; badges none.

Battle bag: none.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 20/20 full; Torrent off | TACKLE: 35/35, TAIL_WHIP: 30/30 | Use TACKLE | 345/360 (95.8%) | 89.0%–99.1% |
| prepared | 20/20 full; Torrent off | TACKLE: 35/35, TAIL_WHIP: 30/30 | Use TACKLE | 345/360 (95.8%) | 89.0%–99.1% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### forest-sammy

Opponent: `TRAINER_BUG_CATCHER_SAMMY` — WEEDLE Lv9.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| WEEDLE (Bug/Poison) Lv9 | Serious; all IVs 0; M; shielddust | 26/11/10/8/8/14 | POISON_STING (35), STRING_SHOT (40) | none |

SQUIRTLE Lv7; EXP 241; raw stats 25/13/13/15/15/12; earned EVs 0/0/0/1/0/2; status clear; held item none; badges none.

Battle bag: antidote ×1.

Player strategy: B. Policy: `B:solo-recovery/1`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Before prepared entry: Restore HP and PP before the Forest trainer; a Viridian Center backtrack is allowed. Full HP, full PP and clear status are required.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 16/25 partial; Torrent off | TACKLE: 28/35, TAIL_WHIP: 30/30, BUBBLE: 29/30 | Use BUBBLE | 830/960 (86.5%) | 80.6%–91.1% |
| prepared | 25/25 full; Torrent off | TACKLE: 35/35, TAIL_WHIP: 30/30, BUBBLE: 30/30 | Use BUBBLE | 158/160 (98.8%) | 90.0%–100.0% |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 12.

### pewter-liam

Opponent: `TRAINER_CAMPER_LIAM` — GEODUDE Lv10, SANDSHREW Lv11.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GEODUDE (Rock/Ground) Lv10 | Jolly; all IVs 0; M; rockhead | 28/21/25/9/11/9 | TACKLE (35), DEFENSE_CURL (40) | none |
| SANDSHREW (Ground) Lv11 | Sassy; all IVs 0; M; sandveil | 32/21/23/9/12/11 | SCRATCH (35), DEFENSE_CURL (40), SAND_ATTACK (15) | none |

SQUIRTLE Lv8; EXP 340; raw stats 27/14/14/16/16/14; earned EVs 0/0/0/1/0/3; status clear; held item none; badges none.

Battle bag: antidote ×1.

Player strategy: A. Policy: `B:solo-recovery/1`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Before prepared entry: Pewter Center before entering the Gym. Full HP, full PP and clear status are required.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 5/27 partial; Torrent on | TACKLE: 28/35, TAIL_WHIP: 30/30, BUBBLE: 25/30 | Use BUBBLE | 1225/1880 (65.2%) | 59.7%–70.3% |
| prepared | 27/27 full; Torrent off | TACKLE: 35/35, TAIL_WHIP: 30/30, BUBBLE: 30/30 | Use BUBBLE | 120/120 (100.0%) | 91.5%–100.0% |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 12.

### brock

Opponent: `TRAINER_LEADER_BROCK` — GEODUDE Lv12, ONIX Lv14.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GEODUDE (Rock/Ground) Lv12 | Jolly; all IVs 0; M; rockhead | 31/24/29/10/12/9 | TACKLE (35), DEFENSE_CURL (40) | none |
| ONIX (Rock/Ground) Lv14 | Careful; all IVs 0; M; rockhead | 33/17/49/11/18/24 | TACKLE (35), BIND (20), ROCK_TOMB (10) | none |

SQUIRTLE Lv11; EXP 742; raw stats 33/18/18/20/21/17; earned EVs 0/0/2/1/0/3; status clear; held item none; badges none.

Battle bag: antidote ×1.

Player strategy: A. Policy: `B:solo-recovery/1`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Before prepared entry: Pewter Center after Liam and before Brock. Full HP, full PP and clear status are required.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 11/33 partial; Torrent on | TACKLE: 26/35, TAIL_WHIP: 30/30, BUBBLE: 22/30, WITHDRAW: 40/40 | Use BUBBLE | 1109/2060 (53.8%) | 48.5%–59.1% |
| prepared | 33/33 full; Torrent off | TACKLE: 35/35, TAIL_WHIP: 30/30, BUBBLE: 30/30, WITHDRAW: 40/40 | Use BUBBLE | 120/120 (100.0%) | 91.5%–100.0% |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 12.

### route3-colton

Opponent: `TRAINER_BUG_CATCHER_COLTON` — CATERPIE Lv10, WEEDLE Lv10, CATERPIE Lv10.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| CATERPIE (Bug) Lv10 | Gentle; all IVs 0; M; shielddust | 29/11/10/9/9/14 | TACKLE (35), STRING_SHOT (40) | none |
| WEEDLE (Bug/Poison) Lv10 | Hasty; all IVs 0; M; shielddust | 28/12/9/9/9/16 | POISON_STING (35), STRING_SHOT (40) | none |
| CATERPIE (Bug) Lv10 | Gentle; all IVs 0; M; shielddust | 29/11/10/9/9/14 | TACKLE (35), STRING_SHOT (40) | none |

SQUIRTLE Lv13; EXP 1286; raw stats 38/20/21/24/24/19; earned EVs 0/0/4/1/0/3; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 6/38 partial; Torrent on | TACKLE: 26/35, BUBBLE: 20/30, WITHDRAW: 40/40, WATER_GUN: 25/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 6/38 partial; Torrent on | TACKLE: 26/35, BUBBLE: 20/30, WITHDRAW: 40/40, WATER_GUN: 25/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route3-greg

Opponent: `TRAINER_BUG_CATCHER_GREG` — WEEDLE Lv9, KAKUNA Lv9, CATERPIE Lv9, METAPOD Lv9.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| WEEDLE (Bug/Poison) Lv9 | Quiet; all IVs 0; M; shielddust | 26/11/10/8/8/12 | POISON_STING (35), STRING_SHOT (40) | none |
| KAKUNA (Bug/Poison) Lv9 | Adamant; all IVs 0; M; shedskin | 27/9/14/8/9/11 | HARDEN (30) | none |
| CATERPIE (Bug) Lv9 | Naughty; all IVs 0; M; shielddust | 27/11/11/8/7/13 | TACKLE (35), STRING_SHOT (40) | none |
| METAPOD (Bug) Lv9 | Gentle; all IVs 0; M; shedskin | 28/8/12/9/9/10 | HARDEN (30) | none |

SQUIRTLE Lv14; EXP 1621; raw stats 40/21/22/25/25/20; earned EVs 2/0/4/1/0/4; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 8/40 partial; Torrent on | TACKLE: 26/35, BUBBLE: 20/30, WITHDRAW: 40/40, WATER_GUN: 22/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 8/40 partial; Torrent on | TACKLE: 26/35, BUBBLE: 20/30, WITHDRAW: 40/40, WATER_GUN: 22/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route3-james

Opponent: `TRAINER_BUG_CATCHER_JAMES` — CATERPIE Lv11, METAPOD Lv11.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| CATERPIE (Bug) Lv11 | Rash; all IVs 0; M; shielddust | 30/11/12/9/8/14 | TACKLE (35), STRING_SHOT (40) | none |
| METAPOD (Bug) Lv11 | Bashful; all IVs 0; M; shedskin | 32/9/17/10/10/11 | HARDEN (30) | none |

SQUIRTLE Lv15; EXP 2096; raw stats 42/23/24/26/27/22; earned EVs 3/0/8/1/0/5; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 10/42 partial; Torrent on | TACKLE: 26/35, BUBBLE: 20/30, WITHDRAW: 40/40, WATER_GUN: 18/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 10/42 partial; Torrent on | TACKLE: 26/35, BUBBLE: 20/30, WITHDRAW: 40/40, WATER_GUN: 18/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### mtmoon-josh

Opponent: `TRAINER_YOUNGSTER_JOSH` — RATTATA Lv10, RATTATA Lv10, ZUBAT Lv10.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| RATTATA (Normal) Lv10 | Timid; all IVs 0; M; runaway | 26/14/12/10/12/20 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30) | none |
| RATTATA (Normal) Lv10 | Lax; all IVs 0; M; runaway | 26/16/13/10/10/19 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30) | none |
| ZUBAT (Poison/Flying) Lv10 | Timid; all IVs 0; M; innerfocus | 28/12/12/11/13/17 | LEECH_LIFE (15), ASTONISH (15) | none |

SQUIRTLE Lv15; EXP 2389; raw stats 42/23/24/26/27/22; earned EVs 4/0/10/1/0/5; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: B. Policy: `B:solo-recovery/1`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Before prepared entry: Route 4 Center before entering Mt. Moon; flee intervening wild encounters. Full HP, full PP and clear status are required.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 10/42 partial; Torrent on | TACKLE: 26/35, BUBBLE: 19/30, WITHDRAW: 40/40, WATER_GUN: 16/25 | Use WATER_GUN | 919/1100 (83.5%) | 77.8%–88.4% |
| prepared | 42/42 full; Torrent off | TACKLE: 35/35, BUBBLE: 30/30, WITHDRAW: 40/40, WATER_GUN: 25/25 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 11.

### mtmoon-rocket

Opponent: `TRAINER_TEAM_ROCKET_GRUNT` — RATTATA Lv13, ZUBAT Lv13.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| RATTATA (Normal) Lv13 | Rash; all IVs 0; M; runaway | 30/19/14/12/12/23 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15) | none |
| ZUBAT (Poison/Flying) Lv13 | Naughty; all IVs 0; M; innerfocus | 33/17/14/12/13/19 | LEECH_LIFE (15), ASTONISH (15), SUPERSONIC (20) | none |

WARTORTLE Lv16; EXP 2746; raw stats 49/29/29/33/33/28; earned EVs 4/0/10/1/0/8; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 10/49 partial; Torrent on | TACKLE: 26/35, BUBBLE: 19/30, WITHDRAW: 40/40, WATER_GUN: 12/25 | Use WATER_GUN | 158/160 (98.8%) | 90.0%–100.0% |
| prepared | 10/49 partial; Torrent on | TACKLE: 26/35, BUBBLE: 19/30, WITHDRAW: 40/40, WATER_GUN: 12/25 | Use WATER_GUN | 158/160 (98.8%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### mtmoon-miguel

Opponent: `TRAINER_SUPER_NERD_MIGUEL` — GRIMER Lv12, VOLTORB Lv12, KOFFING Lv12.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GRIMER (Poison) Lv12 | Hardy; all IVs 0; M; stench | 41/24/17/14/17/11 | POISON_GAS (40), POUND (35), HARDEN (30), DISABLE (20) | none |
| VOLTORB (Electric) Lv12 | Lax; all IVs 0; N; soundproof | 31/12/18/18/16/29 | CHARGE (20), TACKLE (35), SCREECH (40) | none |
| KOFFING (Poison) Lv12 | Brave; all IVs 0; M; levitate | 31/22/27/19/15/11 | POISON_GAS (40), TACKLE (35), SMOG (20) | none |

WARTORTLE Lv16; EXP 3053; raw stats 49/29/29/33/33/28; earned EVs 4/0/10/1/0/10; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×9.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 10/49 partial; Torrent on | TACKLE: 26/35, BUBBLE: 19/30, WITHDRAW: 40/40, WATER_GUN: 10/25 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 10/49 partial; Torrent on | TACKLE: 26/35, BUBBLE: 19/30, WITHDRAW: 40/40, WATER_GUN: 10/25 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### misty

Opponent: `TRAINER_LEADER_MISTY` — STARYU Lv18, STARMIE Lv21.

NPC medicine slots, in source order: SUPER_POTION. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| STARYU (Water) Lv18 | Hasty; all IVs 0; N; illuminate | 38/21/21/30/24/38 | TACKLE (35), HARDEN (30), RECOVER (20), WATER_PULSE (20) | none |
| STARMIE (Water/Psychic) Lv21 | Naughty; all IVs 0; N; illuminate | 56/39/40/47/36/53 | SWIFT (20), RECOVER (20), RAPID_SPIN (40), WATER_PULSE (20) | none |

WARTORTLE Lv20; EXP 5460; raw stats 59/35/36/40/41/34; earned EVs 5/0/11/1/0/11; status clear; held item none; badges boulder.

Battle bag: antidote ×1, awakening ×3, potion ×7.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 54/59 partial; Torrent off | TACKLE: 26/35, WATER_GUN: 5/25, MEGA_KICK: 5/5, BITE: 25/25 | Use BITE | 177/180 (98.3%) | 89.8%–100.0% |
| prepared | 54/59 partial; Torrent off | TACKLE: 26/35, WATER_GUN: 5/25, MEGA_KICK: 5/5, BITE: 25/25 | Use BITE | 177/180 (98.3%) | 89.8%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### cerulean-rival

Opponent: `TRAINER_RIVAL_CERULEAN_BULBASAUR` — PIDGEOTTO Lv17, ABRA Lv16, RATTATA Lv15, BULBASAUR Lv18.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEOTTO (Normal/Flying) Lv17 | Quiet; all IVs 6; M; keeneye | 49/26/24/25/23/27 | TACKLE (35), SAND_ATTACK (15), GUST (35), QUICK_ATTACK (30) | none |
| ABRA (Psychic) Lv16 | Lax; all IVs 6; M; synchronize | 34/12/11/39/20/34 | TELEPORT (20) | none |
| RATTATA (Normal) Lv15 | Adamant; all IVs 6; M; runaway | 34/24/16/11/16/27 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30) | none |
| BULBASAUR (Grass/Poison) Lv18 | Hardy; all IVs 12; M; overgrow | 46/24/24/30/30/23 | SLEEP_POWDER (15), POISON_POWDER (35), VINE_WHIP (10), LEECH_SEED (10) | none |

WARTORTLE Lv21; EXP 6799; raw stats 61/36/37/41/43/35; earned EVs 5/0/11/1/0/14; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: B. Policy: `B:solo-recovery/1`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Before prepared entry: Cerulean Center after Misty and before the bridge rival. Full HP, full PP and clear status are required.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 32/61 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 5/5, BITE: 22/25, WATER_PULSE: 20/20 | Use WATER_PULSE | 932/2060 (45.2%) | 40.0%–50.6% |
| prepared | 61/61 full; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 20/20 | Use WATER_PULSE | 1148/1520 (75.5%) | 70.0%–80.6% |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 11.

### bridge-cale

Opponent: `TRAINER_BUG_CATCHER_CALE` — CATERPIE Lv10, WEEDLE Lv10, METAPOD Lv10, KAKUNA Lv10.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| CATERPIE (Bug) Lv10 | Mild; all IVs 0; M; shielddust | 29/11/10/9/9/14 | TACKLE (35), STRING_SHOT (40) | none |
| WEEDLE (Bug/Poison) Lv10 | Lonely; all IVs 0; M; shielddust | 28/13/9/9/9/15 | POISON_STING (35), STRING_SHOT (40) | none |
| METAPOD (Bug) Lv10 | Sassy; all IVs 0; M; shedskin | 30/9/16/10/11/9 | HARDEN (30) | none |
| KAKUNA (Bug/Poison) Lv10 | Serious; all IVs 0; M; shedskin | 29/10/15/10/10/12 | HARDEN (30) | none |

WARTORTLE Lv22; EXP 7888; raw stats 64/38/39/44/44/37; earned EVs 5/0/11/3/0/17; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 22/64 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 4/5, BITE: 20/25, WATER_PULSE: 17/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 22/64 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 4/5, BITE: 20/25, WATER_PULSE: 17/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-ali

Opponent: `TRAINER_LASS_ALI` — PIDGEY Lv12, ODDISH Lv12, BELLSPROUT Lv12.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEY (Normal/Flying) Lv12 | Quiet; all IVs 0; F; keeneye | 31/15/14/14/13/16 | TACKLE (35), SAND_ATTACK (15), GUST (35) | none |
| ODDISH (Grass/Poison) Lv12 | Sassy; all IVs 0; F; chlorophyll | 32/17/18/23/22/10 | ABSORB (20), SWEET_SCENT (20) | none |
| BELLSPROUT (Grass/Poison) Lv12 | Brave; all IVs 0; F; chlorophyll | 34/25/13/21/12/12 | VINE_WHIP (10), GROWTH (40), WRAP (20) | none |

WARTORTLE Lv22; EXP 8415; raw stats 64/38/39/44/44/37; earned EVs 6/0/15/3/0/18; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 22/64 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 4/5, BITE: 16/25, WATER_PULSE: 17/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 22/64 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 4/5, BITE: 16/25, WATER_PULSE: 17/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-timmy

Opponent: `TRAINER_YOUNGSTER_TIMMY` — SANDSHREW Lv14, EKANS Lv14.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| SANDSHREW (Ground) Lv14 | Docile; all IVs 0; M; sandveil | 38/26/28/10/13/16 | SCRATCH (35), DEFENSE_CURL (40), SAND_ATTACK (15) | none |
| EKANS (Poison) Lv14 | Gentle; all IVs 0; M; intimidate | 33/21/15/16/22/20 | WRAP (20), LEER (30), POISON_STING (35), BITE (25) | none |

WARTORTLE Lv23; EXP 8971; raw stats 66/39/41/46/46/38; earned EVs 6/1/15/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 14/25, WATER_PULSE: 17/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 14/25, WATER_PULSE: 17/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-reli

Opponent: `TRAINER_LASS_RELI` — NIDORAN_M Lv16, NIDORAN_F Lv16.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| NIDORAN_M (Poison) Lv16 | Gentle; all IVs 0; M; poisonpoint | 40/23/15/17/18/21 | LEER (30), PECK (35), FOCUS_ENERGY (30), DOUBLE_KICK (30) | none |
| NIDORAN_F (Poison) Lv16 | Adamant; all IVs 0; F; poisonpoint | 43/22/21/15/17/18 | GROWL (40), SCRATCH (35), TAIL_WHIP (30), DOUBLE_KICK (30) | none |

WARTORTLE Lv23; EXP 9436; raw stats 66/39/41/46/46/38; earned EVs 6/2/16/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 16/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 16/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-ethan

Opponent: `TRAINER_CAMPER_ETHAN` — MANKEY Lv18.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| MANKEY (Fighting) Lv18 | Naive; all IVs 0; M; vitalspirit | 42/33/17/17/18/33 | LEER (30), LOW_KICK (20), KARATE_CHOP (25), FURY_SWIPES (15) | none |

WARTORTLE Lv23; EXP 9842; raw stats 66/39/41/46/46/38; earned EVs 7/3/16/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 14/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 14/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### bridge-rocket

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_6` — EKANS Lv15, ZUBAT Lv15.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| EKANS (Poison) Lv15 | Lonely; all IVs 0; M; intimidate | 35/25/16/17/21/21 | WRAP (20), LEER (30), POISON_STING (35), BITE (25) | none |
| ZUBAT (Poison/Flying) Lv15 | Hasty; all IVs 0; M; innerfocus | 37/18/13/14/17/23 | LEECH_LIFE (15), ASTONISH (15), SUPERSONIC (20) | none |

WARTORTLE Lv23; EXP 10127; raw stats 66/39/41/46/46/38; earned EVs 7/4/16/4/0/19; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 13/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/66 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 13/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-wayne

Opponent: `TRAINER_HIKER_WAYNE` — ONIX Lv17.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ONIX (Rock/Ground) Lv17 | Timid; all IVs 0; M; rockhead | 38/18/59/15/20/30 | TACKLE (35), SCREECH (40), BIND (20), ROCK_THROW (15) | none |

WARTORTLE Lv24; EXP 10497; raw stats 69/41/43/47/48/40; earned EVs 7/5/16/4/0/20; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 11/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 11/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-kelsey

Opponent: `TRAINER_PICNICKER_KELSEY` — NIDORAN_M Lv15, NIDORAN_F Lv15.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| NIDORAN_M (Poison) Lv15 | Lonely; all IVs 0; M; poisonpoint | 38/24/15/17/17/20 | LEER (30), PECK (35), FOCUS_ENERGY (30), DOUBLE_KICK (30) | none |
| NIDORAN_F (Poison) Lv15 | Jolly; all IVs 0; F; poisonpoint | 41/19/20/15/17/18 | GROWL (40), SCRATCH (35), TAIL_WHIP (30), DOUBLE_KICK (30) | none |

WARTORTLE Lv24; EXP 10890; raw stats 69/41/43/47/48/40; earned EVs 7/5/17/4/0/20; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 10/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 10/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-flint

Opponent: `TRAINER_CAMPER_FLINT` — RATTATA Lv14, EKANS Lv14.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| RATTATA (Normal) Lv14 | Bold; all IVs 0; M; runaway | 32/18/15/12/14/25 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15) | none |
| EKANS (Poison) Lv14 | Docile; all IVs 0; M; intimidate | 33/21/17/16/20/20 | WRAP (20), LEER (30), POISON_STING (35), BITE (25) | none |

WARTORTLE Lv24; EXP 11271; raw stats 69/41/43/47/48/40; earned EVs 8/6/17/4/0/20; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 8/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 8/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route25-haley

Opponent: `TRAINER_LASS_HALEY` — ODDISH Lv13, PIDGEY Lv13, ODDISH Lv13.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ODDISH (Grass/Poison) Lv13 | Docile; all IVs 0; F; chlorophyll | 34/18/19/24/21/12 | ABSORB (20), SWEET_SCENT (20) | none |
| PIDGEY (Normal/Flying) Lv13 | Lax; all IVs 0; F; keeneye | 33/16/16/14/12/19 | TACKLE (35), SAND_ATTACK (15), GUST (35), QUICK_ATTACK (30) | none |
| ODDISH (Grass/Poison) Lv13 | Calm; all IVs 0; F; chlorophyll | 34/16/19/24/23/12 | ABSORB (20), SWEET_SCENT (20) | none |

WARTORTLE Lv24; EXP 11628; raw stats 69/41/43/47/48/40; earned EVs 8/7/17/4/0/21; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, potion ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 6/20 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/69 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 13/25, WATER_PULSE: 6/20 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### cerulean-dig-rocket

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_5` — MACHOP Lv17, DROWZEE Lv17.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| MACHOP (Fighting) Lv17 | Adamant; all IVs 0; M; guts | 50/35/22/14/16/16 | LOW_KICK (20), LEER (30), FOCUS_ENERGY (30), KARATE_CHOP (25) | none |
| DROWZEE (Psychic) Lv17 | Lonely; all IVs 0; M; insomnia | 47/23/18/19/35/19 | HYPNOSIS (20), DISABLE (20), CONFUSION (25), HEADBUTT (15) | none |

WARTORTLE Lv25; EXP 12213; raw stats 72/43/45/49/50/42; earned EVs 8/7/17/6/0/22; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, potion ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/72 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 5/5, BITE: 12/25, WATER_PULSE: 6/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/72 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 5/5, BITE: 12/25, WATER_PULSE: 6/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route6-jeff

Opponent: `TRAINER_CAMPER_JEFF` — SPEAROW Lv16, RATICATE Lv16.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| SPEAROW (Normal/Flying) Lv16 | Docile; all IVs 0; M; keeneye | 38/24/14/14/14/27 | PECK (35), GROWL (40), LEER (30), FURY_ATTACK (20) | none |
| RATICATE (Normal) Lv16 | Sassy; all IVs 0; M; runaway | 43/30/24/21/29/32 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15) | none |

WARTORTLE Lv25; EXP 12902; raw stats 72/43/45/49/50/42; earned EVs 8/8/17/6/1/22; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, potion ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 21/72 partial; Torrent on | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 12/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 21/72 partial; Torrent on | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 12/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### ssanne-rival

Opponent: `TRAINER_RIVAL_SS_ANNE_BULBASAUR` — PIDGEOTTO Lv19, RATICATE Lv16, KADABRA Lv18, IVYSAUR Lv20.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEOTTO (Normal/Flying) Lv19 | Quiet; all IVs 6; M; keeneye | 54/28/27/27/25/29 | TACKLE (35), SAND_ATTACK (15), GUST (35), QUICK_ATTACK (30) | none |
| RATICATE (Normal) Lv16 | Adamant; all IVs 6; M; runaway | 44/34/25/18/28/37 | TACKLE (35), TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15) | none |
| KADABRA (Psychic) Lv18 | Naive; all IVs 6; M; synchronize | 43/18/16/49/27/47 | TELEPORT (20), KINESIS (15), CONFUSION (25), DISABLE (20) | none |
| IVYSAUR (Grass/Poison) Lv20 | Serious; all IVs 12; M; overgrow | 56/32/32/39/39/31 | LEECH_SEED (10), VINE_WHIP (10), POISON_POWDER (35), SLEEP_POWDER (15) | none |

WARTORTLE Lv27; EXP 15244; raw stats 76/46/47/52/53/45; earned EVs 8/8/17/6/1/25; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `B:solo-recovery/1`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Before prepared entry: Accept the 1F Room 6 cabin rest before the rival. Full HP, full PP and clear status are required.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 37/76 partial; Torrent off | WATER_GUN: 5/25, MEGA_KICK: 3/5, BITE: 12/25, WATER_PULSE: 3/20 | Use potion | 1025/2080 (49.3%) | 44.0%–54.6% |
| prepared | 76/76 full; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 20/20 | Use WATER_GUN | 1136/1500 (75.7%) | 70.2%–80.8% |

Result source: recorded — preparation control, seed 11; prepared — full rest, seed 11.

### vermilion-tucker

Opponent: `TRAINER_GENTLEMAN_TUCKER` — PIKACHU Lv23.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIKACHU (Electric) Lv23 | Lonely; all IVs 0; M; static | 49/33/16/28/23/46 | THUNDER_WAVE (20), QUICK_ATTACK (30), DOUBLE_TEAM (15), SLAM (20) | none |

WARTORTLE Lv28; EXP 17261; raw stats 79/47/49/55/55/47; earned EVs 8/8/17/9/2/29; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 79/79 full; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 20/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 79/79 full; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 20/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### surge

Opponent: `TRAINER_LEADER_LT_SURGE` — VOLTORB Lv21, PIKACHU Lv18, RAICHU Lv24.

NPC medicine slots, in source order: SUPER_POTION, FULL_HEAL. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| VOLTORB (Electric) Lv21 | Lax; all IVs 0; N; soundproof | 47/17/28/28/25/47 | SONIC_BOOM (20), TACKLE (35), SCREECH (40), SHOCK_WAVE (20) | none |
| PIKACHU (Electric) Lv18 | Sassy; all IVs 0; M; static | 40/24/15/23/20/33 | QUICK_ATTACK (30), THUNDER_WAVE (20), DOUBLE_TEAM (15), SHOCK_WAVE (20) | none |
| RAICHU (Electric) Lv24 | Modest; all IVs 0; M; static | 62/43/31/52/43/53 | QUICK_ATTACK (30), THUNDER_WAVE (20), DOUBLE_TEAM (15), SHOCK_WAVE (20) | none |

WARTORTLE Lv28; EXP 17664; raw stats 79/47/49/55/55/47; earned EVs 8/8/17/9/2/31; status clear; held item none; badges boulder, cascade.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `B:solo-recovery/1`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 79/79 full; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 19/20 | Use WATER_PULSE | 1147/2040 (56.2%) | 50.9%–61.5% |
| prepared | 79/79 full; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 19/20 | Use WATER_PULSE | 1147/2040 (56.2%) | 50.9%–61.5% |

Result source: recorded — preparation control, seed 11; prepared — preparation control, seed 11.

### route9-alicia

Opponent: `TRAINER_PICNICKER_ALICIA` — ODDISH Lv18, BELLSPROUT Lv18, ODDISH Lv18, BELLSPROUT Lv18.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ODDISH (Grass/Poison) Lv18 | Lonely; all IVs 0; F; chlorophyll | 44/25/21/32/28/15 | SWEET_SCENT (20), POISON_POWDER (35), STUN_SPORE (30), SLEEP_POWDER (15) | none |
| BELLSPROUT (Grass/Poison) Lv18 | Relaxed; all IVs 0; F; chlorophyll | 46/32/18/30/15/17 | GROWTH (40), WRAP (20), SLEEP_POWDER (15), POISON_POWDER (35) | none |
| ODDISH (Grass/Poison) Lv18 | Jolly; all IVs 0; F; chlorophyll | 44/23/24/28/28/16 | SWEET_SCENT (20), POISON_POWDER (35), STUN_SPORE (30), SLEEP_POWDER (15) | none |
| BELLSPROUT (Grass/Poison) Lv18 | Rash; all IVs 0; F; chlorophyll | 46/32/17/33/13/19 | GROWTH (40), WRAP (20), SLEEP_POWDER (15), POISON_POWDER (35) | none |

WARTORTLE Lv28; EXP 19069; raw stats 79/47/49/55/55/47; earned EVs 8/8/17/9/2/37; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 43/79 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 4/5, BITE: 25/25, WATER_PULSE: 16/20 | Use MEGA_KICK | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 43/79 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 4/5, BITE: 25/25, WATER_PULSE: 16/20 | Use MEGA_KICK | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route9-conner

Opponent: `TRAINER_BUG_CATCHER_CONNER` — CATERPIE Lv20, WEEDLE Lv20, VENONAT Lv20.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| CATERPIE (Bug) Lv20 | Hasty; all IVs 0; M; shielddust | 48/17/17/13/13/25 | TACKLE (35), STRING_SHOT (40) | none |
| WEEDLE (Bug/Poison) Lv20 | Mild; all IVs 0; M; shielddust | 46/19/15/14/13/25 | POISON_STING (35), STRING_SHOT (40) | none |
| VENONAT (Bug/Poison) Lv20 | Lax; all IVs 0; M; compoundeyes | 54/27/27/21/24/23 | FORESIGHT (40), SUPERSONIC (20), CONFUSION (25), POISON_POWDER (35) | none |

WARTORTLE Lv29; EXP 20317; raw stats 81/49/51/57/57/49; earned EVs 8/10/17/11/2/37; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, elixir ×1, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 45/81 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 2/5, BITE: 23/25, WATER_PULSE: 16/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 45/81 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 2/5, BITE: 23/25, WATER_PULSE: 16/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-ashton

Opponent: `TRAINER_POKEMANIAC_ASHTON` — CUBONE Lv23, SLOWPOKE Lv23.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| CUBONE (Ground) Lv23 | Hardy; all IVs 3; M; rockhead | 56/28/49/24/28/21 | BONE_CLUB (20), HEADBUTT (15), LEER (30), FOCUS_ENERGY (30) | none |
| SLOWPOKE (Water/Psychic) Lv23 | Relaxed; all IVs 3; M; oblivious | 75/35/38/24/24/10 | TACKLE (35), GROWL (40), WATER_GUN (25), CONFUSION (25) | none |

WARTORTLE Lv29; EXP 21086; raw stats 81/49/51/57/57/49; earned EVs 9/10/17/11/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 45/81 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 20/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 45/81 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 25/25, WATER_PULSE: 20/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-winston

Opponent: `TRAINER_POKEMANIAC_WINSTON` — SLOWPOKE Lv25.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| SLOWPOKE (Water/Psychic) Lv25 | Docile; all IVs 3; M; oblivious | 80/38/38/25/25/13 | GROWL (40), WATER_GUN (25), CONFUSION (25), DISABLE (20) | none |

WARTORTLE Lv30; EXP 22000; raw stats 84/50/53/58/59/50; earned EVs 10/10/18/11/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 42/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 23/25, WATER_PULSE: 19/20 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 42/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 23/25, WATER_PULSE: 19/20 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-martha

Opponent: `TRAINER_PICNICKER_MARTHA` — ODDISH Lv22, BULBASAUR Lv22.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ODDISH (Grass/Poison) Lv22 | Relaxed; all IVs 0; F; chlorophyll | 51/27/31/38/33/16 | SWEET_SCENT (20), POISON_POWDER (35), STUN_SPORE (30), SLEEP_POWDER (15) | none |
| BULBASAUR (Grass/Poison) Lv22 | Calm; all IVs 0; M; overgrow | 51/23/26/33/36/24 | VINE_WHIP (10), POISON_POWDER (35), SLEEP_POWDER (15), RAZOR_LEAF (25) | none |

WARTORTLE Lv30; EXP 22529; raw stats 84/50/53/58/59/50; earned EVs 11/10/18/11/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 39/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 21/25, WATER_PULSE: 19/20 | Use potion | 215/220 (97.7%) | 89.8%–99.9% |
| prepared | 39/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 5/5, BITE: 21/25, WATER_PULSE: 19/20 | Use potion | 215/220 (97.7%) | 89.8%–99.9% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-allen

Opponent: `TRAINER_HIKER_ALLEN` — GEODUDE Lv25.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GEODUDE (Rock/Ground) Lv25 | Impish; all IVs 0; M; rockhead | 55/45/60/18/20/15 | MAGNITUDE (30), ROCK_THROW (15), MUD_SPORT (15), DEFENSE_CURL (40) | none |

WARTORTLE Lv30; EXP 23197; raw stats 84/50/53/58/59/50; earned EVs 11/10/18/13/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 39/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 21/25, WATER_PULSE: 19/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 39/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 21/25, WATER_PULSE: 19/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-oliver

Opponent: `TRAINER_HIKER_OLIVER` — ONIX Lv20, ONIX Lv20, GEODUDE Lv20.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ONIX (Rock/Ground) Lv20 | Naughty; all IVs 0; M; rockhead | 44/25/69/17/20/33 | SCREECH (40), BIND (20), ROCK_THROW (15), HARDEN (30) | none |
| ONIX (Rock/Ground) Lv20 | Sassy; all IVs 0; M; rockhead | 44/23/69/17/25/29 | SCREECH (40), BIND (20), ROCK_THROW (15), HARDEN (30) | none |
| GEODUDE (Rock/Ground) Lv20 | Relaxed; all IVs 0; M; rockhead | 46/37/49/17/17/11 | DEFENSE_CURL (40), MUD_SPORT (15), ROCK_THROW (15), MAGNITUDE (30) | none |

WARTORTLE Lv30; EXP 23657; raw stats 84/50/53/58/59/50; earned EVs 11/10/19/13/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 39/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 21/25, WATER_PULSE: 18/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 39/84 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 21/25, WATER_PULSE: 18/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-sofia

Opponent: `TRAINER_PICNICKER_SOFIA` — JIGGLYPUFF Lv21, PIDGEY Lv21, MEOWTH Lv21.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| JIGGLYPUFF (Normal) Lv21 | Quirky; all IVs 0; F; cutecharm | 79/23/13/23/15/13 | DEFENSE_CURL (40), POUND (35), DISABLE (20), ROLLOUT (20) | none |
| PIDGEY (Normal/Flying) Lv21 | Gentle; all IVs 0; F; keeneye | 47/23/18/19/20/28 | SAND_ATTACK (15), GUST (35), QUICK_ATTACK (30), WHIRLWIND (20) | none |
| MEOWTH (Normal) Lv21 | Lonely; all IVs 0; F; pickup | 47/25/17/21/21/42 | SCRATCH (35), GROWL (40), BITE (25), PAY_DAY (20) | none |

WARTORTLE Lv31; EXP 24948; raw stats 86/52/54/60/61/52; earned EVs 11/10/22/13/3/38; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 41/86 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 18/25, WATER_PULSE: 17/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 41/86 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 18/25, WATER_PULSE: 17/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-dudley

Opponent: `TRAINER_HIKER_DUDLEY` — GEODUDE Lv21, GEODUDE Lv21, GRAVELER Lv21.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GEODUDE (Rock/Ground) Lv21 | Hasty; all IVs 0; M; rockhead | 47/38/42/17/17/14 | MAGNITUDE (30), ROCK_THROW (15), MUD_SPORT (15), DEFENSE_CURL (40) | none |
| GEODUDE (Rock/Ground) Lv21 | Hasty; all IVs 0; M; rockhead | 47/38/42/17/17/14 | MAGNITUDE (30), ROCK_THROW (15), MUD_SPORT (15), DEFENSE_CURL (40) | none |
| GRAVELER (Rock/Ground) Lv21 | Naive; all IVs 0; M; rockhead | 54/44/53/23/20/20 | MAGNITUDE (30), ROCK_THROW (15), MUD_SPORT (15), DEFENSE_CURL (40) | none |

WARTORTLE Lv31; EXP 25847; raw stats 86/52/54/60/61/52; earned EVs 13/10/22/13/3/40; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 41/86 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 18/25, WATER_PULSE: 14/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 41/86 partial; Torrent off | WATER_GUN: 25/25, MEGA_KICK: 3/5, BITE: 18/25, WATER_PULSE: 14/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### rocktunnel-dana

Opponent: `TRAINER_PICNICKER_DANA` — MEOWTH Lv20, ODDISH Lv20, PIDGEY Lv20.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| MEOWTH (Normal) Lv20 | Naughty; all IVs 0; F; pickup | 46/25/19/21/18/41 | SCRATCH (35), GROWL (40), BITE (25), PAY_DAY (20) | none |
| ODDISH (Grass/Poison) Lv20 | Jolly; all IVs 0; F; chlorophyll | 48/25/27/31/31/18 | SWEET_SCENT (20), POISON_POWDER (35), STUN_SPORE (30), SLEEP_POWDER (15) | none |
| PIDGEY (Normal/Flying) Lv20 | Naive; all IVs 0; F; keeneye | 46/23/21/19/17/29 | SAND_ATTACK (15), GUST (35), QUICK_ATTACK (30), WHIRLWIND (20) | none |

WARTORTLE Lv32; EXP 27224; raw stats 89/53/56/62/62/53; earned EVs 13/10/26/13/3/40; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 44/89 partial; Torrent off | WATER_GUN: 24/25, MEGA_KICK: 3/5, BITE: 16/25, WATER_PULSE: 14/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 44/89 partial; Torrent off | WATER_GUN: 24/25, MEGA_KICK: 3/5, BITE: 16/25, WATER_PULSE: 14/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route8-rich

Opponent: `TRAINER_GAMER_RICH` — GROWLITHE Lv24, VULPIX Lv24.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GROWLITHE (Fire) Lv24 | Quirky; all IVs 0; M; intimidate | 60/38/26/38/29/33 | ROAR (20), EMBER (25), LEER (30), ODOR_SLEUTH (40) | none |
| VULPIX (Fire) Lv24 | Hasty; all IVs 0; F; flashfire | 52/24/21/29/36/39 | ROAR (20), QUICK_ATTACK (30), WILL_O_WISP (15), CONFUSE_RAY (10) | none |

WARTORTLE Lv32; EXP 28087; raw stats 89/53/56/62/62/53; earned EVs 13/10/26/14/3/42; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 39/89 partial; Torrent off | WATER_GUN: 24/25, MEGA_KICK: 2/5, BITE: 14/25, WATER_PULSE: 14/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 39/89 partial; Torrent off | WATER_GUN: 24/25, MEGA_KICK: 2/5, BITE: 14/25, WATER_PULSE: 14/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-poster-guard

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_7` — RATICATE Lv20, ZUBAT Lv20.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| RATICATE (Normal) Lv20 | Hasty; all IVs 0; M; runaway | 52/37/26/25/33/47 | TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15), SCARY_FACE (10) | none |
| ZUBAT (Poison/Flying) Lv20 | Gentle; all IVs 0; M; innerfocus | 46/23/17/17/23/27 | LEECH_LIFE (15), ASTONISH (15), SUPERSONIC (20), BITE (25) | none |

WARTORTLE Lv32; EXP 28879; raw stats 89/53/56/62/62/53; earned EVs 13/11/26/14/3/43; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 39/89 partial; Torrent off | WATER_GUN: 22/25, MEGA_KICK: 2/5, BITE: 14/25, WATER_PULSE: 14/20 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 39/89 partial; Torrent off | WATER_GUN: 22/25, MEGA_KICK: 2/5, BITE: 14/25, WATER_PULSE: 14/20 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-key-grunt

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_18` — KOFFING Lv21, ZUBAT Lv21.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| KOFFING (Poison) Lv21 | Mild; all IVs 0; M; levitate | 47/32/39/33/23/19 | TACKLE (35), SMOG (20), SELF_DESTRUCT (5), SLUDGE (20) | none |
| ZUBAT (Poison/Flying) Lv21 | Lonely; all IVs 0; M; innerfocus | 47/25/17/17/21/28 | ASTONISH (15), SUPERSONIC (20), BITE (25), WING_ATTACK (35) | none |

WARTORTLE Lv32; EXP 29606; raw stats 89/53/56/62/62/53; earned EVs 13/11/26/14/3/46; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 39/89 partial; Torrent off | WATER_GUN: 22/25, MEGA_KICK: 1/5, BITE: 14/25, WATER_PULSE: 13/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 39/89 partial; Torrent off | WATER_GUN: 22/25, MEGA_KICK: 1/5, BITE: 14/25, WATER_PULSE: 13/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-left-guard

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_16` — SANDSHREW Lv23, EKANS Lv23, SANDSLASH Lv23.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| SANDSHREW (Ground) Lv23 | Docile; all IVs 0; M; sandveil | 56/39/44/14/18/23 | DEFENSE_CURL (40), SAND_ATTACK (15), POISON_STING (35), SLASH (20) | none |
| EKANS (Poison) Lv23 | Gentle; all IVs 0; M; intimidate | 49/32/22/23/31/30 | LEER (30), POISON_STING (35), BITE (25), GLARE (30) | none |
| SANDSLASH (Ground) Lv23 | Relaxed; all IVs 0; M; sandveil | 67/51/60/25/30/30 | SCRATCH (35), DEFENSE_CURL (40), SAND_ATTACK (15), POISON_STING (35) | none |

WARTORTLE Lv33; EXP 30362; raw stats 92/55/58/64/64/55; earned EVs 13/11/27/14/3/47; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 42/92 partial; Torrent off | WATER_GUN: 22/25, MEGA_KICK: 1/5, BITE: 14/25, WATER_PULSE: 11/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 42/92 partial; Torrent off | WATER_GUN: 22/25, MEGA_KICK: 1/5, BITE: 14/25, WATER_PULSE: 11/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-right-guard

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_17` — EKANS Lv23, SANDSHREW Lv23, ARBOK Lv23.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| EKANS (Poison) Lv23 | Lonely; all IVs 0; M; intimidate | 49/35/22/23/29/30 | LEER (30), POISON_STING (35), BITE (25), GLARE (30) | none |
| SANDSHREW (Ground) Lv23 | Gentle; all IVs 0; M; sandveil | 56/39/39/14/19/23 | DEFENSE_CURL (40), SAND_ATTACK (15), POISON_STING (35), SLASH (20) | none |
| ARBOK (Poison) Lv23 | Bashful; all IVs 0; M; intimidate | 60/44/36/34/41/41 | LEER (30), POISON_STING (35), BITE (25), GLARE (30) | none |

WARTORTLE Lv33; EXP 31925; raw stats 92/55/58/64/64/55; earned EVs 13/12/30/14/3/47; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×3, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 42/92 partial; Torrent off | WATER_GUN: 21/25, MEGA_KICK: 1/5, BITE: 13/25, WATER_PULSE: 10/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 42/92 partial; Torrent off | WATER_GUN: 21/25, MEGA_KICK: 1/5, BITE: 13/25, WATER_PULSE: 10/20 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### hideout-giovanni

Opponent: `TRAINER_BOSS_GIOVANNI` — ONIX Lv25, RHYHORN Lv24, KANGASKHAN Lv29.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ONIX (Rock/Ground) Lv25 | Gentle; all IVs 30; M; rockhead | 60/35/82/27/38/47 | BIND (20), ROCK_THROW (15), HARDEN (30), RAGE (20) | none |
| RHYHORN (Ground/Rock) Lv24 | Bashful; all IVs 30; M; lightningrod | 79/53/57/26/26/24 | TAIL_WHIP (30), STOMP (20), FURY_ATTACK (20), SCARY_FACE (10) | none |
| KANGASKHAN (Normal) Lv29 | Quirky; all IVs 30; F; earlybird | 108/68/60/36/60/65 | BITE (25), TAIL_WHIP (30), FAKE_OUT (10), MEGA_PUNCH (20) | none |

BLASTOISE Lv36; EXP 40007; raw stats 114/74/76/85/88/74; earned EVs 13/15/31/14/3/47; status clear; held item none; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 38/114 partial; Torrent on | WATER_GUN: 20/25, MEGA_KICK: 1/5, BITE: 12/25, WATER_PULSE: 8/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 38/114 partial; Torrent on | WATER_GUN: 20/25, MEGA_KICK: 1/5, BITE: 12/25, WATER_PULSE: 8/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rival

Opponent: `TRAINER_RIVAL_POKEMON_TOWER_BULBASAUR` — PIDGEOTTO Lv25, GYARADOS Lv23, GROWLITHE Lv22, KADABRA Lv20, IVYSAUR Lv25.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEOTTO (Normal/Flying) Lv25 | Quiet; all IVs 12; M; keeneye | 69/38/35/36/33/38 | SAND_ATTACK (15), GUST (35), QUICK_ATTACK (30), WHIRLWIND (20) | none |
| GYARADOS (Water/Flying) Lv23 | Docile; all IVs 12; M; intimidate | 79/65/44/35/53/45 | THRASH (20), BITE (25) | none |
| GROWLITHE (Fire) Lv22 | Careful; all IVs 12; M; intimidate | 58/38/27/34/31/34 | ROAR (20), EMBER (25), LEER (30), ODOR_SLEUTH (40) | none |
| KADABRA (Psychic) Lv20 | Lax; all IVs 12; M; synchronize | 48/21/20/55/31/49 | TELEPORT (20), KINESIS (15), CONFUSION (25), DISABLE (20) | none |
| IVYSAUR (Grass/Poison) Lv25 | Relaxed; all IVs 12; M; overgrow | 68/39/42/48/48/34 | VINE_WHIP (10), POISON_POWDER (35), SLEEP_POWDER (15), RAZOR_LEAF (25) | none |

BLASTOISE Lv36; EXP 42364; raw stats 114/74/76/85/88/74; earned EVs 15/15/33/14/3/47; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×21, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +2. If Torrent is inactive, raise that target to +4. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false, "torrent_power": true}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 38/114 partial; Torrent on | WATER_GUN: 18/25, MEGA_KICK: 1/5, BITE: 12/25, WATER_PULSE: 6/20 | Use guardspec | 630/700 (90.0%) | 83.8%–94.5% |
| prepared | 38/114 partial; Torrent on | WATER_GUN: 18/25, MEGA_KICK: 1/5, BITE: 12/25, WATER_PULSE: 6/20 | Use guardspec | 630/700 (90.0%) | 83.8%–94.5% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### tower-tammy

Opponent: `TRAINER_CHANNELER_TAMMY` — HAUNTER Lv23.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| HAUNTER (Ghost/Poison) Lv23 | Mild; all IVs 0; F; levitate | 53/28/22/62/30/48 | SPITE (10), CURSE (10), NIGHT_SHADE (15), CONFUSE_RAY (10) | none |

BLASTOISE Lv37; EXP 45826; raw stats 116/77/78/88/90/77; earned EVs 15/18/33/17/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/116 partial; Torrent on | WATER_GUN: 16/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/116 partial; Torrent on | WATER_GUN: 16/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-jennifer

Opponent: `TRAINER_CHANNELER_JENNIFER` — GASTLY Lv24.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GASTLY (Ghost/Poison) Lv24 | Lax; all IVs 0; F; levitate | 48/21/20/53/18/43 | SPITE (10), CURSE (10), NIGHT_SHADE (15), CONFUSE_RAY (10) | none |

BLASTOISE Lv37; EXP 46447; raw stats 116/77/78/88/90/77; earned EVs 15/18/33/19/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/116 partial; Torrent on | WATER_GUN: 15/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/116 partial; Torrent on | WATER_GUN: 15/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-emilia

Opponent: `TRAINER_CHANNELER_EMILIA` — GASTLY Lv24.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GASTLY (Ghost/Poison) Lv24 | Timid; all IVs 0; F; levitate | 48/18/19/53/21/47 | SPITE (10), CURSE (10), NIGHT_SHADE (15), CONFUSE_RAY (10) | none |

BLASTOISE Lv37; EXP 46934; raw stats 116/77/78/88/90/77; earned EVs 15/18/33/20/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/116 partial; Torrent on | WATER_GUN: 14/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/116 partial; Torrent on | WATER_GUN: 14/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 5/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rocket1

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_19` — ZUBAT Lv25, ZUBAT Lv25, GOLBAT Lv25.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ZUBAT (Poison/Flying) Lv25 | Gentle; all IVs 0; M; innerfocus | 55/27/19/20/27/32 | ASTONISH (15), SUPERSONIC (20), BITE (25), WING_ATTACK (35) | none |
| ZUBAT (Poison/Flying) Lv25 | Docile; all IVs 0; M; innerfocus | 55/27/22/20/25/32 | ASTONISH (15), SUPERSONIC (20), BITE (25), WING_ATTACK (35) | none |
| GOLBAT (Poison/Flying) Lv25 | Naughty; all IVs 0; M; innerfocus | 72/49/40/37/37/50 | ASTONISH (15), SUPERSONIC (20), BITE (25), WING_ATTACK (35) | none |

BLASTOISE Lv38; EXP 47952; raw stats 119/79/81/91/93/79; earned EVs 15/18/35/21/4/49; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/119 partial; Torrent on | WATER_GUN: 13/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 4/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/119 partial; Torrent on | WATER_GUN: 13/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 4/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rocket2

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_20` — KOFFING Lv26, DROWZEE Lv26.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| KOFFING (Poison) Lv26 | Mild; all IVs 0; M; levitate | 56/38/48/39/28/23 | SMOG (20), SELF_DESTRUCT (5), SLUDGE (20), SMOKESCREEN (20) | none |
| DROWZEE (Psychic) Lv26 | Naive; all IVs 0; M; insomnia | 67/29/28/27/45/28 | DISABLE (20), CONFUSION (25), HEADBUTT (15), POISON_GAS (40) | none |

BLASTOISE Lv38; EXP 49443; raw stats 119/79/81/91/93/79; earned EVs 15/18/35/21/4/53; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/119 partial; Torrent on | WATER_GUN: 11/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 3/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/119 partial; Torrent on | WATER_GUN: 11/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 3/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### tower-rocket3

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_21` — ZUBAT Lv23, RATTATA Lv23, RATICATE Lv23, ZUBAT Lv23.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ZUBAT (Poison/Flying) Lv23 | Gentle; all IVs 0; M; innerfocus | 51/25/18/18/25/30 | ASTONISH (15), SUPERSONIC (20), BITE (25), WING_ATTACK (35) | none |
| RATTATA (Normal) Lv23 | Naughty; all IVs 0; M; runaway | 46/33/21/16/18/38 | TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15), FOCUS_ENERGY (30) | none |
| RATICATE (Normal) Lv23 | Naughty; all IVs 0; M; runaway | 58/46/32/28/33/49 | TAIL_WHIP (30), QUICK_ATTACK (30), HYPER_FANG (15), SCARY_FACE (10) | none |
| ZUBAT (Poison/Flying) Lv23 | Naive; all IVs 0; M; innerfocus | 51/25/21/18/20/33 | ASTONISH (15), SUPERSONIC (20), BITE (25), WING_ATTACK (35) | none |

BLASTOISE Lv38; EXP 50644; raw stats 119/79/81/91/93/79; earned EVs 15/18/36/21/5/53; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, guardspec ×2, oranberry ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 27/119 partial; Torrent on | WATER_GUN: 10/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 2/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 27/119 partial; Torrent on | WATER_GUN: 10/25, MEGA_KICK: 1/5, BITE: 9/25, WATER_PULSE: 2/20 | Use WATER_GUN | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### fuchsia-kirk

Opponent: `TRAINER_JUGGLER_KIRK` — DROWZEE Lv31, DROWZEE Lv31, KADABRA Lv31, DROWZEE Lv31.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| DROWZEE (Psychic) Lv31 | Relaxed; all IVs 0; M; insomnia | 78/34/35/31/60/27 | HEADBUTT (15), POISON_GAS (40), MEDITATE (40), PSYCHIC (10) | none |
| DROWZEE (Psychic) Lv31 | Adamant; all IVs 0; M; insomnia | 78/37/32/27/60/31 | HEADBUTT (15), POISON_GAS (40), MEDITATE (40), PSYCHIC (10) | none |
| KADABRA (Psychic) Lv31 | Lonely; all IVs 0; M; synchronize | 65/28/20/79/48/70 | PSYBEAM (20), REFLECT (20), RECOVER (20), FUTURE_SIGHT (15) | none |
| DROWZEE (Psychic) Lv31 | Sassy; all IVs 0; M; insomnia | 78/34/32/31/66/27 | HEADBUTT (15), POISON_GAS (40), MEDITATE (40), PSYCHIC (10) | none |

BLASTOISE Lv38; EXP 52025; raw stats 119/79/81/91/93/79; earned EVs 15/18/36/21/5/58; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 31/119 partial; Torrent on | MEGA_KICK: 1/5, BITE: 6/25, WATER_PULSE: 2/20, SURF: 15/15 | Use SURF | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 31/119 partial; Torrent on | MEGA_KICK: 1/5, BITE: 6/25, WATER_PULSE: 2/20, SURF: 15/15 | Use SURF | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### koga

Opponent: `TRAINER_LEADER_KOGA` — KOFFING Lv37, MUK Lv39, KOFFING Lv37, WEEZING Lv43.

NPC medicine slots, in source order: HYPER_POTION, HYPER_POTION, FULL_HEAL. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| KOFFING (Poison) Lv37 | Quirky; all IVs 0; M; levitate | 76/53/75/49/38/30 | SELF_DESTRUCT (5), SLUDGE (20), SMOKESCREEN (20), TOXIC (10) | none |
| MUK (Poison) Lv39 | Timid; all IVs 0; M; stench | 130/77/63/55/83/48 | MINIMIZE (20), SLUDGE (20), ACID_ARMOR (40), TOXIC (10) | none |
| KOFFING (Poison) Lv37 | Careful; all IVs 0; M; levitate | 76/53/75/44/41/30 | SELF_DESTRUCT (5), SLUDGE (20), SMOKESCREEN (20), TOXIC (10) | none |
| WEEZING (Poison) Lv43 | Serious; all IVs 0; M; levitate | 108/82/108/78/65/56 | TACKLE (35), SLUDGE (20), SMOKESCREEN (20), TOXIC (10) | none |

BLASTOISE Lv39; EXP 55016; raw stats 122/81/82/93/95/81; earned EVs 15/18/36/23/8/58; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder.

Battle bag: antidote ×1, awakening ×3, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×5, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +1. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. Do not spend Guard Spec for this plan. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": false, "outspeed": true, "spa": 1, "target_torrent": false}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 34/122 partial; Torrent on | MEGA_KICK: 1/5, BITE: 6/25, WATER_PULSE: 2/20, SURF: 11/15 | Use WATER_PULSE | 1191/1700 (70.1%) | 64.5%–75.2% |
| prepared | 34/122 partial; Torrent on | MEGA_KICK: 1/5, BITE: 6/25, WATER_PULSE: 2/20, SURF: 11/15 | Use WATER_PULSE | 1191/1700 (70.1%) | 64.5%–75.2% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### blaine

Opponent: `TRAINER_LEADER_BLAINE` — GROWLITHE Lv42, PONYTA Lv40, RAPIDASH Lv42, ARCANINE Lv47.

NPC medicine slots, in source order: HYPER_POTION, HYPER_POTION, FULL_HEAL. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GROWLITHE (Fire) Lv42 | Hasty; all IVs 0; M; intimidate | 98/63/37/63/47/60 | BITE (25), ROAR (20), TAKE_DOWN (20), FIRE_BLAST (5) | none |
| PONYTA (Fire) Lv40 | Relaxed; all IVs 0; M; runaway | 90/73/53/57/57/69 | STOMP (20), BOUNCE (5), FIRE_SPIN (15), FIRE_BLAST (5) | none |
| RAPIDASH (Fire) Lv42 | Calm; all IVs 0; M; runaway | 106/80/63/72/79/93 | STOMP (20), BOUNCE (5), FIRE_SPIN (15), FIRE_BLAST (5) | none |
| ARCANINE (Fire) Lv47 | Quiet; all IVs 0; M; intimidate | 141/108/80/108/80/84 | BITE (25), ROAR (20), TAKE_DOWN (20), FIRE_BLAST (5) | none |

BLASTOISE Lv40; EXP 59726; raw stats 126/83/85/95/98/83; earned EVs 16/19/40/23/8/58; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 24/126 partial; Torrent on | MEGA_KICK: 1/5, BITE: 5/25, WATER_PULSE: 2/20, SURF: 5/15 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 24/126 partial; Torrent on | MEGA_KICK: 1/5, BITE: 5/25, WATER_PULSE: 2/20, SURF: 5/15 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### celadon-tamia

Opponent: `TRAINER_BEAUTY_TAMIA` — BELLSPROUT Lv24, BELLSPROUT Lv24.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| BELLSPROUT (Grass/Poison) Lv24 | Naive; all IVs 0; F; chlorophyll | 58/41/21/38/17/26 | SLEEP_POWDER (15), POISON_POWDER (35), STUN_SPORE (30), ACID (30) | none |
| BELLSPROUT (Grass/Poison) Lv24 | Impish; all IVs 0; F; chlorophyll | 58/41/23/34/19/24 | SLEEP_POWDER (15), POISON_POWDER (35), STUN_SPORE (30), ACID (30) | none |

BLASTOISE Lv41; EXP 65720; raw stats 128/85/87/97/100/85; earned EVs 16/22/40/23/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 26/128 partial; Torrent on | MEGA_KICK: 1/5, BITE: 5/25, WATER_PULSE: 2/20, SURF: 1/15 | Use BITE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 26/128 partial; Torrent on | MEGA_KICK: 1/5, BITE: 5/25, WATER_PULSE: 2/20, SURF: 1/15 | Use BITE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### celadon-lori

Opponent: `TRAINER_BEAUTY_LORI` — EXEGGCUTE Lv24.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| EXEGGCUTE (Grass/Psychic) Lv24 | Lax; all IVs 0; F; chlorophyll | 62/24/47/33/23/24 | HYPNOSIS (20), REFLECT (20), LEECH_SEED (10), CONFUSION (25) | none |

BLASTOISE Lv44; EXP 77440; raw stats 137/91/93/104/107/92; earned EVs 16/24/40/23/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 35/137 partial; Torrent on | BITE: 3/25, WATER_PULSE: 2/20, SURF: 1/15, BLIZZARD: 5/5 | Use BITE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 35/137 partial; Torrent on | BITE: 3/25, WATER_PULSE: 2/20, SURF: 1/15, BLIZZARD: 5/5 | Use BITE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### erika

Opponent: `TRAINER_LEADER_ERIKA` — VICTREEBEL Lv29, TANGELA Lv24, VILEPLUME Lv29.

NPC medicine slots, in source order: HYPER_POTION, FULL_HEAL. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| VICTREEBEL (Grass/Poison) Lv29 | Bold; all IVs 0; F; chlorophyll | 85/58/46/63/39/45 | STUN_SPORE (30), ACID (30), POISON_POWDER (35), GIGA_DRAIN (5) | none |
| TANGELA (Grass) Lv24 | Gentle; all IVs 0; F; chlorophyll | 65/31/54/53/26/33 | POISON_POWDER (35), CONSTRICT (35), INGRAIN (20), GIGA_DRAIN (5) | none |
| VILEPLUME (Grass/Poison) Lv29 | Quirky; all IVs 0; F; chlorophyll | 82/51/54/63/57/34 | SLEEP_POWDER (15), ACID (30), STUN_SPORE (30), GIGA_DRAIN (5) | none |

BLASTOISE Lv44; EXP 77944; raw stats 137/91/93/104/107/92; earned EVs 16/24/41/23/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, maxelixir ×1, parlyzheal ×2, potion ×4, superpotion ×5, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +1. Target accuracy +2 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 1, "target_torrent": false}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 35/137 partial; Torrent on | BITE: 2/25, WATER_PULSE: 2/20, SURF: 1/15, BLIZZARD: 5/5 | Use xspecial | 567/620 (91.5%) | 85.2%–95.8% |
| prepared | 35/137 partial; Torrent on | BITE: 2/25, WATER_PULSE: 2/20, SURF: 1/15, BLIZZARD: 5/5 | Use xspecial | 567/620 (91.5%) | 85.2%–95.8% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### silph-rival

Opponent: `TRAINER_RIVAL_SILPH_BULBASAUR` — PIDGEOT Lv37, GYARADOS Lv38, GROWLITHE Lv35, ALAKAZAM Lv35, VENUSAUR Lv40.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEOT (Normal/Flying) Lv37 | Hardy; all IVs 12; M; keeneye | 112/68/64/61/61/76 | QUICK_ATTACK (30), WHIRLWIND (20), WING_ATTACK (35), FEATHER_DANCE (15) | none |
| GYARADOS (Water/Flying) Lv38 | Naive; all IVs 12; M; intimidate | 124/104/69/55/76/78 | BITE (25), DRAGON_RAGE (10), LEER (30), TWISTER (20) | none |
| GROWLITHE (Fire) Lv35 | Docile; all IVs 12; M; intimidate | 87/58/40/58/44/51 | LEER (30), ODOR_SLEUTH (40), TAKE_DOWN (20), FLAME_WHEEL (25) | none |
| ALAKAZAM (Psychic) Lv35 | Lonely; all IVs 12; M; synchronize | 87/48/36/103/68/93 | REFLECT (20), RECOVER (20), FUTURE_SIGHT (15), CALM_MIND (20) | none |
| VENUSAUR (Grass/Poison) Lv40 | Lonely; all IVs 18; M; overgrow | 121/84/70/92/92/76 | POISON_POWDER (35), SLEEP_POWDER (15), RAZOR_LEAF (25), SWEET_SCENT (20) | none |

BLASTOISE Lv44; EXP 81126; raw stats 137/91/93/104/107/92; earned EVs 16/27/42/26/8/61; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×5, xspecial ×19, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +2. Target accuracy +2 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 85/137 partial; Torrent off | BITE: 25/25, WATER_PULSE: 20/20, SURF: 15/15, BLIZZARD: 5/5 | Use xspecial | 289/300 (96.3%) | 89.0%–99.4% |
| prepared | 85/137 partial; Torrent off | BITE: 25/25, WATER_PULSE: 20/20, SURF: 15/15, BLIZZARD: 5/5 | Use xspecial | 289/300 (96.3%) | 89.0%–99.4% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### silph-boardroom-grunt

Opponent: `TRAINER_TEAM_ROCKET_GRUNT_41` — CUBONE Lv32, DROWZEE Lv32, MAROWAK Lv32.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| CUBONE (Ground) Lv32 | Brave; all IVs 0; M; rockhead | 74/40/65/30/37/24 | LEER (30), FOCUS_ENERGY (30), BONEMERANG (10), RAGE (20) | none |
| DROWZEE (Psychic) Lv32 | Hardy; all IVs 0; M; insomnia | 80/35/33/32/62/31 | HEADBUTT (15), POISON_GAS (40), MEDITATE (40), PSYCHIC (10) | none |
| MAROWAK (Ground) Lv32 | Naive; all IVs 0; M; rockhead | 80/56/75/37/50/36 | LEER (30), FOCUS_ENERGY (30), BONEMERANG (10), RAGE (20) | none |

BLASTOISE Lv45; EXP 88089; raw stats 140/93/95/107/109/94; earned EVs 16/30/42/31/9/64; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×6.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 30/140 partial; Torrent on | BITE: 24/25, WATER_PULSE: 19/20, SURF: 14/15, BLIZZARD: 3/5 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 30/140 partial; Torrent on | BITE: 24/25, WATER_PULSE: 19/20, SURF: 14/15, BLIZZARD: 3/5 | Use potion | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### silph-giovanni

Opponent: `TRAINER_BOSS_GIOVANNI_2` — NIDORINO Lv37, KANGASKHAN Lv35, RHYHORN Lv37, NIDOQUEEN Lv41.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| NIDORINO (Poison) Lv37 | Lonely; all IVs 30; M; poisonpoint | 103/75/52/56/56/64 | POISON_STING (35), HORN_ATTACK (25), HELPING_HAND (20), FURY_ATTACK (20) | none |
| KANGASKHAN (Normal) Lv35 | Relaxed; all IVs 30; F; earlybird | 129/82/78/43/71/70 | TAIL_WHIP (30), FAKE_OUT (10), MEGA_PUNCH (20), RAGE (20) | none |
| RHYHORN (Ground/Rock) Lv37 | Naughty; all IVs 30; M; lightningrod | 117/86/86/38/34/34 | STOMP (20), FURY_ATTACK (20), SCARY_FACE (10), ROCK_BLAST (10) | none |
| NIDOQUEEN (Poison/Ground) Lv41 | Gentle; all IVs 30; F; poisonpoint | 137/84/79/78/95/79 | TAIL_WHIP (30), DOUBLE_KICK (30), POISON_STING (35), BODY_SLAM (15) | none |

BLASTOISE Lv46; EXP 90232; raw stats 143/96/98/110/112/96; earned EVs 16/30/45/31/10/64; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +1. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 1, "target_torrent": false}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 33/143 partial; Torrent on | BITE: 23/25, WATER_PULSE: 17/20, SURF: 14/15, BLIZZARD: 3/5 | Use xspecial | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 33/143 partial; Torrent on | BITE: 23/25, WATER_PULSE: 17/20, SURF: 14/15, BLIZZARD: 3/5 | Use xspecial | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### sabrina

Opponent: `TRAINER_LEADER_SABRINA` — KADABRA Lv38, MR_MIME Lv37, VENOMOTH Lv38, ALAKAZAM Lv43.

NPC medicine slots, in source order: HYPER_POTION, HYPER_POTION, FULL_HEAL. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| KADABRA (Psychic) Lv38 | Docile; all IVs 0; M; synchronize | 78/31/27/96/58/84 | PSYBEAM (20), REFLECT (20), FUTURE_SIGHT (15), CALM_MIND (20) | none |
| MR_MIME (Psychic) Lv37 | Serious; all IVs 0; F; soundproof | 76/38/53/79/93/71 | BARRIER (30), PSYBEAM (20), BATON_PASS (40), CALM_MIND (20) | none |
| VENOMOTH (Bug/Poison) Lv38 | Impish; all IVs 0; F; shielddust | 101/54/55/65/62/73 | PSYBEAM (20), GUST (35), LEECH_LIFE (15), SUPERSONIC (20) | none |
| ALAKAZAM (Psychic) Lv43 | Adamant; all IVs 0; M; synchronize | 100/52/43/108/78/108 | PSYCHIC (10), RECOVER (20), FUTURE_SIGHT (15), CALM_MIND (20) | none |

BLASTOISE Lv46; EXP 95251; raw stats 143/96/98/110/112/96; earned EVs 21/32/46/31/10/64; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×6.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +0. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 0, "target_torrent": false}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 33/143 partial; Torrent on | BITE: 23/25, WATER_PULSE: 16/20, SURF: 11/15, BLIZZARD: 3/5 | Use xspeed | 177/180 (98.3%) | 89.8%–100.0% |
| prepared | 33/143 partial; Torrent on | BITE: 23/25, WATER_PULSE: 16/20, SURF: 11/15, BLIZZARD: 3/5 | Use xspeed | 177/180 (98.3%) | 89.8%–100.0% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### viridian-takashi

Opponent: `TRAINER_BLACK_BELT_TAKASHI` — MACHOKE Lv38, MACHOP Lv38, MACHOKE Lv38.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| MACHOKE (Fighting) Lv38 | Timid; all IVs 12; M; guts | 113/76/62/47/55/47 | SEISMIC_TOSS (20), FORESIGHT (40), REVENGE (10), VITAL_THROW (10) | BLACK_BELT |
| MACHOP (Fighting) Lv38 | Bashful; all IVs 12; M; guts | 105/70/47/36/36/36 | FORESIGHT (40), REVENGE (10), VITAL_THROW (10), SUBMISSION (25) | BLACK_BELT |
| MACHOKE (Fighting) Lv38 | Quiet; all IVs 12; M; guts | 113/85/62/51/55/38 | SEISMIC_TOSS (20), FORESIGHT (40), REVENGE (10), VITAL_THROW (10) | BLACK_BELT |

BLASTOISE Lv47; EXP 100344; raw stats 146/98/99/113/114/98; earned EVs 21/32/46/37/12/65; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: B. Policy: `historical A/B recovery behavior`.

Use B recovery: recompute the attack each turn; take a finishing hit when the B rule allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. Use only the listed bag; do not use X items or deliberately stall for setup.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 25/146 partial; Torrent on | BITE: 23/25, WATER_PULSE: 16/20, SURF: 7/15, BLIZZARD: 3/5 | Use superpotion | 139/140 (99.3%) | 90.4%–100.0% |
| prepared | 25/146 partial; Torrent on | BITE: 23/25, WATER_PULSE: 16/20, SURF: 7/15, BLIZZARD: 3/5 | Use superpotion | 139/140 (99.3%) | 90.4%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### viridian-warren

Opponent: `TRAINER_COOLTRAINER_WARREN` — MAROWAK Lv37, MAROWAK Lv37, RHYHORN Lv38, NIDORINA Lv39, NIDOQUEEN Lv39.

NPC medicine slots, in source order: HYPER_POTION. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| MAROWAK (Ground) Lv37 | Timid; all IVs 12; M; rockhead | 95/61/90/46/68/46 | BONEMERANG (10), HEADBUTT (15), LEER (30), GROWL (40) | none |
| MAROWAK (Ground) Lv37 | Lax; all IVs 12; M; rockhead | 95/68/99/46/61/42 | BONEMERANG (10), HEADBUTT (15), LEER (30), GROWL (40) | none |
| RHYHORN (Ground/Rock) Lv38 | Brave; all IVs 12; M; lightningrod | 113/81/81/32/32/25 | TAKE_DOWN (20), ROCK_BLAST (10), FURY_ATTACK (20), SCARY_FACE (10) | none |
| NIDORINA (Poison) Lv39 | Naughty; all IVs 12; F; poisonpoint | 108/63/61/52/46/53 | FURY_SWIPES (15), BITE (25), POISON_STING (35), DOUBLE_KICK (30) | none |
| NIDOQUEEN (Poison/Ground) Lv39 | Quiet; all IVs 12; F; poisonpoint | 123/73/77/74/75/61 | BODY_SLAM (15), BITE (25), POISON_STING (35), DOUBLE_KICK (30) | none |

BLASTOISE Lv48; EXP 103435; raw stats 149/101/101/115/117/100; earned EVs 21/37/46/37/12/65; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 28/149 partial; Torrent on | BITE: 23/25, WATER_PULSE: 16/20, SURF: 4/15, BLIZZARD: 3/5 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 28/149 partial; Torrent on | BITE: 23/25, WATER_PULSE: 16/20, SURF: 4/15, BLIZZARD: 3/5 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### giovanni-gym

Opponent: `TRAINER_LEADER_GIOVANNI` — RHYHORN Lv45, DUGTRIO Lv42, NIDOQUEEN Lv44, NIDOKING Lv45, RHYHORN Lv50.

NPC medicine slots, in source order: HYPER_POTION, HYPER_POTION, FULL_HEAL. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| RHYHORN (Ground/Rock) Lv45 | Impish; all IVs 0; M; lightningrod | 127/81/99/28/32/27 | TAKE_DOWN (20), ROCK_BLAST (10), SCARY_FACE (10), EARTHQUAKE (10) | none |
| DUGTRIO (Ground) Lv42 | Impish; all IVs 0; M; sandveil | 81/72/51/42/63/105 | SLASH (20), SAND_TOMB (15), MUD_SLAP (10), EARTHQUAKE (10) | none |
| NIDOQUEEN (Poison/Ground) Lv44 | Hardy; all IVs 0; F; poisonpoint | 133/77/81/71/79/71 | BODY_SLAM (15), DOUBLE_KICK (30), POISON_STING (35), EARTHQUAKE (10) | none |
| NIDOKING (Poison/Ground) Lv45 | Hardy; all IVs 0; M; poisonpoint | 127/87/74/81/72/81 | THRASH (20), DOUBLE_KICK (30), POISON_STING (35), EARTHQUAKE (10) | none |
| RHYHORN (Ground/Rock) Lv50 | Sassy; all IVs 0; M; lightningrod | 140/90/100/35/38/27 | TAKE_DOWN (20), ROCK_BLAST (10), SCARY_FACE (10), EARTHQUAKE (10) | none |

BLASTOISE Lv48; EXP 109093; raw stats 149/101/101/115/117/100; earned EVs 26/37/51/37/12/65; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: A. Policy: `historical A/B recovery behavior`.

Use the opening below, then the attack selector. This fight was classified A because the baseline samples used attacks only. The measured controller still has B recovery enabled; retain the listed bag rather than assuming item use is forbidden.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 28/149 partial; Torrent on | BITE: 23/25, WATER_PULSE: 11/20, SURF: 4/15, BLIZZARD: 3/5 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |
| prepared | 28/149 partial; Torrent on | BITE: 23/25, WATER_PULSE: 11/20, SURF: 4/15, BLIZZARD: 3/5 | Use WATER_PULSE | 100/100 (100.0%) | 90.0%–100.0% |

Result source: recorded — original benchmark, seed 1; prepared — original benchmark, seed 1.

### route22-rival

Opponent: `TRAINER_RIVAL_ROUTE22_LATE_BULBASAUR` — PIDGEOT Lv47, RHYHORN Lv45, GYARADOS Lv45, GROWLITHE Lv45, ALAKAZAM Lv47, VENUSAUR Lv53.

NPC medicine slots, in source order: none. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEOT (Normal/Flying) Lv47 | Hardy; all IVs 18; M; keeneye | 143/88/83/79/79/99 | FEATHER_DANCE (15), WING_ATTACK (35), GUST (35), QUICK_ATTACK (30) | none |
| RHYHORN (Ground/Rock) Lv45 | Rash; all IVs 18; M; lightningrod | 135/89/98/44/36/35 | TAKE_DOWN (20), HORN_DRILL (5), ROCK_BLAST (10), FURY_ATTACK (20) | none |
| GYARADOS (Water/Flying) Lv45 | Impish; all IVs 18; M; intimidate | 148/125/92/60/103/86 | HYDRO_PUMP (5), TWISTER (20), LEER (30), RAIN_DANCE (5) | none |
| GROWLITHE (Fire) Lv45 | Hardy; all IVs 18; M; intimidate | 112/76/53/76/58/67 | FLAME_WHEEL (25), TAKE_DOWN (20), LEER (30), AGILITY (30) | none |
| ALAKAZAM (Psychic) Lv47 | Calm; all IVs 18; M; synchronize | 117/54/55/140/102/126 | PSYCHIC (10), CALM_MIND (20), FUTURE_SIGHT (15), DISABLE (20) | none |
| VENUSAUR (Grass/Poison) Lv53 | Calm; all IVs 30; M; overgrow | 163/96/108/126/138/105 | RAZOR_LEAF (25), SWEET_SCENT (20), GROWTH (40), SYNTHESIS (5) | none |

BLASTOISE Lv49; EXP 116923; raw stats 153/103/105/117/119/102; earned EVs 29/40/53/37/12/67; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×4, xspecial ×17, xspeed ×5.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +2. Target accuracy +2 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false}`.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 153/153 full; Torrent off | BITE: 23/25, WATER_PULSE: 6/20, SURF: 4/15, BLIZZARD: 3/5 | Use xspecial | 325/340 (95.6%) | 88.4%–99.0% |
| prepared | 153/153 full; Torrent off | BITE: 23/25, WATER_PULSE: 6/20, SURF: 4/15, BLIZZARD: 3/5 | Use xspecial | 325/340 (95.6%) | 88.4%–99.0% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### lorelei

Opponent: `TRAINER_ELITE_FOUR_LORELEI` — DEWGONG Lv52, CLOYSTER Lv51, SLOWBRO Lv52, JYNX Lv54, LAPRAS Lv54.

NPC medicine slots, in source order: FULL_RESTORE, FULL_RESTORE. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| DEWGONG (Water/Ice) Lv52 | Hardy; all IVs 30; F; thickfat | 171/93/103/93/119/93 | ICE_BEAM (10), SURF (15), HAIL (10), SAFEGUARD (25) | none |
| CLOYSTER (Water/Ice) Lv51 | Careful; all IVs 30; F; shellarmor | 127/117/203/96/72/91 | SPIKES (20), PROTECT (10), HAIL (10), DIVE (10) | none |
| SLOWBRO (Water/Psychic) Lv52 | Brave; all IVs 30; F; oblivious | 176/107/135/124/103/45 | ICE_BEAM (10), SURF (15), AMNESIA (20), YAWN (10) | none |
| JYNX (Ice/Psychic) Lv54 | Sassy; all IVs 30; F; oblivious | 150/75/59/145/135/110 | ICE_PUNCH (15), DOUBLE_SLAP (10), LOVELY_KISS (10), ATTRACT (15) | none |
| LAPRAS (Water/Ice) Lv54 | Jolly; all IVs 30; F; waterabsorb | 220/113/107/101/123/94 | CONFUSE_RAY (10), ICE_BEAM (10), SURF (15), BODY_SLAM (15) | SITRUS_BERRY |

BLASTOISE Lv51; EXP 127126; raw stats 159/107/108/123/124/107; earned EVs 29/43/54/42/13/70; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×13, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×15, xspeed ×4.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +4. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 4, "target_torrent": false}`.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 159/159 full; Torrent off | BITE: 25/25, SURF: 15/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use xspecial | 415/440 (94.3%) | 87.7%–98.1% |
| prepared | 159/159 full; Torrent off | BITE: 25/25, SURF: 15/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use xspecial | 415/440 (94.3%) | 87.7%–98.1% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### bruno

Opponent: `TRAINER_ELITE_FOUR_BRUNO` — ONIX Lv51, HITMONCHAN Lv53, HITMONLEE Lv53, ONIX Lv54, MACHAMP Lv56.

NPC medicine slots, in source order: FULL_RESTORE, FULL_RESTORE. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| ONIX (Rock/Ground) Lv51 | Sassy; all IVs 30; M; rockhead | 112/66/183/50/72/81 | EARTHQUAKE (10), ROCK_TOMB (10), IRON_TAIL (15), ROAR (20) | none |
| HITMONCHAN (Fighting) Lv53 | Serious; all IVs 30; M; keeneye | 131/132/104/58/137/101 | SKY_UPPERCUT (15), MACH_PUNCH (30), ROCK_TOMB (10), COUNTER (20) | none |
| HITMONLEE (Fighting) Lv53 | Serious; all IVs 30; M; limber | 131/148/77/58/137/113 | MEGA_KICK (5), FORESIGHT (40), BRICK_BREAK (15), FACADE (20) | none |
| ONIX (Rock/Ground) Lv54 | Careful; all IVs 30; M; rockhead | 118/69/194/47/75/96 | DOUBLE_EDGE (15), EARTHQUAKE (10), IRON_TAIL (15), SAND_TOMB (15) | none |
| MACHAMP (Fighting) Lv56 | Modest; all IVs 30; M; guts | 183/150/111/103/117/83 | CROSS_CHOP (5), BULK_UP (20), SCARY_FACE (10), ROCK_TOMB (10) | SITRUS_BERRY |

BLASTOISE Lv52; EXP 137248; raw stats 162/109/111/126/126/109; earned EVs 31/43/58/44/15/70; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×12, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×11, xspeed ×4.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +2. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. During the opening setup window, aim for Torrent (HP at most one third), or substitute enough Sp. Atk to match its multiplier. Use productive setup/weak attacks instead of intentionally KOing the setup foe; do not repeat Torrent activation on later foes. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": true}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 130/162 partial; Torrent off | BITE: 19/25, SURF: 14/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use xspecial | 307/320 (95.9%) | 88.7%–99.2% |
| prepared | 130/162 partial; Torrent off | BITE: 19/25, SURF: 14/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use xspecial | 307/320 (95.9%) | 88.7%–99.2% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### agatha

Opponent: `TRAINER_ELITE_FOUR_AGATHA` — GENGAR Lv54, GOLBAT Lv54, HAUNTER Lv53, ARBOK Lv56, GENGAR Lv58.

NPC medicine slots, in source order: FULL_RESTORE, FULL_RESTORE. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GENGAR (Ghost/Poison) Lv54 | Brave; all IVs 30; F; levitate | 145/100/86/161/102/126 | SHADOW_PUNCH (20), CONFUSE_RAY (10), TOXIC (10), DOUBLE_TEAM (15) | none |
| GOLBAT (Poison/Flying) Lv54 | Naive; all IVs 30; F; innerfocus | 161/107/96/91/91/129 | CONFUSE_RAY (10), POISON_FANG (15), AIR_CUTTER (25), BITE (25) | none |
| HAUNTER (Ghost/Poison) Lv53 | Sassy; all IVs 30; F; levitate | 126/73/68/142/86/108 | HYPNOSIS (20), DREAM_EATER (15), CURSE (10), MEAN_LOOK (5) | none |
| ARBOK (Poison) Lv56 | Impish; all IVs 30; F; intimidate | 150/117/108/84/110/111 | SLUDGE_BOMB (10), SCREECH (40), IRON_TAIL (15), BITE (25) | none |
| GENGAR (Ghost/Poison) Lv58 | Modest; all IVs 30; F; levitate | 155/87/92/190/109/150 | SHADOW_BALL (15), SLUDGE_BOMB (10), HYPNOSIS (20), NIGHTMARE (15) | SITRUS_BERRY |

BLASTOISE Lv53; EXP 145160; raw stats 165/112/113/128/129/111; earned EVs 31/48/60/44/17/70; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×12, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×9, xspeed ×3.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +1. If Torrent is inactive, raise that target to +3. Target accuracy +0 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 0, "guard_accuracy": true, "outspeed": true, "spa": 1, "target_torrent": false, "torrent_power": true}`.

Full-heal comparison pending: retain this tested HP/setup condition for both variants.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 45/165 partial; Torrent on | BITE: 19/25, SURF: 9/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use potion | 343/360 (95.3%) | 88.2%–98.8% |
| prepared | 45/165 partial; Torrent on | BITE: 19/25, SURF: 9/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use potion | 343/360 (95.3%) | 88.2%–98.8% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### lance

Opponent: `TRAINER_ELITE_FOUR_LANCE` — GYARADOS Lv56, DRAGONAIR Lv54, DRAGONAIR Lv54, AERODACTYL Lv58, DRAGONITE Lv60.

NPC medicine slots, in source order: FULL_RESTORE, FULL_RESTORE. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| GYARADOS (Water/Flying) Lv56 | Rash; all IVs 30; M; intimidate | 189/161/110/97/119/112 | HYPER_BEAM (5), DRAGON_RAGE (10), TWISTER (20), BITE (25) | none |
| DRAGONAIR (Dragon) Lv54 | Hardy; all IVs 30; M; shedskin | 146/111/91/96/96/96 | HYPER_BEAM (5), SAFEGUARD (25), DRAGON_RAGE (10), OUTRAGE (15) | none |
| DRAGONAIR (Dragon) Lv54 | Docile; all IVs 30; M; shedskin | 146/111/91/96/96/96 | HYPER_BEAM (5), SAFEGUARD (25), THUNDER_WAVE (20), OUTRAGE (15) | none |
| AERODACTYL (Rock/Flying) Lv58 | Bold; all IVs 30; M; rockhead | 178/129/106/92/109/173 | HYPER_BEAM (5), ANCIENT_POWER (5), WING_ATTACK (35), SCARY_FACE (10) | none |
| DRAGONITE (Dragon/Flying) Lv60 | Sassy; all IVs 30; M; innerfocus | 197/183/137/143/157/107 | HYPER_BEAM (5), SAFEGUARD (25), OUTRAGE (15), WING_ATTACK (35) | SITRUS_BERRY |

BLASTOISE Lv54; EXP 154891; raw stats 168/114/116/130/131/113; earned EVs 31/50/60/52/17/72; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, elixir ×1, fullrestore ×11, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×3, xspecial ×8, xspeed ×2.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +3. Target accuracy +2 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 3, "target_torrent": false}`.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 168/168 full; Torrent off | BITE: 19/25, SURF: 4/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use xspecial | 119/120 (99.2%) | 88.9%–100.0% |
| prepared | 168/168 full; Torrent off | BITE: 19/25, SURF: 4/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use xspecial | 119/120 (99.2%) | 88.9%–100.0% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

### champion

Opponent: `TRAINER_CHAMPION_FIRST_BULBASAUR` — PIDGEOT Lv59, ALAKAZAM Lv57, RHYDON Lv59, GYARADOS Lv59, ARCANINE Lv61, VENUSAUR Lv63.

NPC medicine slots, in source order: FULL_RESTORE, FULL_RESTORE, FULL_RESTORE, FULL_RESTORE. AI flags: CHECK_BAD_MOVE, TRY_TO_FAINT, CHECK_VIABILITY.

| Opponent | Nature / IVs / gender / ability | Raw stats HP/Atk/Def/SpA/SpD/Spe | Moves (full entry PP) | Held item |
|---|---|---|---|---|
| PIDGEOT (Normal/Flying) Lv59 | Hardy; all IVs 31; M; keeneye | 185/117/111/105/105/130 | AERIAL_ACE (20), FEATHER_DANCE (15), SAND_ATTACK (15), WHIRLWIND (20) | none |
| ALAKAZAM (Psychic) Lv57 | Calm; all IVs 31; M; synchronize | 147/71/73/176/130/159 | PSYCHIC (10), FUTURE_SIGHT (15), RECOVER (20), REFLECT (20) | none |
| RHYDON (Ground/Rock) Lv59 | Mild; all IVs 31; M; lightningrod | 211/176/147/83/76/70 | TAKE_DOWN (20), EARTHQUAKE (10), ROCK_TOMB (10), SCARY_FACE (10) | none |
| GYARADOS (Water/Flying) Lv59 | Bold; all IVs 31; M; intimidate | 199/153/127/94/141/118 | HYDRO_PUMP (5), DRAGON_RAGE (10), BITE (25), THRASH (20) | none |
| ARCANINE (Fire) Lv61 | Rash; all IVs 31; M; intimidate | 199/158/121/159/108/139 | EXTREME_SPEED (5), FLAMETHROWER (15), ROAR (20), BITE (25) | none |
| VENUSAUR (Grass/Poison) Lv63 | Rash; all IVs 31; M; overgrow | 193/127/129/165/135/125 | SOLAR_BEAM (10), SYNTHESIS (5), SUNNY_DAY (5), GROWTH (40) | SITRUS_BERRY |

BLASTOISE Lv55; EXP 166100; raw stats 171/117/118/134/134/115; earned EVs 31/59/60/52/17/74; status clear; held item BLACK_GLASSES; badges boulder, cascade, thunder, soul, volcano, rainbow, marsh, earth.

Battle bag: antidote ×1, awakening ×3, fullrestore ×9, guardspec ×2, parlyzheal ×2, potion ×4, superpotion ×4, xaccuracy ×2, xspecial ×7, xspeed ×2.

Player strategy: C. Policy: `B:solo-recovery/1; C:goal-based-setup/2`.

Enable C planning over B recovery. Target Sp. Atk +2. Target accuracy +2 plus the active foe's positive evasion stages, capped at +6. Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops. While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent. Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.

Setup goals: `{"accuracy": 2, "guard_accuracy": true, "outspeed": true, "spa": 2, "target_torrent": false}`.

Prepared entry keeps the recorded HP, PP and bag; no additional heal is assumed.

| Variant | Entry HP / Torrent | Exact move PP (remaining/base) | Opening action | Win sample | Simultaneous interval |
|---|---|---|---|---:|---:|
| recorded | 171/171 full; Torrent off | BITE: 25/25, SURF: 13/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use guardspec | 325/340 (95.6%) | 88.4%–99.0% |
| prepared | 171/171 full; Torrent off | BITE: 25/25, SURF: 13/15, BLIZZARD: 5/5, STRENGTH: 15/15 | Use guardspec | 325/340 (95.6%) | 88.4%–99.0% |

Result source: recorded — C2 held-out benchmark, seed 4; prepared — C2 held-out benchmark, seed 4.

## League PP contract and remaining integration work

These entry PP are requirements for the independent League fights. They are not a proven sufficient budget for a continuous run with random misses and extra attacks.

| Fight | Bite PP | Surf PP | Blizzard PP | Strength PP |
|---|---:|---:|---:|---:|
| lorelei | 25 | 15 | 5 | 15 |
| bruno | 19 | 14 | 5 | 15 |
| agatha | 19 | 9 | 5 | 15 |
| lance | 19 | 4 | 5 | 15 |
| champion | 25 | 13 | 5 | 15 |

Before Champion, the observed run uses one Elixir: Bite 18→25, Surf 3→13, Blizzard 0→5, Strength stays 15. Observed League casts total 16 Surf and 7 Blizzard, exceeding their base 15 and 5 PP. Equivalent recovery capability could be supplied by one Max Elixir or two Ether/Max Ether actions targeting Surf and Blizzard, but those alternative entry bags have not been separately benchmarked. Acquire/replenish resources before the League; their pickup/shopping route and additional stochastic reserve remain unresolved.

## Scope and limitations the receiving agent must preserve

- This is Pokeguy's LeafGreen Squirtle route, modeled with FRLG Gen 3 mechanics: 69 trainer battles only. It does not claim to cover every mandatory game objective. Wild fights, captures/escapes and the Tower Marowak objective have no win-rate entries here.
- EXP/EV reconciliation uses the observed route, including the early wild wins. A new run that flees all wild encounters must recompute levels/EVs; do not use these stats unchanged or silently substitute a FireRed trainer team.
- Fight entries are independent snapshots. Do not multiply these rates into a route-clear probability. Propagate actual HP/PP/bag outcomes and healing stops before claiming a continuous-route estimate. A full bag here is a measured assumption, not a shopping list.
- Only the six named rests are adopted changes. Speed-EV/Dig alternatives are excluded. Later full-heal candidates remain unmeasured, especially where Torrent affects C setup.
- Player helper Pokémon, voluntary switches and party-accurate Roar/Whirlwind are not modeled. Player faint means loss. NPC mandatory replacements use a type-first, then damage heuristic; the party table is source order, not a promised send-out sequence. NPC voluntary switching is absent.
- NPC moves use pret scoring scripts and their tie-breaking, not a uniform 25% distribution over four moves. NPC medicine thresholds and damage/history/ability helpers are approximate. The listed personalities/natures are model inputs, not proof of cartridge parity.
- Showdown actual turns and Smogon previews can differ from cartridge accuracy arithmetic. Threat estimates simplify toxic/residuals and critical rates. More trials do not remove model error.
- Rates belong to the specified profile and policy. Attack IV25 is the selected overlay profile; IV24 survived earlier reconciliation as an alternative. Changes to policy, party, moves, bag, PP or HP require a new estimate rather than relabeling these probabilities.
- Fire/grass starters with supporters are deferred future analyses, not included results.

## Provenance and how to use this handoff

Copy this Markdown file into the consuming repo. All 69 player entry contracts, opponent teams, setup goals, strategy rules and rates are embedded; reading other repository files is not required to understand the plan. It is an integration specification, not a bundled battle engine or a guarantee that a separately implemented controller reproduces these rates.

Benchmark source: https://github.com/dayfine/PokemonSimulation. Original AutoStory change: https://github.com/dayfine/Arduino-Source/pull/213. Video: https://www.youtube.com/watch?v=CbfjWuRWH10. pret data revision: `ce6406d8c2eaf46d543c8a2606de0c3cb1951982`. Engine packages: pokemon-showdown 0.11.11 and @smogon/calc 0.12.0, Gen 3 adapter. Policies: B:solo-recovery/1 and C:goal-based-setup/2; retained A/B baseline results preserve their historical provenance. Fresh C validation seed 4; preparation seed 11; supplemental rest seed 12. Intervals use the combined 112-arm family correction.


## Regenerate this file in PokemonSimulation

Only regeneration requires the source repository, Python 3.8+, Node 22+ and the installed pinned engine packages. Opening previews initialize battles but do not run turns or replace measured win rates.

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_conditions
```

The preparation plan contains pinned C2 and supplemental rest counters. The latter used seed 12: Sammy 158/160, Liam 120/120, Brock 120/120. No top-ten reordering is presented as new simulation. The other results come from the existing original and preparation benchmark reports.

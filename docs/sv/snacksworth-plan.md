# Scarlet/Violet Snacksworth automation plan

Status: researched design, not an implemented or console-validated automation.
Research date: 2026-11-09. Companion: [acquisition and encounter routes](snacksworth-routes.md).

## Objective and starting state

Automatically acquire and prepare a catching team, travel to each requested
Snacksworth encounter, catch it, and save verified progress in either Scarlet or
Violet. The required treats are **already in the bag**; earning BBQ rewards is
outside this plan. Do not require trades, HOME, or version-exclusive helpers.

Assume both DLC regions and the postgame are accessible, the mount's free flight
is unlocked, and the player has full obedience. Flight ability does not imply
that every fast-travel destination has been visited: check and register missing
destinations separately. Do not assume an existing trained catcher, money,
candies, TMs, shards, or evolution stones; inventory these at startup.

All 25 encounters are level 70 except Kubfu, level 30.
[Encounter reference](https://www.serebii.net/scarletviolet/snacksworthlegendary.shtml)

## Team decision

Use Golduck, Gallade, and Magic Guard Clefable. Catching all three is possible in
both versions. Add **Ghost Tera to Gallade** for the horses. This is a proposed
solution requiring battle validation, not a claim that Clefable alone makes
every encounter safe at 1 HP.

| Helper | Core moves | Preparation |
|---|---|---|
| 哥达鸭 / Golduck | Soak, Taunt; optional Chilling Water and Amnesia | Level 100; train HP and bulk. No particular ability required. |
| 艾路雷朵 / Gallade | False Swipe, Thunder Wave, Taunt, Swords Dance | Level 100; train HP/Attack, check Speed; Ghost Tera required for horse profile. Ability is not essential. |
| 皮可西 / Clefable | Skill Swap; optional Reflect, Light Screen, Moonlight | Level 100; **Magic Guard** required; train HP/bulk. Recheck ability after evolving. |

Legal moves: [Golduck](https://pokemondb.net/pokedex/golduck/moves/9),
[Gallade](https://pokemondb.net/pokedex/gallade/moves/9),
[Clefable](https://pokemondb.net/pokedex/clefable/moves/9).

Prefer non-damaging setup and False Swipe. Ordinary chip is unnecessary and adds
critical-hit risk, especially against level-30 Kubfu. Chilling Water is optional,
must stop well before low HP, and cannot lower Solgaleo's Attack while it retains
Full Metal Body. Avoid Snarl against the Justified swords of justice.

Soak makes the target pure Water: False Swipe can hit Ghosts, and Thunder Wave
can affect originally Electric/Ground targets. It does not remove abilities.
Do not infer battle typing from the summary-screen Tera Type: these encounters
are not automatically Terastallized. Thunder Wave has 90% accuracy; confirm
paralysis rather than counting one button press as success.
[Soak](https://bulbapedia.bulbagarden.net/wiki/Soak_(move)),
[Thunder Wave](https://bulbapedia.bulbagarden.net/wiki/Thunder_Wave_(move))

Magic Guard prevents normal recoil and sand damage, but **not confusion or
Struggle damage**. Swapping it onto the opponent persists when Clefable leaves;
Clefable regains its normal ability after battle. Never accidentally Skill Swap
a second time and remove protection.
[Magic Guard](https://bulbapedia.bulbagarden.net/wiki/Magic_Guard_(Ability))

## Preparation workflow

1. Audit boxes, bag, money, flight destinations, helper moves/abilities, Tera
   type, and whether each requested legendary was already caught.
2. Catch Golduck and Gallade in Paldea; catch Clefairy in Kitakami. Detailed
   flight starts and search instructions are in the route guide.
3. Obtain a Moon Stone, evolve Clefairy, and inspect its ability. If Cute Charm,
   use an Ability Capsule to obtain Magic Guard. Ordinary wild catches avoid
   the hidden-ability conversion complication of raid catches.
4. Teach essential moves first. Avoid breeding/Mirror Herb dependencies: Yawn
   is unnecessary for the default paralysis plan.
5. Level the helpers and train stats. Use existing candies first; if resources
   are insufficient, run a separately measured EXP/money/material farming phase.
   Do not hide this potentially substantial work inside "prepare team."
6. Change Gallade to Ghost Tera at Medali's Treasure Eatery with 50 Ghost Tera
   Shards. Register Medali and the preparation shops as route checkpoints.
7. Stock configurable quantities of Ultra/Timer Balls, healing items, status
   cures, and PP restoration. Inspect actual stock before each encounter.
   Maximize False Swipe PP if resources allow. Use Leftovers or another harmless
   held item; never Rocky Helmet or an item that damages the opponent.
8. Fix party and move order, disable autosave and nicknaming prompts where
   available, and create a verified manual save before the first trial.

An Ability Capsule costs ₽100,000 at postgame Chansey Supply. Changing Tera type
costs 50 matching shards at the Treasure Eatery after Larry's Gym.
[Capsule](https://bulbapedia.bulbagarden.net/wiki/Ability_Capsule),
[Tera change](https://sv-news.pokemon.co.jp/en/page/20.html)

### Move acquisition checklist

| Move | Preferred source | Fallback |
|---|---|---|
| Golduck: Soak, Amnesia | Remember Moves / level-up | Train to required level, then remember |
| Gallade: False Swipe, Swords Dance | Remember Moves / level-up | False Swipe TM057 if needed |
| Thunder Wave | Existing TM082 | Craft: 400 LP, 3 Mareep Wool, 3 Pawmi Fur |
| Taunt | Existing TM087 | Craft: 3,000 LP, 3 Meowth Fur, 3 Sableye Gem, 3 Sneasel Claw |
| Skill Swap | TM098 pickup at Crystal Pool, southeast pond edge | Craft: 3,000 LP, 3 Girafarig Fur, 3 Flittle Down |
| Chilling Water, optional | Existing Cascarrafa Gym reward TM022 | Craft: 3,000 LP, 3 Psyduck Down, 3 Surskit Syrup |

Audit recipe unlocks and TM counts before material farming. One consumed Taunt
TM is needed per helper taught the move. Crystal Pool's Skill Swap pickup is a
useful stop while acquiring Clefairy.
[TM recipes](https://www.nintendolife.com/guides/pokemon-scarlet-and-violet-how-to-craft-tms-all-tm-recipes),
[Crystal Pool pickup](https://www.thonky.com/pokemon-scarlet-violet/crystal-pool),
[Chilling Water](https://pokemondb.net/item/tm022)

## Battle profiles

### Ordinary encounter

1. Arrive, heal/restore PP, save outside interaction range, then confirm species
   and level when battle starts. Abort safely on an accidental wild encounter.
2. Golduck uses Soak when the target is not already pure Water. Confirm success
   or recognize the harmless "already Water" failure.
3. Use Taunt early for targets that heal, set up, or change typing. Reapply based
   on observed turns/messages; do not blindly repeat Soak after every failure.
4. If recoil or damaging weather requires it, switch to Clefable, Skill Swap
   Magic Guard onto the target, and confirm that exchange before reducing HP.
5. Switch to Gallade, apply Thunder Wave until paralysis is confirmed, then
   False Swipe to 1 HP. Use Swords Dance only if damage/turn-budget measurements
   justify it. Prioritize healing and required Taunt refreshes.
6. Throw balls; switch to Timer Balls according to the configured ball policy.
   Track opponent turns/PP conservatively and reset before Struggle is possible.
7. Confirm capture and species, finish result screens, then save. Only mark the
   target complete after the save is confirmed.

An opponent's red HP bar is not proof of 1 HP. Continue False Swipe until the
conservative HP/damage model guarantees the floor, or validate another detector.
If no exact model exists, use repeated False Swipes against a defensible worst
case rather than a single preset hit count.

### Solgaleo: recoil and Metal Burst

Apply Magic Guard using Clefable **before** low HP, then use Gallade. Full Metal
Body is swappable. Wild Charge/Flare Blitz recoil is then blocked. Metal Burst
can still hurt the catcher: no boosted, large False Swipe without checking the
possible retaliation and current HP. Keep a conservative turn budget.
[Full Metal Body](https://www.serebii.net/abilitydex/fullmetalbody.shtml)

### Glastrier / Spectrier: Thrash and Double-Edge

Use **Ghost-Tera Gallade** as the final active catcher, then keep it active while
throwing balls. Normal attacks cannot hit it. Spectrier must first be Soaked so
False Swipe works. Complete any Magic Guard setup while the horse remains
healthy, then enter Ghost form before weakening it.

Observe and clear any confusion caused during setup before reducing HP. A
Thrash sequence already underway can complicate the switch; the console trial
must cover 2- and 3-turn sequences, interruptions, and confusion expiration.
Do not declare the 1-HP state safe just because Ghost Tera is active.

Use Taunt to control Glastrier's Taunt/Iron Defense and Spectrier's Disable.
An existing Disable needs recovery/expiration handling. Restore Tera charge at
a Pokémon Center before this profile; a reset must restore the saved charge too.
[Thrash mechanics](https://bulbapedia.bulbagarden.net/wiki/Thrash_(move))

### Other exceptions to handle explicitly

| Target or condition | Required behavior |
|---|---|
| Kubfu, level 30 | No ordinary damaging setup; use False Swipe directly after status/setup. |
| Lugia / Ho-Oh | Taunt to prevent Recover; account for Pressure PP consumption. |
| Groudon / Rayquaza | Taunt to prevent Rest healing and clearing paralysis. |
| Kyogre | Prevent Aqua Ring before activation; if already active, repeated HP recovery requires a different loop/reset. |
| Latias | Reflect Type can undo Soak. Detect type changes and reapply only when necessary. |
| Articuno / Kyogre / Groudon | Level-100 helpers exceed the level-70 OHKO users; keep all helpers above 70. |
| Moltres / outdoor sand | Wait for safe weather or give target Magic Guard before reaching low HP. |
| Accuracy/evasion changes | A missed status/setup move must not advance the state machine. |
| Helper status, fainting, depleted PP | Heal/recover or reset; no automatic damaging fallback move. |

Encounter-specific move inventory must be imported and audited before coding
policies; the table is a risk checklist, not a substitute for all four moves.
[Encounter moves](https://www.serebii.net/scarletviolet/snacksworthlegendary.shtml)

## Navigation and recovery design

Each route starts at a registered fast-travel destination and ends at a visually
verified interaction position. Normalize map north/zoom, mount state, and camera
after arrival. Use altitude-aware waypoints for cave entrances, towers, cliff
ledges, and the crater rim. A map pin alone cannot distinguish a cave floor
from the mountain above it.

Persist per-target state: version, treat present, already caught, route revision,
flight destination, checkpoint, last save, party/moves/items/charge, battle
profile, successful status/ability/type changes, HP bounds, turns, PP bounds,
ball count, and capture/save confirmation. Persist battle counters only for
diagnosis: after resetting, rebuild them from the saved battle start.

Bound every search and movement segment. On failure, return to a known flight
anchor and retry a limited number of times. Do not wander indefinitely. On KO,
unexpected battle state, or unsafe PP/stock bounds, reset to the last prebattle
save. Never save a failed capture attempt over that checkpoint.

Treat possession alone does not prove that an absent target is a navigation
failure: distinguish already caught, wrong altitude, wrong location, and not
yet rendered. Preserve previously completed captures when resetting the current
one by saving after each verified success.

## Implementation sequence and acceptance

1. **Preparation pilot:** acquire the three helpers and record short flight-to-
   search routes; verify moves, ability conversion, evolution and Ghost Tera.
2. **First complete catch:** Kubfu from Fury Falls. Implement fly, approach,
   interact, status, False Swipe, balls, capture verification and save.
3. **Generalization:** a simple level-70 target, then an Electric target and a
   Ghost target. Validate Soak/Thunder Wave and hit/miss recognition.
4. **Special battles:** healing, sand, Solgaleo, and both horses. Validate worst
   cases before permitting unattended execution of those profiles.
5. **All routes:** record each route from its anchor, including camera setup,
   landmarks, altitude transitions, search bounds and recovery. Capture actual
   controller timings only here; never invent them from a written guide.
6. **Resume and endurance:** interrupt after a save and during a failed attempt;
   verify that resume catches only remaining requested targets. Run both
   versions and multiple weather/time states; report actual trial counts.

Completion means all requested captures are verified and saved with no manual
intervention after the declared starting state. Team acquisition, training and
supplies count toward end-to-end completion. Research completion does not imply
that controller timings, battle reliability, or resource farms are validated.

## Remaining measurements

- Compare a bounded daytime Gallade search with male Kirlia plus a fixed Dawn
  Stone; wild Gallade is rarer than my earlier "easy to catch" answer suggested.
- Clefairy cave search region and nighttime detection in the target save.
- Missing flight-point registration routes and menu selection across languages.
- Existing EXP/money/shards/TMs versus the resource-farming work actually needed.
- Helper stats, speed margins, worst-case survival, and False Swipe turn bounds.
- Horse transition/confusion handling, Disable recovery, Solgaleo Metal Burst.
- Reliable capture/save detectors, opponent PP bounds, and final ball policy.

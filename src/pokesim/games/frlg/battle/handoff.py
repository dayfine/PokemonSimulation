"""Self-contained handoff content and deterministic opening-policy previews."""

from pokesim.games.frlg.battle.benchmark import scenario_for, reveal
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.battle.npc_ai import move_id
from pokesim.games.frlg.battle.policy import player_action


def opening_contracts(report, pret):
    """Resolve opponents and first decisions, without simulating any turns.

    These previews do not replace measured probabilities or prescribe later
    turns. Use the actual policy so current HP, PP, and setup goals are honored.
    """
    ai, result = NPCTrainerAI(pret), {}
    with Engine() as engine:
        for row in report['fights']:
            variants = {}
            for variant in ('recorded', 'prepared'):
                scenario = scenario_for(row[variant], pret)
                state = engine.request(command='start', scenario=scenario, seed=[1, 2, 3, 4])
                reveal(state, set())
                action = player_action(state, ai, scenario['trainer']['ai'],
                    [move_id(item) for item in scenario['trainer']['items']],
                    enable_complex_planning=row['strategy']['tier'] == 'C',
                    planning_goals=row['strategy'].get('planning_goals'))
                variants[variant] = {'action': action, 'own': state['own'], 'opponents': state['party']}
            result[row['id']] = variants
    return result


def action_text(action, moves):
    if action['kind'] == 'move':
        return 'Use ' + moves[action['slot']]['name']
    if action['kind'] == 'item':
        target = ' on ' + moves[action['slot']]['name'] if 'slot' in action else ''
        return 'Use ' + action['item'] + target
    return action['kind']


def fight_strategy(row):
    """Translate policy goals into a fight-specific conditional playbook."""
    tier = row['strategy']['tier']
    if tier == 'A':
        return ('Use the opening below, then the attack selector. This fight was classified A because '
                'the baseline samples used attacks only. The measured controller still has B recovery '
                'enabled; retain the listed bag rather than assuming item use is forbidden.')
    if tier == 'B':
        return ('Use B recovery: recompute the attack each turn; take a finishing hit when the B rule '
                'allows it, otherwise check status cure, HP medicine, Oran Berry, then PP recovery. '
                'Use only the listed bag; do not use X items or deliberately stall for setup.')
    goals = row['strategy']['planning_goals']
    instructions = ['Enable C planning over B recovery. Target Sp. Atk +{}.'.format(goals.get('spa', 0))]
    if goals.get('torrent_power'):
        target = goals.get('spa', 0)
        stronger = next((s for s in range(target, 7) if (2 + s) / 2 >= 1.5 * (2 + target) / 2), 6)
        instructions.append('If Torrent is inactive, raise that target to +{}.'.format(stronger))
    instructions.append('Target accuracy +{} plus the active foe\'s positive evasion stages, capped at +6.'.format(goals.get('accuracy', 0)))
    if goals.get('outspeed'):
        instructions.append('Use X Speed as needed to be strictly faster than every remaining opponent; repair Speed drops.')
    if goals.get('guard_accuracy'):
        instructions.append('While setup is pending, use Guard Spec first if the active foe has an accuracy-lowering move and Mist is absent.')
    else:
        instructions.append('Do not spend Guard Spec for this plan.')
    if goals.get('target_torrent'):
        instructions.append('During the opening setup window, aim for Torrent (HP at most one third), '
            'or substitute enough Sp. Atk to match its multiplier. Use productive setup/weak attacks '
            'instead of intentionally KOing the setup foe; do not repeat Torrent activation on later foes.')
    instructions.append('Follow C safety/healing rules before spending setup turns, then attack; these are stage targets, not a fixed item-count script.')
    return ' '.join(instructions)


POLICY_GUIDE = r"""## Strategy rules to implement in the consuming repo

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
"""


def progression_guide(moves):
    lines = ['## Move-learning and evolution decisions', '',
        'Keep the per-fight moves and PP exactly as listed. Level-up choices below apply whenever '
        'the stated level is reached, including during a battle; the event is the observed timing, '
        'not a guarantee under a different outcome. New moves start at base PP. Allow the normal '
        'Wartortle/Blastoise evolutions at levels 16/36 on this route. Starting species, EXP and '
        'stats in each fight remain the entry contract.', '',
        '| Move | Action | Replace | Acquisition | Observed timing |', '|---|---|---|---|---|']
    for decision in moves['decisions']:
        when = decision['when']
        method = 'Level ' + str(decision['level']) if decision['method'] == 'level_up' else decision['method']
        event = when['event']
        if event == 'cerulean-candy1':
            event = 'Rare Candy preparation before Misty'
        at = when['at'].replace('_', ' ')
        if 'foe_index' in when:
            at += ' ' + str(when['foe_index'] + 1)
        lines.append('| {} | {} | {} | {} | {}: {} |'.format(decision['move'], decision['action'],
            decision.get('replaces') or 'empty slot / no replacement', method, event, at))
    lines += ['', 'Do not teach Dig in these adopted variants. Mega Kick and Bite are already '
        'included before Misty; Water Pulse replaces Tackle before Cerulean rival. Surf, Blizzard '
        'and Strength replace Water Gun, Mega Kick and Water Pulse at the points above. '
        'Decline Rapid Spin, Protect, Rain Dance and Skull Bash.', '']
    return '\n'.join(lines)


def logistics_and_limits(league, pret):
    rows = ['## League PP contract and remaining integration work', '',
        'These entry PP are requirements for the independent League fights. They are not a proven '
        'sufficient budget for a continuous run with random misses and extra attacks.', '',
        '| Fight | Bite PP | Surf PP | Blizzard PP | Strength PP |', '|---|---:|---:|---:|---:|']
    for fight in league['fights']:
        pp = fight['assumed_entry_pp']
        rows.append('| {} | {} | {} | {} | {} |'.format(fight['fight'],
            pp['BITE'], pp['SURF'], pp['BLIZZARD'], pp['STRENGTH']))
    rows += ['', 'Before Champion, the observed run uses one Elixir: Bite 18→25, Surf 3→13, '
        'Blizzard 0→5, Strength stays 15. Observed League casts total 16 Surf and 7 Blizzard, '
        'exceeding their base 15 and 5 PP. Equivalent recovery capability could be supplied by '
        'one Max Elixir or two Ether/Max Ether actions targeting Surf and Blizzard, but those '
        'alternative entry bags have not been separately benchmarked. Acquire/replenish resources '
        'before the League; their pickup/shopping route and additional stochastic reserve remain unresolved.', '',
        '## Scope and limitations the receiving agent must preserve', '',
        '- This is Pokeguy\'s LeafGreen Squirtle route, modeled with FRLG Gen 3 mechanics: '
        '69 trainer battles only. It does not claim to cover every mandatory game objective. '
        'Wild fights, captures/escapes and the Tower Marowak objective have no win-rate entries here.',
        '- EXP/EV reconciliation uses the observed route, including the early wild wins. '
        'A new run that flees all wild encounters must recompute levels/EVs; do not use these '
        'stats unchanged or silently substitute a FireRed trainer team.',
        '- Fight entries are independent snapshots. Do not multiply these rates into a route-clear '
        'probability. Propagate actual HP/PP/bag outcomes and healing stops before claiming a '
        'continuous-route estimate. A full bag here is a measured assumption, not a shopping list.',
        '- Only the six named rests are adopted changes. Speed-EV/Dig alternatives are excluded. '
        'Later full-heal candidates remain unmeasured, especially where Torrent affects C setup.',
        '- Player helper Pokémon, voluntary switches and party-accurate Roar/Whirlwind are not modeled. '
        'Player faint means loss. NPC mandatory replacements use a type-first, then damage heuristic; '
        'the party table is source order, not a promised send-out sequence. NPC voluntary switching is absent.',
        '- NPC moves use pret scoring scripts and their tie-breaking, not a uniform 25% distribution '
        'over four moves. NPC medicine thresholds and damage/history/ability helpers are approximate. '
        'The listed personalities/natures are model inputs, not proof of cartridge parity.',
        '- Showdown actual turns and Smogon previews can differ from cartridge accuracy arithmetic. '
        'Threat estimates simplify toxic/residuals and critical rates. More trials do not remove model error.',
        '- Rates belong to the specified profile and policy. Attack IV25 is the selected overlay '
        'profile; IV24 survived earlier reconciliation as an alternative. Changes to policy, party, '
        'moves, bag, PP or HP require a new estimate rather than relabeling these probabilities.',
        '- Fire/grass starters with supporters are deferred future analyses, not included results.', '',
        '## Provenance and how to use this handoff', '',
        'Copy this Markdown file into the consuming repo. All 69 player entry contracts, opponent '
        'teams, setup goals, strategy rules and rates are embedded; reading other repository files '
        'is not required to understand the plan. It is an integration specification, not a bundled '
        'battle engine or a guarantee that a separately implemented controller reproduces these rates.', '',
        'Benchmark source: https://github.com/dayfine/PokemonSimulation. Original AutoStory change: '
        'https://github.com/dayfine/Arduino-Source/pull/213. Video: '
        'https://www.youtube.com/watch?v=CbfjWuRWH10. pret data revision: `' + pret['source']['revision'] +
        '`. Engine packages: pokemon-showdown 0.11.11 and @smogon/calc 0.12.0, Gen 3 adapter. '
        'Policies: B:solo-recovery/1 and C:goal-based-setup/2; retained A/B baseline results preserve '
        'their historical provenance. Fresh C validation seed 4; preparation seed 11; supplemental '
        'rest seed 12. Intervals use the combined 112-arm family correction.', '']
    return '\n'.join(rows)

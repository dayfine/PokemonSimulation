# AutoStory plan replay and battle-quality evaluation

This is the proposed integration contract. AutoStory owns the game plan,
including its route, captures, training, preparation and battle strategy.
PokemonSimulation evaluates the battle history produced by replaying that
plan. The existing Pokeguy handoff is one reference fixture, not the fixed
battle list that every AutoStory plan must follow.

```text
AutoStory game plan + starting profile + replay choices
    → planning replay / semantic event log
    → battle history with entering conditions and policies
    → PokemonSimulation validation and battle evaluation
    → per-fight results + plan-quality report
    → revise the AutoStory plan and replay again
```

The replay runs without pressing console buttons. Its rules must describe
the same route and decisions that the console executor will use. This repo
owns the mechanics/evaluation engine and reference data, not the producer's
game-plan logic. An optional generated runtime data bundle is an adapter;
it does not reverse this ownership.

The general history importer, plan grader and Arduino replay exporter are
not implemented yet. Today's reports evaluate independent FRLG solo-lead
entry snapshots. This document defines the direction and the next slices;
it does not claim those future capabilities already work.

## Producer: replay the actual plan

Expose a planning executor alongside the console executor. The existing
native fake-game/story-table seam is a useful starting point, but a fake
that simply returns success for preparation/battles is insufficient. Emit
semantic effects, not controller timings or opaque human log messages.

| Replay event | Information needed to derive or verify battle entries |
|---|---|
| Start / obtain starter | Game/version, party identity, species/profile, starting EXP/stats, money, bag and badges |
| Travel / encounter | Location, triggered trainer ID or encounter objective, chosen branch; record any battle that changes state |
| Catch / recruit | Target/obtained Pokémon, level and profile assumptions, consumed balls, objective result; preserve a stable party-member ID |
| Battle / train | Trainer or wild encounter, objective, participants and policy; EXP/EV/item/PP effects depend on the outcome |
| Learn / forget / evolve | Pokémon ID, move replacement or decline, evolution decision and its trigger |
| Heal / use item | Scope and actual HP/status/PP effect; record consumption, not an implicit reset |
| Shop / pick up / withdraw / deposit | Item/money/party changes and their source; negative inventory is invalid |
| Checkpoint / retry | State restored by a reset, retry/abort policy and branch choice; do not assume infinite free attempts |

Normalize the replay into a versioned battle-history document. Every fight
occurrence needs a unique ID and a source event/checkpoint so a poor result
can be traced back to the AutoStory step that produced it. Additional or
repeated training battles are explicit occurrences, not silently collapsed
by trainer name. Do not copy the 69 Pokeguy encounters into unrelated plans.

## Minimum battle-history contract

The exchange format should be plain versioned JSON/JSONL, independent of
Arduino C++ types. The raw replay may be JSONL; a normalized history can be
one JSON document containing ordered events, state records and battle rows.
The following is a shape sketch, not a complete importable fixture:

```json
{
  "format": "pokesim-autostory-history/1",
  "plan": {"id": "frlg-squirtle", "revision": "producer-commit"},
  "game": "leafgreen",
  "ruleset": "frlg-gen3",
  "replay": {"id": "replay-001", "choices": {}, "coverage": "one-reference-trace"},
  "evaluation_scope": "independent-entry-contracts",
  "events": [],
  "states": {},
  "battles": [
    {
      "id": "pewter/brock/1",
      "source_event": 42,
      "objective": "defeat-trainer",
      "opponent": {"trainer_id": "TRAINER_LEADER_BROCK"},
      "entry_state": "state-042",
      "entry_provenance": "replayed",
      "strategy": {
        "declared_tier": "A",
        "policy_id": "B:solo-recovery/1",
        "parameters": {}
      }
    }
  ]
}
```

Each referenced entry state must resolve all of the following:

- The **whole party**, its order and active member, with stable IDs that
  survive evolution. For each member: species, level, total EXP, nature,
  IVs/EVs or explicit compatible-profile assumptions, all raw summary
  stats, current/max HP, status, ability, held item, and each move's current
  and maximum PP. Include relevant starting stages/volatile/field effects,
  or explicitly declare a fresh battle before switch-in abilities.
- The supported battle bag with quantities, badges, game/version and
  trainer identity/variant. Reference data may be resolved by a pinned
  rules/data revision rather than duplicated in every event.
- Entering requirements and how the preceding replay establishes them:
  full rest, a specified medicine use, required PP, items and setup stock.
  Distinguish a requirement from an observed or derived state.
- The **actual player policy** and version/parameters, including permitted
  switching and setup goals. A/B/C is useful classification metadata;
  it is not a complete executable policy identifier. The current A-labeled
  Pokeguy cases still run B recovery. A new attacks-only plan must request
  and evaluate that policy explicitly.
- Source/profile assumptions, replay branch choices, and any unresolved
  state. Unknown quantities cannot be silently replaced with full HP,
  guessed PP, neutral IVs, or the Pokeguy starter's stats.

The evaluator must reject unknown policy versions and unsupported features
as unsupported/incomplete, not substitute a simpler policy and return a
plausible win rate. Cross-language policy implementations need parity tests
against shared state/action examples. An opening action is not a policy.
An IV/stat range or distribution must be evaluated as declared, or rejected
as unsupported; selecting its most favorable member is not validation of
the exported profile.

## Replay integrity and random outcomes

Validate inventory/money effects, EXP/EV awards and participation, evolution,
move learning, rests, PP consumption and encounter identity against the
trace wherever those effects are known. A Potion restores at most 20 HP;
it is not a full heal. A rest restores HP/status/PP, never the bag. A catch
cannot create a trained/evolved supporter without the preceding events.

Two evaluation scopes must remain distinct:

1. **Independent entry contracts:** evaluate each fully specified entry
   separately. This is the first general-import milestone and corresponds
   to today's per-fight approach. Label assumed entries and unverified
   reachability. An entry is not made feasible merely by writing it into
   the history.
2. **Carried replay simulation:** battle outcomes update the party, bag,
   EXP/EVs, HP and PP before replay continues through the plan's subsequent
   preparation/branches. This is needed for a continuous-route estimate,
   stochastic resource budgets, captures/training and retry behavior.

A planning replay cannot know exact exit HP/PP for a random battle merely
because its fake executor returned success. It must preserve uncertainty,
condition an explicitly labeled reference trace, or obtain the outcome from
the evaluator in the carried scope. Later rests can establish a known
HP/PP state; an unexplained snapshot reset cannot.

The producer declares scenario/branch/profile coverage. One reference trace
does not cover a capture loop, optional grind branches, or every possible
starter/supporter profile. Uncovered cases must remain visible. A report
must not turn conditional entry success into a full game-plan certificate
while feasibility, mandatory objectives or required branches are unresolved.

## Evaluator result contract

Return a versioned report tied to the producer plan/replay revision and
history hash, evaluator/policy/data versions, quality-profile hash and seeds.
For every fight, return its source event, resolved entry and policy,
objective, successes/trials, estimate and interval, stopping reason, and any
invalid/unsupported assumptions. The objective is a trainer win today;
future capture/escape results must measure success at their own objective.

Return each quality criterion's pass/fail/inconclusive status with the
fights/events responsible, plus separate integrity and coverage findings.
Missing inputs/features are incomplete/unsupported, not sampling uncertainty
and not wins. State the evaluation scope prominently. This lets the plan
author change the relevant training, rest, purchase or strategy step and
compare a new replay against the previous plan revision.

## Quality criteria and reporting

A quality profile belongs to a plan evaluation, with its own version/hash.
The user has proposed a minimum fight win rate around 60% or 70%, plus
fractions of easy/high-reliability battles. **The exact floor and X/Y quotas
are not chosen defaults.** Specify the comparison operator, population,
confidence level and interpretation of each criterion before grading.

For a declared population of N fights, report at least:

| Metric | Meaning |
|---|---|
| Minimum win probability | The weakest fight, its entry/policy and uncertainty |
| Fraction at or above 90% | How much of the plan meets the chosen reliability threshold |
| Fraction at a chosen near-certain threshold | For example 99% or 99.9%, if the user selects that interpretation |
| Zero-loss sample fraction | Fights with no losses in the trials actually run, including counts; this is descriptive |
| Proven certain-win fraction | Only fights certified by a proof/exhaustive method within its stated model; currently unavailable |
| Input/coverage integrity | Invalid, assumed, unsupported or uncovered entries/objectives, separately from sampling uncertainty |

Define the denominator explicitly. Required-story trainers, training/wild
fights, capture objectives and optional encounters should be reported
separately; adding easy grind encounters must not silently inflate the
required-story reliability quota. If several profiles/branches are required,
declare whether grading is per scenario or worst case across them. Averages
require explicit weights and must not hide a required weak branch.

Use simultaneous, anytime-valid confidence bounds across the graded fight
cases. Let [L_i, U_i] be a fight's interval. For criteria using `>=`:

```text
minimum probability >= floor:
    pass if every L_i >= floor
    fail if any U_i < floor
    otherwise inconclusive

fraction with probability >= threshold must be >= quota:
    certified_fraction = count(L_i >= threshold) / N
    possible_fraction  = count(U_i >= threshold) / N
    pass if certified_fraction >= quota
    fail if possible_fraction < quota
    otherwise inconclusive
```

Keep point-estimate results beside these certified decisions; do not silently
replace them with confidence bounds. Invalid history cannot pass by treating
missing fights as easy ones. Overall certification requires complete inputs,
declared coverage and satisfied criteria in the stated evaluation scope.

As an example, today's prepared Pokeguy Surge case is about 56.2%, with joint
bounds about 50.9%–61.5%. Its point estimate misses either a 60% or 70%
floor; these existing bounds certify failure at 70%, while 60% remains
inconclusive. The faster Speed-54 diagnostic is not a plan improvement until
the AutoStory replay actually produces that Speed and the resulting
training/EXP/EV changes are included in the new history.

### What “100%” can mean

Monte Carlo cannot establish a true win probability of exactly 1 from a
finite all-win sample. Keep these three claims separate:

- **100% observed:** zero losses in n trials; report n and the lower bound.
- **Statistically near certain:** the lower bound exceeds a user-selected
  threshold such as 99%/99.9%. It may require many more than 100 trials.
- **Guaranteed within the model:** exhaustive/proof coverage of the allowed
  outcomes and entry uncertainty. This requires a separate capability and
  still does not establish cartridge parity.

Do not quietly reinterpret the user's literal 100% quota as 99%, or keep
sampling forever for a bound to equal 1. Report an exact-guarantee criterion
as unsupported until a suitable proof method exists, or let the user choose
the operational near-certain interpretation.

### Sample until a decision is possible

Stop against the configured criteria, not just an arbitrary trial count or
a uniform 10-point interval width. Sample fights whose intervals straddle
the floor/quota thresholds. Stop early when a plan conclusively fails the
minimum, or when enough fights certify a quota; do not spend the remaining
budget on fights irrelevant to that decision. On exhaustion, return
inconclusive rather than inventing a pass/fail result.

Record seeds, stopping reasons, trials and policy/data/profile hashes. Plan
search and comparison also need an error budget across candidates or a
fresh held-out validation phase for the selected plan. Confidence bounds
remain conditional on model/input accuracy; console validation is separate.

## Supporter teams and implementation slices

The same producer contract should later describe Fire/Grass starter plans
that catch, train and evolve supporters. It must include every party member
and the real capture/training resource costs, EXP participation and policy
for switching/setup. A successful KO is not a successful capture objective.
Current solo-lead simulations cannot certify those plans by dropping the
supporters or assuming all captures succeeded.

Implement in this order:

1. Export a deterministic AutoStory planning replay and normalized history
   for its actual Squirtle stage. Include explicit assumptions and mismatch
   failures; keep native producer/controller seam tests in Arduino-Source.
2. Add a generic history importer/validator in PokemonSimulation. Feed the
   supplied fights and registered policies to the existing FRLG evaluator;
   reproduce a known fixture before accepting a different plan's results.
3. Add the configurable criteria/report layer and decision-directed
   adaptive sampling. Reports identify the failing fight/event, expected
   entry, source assumptions and policy so the producer can revise it.
4. Add carried replay/resource propagation and branch/objective coverage.
   Then extend battle policies/engine adapters for full parties, capture,
   training and supporter switching, with explicit unsupported cases until
   each capability is validated.

The producer owns changes to the game plan. The evaluator returns evidence
about that specific exported plan; editing a report or substituting a more
favorable entry snapshot is not a plan revision.

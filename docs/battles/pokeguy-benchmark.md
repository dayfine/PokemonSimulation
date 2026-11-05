# Pokeguy's FRLG trainer battle benchmark

This benchmark simulates all **69 trainer battles** in the reviewed LeafGreen
run, starting each fight independently from its [recorded entry state](../progression/pokeguy-states.md).
It estimates the success rate of our state-dependent player policy under the
model below. It does not replay the video's winning button presses or estimate
the probability of finishing the entire run.

See the [top ten and player-action grouping](pokeguy-action-complexity.md) for
the risk ranking and the attack/recovery/setup split.

The checked table below is the historical `solo-setup-heal/4` baseline.
Current code uses [incremental A/B/C layers](player-strategies.md); see the
[12-fight C rerun and new ranking](pokeguy-c-comparison.md) for the latest comparison.

## Run locally

```sh
npm ci --omit=optional --prefix engines/frlg-showdown
PYTHONPATH=src python3 -m pokesim.cli.frlg_run_battles --out /tmp/pokeguy-battles.json
```

The default uses three independent Python/Node workers, seed 1, a 300-turn
limit, and at most 3,000 trials per fight. `--workers 1` gives the same results
in one worker. For a subset, repeat `--case`, for example `--case ssanne-rival
--case surge`. The confidence family contains the requested cases.

The [adaptive sampler](adaptive-sampling.md) checks every 20 trials. It stops
when its anytime-valid interval spans at most 10 percentage points. Confidence
is 95% simultaneously across all requested battles and all sampling looks,
including work split among processes. An all-win case among 69 typically stops
after 100 trials; a close matchup needs thousands. Reaching the cap is labeled
`budget_exhausted`; it is never presented as meeting the precision target.

The JSON includes exact starting inputs, source fingerprints, seeds, intervals,
trial counts, item consumption, losses by opponent, and example win/loss traces.
Live EXP/EV awards in those traces identify the defeated party member and each
level increase. Repeated progression species data is stored once at
`progression_reference`; combine it with each case's `inputs.progression` to
reconstruct a direct engine scenario. A sibling `.checkpoint.json` preserves
completed cases during execution; it is a partial artifact, not an automatic
resume file.

To reproduce the full battle-data import from the pinned pret checkout:

```sh
PYTHONPATH=src python3 -m pokesim.games.frlg.battle.pret \
  --repo external/pokefirered \
  --run-data data/runs/pokeguy-leafgreen-15934 \
  --out data/runs/pokeguy-leafgreen-15934/battle-reference.json
```

## Inputs and actual battle updates

The case builder reconciles the recorded HP/status, raw stats, IV profile,
accumulated EVs, moves/PP, badges, held item, and tracked medicines/setup items.
It uses Mild and the overlay's Attack IV 25; Attack IV 24 is an unresolved
alternative in the stat reconstruction and is not mixed into this experiment.
The full trainer snapshot imports moves, default learnsets, IVs, deterministic
personalities/natures, held items, medicines, and AI flags from pret. It includes
170 relevant moves and the reachable scoring scripts.

The engine awards solo trainer EXP and EVs after **actual simulated knockouts**,
including opponents selected in a different order from the video. Raw stats
refresh when the lead levels up; its HP increases by the maximum-HP delta.
Badges apply separately to the new raw stats. Move offers follow the native
learnset and the recorded accept/replace/decline decisions, with fresh base PP
for a newly learned move. Evolution remains an after-battle event, represented
by the next fight's starting state. Recorded ending HP and item use never force
a simulated outcome.

Bag items consume a turn, act before attacks, and spend no move PP. Supported
actions include healing/status cures, Oran Berry, X items, Guard Spec, Dire Hit,
and Ether/Elixir variants. Gen 3 X items add **one** stage, capped at +6. Guard
Spec grants five turns of Mist. Held items resolve through the Gen 3 engine.

## Our player policy

`policy.py:player_action` controls our lead; `npc_ai.py:NPCTrainerAI` controls
the opponent. The run policy is `solo-setup-heal/4`:

- Choose a damaging move by estimated turns to knock out, accuracy, then PP
  conservation. Complete a locked move when required. Take a guaranteed faster
  finishing hit before an unnecessary heal, unless useful setup is available.
- Use a suitable cure or the smallest useful heal according to a sampled NPC
  threat estimate. Full Restore can also cure status/confusion.
- Restore exhausted attacking PP when it is safe to spend the turn.
- Consider available X items using previews against the remaining known team.
  Estimate enemy turns/damage prevented by the improved attacks or speed;
  require the benefit to exceed the current setup-turn risk and a margin.

This is a basic heuristic with full trainer-roster knowledge, not an optimal
solver or a reconstruction of Pokeguy's decisions. It may spend supplies
very differently. Guard Spec and Dire Hit have engine actions but are not
selected by the current heuristic. Threat estimates use 32 deterministic
private AI samples and a bounded cache of repeated states; they never inspect
the trial's future random draws.

## Model limits

Showdown resolves Gen 3 turns, while Smogon provides damage previews using live
raw stats, stages, weather, Reflect, and Light Screen. Multi-hit previews use
hit-count distributions and damage quantiles for policy decisions; actual hits
are sampled by Showdown. Oak's opening tutorial guarantees the first player's
damaging hit and suppresses critical hits until that first damage, matching
the relevant pret tutorial behavior exercised by this policy.

NPC scores follow imported pret scripts, but queries and damage helpers remain
an approximation to cartridge `AI_CalcDmg` and battle history. NPC decisions
and battle execution use separate seeded RNG streams. Voluntary NPC switching
is omitted; switch moves such as Baton Pass still execute and request a legal
replacement. Actual accuracy and preview accuracy can differ when both accuracy
and evasion stages change. Healing threat estimates simplify critical rates,
residual damage, and status interactions. See [the remaining gaps](GAPS.md).

Only the lead is modeled. HM helpers present before the Plateau deposits are
omitted; consequently Roar/Whirlwind can fail where the real party would allow
a forced switch. The benchmark does not simulate switching back from a helper.

The two random wild wins and scripted Marowak fight are recorded in the state
ledger but are not included in this trainer report. The two captures and four
escapes need success criteria other than a trainer victory. No rate is invented
for those six objectives. A route simulation carrying random HP/PP/bag outcomes
forward is also separate work; multiplying these conditional rates would not
produce a valid run-completion probability.

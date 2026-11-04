# Adaptive battle sampling

The benchmark can stop each encounter independently when its uncertainty
interval is narrow enough. It does not stop because the last few empirical
win rates happen to be similar or because a short winning streak occurred.

```sh
PYTHONPATH=src python3 -m pokesim.cli.frlg_battle --adaptive \
  --interval-width 0.10 --confidence 0.95 --min-battles 20 --batch-size 20 \
  --battles 2000 --out /tmp/frlg-adaptive.json
```

Without `--adaptive`, fixed-count evaluation and its existing report behavior
are preserved (default 1,000 trials). Adaptive mode defaults to a 2,000-trial
cap. `--battles` overrides that cap; 3,000 is a reasonable initial cap for a
future 69-case family at a total interval width of 0.10. Reaching the cap does
not imply convergence or adequate precision.

`--interval-width 0.10` means the **total interval span is at most ten
percentage points**. It does not mean ±five points around the empirical win
rate, especially at 0/100% observed rates. Set a smaller width when distinguishing
very high reliability such as 99% matters; a broad interval near 100% is not
evidence of a guaranteed win.

## Stopping rule and confidence

For each fixed scenario/policy, treat a trial as success if the player wins
within the turn limit. Losses and turn-limit outcomes are non-wins, with
turn-limit counts also reported separately. Trials use the same independent
seed scheme as fixed-count runs. Checking bounds draws no randomness.

Use a beta(1/2, 1/2) mixture likelihood ratio:

```text
M_n(p) = B(wins + 1/2, losses + 1/2) / B(1/2, 1/2)
         / [p^wins * (1-p)^losses]
C_n    = {p : M_n(p) < 1 / alpha_case}
alpha_case = (1 - confidence) / number_of_requested_cases
```

For each candidate true p, this mixture is a nonnegative test martingale.
Ville's inequality permits repeated looks and data-dependent stopping;
Bonferroni allocates the error across the requested cases. Thus the default
95% guarantee applies jointly to all their intervals and all interim looks
within one `evaluate()` call, under the fixed Bernoulli trial model. This uses
the [time-uniform confidence-sequence framework](https://arxiv.org/abs/1810.08240).

The implementation uses log-gamma arithmetic and outward binary-search bounds,
with explicit handling of all-win/all-loss endpoints. It uses the entire
history of wins/losses, not only the latest streak. It checks after 20 trials
and every 20 afterward by default, and always checks at the cap.

All-win examples with these defaults and a width target of 0.10:

| Cases in the experiment | First stopping sample count | Interval at that point |
|---:|---:|---|
| 1 | 60 | approximately 91.1–100% |
| 4 | 80 | approximately 91.5–100% |
| 69 | 100 | approximately 90.4–100% |

All-loss cases are symmetric. Mixed outcomes usually need more samples.
A single case at 20/20 wins has a much wider anytime interval, approximately
77.6–100%. The chosen sample count is a result of the precision/confidence
settings; it is not a universal fixed number.

## Output and interpretation

Adaptive results contain actual `battles`, `maximum_battles`, win counts,
empirical win probability, and `confidence_sequence` with `bounds`, `width`,
`precision_reached`, and `stop_reason`:

- `interval_width`: requested uncertainty width reached.
- `budget_exhausted`: cap reached while uncertainty remains too wide.

The report records the method, confidence across cases/looks, alpha allocated
per case, target width, minimum, and batch size. Means for turns, remaining HP,
and item use divide by the **actual** number of trials, not the cap. Example
logs retain the same trial seeds and decisions as the fixed-count prefix.

Adaptive reports use a confidence sequence rather than a repeatedly inspected
fixed-sample Wilson interval. Confidence describes Monte Carlo uncertainty
under the stated inputs/policy/engine. More samples cannot repair the
[missing full-run inputs and mechanics](pokeguy-readiness.md), and repeated
experiments with new policy choices need their own stated comparison plan.

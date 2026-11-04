"""Adaptive Bernoulli sampling with an anytime-valid beta-mixture interval.

The Jeffreys beta(1/2, 1/2) mixture likelihood ratio is a test martingale
under each candidate win probability p. Invert M_n(p) < 1/alpha and use
Ville's inequality; repeated looks and data-dependent stopping are allowed.
Bonferroni allocates alpha across all requested cases. No RNG is consumed.
See https://arxiv.org/abs/1810.08240 for time-uniform confidence sequences.
"""

import math


def confidence_sequence(wins, trials, alpha=0.05):
    """Bounds cover a fixed Bernoulli p at every trial count with error <=alpha."""
    if type(trials) is not int or trials < 0 or type(wins) is not int or not 0 <= wins <= trials:
        raise ValueError("Wins and trials must be valid nonnegative integer counts")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")
    if not trials:
        return [0.0, 1.0]
    losses = trials - wins
    # log B(wins+1/2, losses+1/2) - log B(1/2, 1/2).
    mixture = (math.lgamma(wins + 0.5) + math.lgamma(losses + 0.5)
               - math.lgamma(trials + 1) - 2 * math.lgamma(0.5))
    threshold = -math.log(alpha)

    def log_ratio(p):
        if p == 0:
            return math.inf if wins else mixture
        if p == 1:
            return math.inf if losses else mixture
        return mixture - wins * math.log(p) - losses * math.log1p(-p)

    estimate = wins / trials
    low, high = 0.0, estimate
    if wins:
        for _ in range(64):
            mid = (low + high) / 2
            if log_ratio(mid) > threshold:
                low = mid
            else:
                high = mid
        lower = low  # Round outward.
    else:
        lower = 0.0
    low, high = estimate, 1.0
    if losses:
        for _ in range(64):
            mid = (low + high) / 2
            if log_ratio(mid) > threshold:
                high = mid
            else:
                low = mid
        upper = high
    else:
        upper = 1.0
    return [lower, upper]


class AdaptiveSampling:
    """Stop at a requested interval width, or label exhaustion of the budget.

    Width is the total interval span, not ±error about the empirical rate.
    The default 95% guarantee covers all cases and all interim sample counts
    within one evaluate() call; it does not cover model/input inaccuracies.
    """

    def __init__(self, width=0.10, confidence=0.95, minimum=20, batch=20):
        if not 0 < width < 1 or not 0 < confidence < 1:
            raise ValueError("Width and confidence must be between zero and one")
        if any(type(v) is not int or v < 1 for v in (minimum, batch)):
            raise ValueError("Minimum trials and batch size must be positive integers")
        self.width, self.confidence = width, confidence
        self.minimum, self.batch = minimum, batch

    def describe(self, cases):
        return {"method": "jeffreys-beta-mixture-confidence-sequence",
            "confidence_all_cases_all_looks": self.confidence,
            "alpha_per_case": (1 - self.confidence) / cases,
            "target_interval_width": self.width, "minimum_trials": self.minimum,
            "batch_size": self.batch}

    def check(self, wins, trials, maximum, cases):
        """Return None between looks; otherwise bounds, width, and stop reason."""
        if self.minimum > maximum:
            raise ValueError("Minimum trials exceeds maximum trial budget")
        if trials < self.minimum and trials < maximum:
            return None
        if (trials - self.minimum) % self.batch and trials < maximum:
            return None
        bounds = confidence_sequence(wins, trials, (1 - self.confidence) / cases)
        width = bounds[1] - bounds[0]
        reached = width <= self.width
        return {"bounds": bounds, "width": width, "precision_reached": reached,
            "stop_reason": "interval_width" if reached else ("budget_exhausted" if trials >= maximum else None)}

"""Player shots-on-target prop model — with hierarchical shrinkage.

A striker with 3 shots in 1 World Cup game is not a "3 shots/game" player; it's a tiny
sample screaming for regression to the mean. Raw rates overfit and will lose money. This
module shrinks each player's rate toward a group prior (empirical Bayes), so a player with
little data is pulled to the position mean and only earns an extreme estimate with volume.

Two estimators:
  - Gamma-Poisson EB for the SHOT rate (shots per 90): posterior_rate = (alpha + shots) /
    (beta + nineties). Low exposure -> sits near the prior mean; high exposure -> near raw.
  - Beta-Binomial EB for the ON-TARGET rate (SoT / shots): posterior_p = (a + sot) /
    (a + b + shots).
Then expected SoT per 90 = shot_rate * on_target_rate, and prop probabilities come from a
Poisson tail: P(SoT >= line) over the player's expected minutes.

All functions are pure (numpy/scipy only) and CI-tested. The data plumbing that feeds them
(club seasons for the shot-rate base, WC match stats for on-target) lives in
scripts/build_prop_model.py.

NOTE: we have the prop SIGNAL but not prop PRICES — free odds feeds don't carry player
props. So this produces probabilities, not yet EV/value. Sourcing prop odds is the
remaining blocker before any of this is bettable.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import poisson


def gamma_poisson_eb(shots, nineties) -> tuple[float, float, float]:
    """Empirical-Bayes Gamma prior for a Poisson rate, by method of moments.

    Returns (alpha, beta, prior_mean). Posterior rate for a player is
    (alpha + shots_i) / (beta + nineties_i). beta acts as a pseudo-exposure: bigger beta =
    stronger shrinkage (used when between-player variance is small or noisy).
    """
    s = np.asarray(shots, float)
    e = np.asarray(nineties, float)
    m = e > 0
    s, e = s[m], e[m]
    if len(s) == 0 or s.sum() == 0:
        return 1.0, 1.0, 1.0
    mu = s.sum() / e.sum()                       # exposure-weighted global rate
    r = s / e
    w = e / e.sum()
    var_obs = float(np.sum(w * (r - mu) ** 2))   # weighted variance of observed rates
    within = float(np.sum(w * (mu / e)))         # Poisson sampling component (~mu/E)
    var_lambda = var_obs - within               # between-player (true) variance
    if var_lambda <= 1e-9:                        # no real spread -> shrink hard to mu
        beta = 1e4
        return mu * beta, beta, mu
    beta = mu / var_lambda                        # Gamma: mu=a/b, var=a/b^2
    return mu * beta, beta, mu


def beta_binomial_eb(successes, trials) -> tuple[float, float, float]:
    """Empirical-Bayes Beta prior for a binomial rate (e.g. shots-on-target / shots).

    Returns (a, b, prior_mean). Posterior rate = (a + succ_i) / (a + b + trials_i).
    """
    s = np.asarray(successes, float)
    t = np.asarray(trials, float)
    m = t > 0
    s, t = s[m], t[m]
    if len(s) == 0 or t.sum() == 0:
        return 1.0, 1.0, 0.5
    p = s.sum() / t.sum()
    r = s / t
    w = t / t.sum()
    var_obs = float(np.sum(w * (r - p) ** 2))
    within = float(np.sum(w * (p * (1 - p) / t)))
    var_p = var_obs - within
    if var_p <= 1e-9:
        conc = 1e4
    else:
        conc = p * (1 - p) / var_p - 1            # alpha + beta (concentration)
        conc = max(conc, 1.0)
    return p * conc, (1 - p) * conc, p


def posterior_rate(alpha: float, beta: float, shots: float, nineties: float) -> float:
    """Shrunk Poisson rate for one player given the fitted Gamma prior."""
    return (alpha + shots) / (beta + nineties)


def posterior_p(a: float, b: float, successes: float, trials: float) -> float:
    """Shrunk binomial rate for one player given the fitted Beta prior."""
    return (a + successes) / (a + b + trials)


def sot_per90(shot_rate: float, on_target_rate: float) -> float:
    """Expected shots-on-target per 90 = shot rate * on-target rate."""
    return shot_rate * on_target_rate


def prop_at_least(sot_rate_per90: float, line: int, expected_minutes: float = 90.0,
                  opponent_factor: float = 1.0) -> float:
    """P(player records >= `line` shots on target), Poisson over expected minutes.

    opponent_factor scales the rate for opponent defensive strength (1.0 = average; >1 a
    leaky defence, <1 a stingy one). For a '2+ SoT' prop, line=2.
    """
    lam = sot_rate_per90 * (expected_minutes / 90.0) * opponent_factor
    return float(1.0 - poisson.cdf(line - 1, lam))

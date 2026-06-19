"""Pure-logic tests for the prop shrinkage estimators (CI, no data)."""

from __future__ import annotations

import numpy as np
import pytest

from engine.props import (beta_binomial_eb, gamma_poisson_eb, posterior_p,
                          posterior_rate, prop_at_least, sot_per90)


def _realistic_population(rng):
    """A league of players whose TRUE shot rates genuinely vary (mean ~2/90, real spread)."""
    true_rate = rng.gamma(shape=4.0, scale=0.5, size=80)           # mean 2.0, real variance
    nineties = rng.uniform(15, 38, 80)
    shots = rng.poisson(true_rate * nineties).astype(float)
    return shots, nineties


def test_gamma_poisson_shrinks_low_exposure_toward_prior():
    shots, nineties = _realistic_population(np.random.default_rng(0))
    # add a fluke: 3 shots in half a game (raw 6/90), tiny sample
    shots = np.append(shots, 3.0)
    nineties = np.append(nineties, 0.5)
    a, b, mu = gamma_poisson_eb(shots, nineties)
    raw_fluke = 3.0 / 0.5                                            # 6.0/90, absurd
    shrunk_fluke = posterior_rate(a, b, 3.0, 0.5)
    assert mu == pytest.approx(2.0, abs=0.5)
    assert shrunk_fluke < raw_fluke                                 # pulled down
    assert abs(shrunk_fluke - mu) < abs(raw_fluke - mu)            # toward the prior mean


def test_gamma_poisson_high_exposure_keeps_its_rate():
    rng = np.random.default_rng(1)
    shots, nineties = _realistic_population(rng)
    # a genuine high-volume shooter: ~4/90 over a full 35-game sample barely shrinks
    shots = np.append(shots, float(rng.poisson(4.0 * 35.0)))
    nineties = np.append(nineties, 35.0)
    a, b, mu = gamma_poisson_eb(shots, nineties)
    shrunk = posterior_rate(a, b, shots[-1], 35.0)
    assert shrunk == pytest.approx(4.0, abs=0.7)                    # stays near its real 4/90
    assert shrunk > mu + 1.0                                        # still well above average


def test_beta_binomial_shrinks_small_sample_on_target_rate():
    # a player 1-for-1 on target shouldn't read as 100%
    succ = np.concatenate([np.full(50, 12.0), [1.0]])
    trials = np.concatenate([np.full(50, 36.0), [1.0]])            # ~0.33 league rate
    a, b, p = beta_binomial_eb(succ, trials)
    shrunk = posterior_p(a, b, 1.0, 1.0)
    assert p == pytest.approx(0.333, abs=0.05)
    assert shrunk < 0.9 and shrunk > p                             # pulled well below 1.0


def test_prop_at_least_is_monotonic_and_bounded():
    rate = sot_per90(shot_rate=3.0, on_target_rate=0.4)            # 1.2 SoT/90
    p1 = prop_at_least(rate, 1)
    p2 = prop_at_least(rate, 2)
    p3 = prop_at_least(rate, 3)
    assert 1.0 > p1 > p2 > p3 > 0.0                                # more SoT = less likely
    # fewer expected minutes -> lower probability
    assert prop_at_least(rate, 1, expected_minutes=45) < p1
    # leakier opponent -> higher probability
    assert prop_at_least(rate, 1, opponent_factor=1.3) > p1


def test_empty_inputs_are_safe():
    assert gamma_poisson_eb([], []) == (1.0, 1.0, 1.0)
    assert beta_binomial_eb([], []) == (1.0, 1.0, 0.5)

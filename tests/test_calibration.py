"""Pure-logic tests for RPS + temperature calibration (run in CI, no database)."""

from __future__ import annotations

import numpy as np
import pytest

from engine.calibration import apply_temperature, fit_temperature
from engine.evaluate import log_loss, rps


# ---- RPS ------------------------------------------------------------------
def test_rps_perfect_and_worst():
    assert rps(np.array([[1.0, 0, 0]]), np.array([0])) == pytest.approx(0.0)
    assert rps(np.array([[0, 0, 1.0]]), np.array([0])) == pytest.approx(1.0)


def test_rps_respects_outcome_order():
    """Home actually won. Predicting a DRAW (adjacent) must score better than
    predicting an AWAY win (far) — the whole point of RPS vs log-loss."""
    y = np.array([0])
    adjacent = rps(np.array([[0.0, 1.0, 0.0]]), y)   # predicted draw
    far = rps(np.array([[0.0, 0.0, 1.0]]), y)        # predicted away
    assert adjacent < far


# ---- temperature scaling --------------------------------------------------
def test_temperature_identity_and_sum_to_one():
    p = np.array([[0.6, 0.25, 0.15], [0.2, 0.3, 0.5]])
    out = apply_temperature(p, 1.0)
    assert out == pytest.approx(p, abs=1e-9)
    assert apply_temperature(p, 2.0).sum(axis=1) == pytest.approx([1.0, 1.0])


def test_temperature_preserves_ranking():
    p = np.array([[0.6, 0.25, 0.15]])
    for T in (0.5, 2.0, 3.0):
        assert apply_temperature(p, T).argmax() == p.argmax()


def test_higher_temperature_softens():
    p = np.array([[0.8, 0.15, 0.05]])
    assert apply_temperature(p, 3.0).max() < p.max()       # softer
    assert apply_temperature(p, 0.5).max() > p.max()       # sharper


def test_fit_temperature_reduces_logloss_on_overconfident():
    """Synthetic over-confident predictions → fitted T>1 should cut log-loss."""
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 400)
    p = np.full((400, 3), 0.02)
    p[np.arange(400), y] = 0.96            # 96% on the truth = over-confident-but-right
    # flip 25% to be wrong so it's not perfectly separable
    wrong = rng.choice(400, 100, replace=False)
    for i in wrong:
        p[i] = 0.02; p[i, (y[i] + 1) % 3] = 0.96
    T = fit_temperature(p, y)
    assert T > 1.0
    assert log_loss(apply_temperature(p, T), y) < log_loss(p, y)

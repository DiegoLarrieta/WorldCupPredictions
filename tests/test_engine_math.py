"""Pure-logic engine tests — NO database, so they run in CI on a clean runner.

These guard the math that every prediction depends on: probabilities are valid,
the Dixon-Coles score matrix is a proper distribution, the ensemble blend is the
weighted pool it claims to be, and the Elo->W/D/L map is a valid softmax.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from engine.ensemble import Ensemble
from engine.models.base import PredictiveModel
from engine.models.dixon_coles import outcomes, score_matrix
from engine.models.elo import EloModel

PARAMS = json.loads((Path(__file__).resolve().parents[1] / "engine" / "params.json").read_text())


# ---- Dixon-Coles score distribution ----------------------------------------
@pytest.mark.parametrize("lh,la,rho", [(1.5, 1.2, -0.05), (0.7, 2.3, 0.05), (1.0, 1.0, 0.0)])
def test_score_matrix_is_a_distribution(lh, la, rho):
    m = score_matrix(lh, la, rho)
    assert m.shape == (11, 11)
    assert (m >= 0).all()
    assert m.sum() == pytest.approx(1.0, abs=1e-9)


def test_outcomes_partition_to_one():
    m = score_matrix(1.4, 1.1, -0.05)
    o = outcomes(m)
    assert o["home"] + o["draw"] + o["away"] == pytest.approx(1.0, abs=1e-9)
    for k in ("over25", "under25", "btts", "home", "draw", "away"):
        assert 0.0 <= o[k] <= 1.0
    assert o["over25"] + o["under25"] == pytest.approx(1.0, abs=1e-9)


def test_stronger_attack_raises_win_prob():
    """Sanity: a big attack/defence edge should favour the home side."""
    strong = outcomes(score_matrix(2.2, 0.6, -0.05))
    even = outcomes(score_matrix(1.2, 1.2, -0.05))
    assert strong["home"] > even["home"]


# ---- Ensemble blend --------------------------------------------------------
class _Fixed(PredictiveModel):
    def __init__(self, probs):
        self._p = np.array(probs, dtype=float)

    def fit(self, as_of):
        return self

    def predict_wdl(self, home, away, neutral=True):
        return self._p


def test_ensemble_is_the_weighted_pool():
    dc = _Fixed([0.6, 0.2, 0.2])
    elo = _Fixed([0.3, 0.3, 0.4])
    ens = Ensemble(dc, elo, weight_dc=0.5)
    p = ens.predict_wdl("A", "B")
    assert p == pytest.approx([0.45, 0.25, 0.30])
    assert p.sum() == pytest.approx(1.0)


def test_ensemble_weight_extremes():
    dc, elo = _Fixed([0.6, 0.2, 0.2]), _Fixed([0.3, 0.3, 0.4])
    assert Ensemble(dc, elo, weight_dc=1.0).predict_wdl("A", "B") == pytest.approx([0.6, 0.2, 0.2])
    assert Ensemble(dc, elo, weight_dc=0.0).predict_wdl("A", "B") == pytest.approx([0.3, 0.3, 0.4])


# ---- Elo -> W/D/L mapping (no DB: ratings set directly) --------------------
def test_elo_wdl_is_valid_softmax():
    elo = EloModel()
    elo.ratings = {"Strong": 2000.0, "Weak": 1500.0}
    elo.coef = PARAMS["elo_wdl_coef"]
    elo.intercept = PARAMS["elo_wdl_intercept"]
    p = elo.predict_wdl("Strong", "Weak", neutral=True)
    assert len(p) == 3
    assert (p >= 0).all()
    assert p.sum() == pytest.approx(1.0, abs=1e-9)
    # the much stronger team should be favoured
    assert p[0] > p[2]


def test_elo_neutral_vs_home_advantage():
    elo = EloModel()
    elo.ratings = {"A": 1700.0, "B": 1700.0}
    elo.coef = PARAMS["elo_wdl_coef"]
    elo.intercept = PARAMS["elo_wdl_intercept"]
    neutral = elo.predict_wdl("A", "B", neutral=True)
    at_home = elo.predict_wdl("A", "B", neutral=False)
    # equal teams: home advantage should not reduce the home win prob
    assert at_home[0] >= neutral[0] - 1e-9

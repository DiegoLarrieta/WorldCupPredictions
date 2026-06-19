"""CI-safe test for Dixon-Coles fit_frame (the refactor the club backtest reuses).

No DuckDB: builds a tiny synthetic league where one team is clearly strong, and checks
the fit recovers that ordering and yields valid probabilities.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from engine.models.dixon_coles import fit_frame, lambdas, outcomes, score_matrix


def _synthetic_league() -> pd.DataFrame:
    # A > B > C > D in strength; play a few round-robins with scorelines that reflect it
    rng = np.random.default_rng(0)
    strength = {"A": 2.2, "B": 1.5, "C": 1.1, "D": 0.7}
    rows = []
    base = pd.Timestamp("2024-01-01")
    n = 0
    for rep in range(8):
        for h in strength:
            for a in strength:
                if h == a:
                    continue
                hg = rng.poisson(strength[h])
                ag = rng.poisson(strength[a])
                rows.append({"date": base + pd.Timedelta(days=n), "home_team": h,
                             "away_team": a, "hg": hg, "ag": ag, "neutral": False})
                n += 1
    return pd.DataFrame(rows)


def test_fit_frame_recovers_strength_order_and_valid_probs():
    df = _synthetic_league()
    m = fit_frame(df, "2024-12-31", min_matches=6)
    assert m["converged"]
    assert set(m["attack"]) == {"A", "B", "C", "D"}
    # strongest attack should be A, weakest D
    assert m["attack"]["A"] == max(m["attack"].values())
    assert m["attack"]["D"] == min(m["attack"].values())
    # a valid probability distribution for A (home) vs D
    lh, la = lambdas(m, "A", "D", neutral=False)
    o = outcomes(score_matrix(lh, la, m["rho"]))
    assert abs(o["home"] + o["draw"] + o["away"] - 1.0) < 1e-6
    assert o["home"] > o["away"]            # strong home team favoured


def test_fit_frame_min_matches_filters_thin_teams():
    df = _synthetic_league()
    # add a team with only 2 games -> dropped by min_matches=6
    extra = pd.DataFrame([
        {"date": pd.Timestamp("2024-06-01"), "home_team": "Z", "away_team": "A",
         "hg": 0, "ag": 5, "neutral": False},
        {"date": pd.Timestamp("2024-06-02"), "home_team": "B", "away_team": "Z",
         "hg": 4, "ag": 0, "neutral": False}])
    m = fit_frame(pd.concat([df, extra], ignore_index=True), "2024-12-31", min_matches=6)
    assert "Z" not in m["attack"]

"""Elo model: chronological replay → current ratings, then a trained Elo→W/D/L map.

Reuses the SAME Elo update math the data pipeline used to build `team_ratings`
(src/phase0/ingest.py), so engine ratings are identical to the warehouse. The
gap→W/D/L mapping (which also learns the draw rate) is trained offline and stored
in engine/params.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from engine.data import DB_PATH, load_internationals
from engine.models.base import PredictiveModel

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "phase0"))
from ingest import ELO_BASE, ELO_HOME_ADVANTAGE, _expected, _k_factor  # noqa: E402

PARAMS = json.loads((Path(__file__).resolve().parents[1] / "params.json").read_text())


def replay_ratings(as_of: str) -> dict[str, float]:
    """Pre-`as_of` Elo ratings from a chronological replay (leakage-safe)."""
    df = load_internationals(as_of, since="1872-01-01")
    ratings: dict[str, float] = {}
    for r in df.itertuples(index=False):
        rh = ratings.get(r.home_team, ELO_BASE)
        ra = ratings.get(r.away_team, ELO_BASE)
        gd = r.hg - r.ag
        score = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)
        exp = _expected(rh, ra, bool(r.neutral))
        k = _k_factor(r.tournament, gd)
        ratings[r.home_team] = rh + k * (score - exp)
        ratings[r.away_team] = ra + k * ((1 - score) - (1 - exp))
    return ratings


class EloModel(PredictiveModel):
    name = "elo"

    def fit(self, as_of: str) -> "EloModel":
        self.ratings = replay_ratings(as_of)
        self.coef = PARAMS["elo_wdl_coef"]
        self.intercept = PARAMS["elo_wdl_intercept"]
        return self

    def can_rate(self, team: str) -> bool:
        return team in self.ratings

    def rating(self, team: str) -> float:
        return self.ratings.get(team, ELO_BASE)

    def predict_wdl(self, home, away, neutral=True) -> np.ndarray:
        gap = (self.rating(home) - self.rating(away)
               + (0 if neutral else ELO_HOME_ADVANTAGE)) / 100.0
        z = np.array([c[0] * gap + b for c, b in zip(self.coef, self.intercept)])
        z -= z.max()
        return np.exp(z) / np.exp(z).sum()

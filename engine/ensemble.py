"""Ensemble: blend models' W/D/L probabilities with a validated weight.

The weight was fitted on 2,195 held-out internationals and beats both single models
(95% CI [+0.0017,+0.0121]); it lives in engine/params.json. Training/refitting the
weight is an offline step (see predictions/ensemble/build_ensemble.py) — prediction
just loads it, so every match uses the identical validated blend.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from engine.models.base import PredictiveModel

PARAMS = json.loads((Path(__file__).resolve().parent / "params.json").read_text())


class Ensemble(PredictiveModel):
    """Linear pool: w * dixon_coles + (1-w) * elo (order matters: [DC, Elo])."""

    name = "ensemble"

    def __init__(self, dixon_coles, elo, weight_dc: float | None = None):
        self.dc = dixon_coles
        self.elo = elo
        self.w = PARAMS["weight_dc"] if weight_dc is None else weight_dc

    def fit(self, as_of: str) -> "Ensemble":
        self.dc.fit(as_of)
        self.elo.fit(as_of)
        return self

    def can_rate(self, team: str) -> bool:
        return self.dc.can_rate(team) and self.elo.can_rate(team)

    def predict_wdl(self, home, away, neutral=True) -> np.ndarray:
        p_dc = self.dc.predict_wdl(home, away, neutral)
        p_elo = self.elo.predict_wdl(home, away, neutral)
        return self.w * p_dc + (1 - self.w) * p_elo

    def components(self, home, away, neutral=True) -> dict[str, np.ndarray]:
        return {"dixon_coles": self.dc.predict_wdl(home, away, neutral),
                "elo": self.elo.predict_wdl(home, away, neutral),
                "ensemble": self.predict_wdl(home, away, neutral)}

"""The model interface. Every predictive model implements this, so the ensemble,
calibration, and evaluation code is model-agnostic and we can swap in new models
(e.g. a Bayesian dynamic model) without touching anything else.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class PredictiveModel(ABC):
    """A model that, once fit on data before `as_of`, gives W/D/L probabilities."""

    name: str = "base"

    @abstractmethod
    def fit(self, as_of: str) -> "PredictiveModel":
        """Fit on internationals strictly before `as_of` (no leakage). Returns self."""

    @abstractmethod
    def predict_wdl(self, home: str, away: str, neutral: bool = True) -> np.ndarray:
        """Return probabilities [P(home win), P(draw), P(away win)] (sums to 1)."""

    def can_rate(self, team: str) -> bool:
        """Whether the model has enough data to rate this team."""
        return True

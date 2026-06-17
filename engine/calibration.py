"""Probability calibration via temperature scaling.

A model can rank matches well yet be over/under-confident (we measured Elo's tail
over-confidence). Temperature scaling fixes that with ONE parameter T fitted on
held-out data: p_cal ∝ p^(1/T). T>1 softens (less confident), T<1 sharpens. It never
changes which outcome is most likely — only how confident the probabilities are —
which is exactly what you want for honest betting numbers.

The fitted T lives in engine/params.json (key "temperature"); predict.py applies it.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar


def apply_temperature(probs: np.ndarray, T: float) -> np.ndarray:
    """Rescale probabilities by temperature T (keeps rows summing to 1)."""
    logp = np.log(np.clip(np.asarray(probs, dtype=float), 1e-12, 1)) / T
    logp -= logp.max(axis=-1, keepdims=True)
    e = np.exp(logp)
    return e / e.sum(axis=-1, keepdims=True)


def fit_temperature(probs: np.ndarray, y: np.ndarray) -> float:
    """Find T>0 minimising held-out log-loss."""
    from engine.evaluate import log_loss
    y = np.asarray(y)
    res = minimize_scalar(lambda T: log_loss(apply_temperature(probs, T), y),
                          bounds=(0.3, 5.0), method="bounded")
    return float(res.x)

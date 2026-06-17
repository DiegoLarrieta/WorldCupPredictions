"""Evaluation metrics for W/D/L predictions.

RPS (Ranked Probability Score) is the proper scoring rule for football because the
three outcomes are ORDERED (home win > draw > away win): predicting a draw when it
was an away win is "less wrong" than predicting a home win. Log-loss ignores that
order; RPS respects it. We track both, plus a reliability table for calibration.

Probabilities are arrays shaped (n, 3) in order [home, draw, away]; y in {0,1,2}.
"""

from __future__ import annotations

import numpy as np


def rps(probs: np.ndarray, y: np.ndarray) -> float:
    """Mean Ranked Probability Score (lower is better). K=3 outcomes."""
    probs = np.asarray(probs, dtype=float)
    onehot = np.eye(3)[np.asarray(y)]
    cum_p = np.cumsum(probs, axis=1)[:, :-1]      # first K-1 cumulatives
    cum_o = np.cumsum(onehot, axis=1)[:, :-1]
    return float(np.mean(np.sum((cum_p - cum_o) ** 2, axis=1) / (3 - 1)))


def log_loss(probs: np.ndarray, y: np.ndarray) -> float:
    probs = np.clip(np.asarray(probs, dtype=float), 1e-12, 1)
    return float(np.mean([-np.log(probs[i, y[i]]) for i in range(len(y))]))


def reliability(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> list[dict]:
    """Calibration of the predicted favourite: in each confidence bin, predicted
    probability vs how often that favourite actually won. Well-calibrated = equal.
    """
    probs = np.asarray(probs, dtype=float)
    fav = probs.argmax(axis=1)
    conf = probs.max(axis=1)
    hit = (fav == np.asarray(y)).astype(float)
    edges = np.linspace(probs.max() and 1 / 3 or 0, 1.0, bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf >= lo) & (conf < hi) if hi < 1.0 else (conf >= lo) & (conf <= hi)
        if m.sum():
            out.append({"bin": f"{lo:.2f}-{hi:.2f}", "n": int(m.sum()),
                        "predicted": round(float(conf[m].mean()), 3),
                        "actual": round(float(hit[m].mean()), 3)})
    return out

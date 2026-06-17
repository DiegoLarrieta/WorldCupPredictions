"""Fit temperature calibration for the ensemble and measure it honestly.

Reuses build_ensemble's leakage-free collection (held-out internationals with DC + Elo
probabilities), forms the ensemble, then 5-fold CV: fit temperature T on train folds,
evaluate calibrated vs uncalibrated on held-out folds. Reports RPS + log-loss + a
reliability table before/after, and writes the final T (fit on all data) into
engine/params.json so predict.py applies it.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.model_selection import KFold

import build_ensemble as B   # same folder
from engine.calibration import apply_temperature, fit_temperature
from engine.evaluate import log_loss, reliability, rps

ROOT = Path(__file__).resolve().parents[2]
PARAMS_PATH = ROOT / "engine" / "params.json"


def main():
    params = json.loads(PARAMS_PATH.read_text())
    w = params["weight_dc"]

    print("Collecting held-out ensemble predictions ...")
    e = B.replay_elo()
    data = B.collect(e, B.fit_elo_wdl(e))
    dc = np.array([d[0] for d in data])
    el = np.array([d[1] for d in data])
    y = np.array([d[2] for d in data])
    ens = w * dc + (1 - w) * el
    n = len(y)
    print(f"  {n} held-out matches")

    # CV: fit T on train folds, calibrate held-out
    kf = KFold(5, shuffle=True, random_state=0)
    cal = np.zeros_like(ens)
    Ts = []
    for tr, te in kf.split(np.arange(n)):
        T = fit_temperature(ens[tr], y[tr])
        Ts.append(T)
        cal[te] = apply_temperature(ens[te], T)

    print("\n=== before vs after calibration (held-out) ===")
    print(f"  {'metric':<12}{'uncalibrated':>14}{'calibrated':>14}")
    print(f"  {'RPS':<12}{rps(ens, y):>14.4f}{rps(cal, y):>14.4f}")
    print(f"  {'log-loss':<12}{log_loss(ens, y):>14.4f}{log_loss(cal, y):>14.4f}")
    print(f"  fitted T per fold: {[round(t, 2) for t in Ts]}")

    T_full = fit_temperature(ens, y)
    print(f"\n  final temperature (all data): {T_full:.3f}  "
          f"({'softening — was over-confident' if T_full > 1.02 else 'sharpening' if T_full < 0.98 else 'already calibrated'})")

    print("\n  reliability (favourite confidence vs actual win rate):")
    print("    UNCALIBRATED:", reliability(ens, y, bins=5))
    print("    CALIBRATED:  ", reliability(cal, y, bins=5))

    params["temperature"] = T_full
    params["calibration"] = {"n": n, "rps_before": rps(ens, y), "rps_after": rps(cal, y),
                             "logloss_before": log_loss(ens, y), "logloss_after": log_loss(cal, y)}
    PARAMS_PATH.write_text(json.dumps(params, indent=2))
    print(f"\n  saved temperature to {PARAMS_PATH}")


if __name__ == "__main__":
    main()

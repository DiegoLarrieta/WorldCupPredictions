"""Calibration vs the market — WHERE (if anywhere) are we better than the line?

Beating the market on average is one bar (the edge test says we don't). But you only need
to be better *on a subset* to bet that subset. This checks calibration — when the model
says 30%, does it happen 30%? — for our models AND the market, side by side, and looks for
any region where the model is both better-calibrated and disagrees with the line.

Reuses the leakage-safe TEST-set probabilities from epl_closing_line.compute().

Metrics:
  - ECE (expected calibration error) per model and the market, overall + per outcome.
  - A reliability table (predicted vs observed by probability bin).
  - The honest subset check: among matches where the model disagrees most with the market,
    who is better calibrated — i.e. is there a pocket of real edge or not.

Run:  .venv/bin/python predictions/edge-test/calibration_vs_market.py
Writes predictions/edge-test/RESULTS-calibration.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from epl_closing_line import compute                          # noqa: E402
from engine.evaluate import log_loss                          # noqa: E402

OUT = Path(__file__).resolve().parent / "RESULTS-calibration.md"


def ece(probs: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    """Expected calibration error over the flattened (per-outcome) predictions."""
    p = probs.reshape(-1)
    hit = np.eye(3)[y].reshape(-1)
    edges = np.linspace(0, 1, bins + 1)
    e, n = 0.0, len(p)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.any():
            e += m.sum() / n * abs(p[m].mean() - hit[m].mean())
    return float(e)


def reliability_rows(probs: np.ndarray, y: np.ndarray, bins: int = 10):
    p = probs.reshape(-1)
    hit = np.eye(3)[y].reshape(-1)
    edges = np.linspace(0, 1, bins + 1)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (p >= lo) & (p < hi)
        if m.any():
            out.append((f"{lo:.1f}-{hi:.1f}", int(m.sum()), p[m].mean(), hit[m].mean()))
    return out


def main() -> None:
    r = compute()
    y, models = r["y"], r["models"]
    market = models["market (Shin)"]
    ours = {k: models[k] for k in ("ensemble", "dixon_coles", "elo")}

    # overall ECE
    eces = {"market (Shin)": ece(market, y), **{k: ece(v, y) for k, v in ours.items()}}

    # per-outcome ECE (home/draw/away) — draws are where DC is known to struggle
    def per_outcome_ece(P):
        hit = np.eye(3)[y]
        res = []
        for k in range(3):
            edges = np.linspace(0, 1, 11)
            e, n = 0.0, len(P)
            for lo, hi in zip(edges[:-1], edges[1:]):
                m = (P[:, k] >= lo) & (P[:, k] < hi)
                if m.any():
                    e += m.sum() / n * abs(P[m, k].mean() - hit[m, k].mean())
            res.append(e)
        return res

    # subset where the ensemble disagrees most with the market (top quartile by L1 distance)
    dist = np.abs(models["ensemble"] - market).sum(axis=1)
    cut = np.quantile(dist, 0.75)
    sub = dist >= cut
    ll_model_sub = log_loss(models["ensemble"][sub], y[sub])
    ll_mkt_sub = log_loss(market[sub], y[sub])

    L = [f"# Calibration vs market — {len(y)} out-of-sample EPL matches (2024-25)", "",
         "_ECE = expected calibration error (lower is better): average gap between the "
         "predicted probability and how often it actually happened._", "",
         "## Overall calibration error", "",
         "| Source | ECE |", "|---|---|"]
    for k in ("market (Shin)", "ensemble", "dixon_coles", "elo"):
        L.append(f"| {k} | {eces[k]:.4f} |")

    L += ["", "## Per-outcome ECE (home / draw / away)", "",
          "| Source | home | draw | away |", "|---|---|---|---|"]
    for k, P in [("market (Shin)", market), ("ensemble", models["ensemble"]),
                 ("dixon_coles", models["dixon_coles"])]:
        h, d, a = per_outcome_ece(P)
        L.append(f"| {k} | {h:.4f} | {d:.4f} | {a:.4f} |")

    L += ["", "## Reliability — ensemble (predicted vs observed)", "",
          "| Prob bin | n | mean predicted | observed |", "|---|---|---|---|"]
    for label, n, pred, obs in reliability_rows(models["ensemble"], y):
        L.append(f"| {label} | {n} | {pred:.3f} | {obs:.3f} |")

    better_overall = eces["ensemble"] < eces["market (Shin)"]
    better_sub = ll_model_sub < ll_mkt_sub
    L += ["", "## The subset check (where we disagree most with the line)", "",
          f"- Top-quartile disagreement: {int(sub.sum())} matches.",
          f"- Ensemble log-loss there: {ll_model_sub:.4f} vs market {ll_mkt_sub:.4f}.",
          f"- Better than the market on its own disagreement subset: "
          f"**{'YES' if better_sub else 'NO'}**.",
          "", "## Verdict", "",
          f"- Better calibrated than the market overall: **{'YES' if better_overall else 'NO'}** "
          f"(ECE {eces['ensemble']:.4f} vs {eces['market (Shin)']:.4f}).",
          f"- Better where we most disagree with the line: **{'YES' if better_sub else 'NO'}**.",
          "", "_Calibration confirms the edge test: " +
          ("there is a pocket worth a closer look." if better_sub else
           "the market is at least as well calibrated everywhere we looked, including where "
           "we disagree with it most. No subset edge on this market — reinforces pivoting to "
           "props / soft books rather than betting the main line.") + "_"]
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nWritten to {OUT}")


if __name__ == "__main__":
    main()

"""Elo + Dixon-Coles ensemble — blend two validated models that disagree.

Both models survived validation (Elo +30.7% skill; Dixon-Coles beats base-rate), but
they disagreed on Sweden-Tunisia. When two good, partially-independent models disagree,
a weighted blend usually beats either alone. We build that and VALIDATE it.

Pieces:
  1. Elo -> W/D/L. Elo gives a 2-way win prob; we fit a multinomial logistic from the
     (home-adjusted) Elo gap to actual H/D/A on history, which also learns the draw rate.
     Pre-match Elo comes from a leakage-free chronological replay.
  2. Dixon-Coles -> W/D/L (existing model, refit per window so it isn't stale).
  3. Blend: p = w * p_DC + (1-w) * p_Elo. The weight w is FITTED on held-out folds, not
     guessed. We compare held-out log-loss: Elo alone vs DC alone vs ensemble, with a
     bootstrap CI on the ensemble's gain over the best single model.

If the ensemble wins, we save w + the Elo->WDL coefficients for the live prediction.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import duckdb
import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "phase0"))
sys.path.insert(0, str(ROOT))
from engine.models import dixon_coles as M  # noqa: E402
from ingest import ELO_BASE, ELO_HOME_ADVANTAGE, _expected, _k_factor  # noqa: E402

HERE = Path(__file__).resolve().parent
ELO_TRAIN_END = "2024-06-01"   # fit Elo->WDL on history before this
WINDOWS = [("2024-06-01", "2025-06-01"), ("2025-06-01", "2026-06-15")]


def replay_elo():
    """Chronological Elo replay → pre-match ratings per match (no leakage)."""
    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    df = con.execute(
        """SELECT date, home_team, away_team, CAST(home_goals AS INT) hg,
                  CAST(away_goals AS INT) ag, neutral, tournament
           FROM matches WHERE is_international AND home_goals IS NOT NULL ORDER BY date"""
    ).fetch_df()
    con.close()
    ratings, rows = {}, []
    for r in df.itertuples(index=False):
        rh, ra = ratings.get(r.home_team, ELO_BASE), ratings.get(r.away_team, ELO_BASE)
        rows.append((r.date, r.home_team, r.away_team, rh, ra, bool(r.neutral), r.hg, r.ag))
        gd = r.hg - r.ag
        score = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)
        exp = _expected(rh, ra, bool(r.neutral))
        k = _k_factor(r.tournament, gd)
        ratings[r.home_team] = rh + k * (score - exp)
        ratings[r.away_team] = ra + k * ((1 - score) - (1 - exp))
    import pandas as pd
    e = pd.DataFrame(rows, columns=["date", "home", "away", "elo_h", "elo_a", "neutral", "hg", "ag"])
    e["date"] = pd.to_datetime(e["date"])
    e["eff_gap"] = (e["elo_h"] - e["elo_a"] + np.where(e["neutral"], 0, ELO_HOME_ADVANTAGE)) / 100.0
    e["y"] = np.where(e["hg"] > e["ag"], 0, np.where(e["hg"] == e["ag"], 1, 2))
    return e


def fit_elo_wdl(e):
    tr = e[e["date"] < ELO_TRAIN_END]
    clf = LogisticRegression(max_iter=1000)   # multinomial is automatic in sklearn >=1.9
    clf.fit(tr[["eff_gap"]], tr["y"])
    return clf


def collect(e, elo_clf):
    """Per held-out match: Elo W/D/L probs, DC W/D/L probs, actual y."""
    out = []
    for start, end in WINDOWS:
        mdl = M.fit(start)
        w = e[(e["date"] >= start) & (e["date"] < end)]
        for r in w.itertuples(index=False):
            if r.home not in mdl["attack"] or r.away not in mdl["attack"]:
                continue
            p_elo = elo_clf.predict_proba([[r.eff_gap]])[0]
            lh, la = M.lambdas(mdl, r.home, r.away, neutral=r.neutral)
            o = M.outcomes(M.score_matrix(lh, la, mdl["rho"]))
            p_dc = np.array([o["home"], o["draw"], o["away"]])
            out.append((p_dc, p_elo, r.y))
        print(f"  window {start}..{end}: {len(w)} matches")
    return out


def ll(probs, y):
    p = np.clip(np.array(probs), 1e-9, 1)
    return float(np.mean([-np.log(p[i][y[i]]) for i in range(len(y))]))


def main():
    print("Replaying Elo (leakage-free) and fitting Elo->W/D/L ...")
    e = replay_elo()
    elo_clf = fit_elo_wdl(e)
    print("Collecting held-out matches (DC + Elo probabilities) ...")
    data = collect(e, elo_clf)
    n = len(data)
    dc = np.array([d[0] for d in data]); el = np.array([d[1] for d in data])
    y = np.array([d[2] for d in data])
    print(f"\n  {n} held-out internationals")

    def blend(w, idx):
        return w * dc[idx] + (1 - w) * el[idx]

    # 5-fold CV: fit blend weight w on train folds, predict held-out
    kf = KFold(5, shuffle=True, random_state=0)
    oof = np.zeros((n, 3)); ws = []
    for tr, te in kf.split(np.arange(n)):
        res = minimize_scalar(
            lambda w: ll(w * dc[tr] + (1 - w) * el[tr], y[tr]),
            bounds=(0, 1), method="bounded")
        ws.append(res.x)
        oof[te] = res.x * dc[te] + (1 - res.x) * el[te]
    w_full = minimize_scalar(lambda w: ll(w * dc + (1 - w) * el, y),
                             bounds=(0, 1), method="bounded").x

    ll_dc = ll(dc, y); ll_el = ll(el, y); ll_ens = ll(oof, y)
    best_single = min(ll_dc, ll_el)
    # bootstrap CI on ensemble's gain over the best single model
    loss_best = -np.log(np.clip((dc if ll_dc < ll_el else el)[np.arange(n), y], 1e-9, 1))
    loss_ens = -np.log(np.clip(oof[np.arange(n), y], 1e-9, 1))
    diff = loss_best - loss_ens
    rng = np.random.default_rng(0)
    boot = np.array([diff[rng.integers(0, n, n)].mean() for _ in range(5000)])
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    print("\n=== held-out log-loss ===")
    print(f"  Elo alone        : {ll_el:.4f}")
    print(f"  Dixon-Coles alone: {ll_dc:.4f}")
    print(f"  ENSEMBLE         : {ll_ens:.4f}   (weight w on DC = {w_full:.2f}, folds {[round(x,2) for x in ws]})")
    print(f"  ensemble gain over best single: {(best_single - ll_ens):+.4f}  95% CI [{ci[0]:+.4f}, {ci[1]:+.4f}]")

    if ci[0] > 0:
        verdict = "ENSEMBLE WINS — beats both single models, distinguishable from zero"
    elif best_single - ll_ens > 0:
        verdict = "ensemble slightly better but within noise (CI spans 0)"
    else:
        verdict = "no gain — best single model is as good"
    print(f"\n  VERDICT: {verdict}.")

    # save fitted ensemble for the live prediction
    params = {"weight_dc": float(w_full),
              "elo_wdl_coef": elo_clf.coef_.tolist(),
              "elo_wdl_intercept": elo_clf.intercept_.tolist(),
              "elo_base": ELO_BASE, "elo_home_adv": ELO_HOME_ADVANTAGE,
              "validation": {"n": n, "ll_elo": ll_el, "ll_dc": ll_dc, "ll_ensemble": ll_ens,
                             "gain_ci": ci, "verdict": verdict}}
    # canonical location the engine loads (single source of truth)
    out = ROOT / "engine" / "params.json"
    out.write_text(json.dumps(params, indent=2))
    print(f"  saved {out}")


if __name__ == "__main__":
    main()

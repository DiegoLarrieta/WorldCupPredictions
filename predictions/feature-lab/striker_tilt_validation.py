"""Validate the striker/attack tilt by ablation — does boosting the team with the
sharper attackers actually improve out-of-sample prediction, or is it a heuristic?

Faithful to the real tilt: we take Dixon-Coles' expected goals and multiply them by
(1 ± factor), where factor = beta * (attack_index_home - attack_index_away). The
attack index mirrors the prediction's signal: the mean goal-threat per 90 of a squad's
TOP-3 attackers (np_xG/90 where we have xG, else goals/90).

Test (leakage-aware):
  - Fit Dixon-Coles on internationals BEFORE the cutoff.
  - Test matches: internationals AFTER the cutoff, between teams we have an attack index
    for (the 48 WC squads).
  - 5-fold CV: fit beta on train folds, evaluate held-out. Compare held-out log-loss of
    DC-with-tilt (fitted beta) vs DC-alone (beta=0). The tilt is justified iff it lowers
    held-out log-loss; beta is the coefficient that replaces the hand-tuned 0.5/±20%.

Caveat: uses CURRENT squads as each nation's pool (no historical squads) → directional.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import numpy as np
from scipy.optimize import minimize_scalar
from sklearn.model_selection import KFold

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.models import dixon_coles as M  # noqa: E402

CUTOFF = "2025-06-01"      # fit DC before this; test after
TILT_CAP = 0.30           # same shape as the live tilt, slightly looser for fitting


def attack_index(con) -> dict:
    """Mean top-3 attacker goal-threat per 90 per country (np_xG/90, else goals/90)."""
    rows = con.execute(
        """
        WITH threat AS (
            SELECT country,
                   COALESCE(np_xg_per90, 90.0 * club_goals / NULLIF(minutes_played, 0)) AS t
            FROM wc_squad_form WHERE minutes_played >= 500
        ), ranked AS (
            SELECT country, t, ROW_NUMBER() OVER (PARTITION BY country ORDER BY t DESC) rn
            FROM threat WHERE t IS NOT NULL
        )
        SELECT country, AVG(t) FROM ranked WHERE rn <= 3 GROUP BY country
        """
    ).fetchall()
    return {c: float(v) for c, v in rows}


def test_matches(con, idx):
    teams = tuple(idx)
    rows = con.execute(
        f"""SELECT home_team, away_team, CAST(home_goals AS INT) hg, CAST(away_goals AS INT) ag, neutral
            FROM matches WHERE is_international AND home_goals IS NOT NULL
            AND date >= DATE '{CUTOFF}' AND date < DATE '2026-06-15'
            AND home_team IN {teams} AND away_team IN {teams}"""
    ).fetchall()
    return rows


def main():
    print(f"Fitting Dixon-Coles before {CUTOFF} ...")
    mdl = M.fit(CUTOFF)
    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    idx = attack_index(con)
    rows = test_matches(con, idx)
    con.close()

    # precompute DC base lambdas + attack gap + outcome for each test match
    data = []
    for home, away, hg, ag, neutral in rows:
        if home not in mdl["attack"] or away not in mdl["attack"]:
            continue
        lh, la = M.lambdas(mdl, home, away, neutral=bool(neutral))
        adiff = idx[home] - idx[away]
        y = 0 if hg > ag else (1 if hg == ag else 2)
        data.append((lh, la, adiff, y))
    n = len(data)
    print(f"  {n} held-out internationals between squad-form teams")
    if n < 40:
        print("  ! small sample — directional only")

    lh = np.array([d[0] for d in data]); la = np.array([d[1] for d in data])
    adiff = np.array([d[2] for d in data]); y = np.array([d[3] for d in data])
    rho = mdl["rho"]

    def probs(beta, i):
        f = np.clip(beta * adiff[i], -TILT_CAP, TILT_CAP)
        m = M.score_matrix(lh[i] * (1 + f), la[i] * (1 - f), rho, max_goals=8)
        o = M.outcomes(m)
        return np.clip([o["home"], o["draw"], o["away"]], 1e-9, 1)

    def nll(beta, idxs):
        return float(np.mean([-np.log(probs(beta, i)[y[i]]) for i in idxs]))

    # 5-fold CV: fit beta on train folds, score held-out at beta=0 (DC) and beta=fit (tilt)
    kf = KFold(n_splits=5, shuffle=True, random_state=0)
    ll_dc, ll_tilt, betas = [], [], []
    for tr, te in kf.split(np.arange(n)):
        res = minimize_scalar(lambda b: nll(b, tr), bounds=(-5, 5), method="bounded")
        b = res.x
        betas.append(b)
        ll_dc.extend([-np.log(probs(0.0, i)[y[i]]) for i in te])
        ll_tilt.extend([-np.log(probs(b, i)[y[i]]) for i in te])
    ll_dc, ll_tilt = float(np.mean(ll_dc)), float(np.mean(ll_tilt))
    beta_full = minimize_scalar(lambda b: nll(b, range(n)), bounds=(-5, 5), method="bounded").x

    print("\n=== ABLATION (5-fold CV, held-out) ===")
    print(f"  Dixon-Coles alone     log-loss: {ll_dc:.4f}")
    print(f"  Dixon-Coles + tilt    log-loss: {ll_tilt:.4f}")
    print(f"  improvement from tilt          : {ll_dc - ll_tilt:+.4f}")
    print(f"  fitted beta (per CV fold)      : {[round(b,2) for b in betas]}")
    print(f"  fitted beta (all data)         : {beta_full:.2f}   (hand-tuned was 0.50)")

    helps = ll_dc - ll_tilt
    verdict = ("JUSTIFIED — improves held-out prediction" if helps > 0.002 else
               "NOT justified — no measurable help" if helps > -0.002 else
               "HARMFUL — hurts held-out prediction")
    print(f"\n  VERDICT: the striker tilt is {verdict}.")
    _write(n, ll_dc, ll_tilt, beta_full, betas, verdict)
    print(f"  wrote {Path(__file__).with_name('striker_tilt_verdict.md')}")


def _write(n, ll_dc, ll_tilt, beta_full, betas, verdict):
    L = [
        "# Does the striker tilt actually help? (ablation)", "",
        f"_Dixon-Coles fit before {CUTOFF}; tested on {n} later internationals between "
        f"squad-form teams. 5-fold CV, leakage-aware. Current-squad proxy → directional._", "",
        "## Result", "",
        f"| Model | held-out log-loss |", "|---|---|",
        f"| Dixon-Coles alone | {ll_dc:.4f} |",
        f"| Dixon-Coles + striker tilt | {ll_tilt:.4f} |",
        f"| **Improvement** | **{ll_dc - ll_tilt:+.4f}** |", "",
        f"- Fitted tilt coefficient (beta): **{beta_full:.2f}** (the hand-tuned value was 0.50).",
        f"- Per-fold betas: {[round(b,2) for b in betas]}", "",
        f"## Verdict", "",
        f"The striker tilt is **{verdict}**.", "",
        "_If justified, we adopt the fitted beta and trust the Sweden lean. If not, the "
        "+19% that drove the prediction was overrated and should be cut or shrunk._",
    ]
    Path(__file__).with_name("striker_tilt_verdict.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()

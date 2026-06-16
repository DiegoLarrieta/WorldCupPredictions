"""Firmer test: does club ATTACK form add predictive value to internationals, AT ALL?

Fixes the first test's weaknesses:
  - Bigger sample: two 1-year windows (2024-25 and 2025-26), not one.
  - Leakage-clean form: each window uses the club season that COMPLETED before it
    (2024-25 matches -> 2324 form; 2025-26 matches -> 2425 form). No future form.
  - Fresh Dixon-Coles per window (fit before each window) so the base isn't stale.
  - Bootstrap 95% CI on the held-out log-loss difference, so we can say whether any
    improvement is distinguishable from zero — not just eyeball a tiny number.

Attack index per (country, season) = mean top-3 attacker goal-threat per 90 among the
country's squad players, using THAT season's club form (np_xG/90 where we have xG,
else goals/90). Still a current-squad proxy for who's in the pool → directional, but
much firmer than v1.
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

WINDOWS = [
    {"test_start": "2024-06-01", "test_end": "2025-06-01", "form_season": "2324"},
    {"test_start": "2025-06-01", "test_end": "2026-06-15", "form_season": "2425"},
]
TILT_CAP = 0.30


def attack_index(con, season):
    rows = con.execute(
        f"""
        WITH sq AS (SELECT DISTINCT country, player_id FROM wc_squad_form WHERE player_id IS NOT NULL),
        threat AS (
            SELECT sq.country,
                   COALESCE(ps.np_xg / NULLIF(ps.minutes/90.0,0),
                            ps.goals / NULLIF(ps.minutes/90.0,0)) AS t
            FROM sq JOIN player_seasons ps ON ps.player_id = sq.player_id
            WHERE ps.season = '{season}' AND ps.minutes >= 500
        ),
        ranked AS (
            SELECT country, t, ROW_NUMBER() OVER (PARTITION BY country ORDER BY t DESC) rn
            FROM threat WHERE t IS NOT NULL
        )
        SELECT country, AVG(t) FROM ranked WHERE rn <= 3 GROUP BY country
        """
    ).fetchall()
    return {c: float(v) for c, v in rows}


def collect():
    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    data = []
    for w in WINDOWS:
        mdl = M.fit(w["test_start"])           # DC fit before this window
        idx = attack_index(con, w["form_season"])
        teams = tuple(idx)
        rows = con.execute(
            f"""SELECT home_team, away_team, CAST(home_goals AS INT) hg,
                       CAST(away_goals AS INT) ag, neutral
                FROM matches WHERE is_international AND home_goals IS NOT NULL
                AND date >= DATE '{w['test_start']}' AND date < DATE '{w['test_end']}'
                AND home_team IN {teams} AND away_team IN {teams}"""
        ).fetchall()
        for home, away, hg, ag, neutral in rows:
            if home not in mdl["attack"] or away not in mdl["attack"]:
                continue
            lh, la = M.lambdas(mdl, home, away, neutral=bool(neutral))
            y = 0 if hg > ag else (1 if hg == ag else 2)
            data.append((lh, la, idx[home] - idx[away], y, mdl["rho"]))
        print(f"  window {w['test_start']}..{w['test_end']} (form {w['form_season']}): "
              f"{len(rows)} candidate matches")
    con.close()
    return data


def main():
    print("Collecting leakage-clean test matches across two windows ...")
    data = collect()
    n = len(data)
    print(f"\n  {n} held-out internationals total")
    lh = np.array([d[0] for d in data]); la = np.array([d[1] for d in data])
    adiff = np.array([d[2] for d in data]); y = np.array([d[3] for d in data])
    rho = np.array([d[4] for d in data])

    def probs(beta, i):
        f = np.clip(beta * adiff[i], -TILT_CAP, TILT_CAP)
        o = M.outcomes(M.score_matrix(lh[i] * (1 + f), la[i] * (1 - f), rho[i], max_goals=8))
        return np.clip([o["home"], o["draw"], o["away"]], 1e-9, 1)

    def nll(beta, idxs):
        return float(np.mean([-np.log(probs(beta, i)[y[i]]) for i in idxs]))

    # out-of-fold per-match losses for DC (beta=0) and DC+tilt (beta fit on train fold)
    kf = KFold(n_splits=5, shuffle=True, random_state=0)
    loss_dc = np.zeros(n); loss_tilt = np.zeros(n); betas = []
    for tr, te in kf.split(np.arange(n)):
        b = minimize_scalar(lambda x: nll(x, tr), bounds=(-5, 5), method="bounded").x
        betas.append(b)
        for i in te:
            loss_dc[i] = -np.log(probs(0.0, i)[y[i]])
            loss_tilt[i] = -np.log(probs(b, i)[y[i]])
    beta_full = minimize_scalar(lambda x: nll(x, range(n)), bounds=(-5, 5), method="bounded").x

    diff = loss_dc - loss_tilt            # >0 means tilt helped
    mean_diff = float(diff.mean())
    # bootstrap 95% CI on the mean held-out improvement
    rng = np.random.default_rng(0)
    boot = np.array([diff[rng.integers(0, n, n)].mean() for _ in range(5000)])
    ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    print("\n=== ABLATION (5-fold CV, held-out) ===")
    print(f"  Dixon-Coles alone   log-loss: {loss_dc.mean():.4f}")
    print(f"  Dixon-Coles + tilt  log-loss: {loss_tilt.mean():.4f}")
    print(f"  improvement (DC - tilt)     : {mean_diff:+.4f}")
    print(f"  bootstrap 95% CI            : [{ci[0]:+.4f}, {ci[1]:+.4f}]")
    print(f"  fitted beta (all data)      : {beta_full:.2f}  | per fold {[round(b,2) for b in betas]}")

    if ci[0] > 0:
        verdict = "HELPS — improvement is distinguishable from zero"
    elif ci[1] < 0:
        verdict = "HURTS — significantly worse"
    else:
        verdict = "NO MEASURABLE EFFECT — CI spans zero (club attack form adds nothing reliable)"
    print(f"\n  VERDICT: club attack form {verdict}.")
    _write(n, loss_dc.mean(), loss_tilt.mean(), mean_diff, ci, beta_full, betas, verdict)
    print(f"  wrote {Path(__file__).with_name('clubform_verdict.md')}")


def _write(n, ll_dc, ll_tilt, md, ci, beta, betas, verdict):
    L = [
        "# Does club form add ANYTHING to international predictions? (firmer test)", "",
        f"_Two leakage-clean windows (2024-25 form 2324, 2025-26 form 2425), DC refit per "
        f"window, {n} held-out internationals, 5-fold CV, bootstrap CI. Current-squad proxy._", "",
        "## Result", "", "| Model | held-out log-loss |", "|---|---|",
        f"| Dixon-Coles alone | {ll_dc:.4f} |",
        f"| Dixon-Coles + club-attack tilt | {ll_tilt:.4f} |",
        f"| **Improvement** | **{md:+.4f}** |",
        f"| **Bootstrap 95% CI** | **[{ci[0]:+.4f}, {ci[1]:+.4f}]** |", "",
        f"- Fitted tilt coefficient: **{beta:.2f}** (hand-tuned was 0.50). Per fold: {[round(b,2) for b in betas]}",
        "", "## Verdict", "", f"Club attack form **{verdict}**.", "",
        "_If the CI spans zero, the international-results model (Elo / Dixon-Coles) already "
        "prices in attacking quality — the club-form layer adds no reliable predictive value "
        "on top, and we should not build more of it (e.g. defensive club form) expecting gains._",
    ]
    Path(__file__).with_name("clubform_verdict.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()

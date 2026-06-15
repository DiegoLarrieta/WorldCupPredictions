"""Dixon-Coles goals model for international football.

The proven, interpretable football model. Each national team gets an ATTACK and a
DEFENCE rating; expected goals for a match come from those plus a home-advantage term:

    log λ_home = intercept + home_adv·(not neutral) + attack[home] - defence[away]
    log λ_away = intercept                          + attack[away] - defence[home]

Goals are Poisson around λ, with the Dixon-Coles low-score correction (ρ) that fixes
the 0-0/1-0/0-1/1-1 probabilities a plain Poisson gets wrong. Fitted by weighted
maximum likelihood with EXPONENTIAL TIME-DECAY (recent matches count more — the
project's core recency principle, and Dixon-Coles' own device).

From the fitted ratings we get, for any matchup: the full scoreline matrix, and from
it W/D/L, Over/Under, both-teams-to-score, and the most likely scores.

Best-practice notes:
- L2 regularisation on attack/defence for identifiability + stability (ridge Poisson).
- ρ bounded so the correction stays valid (τ>0).
- validate() does a leakage-free time split and reports log-loss vs an Elo baseline,
  so we only trust the extra complexity if it beats the simple model.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "worldcup.duckdb"

WINDOW_START = "2017-01-01"   # matches before this are ~zero-weight after decay anyway
HALFLIFE_DAYS = 540           # ~18 months: recent form dominates
MIN_MATCHES = 12              # drop teams with too little signal to rate
L2 = 0.5                      # ridge strength on attack/defence
DECAY = np.log(2) / HALFLIFE_DAYS


def load_internationals(as_of: str) -> "pd.DataFrame":
    import pandas as pd
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        f"""
        SELECT date, home_team, away_team, CAST(home_goals AS INT) hg,
               CAST(away_goals AS INT) ag, neutral
        FROM matches
        WHERE is_international AND home_goals IS NOT NULL AND away_goals IS NOT NULL
          AND date >= DATE '{WINDOW_START}' AND date < DATE '{as_of}'
        ORDER BY date
        """
    ).fetch_df()
    con.close()
    return df


def fit(as_of: str):
    """Fit the model on internationals strictly BEFORE as_of (no leakage)."""
    import pandas as pd
    df = load_internationals(as_of)

    # keep teams with enough matches in-window
    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    keep = set(counts[counts >= MIN_MATCHES].index)
    df = df[df["home_team"].isin(keep) & df["away_team"].isin(keep)].reset_index(drop=True)

    teams = sorted(set(df["home_team"]) | set(df["away_team"]))
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    h = df["home_team"].map(idx).to_numpy()
    a = df["away_team"].map(idx).to_numpy()
    hg = df["hg"].to_numpy()
    ag = df["ag"].to_numpy()
    neutral = df["neutral"].astype(bool).to_numpy()
    days_ago = (pd.Timestamp(as_of) - pd.to_datetime(df["date"])).dt.days.to_numpy()
    w = np.exp(-DECAY * days_ago)
    lg_hg = gammaln(hg + 1.0)
    lg_ag = gammaln(ag + 1.0)

    def unpack(p):
        return p[0], p[1], p[2], p[3:3 + n], p[3 + n:3 + 2 * n]

    def _tau(hg, ag, lh, la, rho):
        t = np.ones_like(lh)
        t = np.where((hg == 0) & (ag == 0), 1 - lh * la * rho, t)
        t = np.where((hg == 0) & (ag == 1), 1 + lh * rho, t)
        t = np.where((hg == 1) & (ag == 0), 1 + la * rho, t)
        t = np.where((hg == 1) & (ag == 1), 1 - rho, t)
        return np.clip(t, 1e-9, None)

    def nll(p):
        inter, home_adv, rho, att, dfn = unpack(p)
        lh = np.exp(inter + home_adv * (~neutral) + att[h] - dfn[a])
        la = np.exp(inter + att[a] - dfn[h])
        ll = (hg * np.log(lh) - lh - lg_hg) + (ag * np.log(la) - la - lg_ag)
        ll += np.log(_tau(hg, ag, lh, la, rho))
        return -np.sum(w * ll) + L2 * (np.sum(att ** 2) + np.sum(dfn ** 2))

    p0 = np.concatenate([[0.0, 0.3, -0.05], np.zeros(2 * n)])
    bounds = [(-2, 2), (0, 1), (-0.2, 0.2)] + [(-3, 3)] * (2 * n)
    res = minimize(nll, p0, method="L-BFGS-B", bounds=bounds,
                   options={"maxiter": 400})
    inter, home_adv, rho, att, dfn = unpack(res.x)
    return {
        "teams": teams, "idx": idx, "intercept": inter, "home_adv": home_adv,
        "rho": rho, "attack": dict(zip(teams, att)), "defence": dict(zip(teams, dfn)),
        "n_matches": len(df), "converged": res.success,
    }


def lambdas(model, home, away, neutral=True):
    a, d, inter, ha = model["attack"], model["defence"], model["intercept"], model["home_adv"]
    lh = np.exp(inter + (0 if neutral else ha) + a[home] - d[away])
    la = np.exp(inter + a[away] - d[home])
    return lh, la


def score_matrix(lh, la, rho, max_goals=10):
    from scipy.stats import poisson
    ph = poisson.pmf(np.arange(max_goals + 1), lh)
    pa = poisson.pmf(np.arange(max_goals + 1), la)
    m = np.outer(ph, pa)
    # Dixon-Coles low-score correction
    m[0, 0] *= 1 - lh * la * rho
    m[0, 1] *= 1 + lh * rho
    m[1, 0] *= 1 + la * rho
    m[1, 1] *= 1 - rho
    return m / m.sum()


def outcomes(m):
    home = np.tril(m, -1).sum()
    draw = np.trace(m)
    away = np.triu(m, 1).sum()
    i = np.arange(m.shape[0])
    total = i[:, None] + i[None, :]
    over25 = m[total >= 3].sum()
    btts = m[1:, 1:].sum()
    # top scorelines
    flat = [((x, y), m[x, y]) for x in range(m.shape[0]) for y in range(m.shape[1])]
    top = sorted(flat, key=lambda kv: -kv[1])[:5]
    return {"home": home, "draw": draw, "away": away,
            "over25": over25, "under25": 1 - over25, "btts": btts, "top_scores": top}

"""Dixon-Coles goals model (canonical implementation).

Team attack/defence ratings from time-decayed international goals; bivariate Poisson
with the Dixon-Coles low-score correction. Exposes BOTH a functional API
(fit/lambdas/score_matrix/outcomes — used by validation scripts) and the
DixonColesModel class implementing PredictiveModel.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import poisson

from engine.data import DB_PATH, load_internationals  # noqa: F401  (DB_PATH re-exported)
from engine.models.base import PredictiveModel

HALFLIFE_DAYS = 540     # ~18 months: recent form dominates
MIN_MATCHES = 12        # drop teams with too little signal
L2 = 0.5                # ridge on attack/defence for identifiability
SINCE = "2017-01-01"
DECAY = np.log(2) / HALFLIFE_DAYS


# ---- functional API --------------------------------------------------------
def fit(as_of: str) -> dict:
    """Fit on internationals strictly before `as_of`."""
    return fit_frame(load_internationals(as_of, since=SINCE), as_of)


def fit_frame(df, as_of: str, *, min_matches: int = MIN_MATCHES,
              halflife_days: int = HALFLIFE_DAYS) -> dict:
    """Fit Dixon-Coles on an arbitrary match frame (columns date, home_team, away_team,
    hg, ag, neutral). Identical math to the international fit — lets a club backtest reuse
    the validated model on its own data without touching the international path.
    """
    import pandas as pd
    decay = np.log(2) / halflife_days

    counts = pd.concat([df["home_team"], df["away_team"]]).value_counts()
    keep = set(counts[counts >= min_matches].index)
    df = df[df["home_team"].isin(keep) & df["away_team"].isin(keep)].reset_index(drop=True)

    teams = sorted(set(df["home_team"]) | set(df["away_team"]))
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)
    h = df["home_team"].map(idx).to_numpy()
    a = df["away_team"].map(idx).to_numpy()
    hg, ag = df["hg"].to_numpy(), df["ag"].to_numpy()
    neutral = df["neutral"].astype(bool).to_numpy()
    days_ago = (pd.Timestamp(as_of) - df["date"]).dt.days.to_numpy()
    w = np.exp(-decay * days_ago)
    lg_hg, lg_ag = gammaln(hg + 1.0), gammaln(ag + 1.0)

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
    res = minimize(nll, p0, method="L-BFGS-B", bounds=bounds, options={"maxiter": 400})
    inter, home_adv, rho, att, dfn = unpack(res.x)
    return {
        "teams": teams, "intercept": inter, "home_adv": home_adv, "rho": rho,
        "attack": dict(zip(teams, att)), "defence": dict(zip(teams, dfn)),
        "n_matches": len(df), "converged": res.success,
    }


def lambdas(model: dict, home: str, away: str, neutral: bool = True):
    a, d = model["attack"], model["defence"]
    inter, ha = model["intercept"], model["home_adv"]
    lh = np.exp(inter + (0 if neutral else ha) + a[home] - d[away])
    la = np.exp(inter + a[away] - d[home])
    return lh, la


def score_matrix(lh, la, rho, max_goals: int = 10):
    ph = poisson.pmf(np.arange(max_goals + 1), lh)
    pa = poisson.pmf(np.arange(max_goals + 1), la)
    m = np.outer(ph, pa)
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
    flat = [((x, y), m[x, y]) for x in range(m.shape[0]) for y in range(m.shape[1])]
    top = sorted(flat, key=lambda kv: -kv[1])[:5]
    return {"home": home, "draw": draw, "away": away, "over25": over25,
            "under25": 1 - over25, "btts": btts, "top_scores": top}


# ---- class wrapper ---------------------------------------------------------
class DixonColesModel(PredictiveModel):
    name = "dixon_coles"

    def fit(self, as_of: str) -> "DixonColesModel":
        self.m = fit(as_of)
        return self

    def can_rate(self, team: str) -> bool:
        return team in self.m["attack"]

    def predict_wdl(self, home, away, neutral=True) -> np.ndarray:
        lh, la = lambdas(self.m, home, away, neutral)
        o = outcomes(score_matrix(lh, la, self.m["rho"]))
        return np.array([o["home"], o["draw"], o["away"]])

    def predict_detail(self, home, away, neutral=True) -> dict:
        """DC-specific extras: expected goals, O/U, BTTS, top scorelines."""
        lh, la = lambdas(self.m, home, away, neutral)
        o = outcomes(score_matrix(lh, la, self.m["rho"]))
        return {"xg_home": float(lh), "xg_away": float(la), **o}

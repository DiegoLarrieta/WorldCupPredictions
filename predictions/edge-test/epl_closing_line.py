"""THE EDGE-EXISTENCE TEST: can our modeling approach beat a real closing line?

We hold 760 EPL matches (2 seasons) with Bet365 closing 1X2 odds. EPL is softer than the
WC main line, so this is the friendliest possible test. If a club-level Elo + Dixon-Coles
(the same approach we use for internationals) cannot beat the EPL close, it will not beat
the WC close — and the honest conclusion is to stop betting main markets and go all-in on
props / soft books.

Method (leakage-safe, train/test split):
  - TRAIN = season 1 (2023-24): warm up Elo, fit the Elo gap->W/D/L map and the ensemble
    weight. TEST = season 2 (2024-25): genuine out-of-sample.
  - Elo: online, neutral update (home effect learned by the map). Predict BEFORE update.
  - Dixon-Coles: refit by date on every match strictly before it (engine reuse, fit_frame).
  - Market: Bet365 closing odds, de-vigged with Shin.
  - Scored on TEST: log-loss / RPS / Brier for each model vs the MARKET, plus a flat-stake
    betting simulation (ROI with bootstrap 95% CI) at the prices we'd actually have taken.

Run:  .venv/bin/python predictions/edge-test/epl_closing_line.py
Writes predictions/edge-test/RESULTS.md.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from engine.evaluate import log_loss, rps                      # noqa: E402
from engine.market import devig                                # noqa: E402
from engine.models.dixon_coles import (fit_frame, lambdas,     # noqa: E402
                                        outcomes, score_matrix)

DB = Path(__file__).resolve().parents[2] / "data" / "worldcup.duckdb"
OUT = Path(__file__).resolve().parent / "RESULTS.md"
K_ELO = 20.0
SEASON_SPLIT = "2024-07-01"     # before = train (23-24), after = test (24-25)
RESULT_ORDER = ("home", "draw", "away")   # y: 0,1,2


# ---- data ------------------------------------------------------------------
def load() -> pd.DataFrame:
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute("""
        SELECT m.date, m.home_team, m.away_team,
               CAST(m.home_goals AS INT) hg, CAST(m.away_goals AS INT) ag,
               MAX(CASE WHEN o.selection='home' THEN o.price END) AS o_home,
               MAX(CASE WHEN o.selection='draw' THEN o.price END) AS o_draw,
               MAX(CASE WHEN o.selection='away' THEN o.price END) AS o_away
        FROM matches m
        JOIN match_odds o ON o.match_id=m.match_id AND o.bookmaker='bet365' AND o.market='1x2'
        WHERE NOT m.is_international
        GROUP BY 1,2,3,4,5 ORDER BY m.date
    """).df()
    con.close()
    df["date"] = pd.to_datetime(df["date"])
    df["neutral"] = False                      # club games are played at a home venue
    df["y"] = np.where(df.hg > df.ag, 0, np.where(df.hg == df.ag, 1, 2))
    return df


# ---- Elo (online, neutral update) ------------------------------------------
def elo_gaps(df: pd.DataFrame) -> np.ndarray:
    """Pre-match (rating_home - rating_away) for every row, updating online after each."""
    r: dict[str, float] = {}
    gaps = np.empty(len(df))
    for i, row in enumerate(df.itertuples(index=False)):
        rh, ra = r.get(row.home_team, 1500.0), r.get(row.away_team, 1500.0)
        gaps[i] = rh - ra
        exp_h = 1.0 / (1.0 + 10 ** (-(rh - ra) / 400.0))
        s_h = 1.0 if row.hg > row.ag else (0.5 if row.hg == row.ag else 0.0)
        r[row.home_team] = rh + K_ELO * (s_h - exp_h)
        r[row.away_team] = ra + K_ELO * ((1 - s_h) - (1 - exp_h))
    return gaps


# ---- model probability matrices (one row per match: [home, draw, away]) -----
def market_probs(df: pd.DataFrame, method: str) -> np.ndarray:
    out = np.empty((len(df), 3))
    for i, row in enumerate(df.itertuples(index=False)):
        p = devig({"home": row.o_home, "draw": row.o_draw, "away": row.o_away}, method)
        out[i] = [p["home"], p["draw"], p["away"]]
    return out


def dc_probs(df: pd.DataFrame) -> np.ndarray:
    """Walk-forward DC: for each date, fit on matches strictly before it, predict that day.

    NaN row when either team isn't yet rateable (too little history) — excluded downstream.
    """
    out = np.full((len(df), 3), np.nan)
    for d in df["date"].unique():
        train = df[df["date"] < d]
        if len(train) < 60:
            continue
        m = fit_frame(train, pd.Timestamp(d).strftime("%Y-%m-%d"), min_matches=6)
        att = m["attack"]
        todays = df.index[df["date"] == d]
        for i in todays:
            h, a = df.at[i, "home_team"], df.at[i, "away_team"]
            if h in att and a in att:
                lh, la = lambdas(m, h, a, neutral=False)
                o = outcomes(score_matrix(lh, la, m["rho"]))
                out[i] = [o["home"], o["draw"], o["away"]]
    return out


# ---- metrics ---------------------------------------------------------------
def scores(P: np.ndarray, y: np.ndarray) -> dict:
    onehot = np.eye(3)[y]
    return {"log_loss": log_loss(P, y), "rps": rps(P, y),
            "brier": float(np.mean(np.sum((P - onehot) ** 2, axis=1)))}


def bet_sim(P: np.ndarray, odds: np.ndarray, y: np.ndarray, threshold: float):
    """Flat 1u on every selection whose model EV at the offered price clears threshold."""
    ev = P * odds - 1.0
    pnl, n = [], 0
    for i in range(len(P)):
        for k in range(3):
            if ev[i, k] >= threshold:
                n += 1
                pnl.append((odds[i, k] - 1.0) if y[i] == k else -1.0)
    if not pnl:
        return {"bets": 0, "roi": None, "ci": None}
    pnl = np.array(pnl)
    boot = [np.mean(np.random.choice(pnl, len(pnl), replace=True)) for _ in range(2000)]
    return {"bets": n, "roi": float(pnl.mean()),
            "ci": (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))}


def main() -> None:
    df = load()
    df["elo_gap"] = elo_gaps(df)
    test_mask = df["date"] >= SEASON_SPLIT
    train_mask = ~test_mask

    # Elo gap -> W/D/L, fit on TRAIN only (home effect learned by the intercepts)
    lr = LogisticRegression(max_iter=1000)
    lr.fit(df.loc[train_mask, ["elo_gap"]].to_numpy() / 100.0, df.loc[train_mask, "y"])

    def elo_probs(rows):
        return lr.predict_proba(df.loc[rows, ["elo_gap"]].to_numpy() / 100.0)

    DC = dc_probs(df)
    mkt_shin = market_probs(df, "shin")
    mkt_mult = market_probs(df, "multiplicative")

    # ensemble weight w (on DC) fit on TRAIN rows where DC exists
    tr = df.index[train_mask & ~np.isnan(DC[:, 0])]
    elo_tr = elo_probs(tr)
    yo = df.loc[tr, "y"].to_numpy()
    ws = np.linspace(0, 1, 21)
    w = ws[np.argmin([log_loss(wv * DC[tr] + (1 - wv) * elo_tr, yo) for wv in ws])]

    # ---- evaluate on TEST (rows where DC exists) ----
    te = df.index[test_mask & ~np.isnan(DC[:, 0])]
    y = df.loc[te, "y"].to_numpy()
    elo_te = elo_probs(te)
    ens = w * DC[te] + (1 - w) * elo_te
    odds = df.loc[te, ["o_home", "o_draw", "o_away"]].to_numpy()

    models = {"market (Shin)": mkt_shin[te], "market (mult)": mkt_mult[te],
              "elo": elo_te, "dixon_coles": DC[te], "ensemble": ens}
    sc = {name: scores(P, y) for name, P in models.items()}
    vig = float(np.mean(1 / odds[:, 0] + 1 / odds[:, 1] + 1 / odds[:, 2]) - 1)

    # write + print
    L = [f"# EPL closing-line edge test — {len(te)} out-of-sample matches (season 2024-25)",
         "",
         f"_Train: 2023-24. Test: 2024-25. Ensemble weight on DC = {w:.2f}. "
         f"Mean Bet365 overround (vig) = {vig:.1%}. Market de-vigged with Shin._", "",
         "## Predictive accuracy vs the market (lower is better)", "",
         "| Model | Log-loss | RPS | Brier |", "|---|---|---|---|"]
    for name in ("market (Shin)", "market (mult)", "ensemble", "dixon_coles", "elo"):
        s = sc[name]
        L.append(f"| {name} | {s['log_loss']:.4f} | {s['rps']:.4f} | {s['brier']:.4f} |")

    beat = sc["ensemble"]["log_loss"] < sc["market (Shin)"]["log_loss"]
    L += ["", f"**Does our best model beat the market as a predictor? "
          f"{'YES' if beat else 'NO'}** "
          f"(ensemble log-loss {sc['ensemble']['log_loss']:.4f} vs market "
          f"{sc['market (Shin)']['log_loss']:.4f}).", "",
          "## Flat-stake betting simulation (1u per qualifying selection, at Bet365 odds)",
          "", "| Model | EV threshold | Bets | ROI | 95% CI |", "|---|---|---|---|---|"]
    for name in ("ensemble", "dixon_coles", "elo"):
        for thr in (0.0, 0.03, 0.05):
            r = bet_sim(models[name], odds, y, thr)
            if r["bets"]:
                ci = f"[{r['ci'][0]:+.3f}, {r['ci'][1]:+.3f}]"
                L.append(f"| {name} | {thr:.0%} | {r['bets']} | {r['roi']:+.3f} | {ci} |")
            else:
                L.append(f"| {name} | {thr:.0%} | 0 | — | — |")

    pos = any((bet_sim(models[m], odds, y, 0.0)["ci"] or (-1, -1))[0] > 0
              for m in ("ensemble", "dixon_coles", "elo"))
    L += ["", "## Verdict", "",
          f"- Beats the closing line as a predictor: **{'YES' if beat else 'NO'}**.",
          f"- Any positive-ROI strategy with CI above zero (real edge, not noise): "
          f"**{'YES' if pos else 'NO'}**.",
          "", "_If both are NO: the approach does not beat a soft real market, so it will "
          "not beat the WC main line. Pivot to props / soft books — do not bet WC 1X2/O-U "
          "as if the model has edge._" if not (beat or pos) else
          "_At least one signal is positive — worth a deeper look before trusting it "
          "(check robustness across seasons, books, and de-vig method)._"]
    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nWritten to {OUT}")


if __name__ == "__main__":
    main()

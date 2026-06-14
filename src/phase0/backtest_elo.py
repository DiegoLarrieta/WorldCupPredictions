"""Elo calibration backtest — does our Elo actually predict reality?

Matching eloratings.net's numbers would only prove we copied them. The real test of
correctness is CALIBRATION: when the Elo says "0.70 expected score," does the team
actually average ~0.70 (win=1, draw=0.5, loss=0) across thousands of past matches?

Method: replay every international in date order. BEFORE each match, record the
pre-match expected score from the current ratings (the genuine out-of-sample
prediction — the model has not seen this match yet). Then update the ratings and
move on. Finally, compare predictions to outcomes.

Outputs:
- Brier score (mean squared error of the prediction) vs a naive 0.5 baseline. Lower
  is better; beating 0.5 proves the ratings carry real signal.
- A calibration table: bin predictions into deciles, compare predicted vs actual.
  A well-calibrated model sits on the diagonal (predicted ≈ actual in every bin).
- Decisive-match accuracy: when the match isn't a draw, does the favored team win?

Burn-in: only score matches from MIN_YEAR onward where BOTH teams already have
>= MIN_PRIOR games, so cold-start 1500s don't pollute the measurement.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from ingest import DB_PATH, ELO_BASE, _expected, _k_factor

MIN_YEAR = 2000      # ignore early eras (different game, sparse data)
MIN_PRIOR = 30       # both teams must have this many prior matches to be scored
CSV_OUT = Path(__file__).resolve().parents[2] / "data" / "csv" / "elo_calibration.csv"


def load_internationals() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        """
        SELECT date, home_team, away_team, home_goals, away_goals, tournament, neutral
        FROM fact_match
        WHERE is_international AND home_goals IS NOT NULL AND away_goals IS NOT NULL
        ORDER BY date
        """
    ).fetch_df()
    con.close()
    return df


def replay() -> pd.DataFrame:
    """Return one row per scored match: (predicted expected score, actual score)."""
    ratings: dict[str, float] = {}
    counts: dict[str, int] = {}
    preds = []
    for r in load_internationals().itertuples(index=False):
        h, a = r.home_team, r.away_team
        rh, ra = ratings.get(h, ELO_BASE), ratings.get(a, ELO_BASE)
        exp_home = _expected(rh, ra, bool(r.neutral))  # pre-match prediction

        gd = int(r.home_goals) - int(r.away_goals)
        actual_home = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)

        eligible = (
            str(r.date) >= f"{MIN_YEAR}-01-01"
            and counts.get(h, 0) >= MIN_PRIOR
            and counts.get(a, 0) >= MIN_PRIOR
        )
        if eligible:
            preds.append((exp_home, actual_home, gd))

        # update ratings regardless, to keep them warm
        k = _k_factor(r.tournament, gd)
        ratings[h] = rh + k * (actual_home - exp_home)
        ratings[a] = ra + k * ((1.0 - actual_home) - (1.0 - exp_home))
        counts[h] = counts.get(h, 0) + 1
        counts[a] = counts.get(a, 0) + 1
    return pd.DataFrame(preds, columns=["pred", "actual", "gd"])


def main() -> None:
    df = replay()
    n = len(df)
    print(f"Scored {n:,} internationals (from {MIN_YEAR}, both teams >= {MIN_PRIOR} prior games)\n")

    # --- Brier score (vs naive 0.5 baseline) ---
    brier = ((df["pred"] - df["actual"]) ** 2).mean()
    baseline = ((0.5 - df["actual"]) ** 2).mean()
    skill = 1 - brier / baseline
    print("=== ACCURACY ===")
    print(f"  Brier score      : {brier:.4f}   (lower is better)")
    print(f"  baseline (0.5)   : {baseline:.4f}")
    print(f"  skill vs baseline: {skill:+.1%}   (>0 means the ratings carry real signal)")

    # decisive-match accuracy: among non-draws, did the favored side win?
    dec = df[df["gd"] != 0].copy()
    dec["fav_home"] = dec["pred"] > 0.5
    dec["home_won"] = dec["gd"] > 0
    acc = (dec["fav_home"] == dec["home_won"]).mean()
    print(f"  favorite accuracy: {acc:.1%}   (decisive matches only, n={len(dec):,})\n")

    # --- calibration table (deciles) ---
    print("=== CALIBRATION (predicted vs actual, by prediction bin) ===")
    df["bin"] = (df["pred"] * 10).clip(0, 9).astype(int)
    cal = df.groupby("bin").agg(
        predicted=("pred", "mean"), actual=("actual", "mean"), n=("pred", "size")
    ).reset_index()
    print(f"  {'bin':<10}{'predicted':>10}{'actual':>9}{'n':>8}   calibration")
    for row in cal.itertuples(index=False):
        lo, hi = row.bin / 10, row.bin / 10 + 0.1
        diff = row.actual - row.predicted
        bar = "█" * max(0, round(row.actual * 20))
        flag = "" if abs(diff) < 0.03 else ("  HIGH" if diff > 0 else "  LOW")
        print(f"  {lo:.1f}-{hi:.1f}   {row.predicted:>9.2f}{row.actual:>9.2f}{row.n:>8,}   {bar}{flag}")

    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    cal.to_csv(CSV_OUT, index=False)
    print(f"\nCalibration table written to {CSV_OUT}")


if __name__ == "__main__":
    main()

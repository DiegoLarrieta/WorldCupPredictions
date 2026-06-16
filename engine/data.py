"""Leakage-safe data access for the prediction engine.

One place to load matches with an `as_of` cutoff, so no model can ever see a match
dated on/after the one it predicts. The DuckDB warehouse is the source of truth.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "worldcup.duckdb"


def load_internationals(as_of: str, since: str = "1990-01-01") -> pd.DataFrame:
    """All completed internationals in [since, as_of) — strictly before the cutoff."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        f"""
        SELECT date, home_team, away_team, CAST(home_goals AS INT) hg,
               CAST(away_goals AS INT) ag, neutral, tournament
        FROM matches
        WHERE is_international AND home_goals IS NOT NULL AND away_goals IS NOT NULL
          AND date >= DATE '{since}' AND date < DATE '{as_of}'
        ORDER BY date
        """
    ).fetch_df()
    con.close()
    df["date"] = pd.to_datetime(df["date"])
    return df


def team_ratings() -> dict[str, float]:
    """Current Elo ratings (team_ratings table) — convenience lookup."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    rows = con.execute("SELECT team_name, elo FROM team_ratings").fetchall()
    con.close()
    return {t: float(e) for t, e in rows}

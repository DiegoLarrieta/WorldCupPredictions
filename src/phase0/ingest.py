"""Phase 0 ingestion slice.

Pulls free club-league results + closing odds (football-data.co.uk via soccerdata)
and ClubElo team strength, then lands them in a local DuckDB warehouse:

    fact_match   one row per match (teams, goals, result)
    fact_odds    LONG format: one row per (match, bookmaker, market, selection)
    team_elo     ClubElo rating per team as of a reference date

This is deliberately the THIN slice from the design doc's Assignment: prove the
implied-probability harness end to end before building the medallion warehouse.
Schema names match design/design-step1-data-layer.md so Phase 1 can formalize them.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import duckdb
import pandas as pd
import soccerdata as sd

# --- config -----------------------------------------------------------------
# Phase 0 just needs SOME league with closing odds to prove the harness; the same
# code runs for any league soccerdata exposes. Expand later.
LEAGUES = ["ENG-Premier League"]
SEASONS = ["2324"]  # one season is plenty to prove the query
ELO_REF_DATE = dt.date(2024, 5, 1)  # a date inside the season for a strength snapshot

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "worldcup.duckdb"

# football-data.co.uk closing-odds columns we melt into long fact_odds.
# B365 = Bet365 closing 1X2; Avg = market average closing 1X2.
ODDS_BOOKS = {
    "bet365": ("B365H", "B365D", "B365A"),
    "market_avg": ("AvgH", "AvgD", "AvgA"),
}


def load_match_history() -> pd.DataFrame:
    mh = sd.MatchHistory(leagues=LEAGUES, seasons=SEASONS)
    games = mh.read_games().reset_index()
    print(f"  MatchHistory: {len(games)} games")
    return games


def build_fact_match(games: pd.DataFrame) -> pd.DataFrame:
    fm = pd.DataFrame(
        {
            "match_id": games.index.astype("int64"),
            "date": pd.to_datetime(games["date"]).dt.date,
            "home_team": games["home_team"],
            "away_team": games["away_team"],
            "home_goals": games.get("FTHG"),
            "away_goals": games.get("FTAG"),
            "result": games.get("FTR"),  # H / D / A
        }
    )
    return fm


def build_fact_odds(games: pd.DataFrame) -> pd.DataFrame:
    rows = []
    captured_at = dt.datetime.utcnow()
    for match_id, row in games.iterrows():
        for book, (ch, cd, ca) in ODDS_BOOKS.items():
            for selection, col in (("home", ch), ("draw", cd), ("away", ca)):
                price = row.get(col)
                if pd.isna(price):
                    continue
                rows.append(
                    {
                        "match_id": int(match_id),
                        "bookmaker": book,
                        "market": "1x2",
                        "selection": selection,
                        "line": None,
                        "price": float(price),
                        "captured_at": captured_at,  # closing snapshot
                    }
                )
    fo = pd.DataFrame(rows)
    print(f"  fact_odds: {len(fo)} odds rows")
    return fo


def load_team_elo() -> pd.DataFrame:
    elo = sd.ClubElo()
    df = elo.read_by_date(ELO_REF_DATE).reset_index()
    out = pd.DataFrame(
        {
            "team": df["team"],
            "elo": df["elo"],
            "as_of": ELO_REF_DATE,
        }
    )
    print(f"  team_elo: {len(out)} teams as of {ELO_REF_DATE}")
    return out


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Fetching free data via soccerdata (first run downloads + caches)...")
    games = load_match_history()
    fact_match = build_fact_match(games)
    fact_odds = build_fact_odds(games)
    team_elo = load_team_elo()

    con = duckdb.connect(str(DB_PATH))
    for name, frame in (
        ("fact_match", fact_match),
        ("fact_odds", fact_odds),
        ("team_elo", team_elo),
    ):
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM frame")
    con.close()
    print(f"\nLoaded into {DB_PATH}")
    print("Next: duckdb data/worldcup.duckdb < sql/implied_prob.sql")


if __name__ == "__main__":
    main()

"""Player layer: dim_club, dim_player, fact_player_season from Understat.

This is the bridge between the club world and the country world (see
design/data-model.md). It builds three tables:

    dim_club             one row per club  (Real Madrid, Bayern, ...)
    dim_player           one row per player — the PIVOT. nationality is left NULL
                         here; Understat is club-only and never says "Mbappé is
                         French". That join is the next step (a squad/nationality
                         source), and it is the real entity-resolution work.
    fact_player_season   one row per player·season·club — the FORM signal:
                         minutes, goals, xg, npxg, assists, xa, shots, key passes.

Big-5 leagues so most World Cup players' clubs are covered. read_player_season_stats
is one page per league-season (fast), unlike the per-match shot scrape.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import soccerdata as sd

from ingest import DB_PATH

# Big-5 European leagues — where the vast majority of national-team players play club
# football. Expand by adding entries; each league-season is a single page fetch.
PLAYER_LEAGUES = [
    "ENG-Premier League",
    "ESP-La Liga",
    "GER-Bundesliga",
    "ITA-Serie A",
    "FRA-Ligue 1",
]
PLAYER_SEASONS = ["2324", "2425"]

# Understat player-season columns we keep, renamed to our schema.
STAT_COLS = {
    "matches": "appearances",
    "minutes": "minutes",
    "goals": "goals",
    "xg": "xg",
    "np_goals": "np_goals",
    "np_xg": "np_xg",
    "assists": "assists",
    "xa": "xa",
    "shots": "shots",
    "key_passes": "key_passes",
    "xg_chain": "xg_chain",
    "xg_buildup": "xg_buildup",
}


def load_player_seasons() -> pd.DataFrame:
    us = sd.Understat(leagues=PLAYER_LEAGUES, seasons=PLAYER_SEASONS)
    df = us.read_player_season_stats().reset_index()
    print(f"  pulled {len(df)} player-season rows across {len(PLAYER_LEAGUES)} leagues")
    return df


def build_tables(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # --- fact_player_season: one row per player·season·club ---
    fact = pd.DataFrame(
        {
            "player_id": df["player_id"],
            "season": df["season"],
            "club_id": df["team_id"],
            "league": df["league"],
            "position": df["position"],
            **{out: df[src] for src, out in STAT_COLS.items()},
        }
    )

    # --- dim_club: one row per club ---
    dim_club = (
        df[["team_id", "team", "league"]]
        .drop_duplicates("team_id")
        .rename(columns={"team_id": "club_id", "team": "name"})
        .sort_values("name")
        .reset_index(drop=True)
    )

    # --- dim_player: one row per player; current club = most recent season's club ---
    latest = df.sort_values("season").drop_duplicates("player_id", keep="last")
    dim_player = pd.DataFrame(
        {
            "player_id": latest["player_id"],
            "name": latest["player"],
            "position": latest["position"],
            "nationality": pd.NA,          # filled later from a squad/nationality source
            "current_club_id": latest["team_id"],
        }
    ).sort_values("name").reset_index(drop=True)

    return {"dim_club": dim_club, "dim_player": dim_player, "fact_player_season": fact}


def main() -> None:
    print("Player layer: Understat player-season stats ...")
    df = load_player_seasons()
    tables = build_tables(df)

    con = duckdb.connect(str(DB_PATH))
    for name, frame in tables.items():
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM frame")
        print(f"  {name:20} {len(frame):>6,} rows")
    con.close()
    print(f"\nLoaded player layer into {DB_PATH}")


if __name__ == "__main__":
    main()

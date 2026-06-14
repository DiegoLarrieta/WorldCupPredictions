"""Step 2 ingestion: rich per-match team stats (xG and friends) from Understat.

Why Understat, not FBref: FBref blocks plain requests, so soccerdata scrapes it by
driving a headless Chrome (slow, fragile — exactly the scraper tax the eng review
warned about). Understat serves the same advanced metrics as embedded JSON: fast,
no browser, locally cached after the first pull.

Builds `fact_match_team_stats` — one row per (match, team):

    xg                 expected goals (chance quality — predicts better than raw goals)
    np_xg              non-penalty xG (strips penalty noise — cleaner skill signal)
    ppda               passes allowed per defensive action (LOW = aggressive pressing)
    deep_completions   passes/crosses completed near the box (territorial dominance)
    shots, shots_on_target   from the shot-event feed (on target = Goal + SavedShot)
    goals              actual goals (for reference / reconciliation)

NOTE on possession: Understat doesn't carry possession% — and that's fine. Possession
is a famously weak predictor (70% possession routinely draws 0-0); npxG / PPDA / deep
completions describe *threat*, which is what actually moves results. If we later want
possession/passes/corners, those live on FBref (the slow scraper path).

These are CLUB matches. They join to a national lineup later via the player
(bridge_player_season) — internationals are too rare to carry a player's form.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import soccerdata as sd

from ingest import DB_PATH

# Same leagues/seasons as the odds slice so the datasets line up; expand later.
STATS_LEAGUES = ["ENG-Premier League"]
STATS_SEASONS = ["2324", "2425"]

# Understat shot outcomes that count as "on target": the keeper had to deal with it.
ON_TARGET = {"Goal", "Saved Shot"}


def _shots_per_team(us: sd.Understat) -> pd.DataFrame:
    """Aggregate the shot-event feed to shots + shots_on_target per (game, team_id).

    The shot feed carries only `team_id` (no team name / home-away flag), so we key
    on team_id and let the caller merge it onto the stats rows by (game_id, team_id).
    """
    sh = us.read_shot_events().reset_index()
    sh["on_target"] = sh["result"].isin(ON_TARGET)
    agg = (
        sh.groupby(["game_id", "team_id"])
        .agg(shots=("result", "size"), shots_on_target=("on_target", "sum"))
        .reset_index()
    )
    return agg


def _team_rows(tms: pd.DataFrame) -> pd.DataFrame:
    """Pivot the home/away-wide team_match_stats into one row per (game, team)."""
    tms = tms.reset_index()
    frames = []
    for side, opp in (("home", "away"), ("away", "home")):
        frames.append(
            pd.DataFrame(
                {
                    "game_id": tms["game_id"],
                    "team_id": tms[f"{side}_team_id"],
                    "date": pd.to_datetime(tms["date"]).dt.date,
                    "team": tms[f"{side}_team"],
                    "opponent": tms[f"{opp}_team"],
                    "is_home": side == "home",
                    "goals": tms[f"{side}_goals"],
                    "xg": tms[f"{side}_xg"],
                    "np_xg": tms[f"{side}_np_xg"],
                    "ppda": tms[f"{side}_ppda"],
                    "deep_completions": tms[f"{side}_deep_completions"],
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    print("Step 2: Understat team match stats ...")
    us = sd.Understat(leagues=STATS_LEAGUES, seasons=STATS_SEASONS)

    stats = _team_rows(us.read_team_match_stats())
    print(f"  team_match_stats: {len(stats)} team-match rows")

    try:
        shots = _shots_per_team(us)
        stats = stats.merge(shots, on=["game_id", "team_id"], how="left")
        print(f"  shots merged: {int(stats['shots'].notna().sum())} rows have shot data")
    except Exception as e:
        print(f"  ! shots skipped ({type(e).__name__}: {e})")
        stats["shots"] = pd.NA
        stats["shots_on_target"] = pd.NA

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE fact_match_team_stats AS SELECT * FROM stats")
    con.close()
    print(f"\nLoaded fact_match_team_stats ({len(stats)} rows) into {DB_PATH}")


if __name__ == "__main__":
    main()

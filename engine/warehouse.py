"""Warehouse writes — feed finished results back into the match spine.

Ratings are not stored; `engine.models.elo.replay_ratings` recomputes them by replaying
the whole `matches` table in date order. So "update the ratings after a match" means one
thing: put the finished result into `matches`. The next prediction's replay then includes
it automatically — no separate Elo state to maintain.

martj42 (the spine's upstream) lags days behind live results, so during a tournament we
insert the result ourselves tagged `source='wc2026-feedback'`. When martj42 catches up,
`make spine` does CREATE OR REPLACE on `matches` and rebuilds purely from the official
source, harmlessly superseding our interim row.

This module imports duckdb (not CI-safe by design); its tests auto-skip without a warehouse.
"""

from __future__ import annotations

import duckdb

from engine.data import DB_PATH

FEEDBACK_SOURCE = "wc2026-feedback"
# WC finals: lowercase contains "world cup" (not "qualif") so _k_factor gives the
# top tier (base K=60). Keep this label in sync with that check in src/phase0/ingest.py.
DEFAULT_TOURNAMENT = "FIFA World Cup"


def _team_seen(con, team: str) -> bool:
    row = con.execute(
        "SELECT 1 FROM matches WHERE home_team = ? OR away_team = ? LIMIT 1",
        [team, team],
    ).fetchone()
    return row is not None


def append_result(date: str, home_team: str, away_team: str,
                  home_goals: int, away_goals: int, *,
                  tournament: str = DEFAULT_TOURNAMENT, neutral: bool = True,
                  source: str = FEEDBACK_SOURCE) -> dict:
    """Insert one finished result into `matches` so the next replay sees it. Idempotent.

    Re-inserting the same (date, home, away) for the same source replaces the prior row,
    so re-scoring or correcting a result never double-counts. Raises if a team name has no
    prior history in the warehouse (almost always a name mismatch — silently seeding a
    phantom team at the Elo base would corrupt every future prediction).
    """
    con = duckdb.connect(str(DB_PATH))
    try:
        for t in (home_team, away_team):
            if not _team_seen(con, t):
                raise ValueError(
                    f"'{t}' has no history in the warehouse — likely a name mismatch. "
                    f"Use the exact name the engine rates by (the one predict_match accepted)."
                )
        # idempotent: drop any prior feedback row for this fixture, then insert fresh
        con.execute(
            "DELETE FROM matches WHERE source = ? AND date = CAST(? AS DATE) "
            "AND home_team = ? AND away_team = ?",
            [source, date, home_team, away_team],
        )
        next_id = con.execute("SELECT COALESCE(MAX(match_id), -1) + 1 FROM matches").fetchone()[0]
        con.execute(
            """
            INSERT INTO matches
              (match_id, date, home_team, away_team, home_goals, away_goals,
               tournament, neutral, is_international, source)
            VALUES (?, CAST(? AS DATE), ?, ?, ?, ?, ?, ?, TRUE, ?)
            """,
            [next_id, date, home_team, away_team, int(home_goals), int(away_goals),
             tournament, bool(neutral), source],
        )
        return {"match_id": int(next_id), "date": date,
                "match": f"{home_team} {home_goals}-{away_goals} {away_team}",
                "tournament": tournament, "source": source}
    finally:
        con.close()


def append_from_record(record: dict) -> dict:
    """Convenience: feed a worldcupmatches record (from engine.feedback) into the spine."""
    idn, sp = record["identity"], record["outcome"]["spine"]
    return append_result(
        idn["date"], idn["home"], idn["away"], sp["home_goals"], sp["away_goals"],
        tournament=idn.get("competition") or DEFAULT_TOURNAMENT,
        neutral=bool(idn.get("neutral", True)),
    )


def feedback_rows() -> list[dict]:
    """All interim feedback results currently in the spine (for inspection / reconcile)."""
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        cols = ["match_id", "date", "home_team", "away_team",
                "home_goals", "away_goals", "tournament"]
        rows = con.execute(
            f"SELECT {', '.join(cols)} FROM matches WHERE source = ? ORDER BY date",
            [FEEDBACK_SOURCE],
        ).fetchall()
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


def remove_results(source: str = FEEDBACK_SOURCE) -> int:
    """Delete all rows for a source (manual reconcile / test cleanup). Returns count removed."""
    con = duckdb.connect(str(DB_PATH))
    try:
        n = con.execute("SELECT COUNT(*) FROM matches WHERE source = ?", [source]).fetchone()[0]
        con.execute("DELETE FROM matches WHERE source = ?", [source])
        return int(n)
    finally:
        con.close()

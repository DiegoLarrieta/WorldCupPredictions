"""Squad -> club-form bridge with graceful degradation (Plan C).

For every one of the 1,248 World Cup squad players, attach their current club form
where we have it, and fall back to international caps/goals where we don't. This is
the honest "knows more about France than Panama" table the model will read.

Matching: national_squad (name + full DOB + club) -> dim_player (name + birth year +
club). Name match, disambiguated by birth YEAR (from DOB) then club fuzzy — DOB is the
strong key the eng review wanted (separates the two Mbappés cleanly).

Builds:
    national_squad_form   one row per squad player: squad info + matched player_id +
                          current-season club form (NULL if uncovered) + has_club_form
    squad_strength        per-country rollup (graceful degradation): club attack signal
                          where available + caps depth + team Elo
"""

from __future__ import annotations

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process

from ingest import DB_PATH
from ingest_nationality import norm

FORM_SEASON = "2425"
FUZZY_CUTOFF = 88


def _match(squad: pd.DataFrame, players: pd.DataFrame) -> pd.Series:
    """Return squad-index -> matched player_id (or NA)."""
    by_norm: dict[str, list] = {}
    for r in players.itertuples(index=False):
        by_norm.setdefault(norm(r.name), []).append(r)
    names = list(by_norm.keys())

    matched = {}
    for row in squad.itertuples():
        key = norm(row.player)
        cands = by_norm.get(key)
        if not cands:
            hit = process.extractOne(key, names, scorer=fuzz.token_set_ratio,
                                     score_cutoff=FUZZY_CUTOFF)
            if hit:
                cands = by_norm[hit[0]]
        if not cands:
            continue
        born_yr = int(row.dob[:4]) if isinstance(row.dob, str) and row.dob[:4].isdigit() else None
        sclub = norm(row.club or "")

        def score(c):
            c_born = int(c.born) if pd.notna(c.born) else None
            born_match = 100 if (c_born and born_yr and c_born == born_yr) else 0
            club = c.club if isinstance(c.club, str) else ""
            return born_match + fuzz.token_set_ratio(sclub, norm(club)) / 100.0
        best = max(cands, key=score)
        matched[row.Index] = best.player_id
    return pd.Series(matched, dtype="Int64")


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    squad = con.execute("SELECT * FROM national_squad").fetch_df()
    players = con.execute(
        "SELECT p.player_id, p.name, p.born, c.name AS club "
        "FROM dim_player p LEFT JOIN dim_club c ON c.club_id = p.current_club_id"
    ).fetch_df()
    # current-season club form, summed across clubs within the season
    form = con.execute(
        f"""SELECT player_id,
                   SUM("minutes") minutes_played, SUM(goals) club_goals, SUM(xg) xg,
                   SUM(np_xg) np_xg, SUM(assists) assists, SUM(xa) xa
            FROM fact_player_season WHERE season = '{FORM_SEASON}'
            GROUP BY player_id"""
    ).fetch_df()

    print("Matching 1,248 squad players to club form (name + birth-year + club) ...")
    squad["player_id"] = _match(squad, players)
    out = squad.merge(form, on="player_id", how="left")
    out["has_club_form"] = out["minutes_played"].notna()
    # np_xG per 90: the count-bias-free attacking signal (only where minutes exist)
    out["np_xg_per90"] = (out["np_xg"] / (out["minutes_played"] / 90)).where(
        out["minutes_played"] >= 1)

    con.execute("CREATE OR REPLACE TABLE national_squad_form AS SELECT * FROM out")
    con.execute(
        "COPY (SELECT * FROM national_squad_form) TO 'data/csv/national_squad_form.csv' (HEADER)"
    )

    cov = out["has_club_form"].mean()
    print(f"  matched club form for {out['has_club_form'].sum()}/{len(out)} ({cov:.0%})")

    # --- squad_strength: graceful-degradation rollup per country ---
    con.execute(
        """
        CREATE OR REPLACE TABLE squad_strength AS
        WITH per_country AS (
            SELECT s.country,
                   COUNT(*)                                   AS squad_size,
                   SUM(CASE WHEN s.has_club_form THEN 1 ELSE 0 END) AS with_form,
                   -- attack signal: avg np_xG/90 of the squad's 5 busiest attackers
                   AVG(s.np_xg_per90) FILTER (WHERE s.minutes_played >= 500) AS avg_npxg_per90,
                   SUM(s.caps)                                AS total_caps,
                   SUM(s.intl_goals)                          AS total_intl_goals
            FROM national_squad_form s GROUP BY s.country
        )
        SELECT pc.*, e.elo AS team_elo
        FROM per_country pc
        LEFT JOIN team_elo e ON e.team = pc.country
        """
    )
    con.execute("COPY (SELECT * FROM squad_strength) TO 'data/csv/squad_strength.csv' (HEADER)")
    con.close()
    print("  built squad_strength + exported both CSVs")


if __name__ == "__main__":
    main()

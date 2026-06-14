"""Export every table/view to organized CSV folders (the human-browsable mirror).

DuckDB is the source of truth; this writes a fresh CSV copy grouped by domain so the
data is easy to read in Excel/Numbers and easy to reason about. Regenerate any time;
never edit the CSVs by hand (they get overwritten).

Layout:
    data/csv/reference/   teams, team_ratings, clubs, players   (the nouns)
    data/csv/matches/     matches, match_odds
    data/csv/form/        player_seasons
    data/csv/worldcup/    wc_squads, wc_squad_form, wc_team_strength
    data/csv/derived/     market_prob, match_vs_market   (views; elo_calibration is written by the backtest)
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from ingest import DB_PATH

CSV_ROOT = Path(__file__).resolve().parents[2] / "data" / "csv"
SQL_VIEWS = Path(__file__).resolve().parents[2] / "sql" / "implied_prob.sql"

# table/view -> subfolder
EXPORTS = {
    "reference": ["teams", "team_ratings", "clubs", "players"],
    "matches": ["matches", "match_odds"],
    "form": ["player_seasons"],
    "worldcup": ["wc_squads", "wc_squad_form", "wc_team_strength"],
    "derived": ["market_prob", "match_vs_market"],
}


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    # (re)create the derived views before exporting them
    con.execute(SQL_VIEWS.read_text())

    existing = {r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()}

    for folder, names in EXPORTS.items():
        (CSV_ROOT / folder).mkdir(parents=True, exist_ok=True)
        for name in names:
            if name not in existing:
                print(f"  ! skip {name} (not built yet)")
                continue
            path = CSV_ROOT / folder / f"{name}.csv"
            con.execute(f'COPY (SELECT * FROM "{name}") TO \'{path}\' (HEADER)')
            n = con.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
            print(f"  {folder}/{name}.csv  ({n:,} rows)")
    con.close()
    print(f"\nExported to {CSV_ROOT}")


if __name__ == "__main__":
    main()

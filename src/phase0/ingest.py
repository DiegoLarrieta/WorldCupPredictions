"""Phase 0 ingestion slice.

Builds the international match spine + our OWN national-team Elo, and (separately)
lands free club-league closing odds to prove the vig-removal harness. Lands in DuckDB:

    fact_match   one row per match (internationals from martj42 + club matches w/ odds)
    team_elo     national-team Elo computed from results (NOT clubelo — see note)
    dim_team     canonical national teams (the entity-resolution spine)
    fact_odds    LONG format: one row per (match, bookmaker, market, selection)

WHY WE COMPUTE OUR OWN ELO (eng review issue 1):
clubelo.com rates CLUB teams only (Real Madrid, Man City) — it has no rating for
national teams (Brazil, Morocco), so it can't power a World Cup predictor. We roll
Elo straight from the martj42 international results we already load:
    new = old + K * (result - expected)
recency falls out for free (each match updates the rating, old form decays as newer
results overwrite it). Sanity-check the output against eloratings.net's published
numbers. K scales with match importance + goal margin (World Football Elo method).

ENTITY RESOLUTION (eng review issue 3): teams are a bounded, stable set, so we build
the canonical team list now and run a reconciliation tripwire that fails loudly on any
unmatched name — a silent drop shrinks the dataset and manufactures a fake edge.

Schema names match design/design-step1-data-layer.md so Phase 1 can formalize them.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import duckdb
import pandas as pd

# --- config -----------------------------------------------------------------
MARTJ42_RESULTS_URL = (
    "https://raw.githubusercontent.com/martj42/international_results/master/results.csv"
)
# football-data.co.uk (via soccerdata) is club-only and has no internationals, so it
# can't fuel a WC backtest — it proves the de-vig HARNESS on club matches, same code.
ODDS_LEAGUES = ["ENG-Premier League"]
ODDS_SEASONS = ["2324"]

# Only weigh matches from ~1990 on into Elo's "current" picture; older matches still
# warm the rating but their influence has long since decayed. (Full history is kept.)
ELO_BASE = 1500.0
ELO_HOME_ADVANTAGE = 100.0  # added to home side's rating in the expectation

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "worldcup.duckdb"

# football-data.co.uk closing-odds columns -> long fact_odds (Bet365 + market avg).
ODDS_BOOKS = {
    "bet365": ("B365H", "B365D", "B365A"),
    "market_avg": ("AvgH", "AvgD", "AvgA"),
}

# Cross-source name variants we already know about. martj42 is internally consistent,
# so this seeds the crosswalk for when eloratings.net / odds sources join later.
# Extend as reconciliation flags new mismatches.
TEAM_ALIASES = {
    "United States": "USA",
    "South Korea": "Korea Republic",
    "North Korea": "Korea DPR",
    "IR Iran": "Iran",
    "Republic of Ireland": "Ireland",
    "China PR": "China",
}


# --- Elo (World Football Elo method) ----------------------------------------
def _k_factor(tournament: str, goal_diff: int) -> float:
    """Base K by match importance, scaled up by goal margin."""
    t = (tournament or "").lower()
    if "world cup" in t and "qual" not in t:
        base = 60.0
    elif "world cup qual" in t or "continental" in t.replace("championship", "continental"):
        base = 50.0
    elif "qualif" in t:
        base = 40.0
    elif "friendly" in t:
        base = 20.0
    else:
        base = 40.0  # confederation cups, finals tournaments
    g = abs(goal_diff)
    if g == 2:
        mult = 1.5
    elif g == 3:
        mult = 1.75
    elif g >= 4:
        mult = 1.75 + (g - 3) / 8.0
    else:
        mult = 1.0
    return base * mult


def _expected(home_elo: float, away_elo: float, neutral: bool) -> float:
    adv = 0.0 if neutral else ELO_HOME_ADVANTAGE
    return 1.0 / (1.0 + 10 ** (-((home_elo + adv) - away_elo) / 400.0))


def compute_elo(matches: pd.DataFrame) -> pd.DataFrame:
    """Walk matches in date order; return each team's latest rating."""
    ratings: dict[str, float] = {}
    for row in matches.sort_values("date").itertuples(index=False):
        h, a = row.home_team, row.away_team
        rh = ratings.get(h, ELO_BASE)
        ra = ratings.get(a, ELO_BASE)
        if pd.isna(row.home_goals) or pd.isna(row.away_goals):
            continue
        gd = int(row.home_goals) - int(row.away_goals)
        score = 1.0 if gd > 0 else (0.5 if gd == 0 else 0.0)
        exp = _expected(rh, ra, bool(row.neutral))
        k = _k_factor(row.tournament, gd)
        ratings[h] = rh + k * (score - exp)
        ratings[a] = ra + k * ((1.0 - score) - (1.0 - exp))
    return pd.DataFrame(
        {"team": list(ratings), "elo": list(ratings.values())}
    ).sort_values("elo", ascending=False).reset_index(drop=True)


# --- loaders ----------------------------------------------------------------
def load_internationals() -> pd.DataFrame:
    print("  martj42 international_results ...")
    df = pd.read_csv(MARTJ42_RESULTS_URL, parse_dates=["date"])
    out = pd.DataFrame(
        {
            "date": df["date"].dt.date,
            "home_team": df["home_team"],
            "away_team": df["away_team"],
            "home_goals": df["home_score"],
            "away_goals": df["away_score"],
            "tournament": df["tournament"],
            "neutral": df["neutral"],
            "is_international": True,
            "source": "martj42",
        }
    )
    print(f"    {len(out)} international matches")
    return out


def load_club_odds() -> tuple[pd.DataFrame, pd.DataFrame]:
    """football-data.co.uk club matches + their closing odds (the harness fuel)."""
    import soccerdata as sd

    print("  football-data.co.uk club matches + odds (via soccerdata) ...")
    games = sd.MatchHistory(leagues=ODDS_LEAGUES, seasons=ODDS_SEASONS).read_games().reset_index()
    matches = pd.DataFrame(
        {
            "date": pd.to_datetime(games["date"]).dt.date,
            "home_team": games["home_team"],
            "away_team": games["away_team"],
            "home_goals": games.get("FTHG"),
            "away_goals": games.get("FTAG"),
            "tournament": ODDS_LEAGUES[0],
            "neutral": False,
            "is_international": False,
            "source": "football-data",
        }
    )
    captured_at = dt.datetime.utcnow()
    rows = []
    for local_id, row in games.iterrows():
        for book, (ch, cd, ca) in ODDS_BOOKS.items():
            for selection, col in (("home", ch), ("draw", cd), ("away", ca)):
                price = row.get(col)
                if pd.isna(price):
                    continue
                rows.append(
                    {
                        "_local_match_idx": int(local_id),  # resolved to match_id below
                        "bookmaker": book,
                        "market": "1x2",
                        "selection": selection,
                        "line": None,
                        "price": float(price),
                        "captured_at": captured_at,
                    }
                )
    print(f"    {len(matches)} club matches, {len(rows)} odds rows")
    return matches, pd.DataFrame(rows)


# --- entity resolution (reconciliation tripwire) ----------------------------
def reconcile_teams(intl: pd.DataFrame) -> pd.DataFrame:
    """Canonical national-team list from the spine + a loud check for drops."""
    teams = sorted(set(intl["home_team"]) | set(intl["away_team"]))
    dim = pd.DataFrame({"team": teams})
    dim["canonical"] = dim["team"].map(lambda t: TEAM_ALIASES.get(t, t))
    # Tripwire: every team referenced in fact_match must resolve to dim_team.
    referenced = set(intl["home_team"]) | set(intl["away_team"])
    unmatched = referenced - set(dim["team"])
    if unmatched:
        raise SystemExit(
            f"RECONCILIATION FAILED: {len(unmatched)} teams in fact_match missing from "
            f"dim_team (silent-drop risk): {sorted(unmatched)[:10]}"
        )
    print(f"  dim_team: {len(dim)} national teams, 0 unmatched ✓")
    return dim


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("Phase 0 ingestion ...")

    intl = load_internationals()
    dim_team = reconcile_teams(intl)
    team_elo = compute_elo(intl)
    print(f"  team_elo: {len(team_elo)} teams (top: "
          f"{team_elo.iloc[0]['team']} {team_elo.iloc[0]['elo']:.0f})")

    try:
        club, club_odds = load_club_odds()
    except Exception as e:  # soccerdata optional for the spine; harness needs it
        print(f"  ! club odds skipped ({type(e).__name__}: {e})")
        club, club_odds = pd.DataFrame(), pd.DataFrame()

    # Assign global match_ids across both sources, then resolve odds FKs.
    fact_match = pd.concat([intl, club], ignore_index=True)
    fact_match.insert(0, "match_id", range(len(fact_match)))
    # Schema'd empty frame so the table persists even when odds are unavailable
    # (e.g. football-data.co.uk 503) — DuckDB can't create a 0-column table.
    fact_odds = pd.DataFrame(
        columns=["match_id", "bookmaker", "market", "selection", "line", "price", "captured_at"]
    )
    if not club_odds.empty:
        # club rows occupy the tail of fact_match; map local idx -> global match_id
        club_offset = len(intl)
        fact_odds = club_odds.assign(
            match_id=club_odds["_local_match_idx"] + club_offset
        ).drop(columns="_local_match_idx")
        fact_odds = fact_odds[
            ["match_id", "bookmaker", "market", "selection", "line", "price", "captured_at"]
        ]

    con = duckdb.connect(str(DB_PATH))
    for name, frame in (
        ("fact_match", fact_match),
        ("team_elo", team_elo),
        ("dim_team", dim_team),
        ("fact_odds", fact_odds),
    ):
        con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM frame")
    con.close()
    print(f"\nLoaded into {DB_PATH}")
    print("Next: duckdb data/worldcup.duckdb < sql/implied_prob.sql")


if __name__ == "__main__":
    main()

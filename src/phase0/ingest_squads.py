"""National squads (the convocados) for the 2026 World Cup — the real prediction spine.

A World Cup match is between two 23-26 man squads, NOT between "all players of
nationality X". This pulls the official squad lists from Wikipedia (one table per
country: player, position, DOB, caps, goals, club) and builds:

    national_squad   one row per (country, player) — the called-up roster

This is the ground truth for "who is France". Club form (fact_player_season) attaches
to these players by name + DOB; squad players in leagues Understat doesn't cover
(Liga MX, MLS, Saudi, ...) will have a roster slot but no form yet — an honest gap.
"""

from __future__ import annotations

import io
import re
import urllib.request

import duckdb
import pandas as pd
from bs4 import BeautifulSoup

from ingest import DB_PATH

SQUADS_URL = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads"
MIN_SQUAD, MAX_SQUAD = 23, 26  # FIFA 2026 allows 23-26 players


def _clean(s: str) -> str:
    """Strip footnote markers [a]/[1], flag artifacts, and surrounding whitespace."""
    s = re.sub(r"\[[^\]]*\]", "", str(s))
    return re.sub(r"\s+", " ", s).strip()


def fetch_squads() -> pd.DataFrame:
    html = urllib.request.urlopen(
        urllib.request.Request(SQUADS_URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=30
    ).read().decode("utf-8", "ignore")
    soup = BeautifulSoup(html, "html.parser")

    rows = []
    for table in soup.find_all("table", class_="wikitable"):
        heading = table.find_previous(["h3", "h2"])
        country = _clean(heading.get_text()) if heading else "?"
        try:
            df = pd.read_html(io.StringIO(str(table)))[0]
        except ValueError:
            continue
        cols = [str(c) for c in df.columns]
        if not any("Player" in c for c in cols):
            continue
        if not (MIN_SQUAD <= len(df) <= MAX_SQUAD):  # drop summary/stat tables
            continue

        def col(name):
            hit = [c for c in df.columns if name in str(c)]
            return df[hit[0]] if hit else pd.Series([None] * len(df))

        dob_raw = col("Date of birth").astype(str)
        for i in range(len(df)):
            rows.append(
                {
                    "country": country,
                    "shirt_no": _clean(col("No.").iloc[i]),
                    "position": _clean(col("Pos.").iloc[i]),
                    "player": _clean(col("Player").iloc[i]),
                    "dob": (re.search(r"(\d{4}-\d{2}-\d{2})", dob_raw.iloc[i]) or [None, None])[1]
                    if re.search(r"(\d{4}-\d{2}-\d{2})", dob_raw.iloc[i]) else None,
                    "caps": pd.to_numeric(_clean(col("Caps").iloc[i]), errors="coerce"),
                    "intl_goals": pd.to_numeric(_clean(col("Goals").iloc[i]), errors="coerce"),
                    "club": _clean(col("Club").iloc[i]),
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    print("National squads: 2026 World Cup convocados (Wikipedia) ...")
    squads = fetch_squads()
    teams = squads["country"].nunique()
    print(f"  parsed {teams} squads, {len(squads)} players")
    sizes = squads.groupby("country").size()
    bad = sizes[(sizes < MIN_SQUAD) | (sizes > MAX_SQUAD)]
    if len(bad):
        print(f"  ! squads outside {MIN_SQUAD}-{MAX_SQUAD}: {bad.to_dict()}")

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE national_squad AS SELECT * FROM squads")
    con.execute("COPY (SELECT * FROM national_squad) TO 'data/csv/national_squad.csv' (HEADER)")
    con.close()
    print(f"  loaded national_squad ({len(squads)} rows) + exported CSV")
    print("\n  sample (Mexico):")
    for r in squads[squads["country"] == "Mexico"].head(6).itertuples(index=False):
        print(f"    {r.shirt_no:>2} {r.position:<3} {r.player:<24} {r.club}")


if __name__ == "__main__":
    main()

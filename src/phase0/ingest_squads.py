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


def _clean_player(s: str) -> str:
    """Player name without the Wikipedia role annotations that break name matching."""
    s = re.sub(r"\s*\((?:vice-?)?captain\)", "", _clean(s), flags=re.IGNORECASE)
    return s.strip()


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

        # Real birthdate lives in a hidden <span class="bday"> that read_html drops;
        # pull it straight from the table HTML, in player row order.
        bdays = [s.get_text(strip=True) for s in table.find_all("span", class_="bday")]
        for i in range(len(df)):
            rows.append(
                {
                    "country": country,
                    "shirt_no": _clean(col("No.").iloc[i]),
                    "position": _clean(col("Pos.").iloc[i]),
                    "player": _clean_player(col("Player").iloc[i]),
                    "dob": bdays[i] if i < len(bdays) else None,
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

    # Stable primary key for every squad player (the spine identity) — distinct from
    # the nullable player_id FK that only links to club-form data where we have it.
    squads = squads.sort_values(["country", "player"]).reset_index(drop=True)
    squads.insert(0, "squad_player_id", range(1, len(squads) + 1))

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE wc_squads AS SELECT * FROM squads")
    con.close()
    print(f"  loaded wc_squads ({len(squads)} rows)")
    print("\n  sample (Mexico):")
    for r in squads[squads["country"] == "Mexico"].head(6).itertuples(index=False):
        print(f"    {r.shirt_no:>2} {r.position:<3} {r.player:<24} {r.club}")


if __name__ == "__main__":
    main()

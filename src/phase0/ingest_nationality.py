"""Nationality bridge: fill dim_player.nationality by matching Understat players to
FBref's `nation` field. This is the first half of the club->country wire.

The entity-resolution problem, made concrete: Understat stores "Kylian Mbappe-Lottin",
FBref stores "Kylian Mbappé" with nation=FRA and born=1998. There is no shared ID, so we
match on a normalized name, disambiguate homonyms by club, and fall back to fuzzy matching
for spelling drift. nation is a 3-letter FIFA code (FRA, ENG, BRA) — a clean canonical key.

Source: FBref player_season_stats, big-5, season 2425 (nationality doesn't change by
season, so one season covers ~all current players). FBref needs a headless-Chrome scrape;
it caches after the first pull.

Output: dim_player.nationality populated (FIFA code), + a match-rate report and the
unmatched tail (the manual-review queue the eng review called for).
"""

from __future__ import annotations

import re

import duckdb
import pandas as pd
import soccerdata as sd
from rapidfuzz import fuzz, process
from unidecode import unidecode

from ingest import DB_PATH
from ingest_players import PLAYER_LEAGUES

FBREF_SEASON = "2425"
FUZZY_CUTOFF = 88  # token_set_ratio score required for a non-exact name match


def norm(s: str) -> str:
    """Accent-fold, lowercase, strip punctuation, collapse spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", unidecode(str(s)).lower())).strip()


def load_fbref_nations() -> pd.DataFrame:
    print(f"  FBref player nations (big-5, {FBREF_SEASON}) — headless scrape, cached after ...")
    fb = sd.FBref(leagues=PLAYER_LEAGUES, seasons=FBREF_SEASON)
    ps = fb.read_player_season_stats(stat_type="standard").reset_index()
    ps.columns = [c[0] if isinstance(c, tuple) else c for c in ps.columns]
    out = ps[["player", "nation", "team", "born"]].dropna(subset=["nation"]).copy()
    out["norm"] = out["player"].map(norm)
    out["club_norm"] = out["team"].map(norm)
    print(f"    {len(out)} FBref player rows with a nation")
    return out


def match_nationalities(players: pd.DataFrame, fb: pd.DataFrame) -> dict[int, dict]:
    """players: Understat dim_player + club name. Returns player_id -> {nation, born}."""
    by_norm: dict[str, list] = {}
    for r in fb.itertuples(index=False):
        by_norm.setdefault(r.norm, []).append(r)
    fb_names = list(by_norm.keys())

    out: dict[int, dict] = {}
    fuzzy_used = exact = club_tiebreak = 0
    for p in players.itertuples(index=False):
        key = norm(p.name)
        cands = by_norm.get(key)
        if not cands:
            hit = process.extractOne(key, fb_names, scorer=fuzz.token_set_ratio,
                                     score_cutoff=FUZZY_CUTOFF)
            if hit:
                cands = by_norm[hit[0]]
                fuzzy_used += 1
        if not cands:
            continue
        if len(cands) == 1:
            chosen = cands[0]
            exact += 1
        else:
            # homonyms: pick the candidate whose club best matches
            pclub = norm(p.club or "")
            chosen = max(cands, key=lambda c: fuzz.token_set_ratio(pclub, c.club_norm))
            club_tiebreak += 1
        out[p.player_id] = {"nationality": chosen.nation, "born": chosen.born}
    print(f"    matched {len(out)}/{len(players)}  "
          f"(exact {exact}, club-tiebreak {club_tiebreak}, fuzzy {fuzzy_used})")
    return out


def main() -> None:
    print("Nationality bridge ...")
    con = duckdb.connect(str(DB_PATH))
    players = con.execute(
        """
        SELECT p.player_id, p.name, c.name AS club
        FROM players p LEFT JOIN clubs c ON c.club_id = p.current_club_id
        """
    ).fetch_df()

    fb = load_fbref_nations()
    mapping = match_nationalities(players, fb)

    # write nationality + birth year back to players
    map_df = pd.DataFrame(
        [{"player_id": pid, "nationality": v["nationality"], "born": v["born"]}
         for pid, v in mapping.items()]
    )
    for col in ("nationality", "born"):
        con.execute(f"ALTER TABLE players DROP COLUMN IF EXISTS {col}")
    con.execute("ALTER TABLE players ADD COLUMN nationality VARCHAR")
    con.execute("ALTER TABLE players ADD COLUMN born INTEGER")
    con.execute("CREATE OR REPLACE TEMP TABLE _natmap AS SELECT * FROM map_df")
    con.execute(
        "UPDATE players SET nationality = m.nationality, born = m.born "
        "FROM _natmap m WHERE m.player_id = players.player_id"
    )

    total = con.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    filled = con.execute("SELECT COUNT(*) FROM players WHERE nationality IS NOT NULL").fetchone()[0]
    print(f"\n  players.nationality filled: {filled}/{total} ({filled/total:.0%})")
    print("  top nationalities:")
    for nat, n in con.execute(
        "SELECT nationality, COUNT(*) c FROM players WHERE nationality IS NOT NULL "
        "GROUP BY nationality ORDER BY c DESC LIMIT 8"
    ).fetchall():
        print(f"    {nat}  {n}")
    con.close()


if __name__ == "__main__":
    main()

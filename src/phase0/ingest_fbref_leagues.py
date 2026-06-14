"""Extra non-European leagues via FBref: Liga MX, MLS, Brazil, Saudi.

Understat only covers the big-5, so World Cup players at clubs like Inter Miami (MLS),
Al-Nassr (Saudi), or Cruz Azul (Liga MX) had no club form. FBref covers these leagues
(custom entries in ~/soccerdata/config/league_dict.json), so we pull them here.

HONEST LIMITATION: FBref has NO xG for these leagues — only goals, assists, minutes.
So these players get a goals/minutes form signal, not the richer xG the big-5 players
get. That asymmetry is real and the model should treat it as such (we know Mbappé's
chance quality; for Messi in MLS we only know goals).

Appends to the existing clubs / players / player_seasons tables with synthesized IDs
(offset so they never collide with Understat's IDs). Run AFTER ingest_nationality
(which recreates players) and BEFORE bridge_squad_form.
"""

from __future__ import annotations

import duckdb
import pandas as pd
import soccerdata as sd
from soccerdata import _config

from ingest import DB_PATH

# Register custom FBref leagues in-process (self-contained — no external
# ~/soccerdata config needed, so the repo reproduces anywhere). The FBref value
# must match FBref's exact competition_name.
CUSTOM_LEAGUES = {
    "MEX-Liga MX": {"FBref": "Liga MX", "season_start": "Jul", "season_end": "May"},
    "USA-Major League Soccer": {"FBref": "Major League Soccer", "season_start": "Feb", "season_end": "Dec"},
    "BRA-Serie A": {"FBref": "Campeonato Brasileiro Série A", "season_start": "Apr", "season_end": "Dec"},
    # NOTE: Saudi Pro League is unresolved — FBref via soccerdata rejects every name
    # variant tried ("Saudi Pro League", "Saudi Professional League", ...). Known gap;
    # affects mainly club form for players based in Saudi Arabia (e.g. Al-Nassr).
}
_config.LEAGUE_DICT.update(CUSTOM_LEAGUES)

# (league, season) — MLS/Brazil run on a single calendar year; Liga MX cross-year.
# All are tagged season='2526' in player_seasons = "current form" so the bridge
# (FORM_SEASON='2526') picks them up uniformly.
LEAGUE_SEASONS = [
    ("MEX-Liga MX", "2526"),
    ("USA-Major League Soccer", "2025"),
    ("BRA-Serie A", "2025"),
]
ID_OFFSET = 90_000_000  # synthetic IDs live far above Understat's range


def _col(df: pd.DataFrame, *path):
    """Fetch a column from FBref's MultiIndex headers.

    Single-name lookups (e.g. 'player') match a top-level column whose header is
    ('player', '') after reset_index; two-part lookups ('Performance','Gls') match
    the full tuple.
    """
    for c in df.columns:
        if isinstance(c, tuple):
            if len(path) == 1 and c[0] == path[0] and (len(c) < 2 or not str(c[1]) or c[1] == c[0]):
                return df[c]
            if len(path) == 2 and c[0] == path[0] and c[1] == path[1]:
                return df[c]
        elif len(path) == 1 and c == path[0]:
            return df[c]
    return pd.Series([None] * len(df))


def pull() -> pd.DataFrame:
    frames = []
    for league, season in LEAGUE_SEASONS:
        try:
            fb = sd.FBref(leagues=league, seasons=season)
            ps = fb.read_player_season_stats(stat_type="standard").reset_index()
            out = pd.DataFrame(
                {
                    "name": _col(ps, "player"),
                    "nationality": _col(ps, "nation"),
                    "club": _col(ps, "team"),
                    "born": pd.to_numeric(_col(ps, "born"), errors="coerce"),
                    "position": _col(ps, "pos"),
                    "league": league,
                    "appearances": pd.to_numeric(_col(ps, "Playing Time", "MP"), errors="coerce"),
                    "minutes": pd.to_numeric(_col(ps, "Playing Time", "Min"), errors="coerce"),
                    "goals": pd.to_numeric(_col(ps, "Performance", "Gls"), errors="coerce"),
                    "assists": pd.to_numeric(_col(ps, "Performance", "Ast"), errors="coerce"),
                }
            )
            frames.append(out.dropna(subset=["name", "club"]))
            print(f"  {league} {season}: {len(out)} players")
        except Exception as e:
            print(f"  ! {league} {season} skipped ({type(e).__name__}: {e})")
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def main() -> None:
    print("Extra leagues via FBref (no xG — goals/minutes only) ...")
    df = pull()
    if df.empty:
        print("  nothing pulled; aborting")
        return

    con = duckdb.connect(str(DB_PATH))

    # synthesize club IDs (one per distinct club name not already present)
    clubs = df[["club", "league"]].drop_duplicates("club").reset_index(drop=True)
    clubs["club_id"] = ID_OFFSET + clubs.index
    df = df.merge(clubs[["club", "club_id"]], on="club")

    # synthesize player IDs (one per distinct name+born)
    players = df.drop_duplicates(["name", "born"]).reset_index(drop=True).copy()
    players["player_id"] = ID_OFFSET + players.index
    df = df.merge(players[["name", "born", "player_id"]], on=["name", "born"])

    # append clubs
    clubs_out = clubs.rename(columns={"club": "name"})[["club_id", "name", "league"]]
    con.execute("INSERT INTO clubs SELECT club_id, name, league FROM clubs_out")

    # append players (match column order of the players table)
    players_out = players.assign(current_club_id=players["club_id"])[
        ["player_id", "name", "position", "current_club_id", "nationality", "born"]
    ]
    con.execute(
        "INSERT INTO players SELECT player_id, name, position, current_club_id, "
        "nationality, CAST(born AS INTEGER) FROM players_out"
    )

    # append player_seasons (xG-family columns are NULL — FBref lacks them here)
    seasons_out = df.assign(
        season="2526", np_goals=None, xg=None, np_xg=None, xa=None,
        shots=None, key_passes=None, xg_chain=None, xg_buildup=None,
    )[
        ["player_id", "season", "club_id", "league", "position", "appearances",
         "minutes", "goals", "xg", "np_goals", "np_xg", "assists", "xa", "shots",
         "key_passes", "xg_chain", "xg_buildup"]
    ]
    con.execute("INSERT INTO player_seasons SELECT * FROM seasons_out")

    print(f"\n  appended {len(clubs)} clubs, {len(players)} players, {len(df)} player-seasons")
    con.close()


if __name__ == "__main__":
    main()

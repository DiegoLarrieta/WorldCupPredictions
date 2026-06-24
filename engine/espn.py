"""Granular match stats from ESPN's open API — team + per-player shots.

ESPN's hidden site API needs no key and isn't Cloudflare-walled (unlike Sofascore /
Fotmob), and it carries exactly the signal the redirect cares about: per-player
totalShots + shotsOnTarget, plus team possession / shots / corners. That feeds two
things — calibration (did the model's goal expectation match reality) and, later, the
player shots-on-target PROP model. It is NOT a 1X2 feature (granular stats were
CI-disproven for the winner market; same data, correct target).

    from engine.espn import fetch_match_stats
    stats = fetch_match_stats("England", "Croatia", "2026-06-17")
    stats["team"]["home"]["shots_on_target"]   # 11
    stats["player_shots"]                       # [{player, side, shots, on_target, ...}, ...]

Network lives in fetch_scoreboard / fetch_summary; parsing is pure and CI-tested.
Team names are matched by sorted, accent-folded tokens, so 'Congo DR' (ESPN) lines up
with 'DR Congo' (ours).
"""

from __future__ import annotations

import datetime as _dt
import json
import urllib.request
from unidecode import unidecode

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
DEFAULT_LEAGUE = "fifa.world"   # FIFA World Cup

# ESPN per-team statistic name -> our key
_TEAM_MAP = {
    "possessionPct": "possession", "totalShots": "shots",
    "shotsOnTarget": "shots_on_target", "wonCorners": "corners",
    "foulsCommitted": "fouls", "saves": "saves", "offsides": "offsides",
    "yellowCards": "yellow_cards", "redCards": "red_cards",
}


class ESPNError(RuntimeError):
    pass


def _toks(name: str) -> frozenset:
    """Accent-folded, order-independent token set for team matching."""
    return frozenset(unidecode(str(name)).lower().replace("-", " ").split())


def _same(a: str, b: str) -> bool:
    return _toks(a) == _toks(b)


# ESPN's display names differ from ours for a few WC teams (full-name resolution).
_ESPN_ALIASES = {
    "czechia": "czech republic", "turkiye": "turkey", "korea republic": "south korea",
    "korea dpr": "north korea", "ir iran": "iran", "cabo verde": "cape verde",
}


def _canon(name: str) -> frozenset:
    s = " ".join(unidecode(str(name)).lower().replace("-", " ").replace("&", " ").split())
    return frozenset(_ESPN_ALIASES.get(s, s).split())


def _name_match(a: str, b: str) -> bool:
    """Alias-aware, accent-folded match; one token set may be a subset of the other
    (handles 'Bosnia-Herzegovina' vs 'Bosnia and Herzegovina')."""
    ta, tb = _canon(a), _canon(b)
    return bool(ta) and (ta == tb or ta <= tb or tb <= ta)


# ---- network --------------------------------------------------------------
def _get(url: str, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise ESPNError(f"ESPN HTTP {e.code} for {url}") from e
    except urllib.error.URLError as e:
        raise ESPNError(f"ESPN unreachable: {e.reason}") from e


def fetch_scoreboard(date: str, league: str = DEFAULT_LEAGUE) -> dict:
    """All games on a date. `date` is YYYY-MM-DD or YYYYMMDD."""
    d = date.replace("-", "")
    return _get(f"{ESPN_BASE}/{league}/scoreboard?dates={d}")


def fetch_summary(event_id: str, league: str = DEFAULT_LEAGUE) -> dict:
    return _get(f"{ESPN_BASE}/{league}/summary?event={event_id}")


# ---- parsing (pure, CI-safe) ----------------------------------------------
def find_event_id(scoreboard: dict, home: str, away: str) -> str:
    """Event id for our two teams on that date (order-, accent- and alias-independent)."""
    for ev in scoreboard.get("events", []):
        comps = (ev.get("competitions") or [{}])[0].get("competitors", [])
        names = [(c.get("team") or {}).get("displayName", "") for c in comps]
        if (any(_name_match(n, home) for n in names)
                and any(_name_match(n, away) for n in names)):
            return ev["id"]
    raise ESPNError(f"No ESPN event for {home} vs {away} on that date.")


def _stat_dict(stats: list[dict]) -> dict[str, str]:
    return {s["name"]: s.get("displayValue") for s in (stats or [])}


def parse_team_stats(summary: dict, home: str, away: str) -> dict:
    """Team-level stats mapped to our home/away (by team name)."""
    out: dict[str, dict] = {}
    for team in summary.get("boxscore", {}).get("teams", []):
        name = (team.get("team") or {}).get("displayName", "")
        side = "home" if _name_match(name, home) else "away" if _name_match(name, away) else None
        if not side:
            continue
        d = _stat_dict(team.get("statistics", []))
        out[side] = {our: _num(d[espn]) for espn, our in _TEAM_MAP.items() if espn in d}
    if "home" not in out or "away" not in out:
        raise ESPNError("Could not map ESPN team stats to home/away (name mismatch).")
    return out


def team_for_against(summary: dict, home: str, away: str) -> dict:
    """Per-side stats with FOR and AGAINST (against = the opponent's). The 'against'
    columns are the opponent-defense signal the prop model needs (a team that concedes
    many shots-on-target lifts the opposing players' prop probabilities)."""
    t = parse_team_stats(summary, home, away)
    h, a = t["home"], t["away"]
    def row(mine, opp):
        return {"possession": mine.get("possession"),
                "shots_for": mine.get("shots"), "sot_for": mine.get("shots_on_target"),
                "shots_against": opp.get("shots"), "sot_against": opp.get("shots_on_target"),
                "corners": mine.get("corners"), "fouls": mine.get("fouls"),
                "yellow_cards": mine.get("yellow_cards"), "red_cards": mine.get("red_cards")}
    return {"home": row(h, a), "away": row(a, h)}


MATCH_MINUTES = 90.0   # regulation baseline for per-90 normalisation (stoppage ignored)


def player_minutes(summary: dict) -> dict[str, float]:
    """Minutes played per athlete id, derived from starter/sub flags + substitution clocks.

    starter & not subbed off -> 90; starter subbed off -> off-minute; came on -> 90 - on-minute;
    unused -> 0. Lets shot rates be per-90 and catches rotation (the dominant prop input).
    """
    sub_min: dict[str, float] = {}
    for e in summary.get("keyEvents", []):
        if (e.get("type") or {}).get("type") != "substitution":
            continue
        clk = (e.get("clock") or {}).get("value")
        minute = (float(clk) / 60.0) if clk not in (None, "") else None
        if minute is None:
            continue
        for part in e.get("participants", []):
            aid = (part.get("athlete") or {}).get("id")
            if aid:
                sub_min[aid] = minute
    out: dict[str, float] = {}
    for team in summary.get("rosters", []):
        for p in (team.get("roster") or []):
            aid = (p.get("athlete") or {}).get("id")
            if not aid:
                continue
            starter, sin, sout = bool(p.get("starter")), bool(p.get("subbedIn")), bool(p.get("subbedOut"))
            m = sub_min.get(aid)
            if starter and not sout:
                out[aid] = MATCH_MINUTES
            elif starter and sout:
                out[aid] = min(m, MATCH_MINUTES) if m is not None else MATCH_MINUTES
            elif sin:
                out[aid] = max(MATCH_MINUTES - m, 0.0) if m is not None else 30.0
            else:
                out[aid] = 0.0
    return out


def parse_player_shots(summary: dict, home: str, away: str) -> list[dict]:
    """Per-player shots / SoT / goals / assists / minutes (+ per-90), only players who shot."""
    mins = player_minutes(summary)
    rows = []
    for team in summary.get("rosters", []):
        name = (team.get("team") or {}).get("displayName", "")
        side = "home" if _name_match(name, home) else "away" if _name_match(name, away) else None
        if not side:
            continue
        for p in (team.get("roster") or []):
            d = _stat_dict(p.get("stats", []))
            shots = _num(d.get("totalShots"))
            sot = _num(d.get("shotsOnTarget"))
            if not shots and not sot:
                continue
            aid = (p.get("athlete") or {}).get("id")
            played = mins.get(aid, MATCH_MINUTES) or 0.0
            scale = (MATCH_MINUTES / played) if played else None
            rows.append({
                "player": (p.get("athlete") or {}).get("displayName"),
                "side": side, "team": name,
                "shots": shots, "on_target": sot,
                "goals": _num(d.get("totalGoals")), "assists": _num(d.get("goalAssists")),
                "minutes": round(played, 1), "starter": bool(p.get("starter")),
                "shots_p90": round((shots or 0) * scale, 2) if scale else None,
                "sot_p90": round((sot or 0) * scale, 2) if scale else None,
            })
    rows.sort(key=lambda r: (-(r["shots"] or 0), -(r["on_target"] or 0)))
    return rows


def _num(v):
    if v in (None, ""):
        return None
    try:
        f = float(str(v).replace("%", ""))
        return int(f) if f.is_integer() else f
    except ValueError:
        return v


def match_result(home: str, away: str, date: str, league: str = DEFAULT_LEAGUE) -> dict:
    """Final score for our two teams from ESPN — reaches arbitrarily far back (unlike the
    Odds API /scores 3-day window). Searches `date` ±1 because ESPN dates by US timezone
    (off-by-one for late kickoffs). Same shape as odds_api.parse_score:
    {completed, home_goals, away_goals}."""
    d0 = _dt.date.fromisoformat(date)
    for off in (0, -1, 1):
        day = (d0 + _dt.timedelta(days=off)).isoformat()
        for ev in fetch_scoreboard(day, league).get("events", []):
            comp = (ev.get("competitions") or [{}])[0]
            comps = comp.get("competitors", [])
            names = [(c.get("team") or {}).get("displayName", "") for c in comps]
            if not (any(_name_match(n, home) for n in names)
                    and any(_name_match(n, away) for n in names)):
                continue
            st = (comp.get("status") or ev.get("status") or {}).get("type", {})
            goals = {}
            for c, nm in zip(comps, names):
                side = "home" if _name_match(nm, home) else "away" if _name_match(nm, away) else None
                if side:
                    goals[side] = _num(c.get("score"))
            return {"completed": bool(st.get("completed")),
                    "home_goals": goals.get("home"), "away_goals": goals.get("away")}
    raise ESPNError(f"No ESPN event for {home} vs {away} near {date}.")


def lineups(home: str, away: str, date: str, league: str = DEFAULT_LEAGUE) -> list[tuple[str, str]]:
    """Confirmed XI from ESPN as [(player_display_name, 'start'|'bench')] for both teams.
    Posted ~1h before kickoff; returns [] if not announced yet. Searches date ±1."""
    d0 = _dt.date.fromisoformat(date)
    for off in (0, -1, 1):
        day = (d0 + _dt.timedelta(days=off)).isoformat()
        try:
            eid = find_event_id(fetch_scoreboard(day, league), home, away)
        except ESPNError:
            continue
        s = fetch_summary(eid, league)
        out = []
        for team in s.get("rosters", []):
            for p in (team.get("roster") or []):
                nm = (p.get("athlete") or {}).get("displayName")
                if nm:
                    out.append((nm, "start" if p.get("starter") else "bench"))
        if out:
            return out
    return []


# ---- convenience ----------------------------------------------------------
def fetch_match_stats(home: str, away: str, date: str, league: str = DEFAULT_LEAGUE) -> dict:
    """One call: scoreboard -> event id -> summary -> {team, player_shots}. Searches
    `date` ±1 (ESPN dates by US timezone, off-by-one for late kickoffs)."""
    d0 = _dt.date.fromisoformat(date)
    for off in (0, -1, 1):
        day = (d0 + _dt.timedelta(days=off)).isoformat()
        try:
            eid = find_event_id(fetch_scoreboard(day, league), home, away)
        except ESPNError:
            continue
        s = fetch_summary(eid, league)
        return {"event_id": eid, "team": parse_team_stats(s, home, away),
                "player_shots": parse_player_shots(s, home, away)}
    raise ESPNError(f"No ESPN event for {home} vs {away} near {date}.")

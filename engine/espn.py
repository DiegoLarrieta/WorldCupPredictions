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
    """Event id for our two teams on that date (order- and accent-independent)."""
    want = {_toks(home), _toks(away)}
    for ev in scoreboard.get("events", []):
        comps = (ev.get("competitions") or [{}])[0].get("competitors", [])
        names = {_toks((c.get("team") or {}).get("displayName", "")) for c in comps}
        if names == want:
            return ev["id"]
    raise ESPNError(f"No ESPN event for {home} vs {away} on that date.")


def _stat_dict(stats: list[dict]) -> dict[str, str]:
    return {s["name"]: s.get("displayValue") for s in (stats or [])}


def parse_team_stats(summary: dict, home: str, away: str) -> dict:
    """Team-level stats mapped to our home/away (by team name)."""
    out: dict[str, dict] = {}
    for team in summary.get("boxscore", {}).get("teams", []):
        name = (team.get("team") or {}).get("displayName", "")
        side = "home" if _same(name, home) else "away" if _same(name, away) else None
        if not side:
            continue
        d = _stat_dict(team.get("statistics", []))
        out[side] = {our: _num(d[espn]) for espn, our in _TEAM_MAP.items() if espn in d}
    if "home" not in out or "away" not in out:
        raise ESPNError("Could not map ESPN team stats to home/away (name mismatch).")
    return out


def parse_player_shots(summary: dict, home: str, away: str) -> list[dict]:
    """Per-player shots / shots-on-target / goals / assists, only players who shot."""
    rows = []
    for team in summary.get("rosters", []):
        name = (team.get("team") or {}).get("displayName", "")
        side = "home" if _same(name, home) else "away" if _same(name, away) else None
        if not side:
            continue
        for p in (team.get("roster") or []):
            d = _stat_dict(p.get("stats", []))
            shots = _num(d.get("totalShots"))
            sot = _num(d.get("shotsOnTarget"))
            if not shots and not sot:
                continue
            rows.append({
                "player": (p.get("athlete") or {}).get("displayName"),
                "side": side, "team": name,
                "shots": shots, "on_target": sot,
                "goals": _num(d.get("totalGoals")), "assists": _num(d.get("goalAssists")),
                "starter": bool(p.get("starter")),
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


# ---- convenience ----------------------------------------------------------
def fetch_match_stats(home: str, away: str, date: str, league: str = DEFAULT_LEAGUE) -> dict:
    """One call: scoreboard -> event id -> summary -> {team, player_shots}."""
    eid = find_event_id(fetch_scoreboard(date, league), home, away)
    s = fetch_summary(eid, league)
    return {"event_id": eid, "team": parse_team_stats(s, home, away),
            "player_shots": parse_player_shots(s, home, away)}

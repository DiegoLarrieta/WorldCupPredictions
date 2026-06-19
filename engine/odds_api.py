"""Fetch a fixture's odds from The Odds API, in the shape engine.market wants.

The model-vs-market core (engine.market) needs prices. This module pulls them
automatically for a World Cup fixture instead of pasting them by hand:

    from engine.odds_api import fetch_odds
    from engine.market import compare_folder
    odds = fetch_odds("Iraq", "Norway")          # {'1x2': {...}, 'ou_2.5': {...}}
    compare_folder("predictions/ira-nor", odds)  # writes market_compare.{json,md}

Set the key once:  export ODDS_API_KEY=...   (free tier ~500 req/mo at the-odds-api.com)

Design notes:
  - Network lives in fetch_events() only; parsing (extract_odds / find_event) is pure
    so it is CI-safe and unit-tested against captured JSON, no key or network needed.
  - Outcomes are mapped to home/away by TEAM NAME, not the API's home/away role, so a
    neutral-venue fixture whose nominal home differs from ours still lines up with the
    prediction's home/away ordering.
  - book='best' takes the best (highest) price per selection across books — that is the
    price a value bettor would actually take. Pass a book key (e.g. 'pinnacle') for a
    single sharp book when you want a closing-line proxy instead.
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from unidecode import unidecode

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
DEFAULT_SPORT = "soccer_fifa_world_cup"   # The Odds API key for the FIFA World Cup
DEFAULT_REGIONS = "eu,uk"
DEFAULT_TOTALS_POINT = 2.5                # matches the model's over_under_2_5


class OddsAPIError(RuntimeError):
    """Raised when the API call fails or a fixture/market can't be found."""


def _norm(name: str) -> str:
    """Normalise a team name for matching (accent-fold, lowercase, trim)."""
    return unidecode(str(name)).strip().lower()


# Team names that differ across sources (our warehouse / martj42 vs The Odds API).
# Each group maps to one canonical token so 'United States' (ours) == 'USA' (API).
_ALIAS_GROUPS = [
    {"united states", "usa"},
    {"south korea", "korea republic"},
    {"ivory coast", "cote d'ivoire"},
    {"dr congo", "congo dr"},
    {"czechia", "czech republic"},
]


def _canon(name: str) -> str:
    """Canonical key for a team name, collapsing known cross-source aliases."""
    n = _norm(name)
    for g in _ALIAS_GROUPS:
        if n in g:
            return min(g)
    return n


# ---- network (the only impure part) ---------------------------------------
def fetch_events(api_key: str | None = None, *, sport: str = DEFAULT_SPORT,
                 regions: str = DEFAULT_REGIONS, markets: str = "h2h,totals",
                 timeout: int = 30) -> list[dict]:
    """Hit The Odds API and return the raw list of events (with bookmaker odds)."""
    api_key = api_key or os.environ.get("ODDS_API_KEY")
    if not api_key:
        raise OddsAPIError("No API key. Set ODDS_API_KEY or pass api_key=...")
    q = urllib.parse.urlencode({
        "apiKey": api_key, "regions": regions, "markets": markets,
        "oddsFormat": "decimal", "dateFormat": "iso",
    })
    url = f"{ODDS_API_BASE}/sports/{sport}/odds?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "worldcup-predictor"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")[:300]
        raise OddsAPIError(f"Odds API HTTP {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise OddsAPIError(f"Odds API unreachable: {e.reason}") from e


# ---- parsing (pure, CI-safe) ----------------------------------------------
def find_event(events: list[dict], home: str, away: str) -> dict:
    """Find the event for our two teams (order-independent, accent-insensitive)."""
    want = {_canon(home), _canon(away)}
    for ev in events:
        if {_canon(ev.get("home_team", "")), _canon(ev.get("away_team", ""))} == want:
            return ev
    raise OddsAPIError(f"No upcoming event for {home} vs {away} (not listed / wrong sport key).")


def _best_across_books(event: dict, market_key: str) -> list[dict]:
    """Best (highest) price per outcome across every book offering this market.

    Outcomes keyed by (name, point) so totals lines don't collide. Returns the
    underlying API outcome dicts with the winning price.
    """
    best: dict[tuple, dict] = {}
    for bk in event.get("bookmakers", []):
        for mk in bk.get("markets", []):
            if mk.get("key") != market_key:
                continue
            for o in mk.get("outcomes", []):
                key = (_norm(o["name"]), o.get("point"))
                if key not in best or o["price"] > best[key]["price"]:
                    best[key] = o
    return list(best.values())


def _book_outcomes(event: dict, market_key: str, book: str) -> list[dict]:
    """Outcomes for a single named bookmaker; [] if the book doesn't offer this market.

    Non-fatal so a book with only h2h (e.g. Pinnacle without a totals line) still yields
    its 1X2. extract_odds raises only if NO market is usable for the book.
    """
    for bk in event.get("bookmakers", []):
        if bk.get("key") == book or _norm(bk.get("title", "")) == _norm(book):
            for mk in bk.get("markets", []):
                if mk.get("key") == market_key:
                    return mk.get("outcomes", [])
    return []


def extract_odds(event: dict, home: str, away: str, *, book: str = "best",
                 totals_point: float = DEFAULT_TOTALS_POINT) -> dict:
    """Turn one API event into the {'1x2': {...}, 'ou_2.5': {...}} compare() shape.

    Markets that aren't offered are simply omitted (no crash) so a fixture with only
    h2h still produces a usable 1x2 comparison.
    """
    odds: dict[str, dict[str, float]] = {}

    # 1X2 (h2h): map by team name to our home/away, plus Draw.
    h2h = _best_across_books(event, "h2h") if book == "best" else _book_outcomes(event, "h2h", book)
    by_name = {_norm(o["name"]): o["price"] for o in h2h}
    if {_norm(home), _norm(away), "draw"} <= set(by_name):
        odds["1x2"] = {"home": by_name[_norm(home)], "draw": by_name["draw"],
                       "away": by_name[_norm(away)]}

    # Totals at the requested point (default 2.5).
    totals = _best_across_books(event, "totals") if book == "best" else _book_outcomes(event, "totals", book)
    line = {o["name"].lower(): o["price"] for o in totals if _matches_point(o.get("point"), totals_point)}
    if "over" in line and "under" in line:
        odds[f"ou_{totals_point}"] = {"over": line["over"], "under": line["under"]}

    if not odds:
        raise OddsAPIError("Event found but no usable h2h/totals odds in it.")
    return odds


def _matches_point(point, target: float) -> bool:
    try:
        return abs(float(point) - float(target)) < 1e-6
    except (TypeError, ValueError):
        return False


# ---- player props ---------------------------------------------------------
DEFAULT_PROP_MARKET = "player_shots_on_target"


def fetch_event_list(api_key: str | None = None, *, sport: str = DEFAULT_SPORT,
                     timeout: int = 30) -> list[dict]:
    """Upcoming fixtures (id, teams, kickoff) — the /events endpoint, costs 0 credits."""
    api_key = api_key or os.environ.get("ODDS_API_KEY")
    if not api_key:
        raise OddsAPIError("No API key. Set ODDS_API_KEY or pass api_key=...")
    url = f"{ODDS_API_BASE}/sports/{sport}/events?apiKey={api_key}&dateFormat=iso"
    req = urllib.request.Request(url, headers={"User-Agent": "worldcup-predictor"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise OddsAPIError(f"Odds API HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    except urllib.error.URLError as e:
        raise OddsAPIError(f"Odds API unreachable: {e.reason}") from e


def fetch_event_odds(event_id: str, *, markets: str, regions: str = "us",
                     api_key: str | None = None, sport: str = DEFAULT_SPORT,
                     timeout: int = 30) -> dict:
    """Per-event odds (the endpoint player props live on). Costs ~1 credit per market."""
    api_key = api_key or os.environ.get("ODDS_API_KEY")
    if not api_key:
        raise OddsAPIError("No API key. Set ODDS_API_KEY or pass api_key=...")
    q = urllib.parse.urlencode({"apiKey": api_key, "regions": regions, "markets": markets,
                                "oddsFormat": "decimal", "dateFormat": "iso"})
    url = f"{ODDS_API_BASE}/sports/{sport}/events/{event_id}/odds?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "worldcup-predictor"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise OddsAPIError(f"Odds API HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    except urllib.error.URLError as e:
        raise OddsAPIError(f"Odds API unreachable: {e.reason}") from e


def parse_player_props(event: dict, market: str = DEFAULT_PROP_MARKET, book: str = "best") -> list[dict]:
    """Per-event player-prop odds -> one row per (player, line): best over/under price.

    book='best' takes the best (highest) price per side across books — the price a value
    bettor would actually take. Pass a book key (e.g. 'fanduel') for a single book.
    """
    agg: dict[tuple, dict] = {}
    for bk in event.get("bookmakers", []):
        if book != "best" and not (bk.get("key") == book or _norm(bk.get("title", "")) == _norm(book)):
            continue
        for mk in bk.get("markets", []):
            if mk.get("key") != market:
                continue
            for o in mk.get("outcomes", []):
                player, side, point = o.get("description"), str(o.get("name", "")).lower(), o.get("point")
                if player is None or side not in ("over", "under"):
                    continue
                key = (player, point)
                agg.setdefault(key, {"over": [], "under": []})[side].append(float(o["price"]))
    rows = []
    for (player, point), d in agg.items():
        rows.append({"player": player, "line": point,
                     "over_price": max(d["over"]) if d["over"] else None,
                     "under_price": max(d["under"]) if d["under"] else None})
    rows.sort(key=lambda r: r["player"] or "")
    return rows


def fetch_player_props(home: str, away: str, *, market: str = DEFAULT_PROP_MARKET,
                       book: str = "best", regions: str = "us", api_key: str | None = None,
                       sport: str = DEFAULT_SPORT) -> list[dict]:
    """One call: find the fixture's event id, fetch its prop odds, return parsed rows."""
    eid = find_event(fetch_event_list(api_key, sport=sport), home, away)["id"]
    ev = fetch_event_odds(eid, markets=market, regions=regions, api_key=api_key, sport=sport)
    return parse_player_props(ev, market, book)


# ---- scores / results -----------------------------------------------------
def fetch_scores(api_key: str | None = None, *, sport: str = DEFAULT_SPORT,
                 days_from: int = 3, timeout: int = 30) -> list[dict]:
    """Recent + live games with scores. Free tier allows days_from up to 3."""
    api_key = api_key or os.environ.get("ODDS_API_KEY")
    if not api_key:
        raise OddsAPIError("No API key. Set ODDS_API_KEY or pass api_key=...")
    q = urllib.parse.urlencode({"apiKey": api_key, "daysFrom": days_from, "dateFormat": "iso"})
    url = f"{ODDS_API_BASE}/sports/{sport}/scores?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": "worldcup-predictor"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise OddsAPIError(f"Odds API HTTP {e.code}: {e.read().decode(errors='replace')[:300]}") from e
    except urllib.error.URLError as e:
        raise OddsAPIError(f"Odds API unreachable: {e.reason}") from e


def parse_score(event: dict, home: str, away: str) -> dict:
    """Map a /scores event to OUR home/away goals (by team name, role-independent).

    Returns {'completed': bool, 'home_goals': int|None, 'away_goals': int|None}. Goals
    are None until the game is completed (live games carry partial scores we ignore).
    """
    if not event.get("completed"):
        return {"completed": False, "home_goals": None, "away_goals": None}
    by_name = {_norm(s["name"]): int(s["score"]) for s in (event.get("scores") or [])}
    h, a = _norm(home), _norm(away)
    if h not in by_name or a not in by_name:
        raise OddsAPIError(f"Score for {home}/{away} not found in event.")
    return {"completed": True, "home_goals": by_name[h], "away_goals": by_name[a]}


# ---- snapshots (open -> close capture) ------------------------------------
def snapshot_rows(events: list[dict], books=("pinnacle", "best"),
                  captured_at: str | None = None, totals_point: float = DEFAULT_TOTALS_POINT) -> list[dict]:
    """Flatten current odds for every listed fixture into snapshot rows for CLOV capture.

    One row per (match, market, selection, book). Captures a SHARP book (Pinnacle, the
    closing-line reference) and 'best' (where you'd actually place) so honest CLOV is
    possible later. Append these to a log over time to build open->close movement.
    """
    import datetime as dt
    ts = captured_at or dt.datetime.now().astimezone().isoformat(timespec="seconds")
    rows = []
    for ev in events:
        home, away = ev.get("home_team", ""), ev.get("away_team", "")
        match = f"{home} vs {away}"
        for book in books:
            try:
                odds = extract_odds(ev, home, away, book=book, totals_point=totals_point)
            except OddsAPIError:
                continue
            for market, sels in odds.items():
                for selection, price in sels.items():
                    rows.append({"match": match, "commence_time": ev.get("commence_time"),
                                 "market": market, "selection": selection, "book": book,
                                 "price": price, "captured_at": ts})
    return rows


# ---- convenience ----------------------------------------------------------
def fetch_odds(home: str, away: str, *, book: str = "best", api_key: str | None = None,
               sport: str = DEFAULT_SPORT, regions: str = DEFAULT_REGIONS,
               totals_point: float = DEFAULT_TOTALS_POINT) -> dict:
    """One call: fetch events, find our fixture, return compare()-ready odds."""
    events = fetch_events(api_key, sport=sport, regions=regions)
    event = find_event(events, home, away)
    return extract_odds(event, home, away, book=book, totals_point=totals_point)

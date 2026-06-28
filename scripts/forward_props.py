#!/usr/bin/env python3
"""Full forwards prop table: every forward of both teams × {total shots, shots on target}.

Where /prop-bets surfaces only the value-overs that pass the CLOV filter, this builds the
COMPLETE picture analyze_match shows: each FORWARD of both squads, with whatever lines the
book actually offers for **total shots** (`player_shots`) and **shots on target**
(`player_shots_on_target`) — a star striker is quoted o2.5 shots, a role player o0.5, so we
show the line the book sets, not a fixed one. Model P(over) reuses the same Gamma-Poisson
prop model (engine.props.prop_at_least) on the player's shot rate (total) or SoT rate.

Honest scope unchanged from /prop-bets: US prop books are one-sided (over-only), so EV is
model-vs-vigged-price, not de-vigged value. Value flags are CANDIDATES judged by CLOV, not
proven edge. This module only widens the *display* to all forwards + both markets.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from engine.espn import ESPNError, lineups as fetch_lineups
from engine.odds_api import OddsAPIError, fetch_player_props
from engine.props import prop_at_least
from scripts.prop_bets import (RATES_CSV, START_MIN, BENCH_MIN, _norm, _toks,
                               _squad_ids, _lineup_status)

# The two prop markets, in display order, with the rate column each one models against.
MARKETS = [("tiros", "player_shots", "shot_rate"),
           ("a puerta", "player_shots_on_target", "sot_per90")]


def _rate_rows(only_ids: set | None):
    """[(norm_name, tokenset, record)] sorted by minutes desc, where record carries the
    position + both shot rates + typical minutes + player_id (for team assignment)."""
    df = pd.read_csv(RATES_CSV).sort_values("mins", ascending=False)
    if only_ids is not None:
        df = df[df["player_id"].isin(only_ids)]
    rows = []
    for _, r in df.iterrows():
        mpa = float(r["min_per_app"]) if pd.notna(r.get("min_per_app")) else None
        rec = {"pos": r.get("pos"), "shot_rate": float(r["shot_rate"]),
               "sot_per90": float(r["sot_per90"]), "mpa": mpa,
               "player_id": int(r["player_id"]) if pd.notna(r.get("player_id")) else None}
        rows.append((_norm(r["name"]), _toks(r["name"]), rec))
    return rows


def _match(player: str, rows: list):
    """Exact normalized match, else the best token-subset match scored by token OVERLAP.
    Scoring by overlap (not bare subset) stops a long book name like 'Luis Fernando Diaz
    Marulanda' from being thrown out as ambiguous just because a one-token 'Fernando' also
    sits inside it: 'Luis Diaz' overlaps 2 tokens, 'Fernando' only 1, so Díaz wins. Still
    returns None when the top overlap is a genuine tie between different players."""
    k = _norm(player)
    for nm, _tk, rec in rows:
        if nm == k:
            return rec
    bt = _toks(player)
    if not bt:
        return None
    scored = [(len(tk & bt), nm, rec) for nm, tk, rec in rows if tk and (tk <= bt or bt <= tk)]
    if not scored:
        return None
    best = max(s[0] for s in scored)
    top = [(nm, rec) for ov, nm, rec in scored if ov == best]
    names = {nm for nm, _ in top}
    return top[0][1] if len(names) == 1 else None        # rows sorted by mins -> best first


def forward_prop_table(home: str, away: str, as_of: str, *, book: str = "best",
                       opp: float = 1.0) -> tuple[list[dict], str | None, dict[str, str]]:
    """Returns (rows, note, excluded). One row per (forward, market, line) the book offers,
    with the model's P(over), the offered over price, and EV = model·price − 1. Forwards only
    (pos FW), both teams. `note` is set (rows empty) when nothing is available; `excluded` maps
    quoted players we dropped -> why (non-FW position, or no shot-rate data)."""
    if not RATES_CSV.exists():
        return [], "prop model missing — run scripts/build_prop_model.py", {}

    home_ids, away_ids = _squad_ids(home, home), _squad_ids(away, away)
    pool_ids = (home_ids | away_ids) or None
    rate_rows = _rate_rows(pool_ids)
    fallback_rows = _rate_rows(None)                       # global, for names outside the squad table

    lineup_toks = []
    try:
        lineup_toks = [(_toks(nm), st) for nm, st in fetch_lineups(home, away, as_of)]
    except ESPNError:
        pass

    # Pull both prop markets; tolerate one being absent for a fixture.
    quotes: dict[str, list] = {}
    for _lab, mkt, _col in MARKETS:
        try:
            quotes[mkt] = fetch_player_props(home, away, market=mkt, book=book)
        except OddsAPIError:
            quotes[mkt] = []
    if not any(quotes.values()):
        return [], "no player props listed for this fixture", {}

    out: list[dict] = []
    excluded: dict[str, str] = {}      # quoted player -> reason dropped (so nothing vanishes silently)
    for label, mkt, rate_col in MARKETS:
        for p in quotes.get(mkt, []):
            if p.get("line") is None or p.get("over_price") is None:
                continue
            rec = _match(p["player"], rate_rows) or _match(p["player"], fallback_rows)
            if rec is None:                                     # no shot-rate data to model with
                excluded.setdefault(p["player"], "sin datos de tiros")
                continue
            if str(rec.get("pos")) != "FW":                    # forwards only (user's choice)
                excluded.setdefault(p["player"], f"pos {rec.get('pos')}")
                continue
            status = _lineup_status(p["player"], lineup_toks) if lineup_toks else None
            if status == "start":
                exp_min = START_MIN
            elif status == "bench":
                exp_min = BENCH_MIN
            else:
                exp_min = min(max(rec["mpa"], 30.0), 90.0) if rec["mpa"] else 80.0
            need = math.ceil(p["line"])                          # over 1.5 -> need >= 2
            model_over = prop_at_least(rec[rate_col], need, expected_minutes=exp_min,
                                       opponent_factor=opp)
            ev = model_over * p["over_price"] - 1.0
            pid = rec.get("player_id")
            team = home if pid in home_ids else away if pid in away_ids else "?"
            out.append({"player": p["player"], "team": team, "market": label, "line": p["line"],
                        "model_over": round(model_over, 3), "over_price": p["over_price"],
                        "ev": round(ev, 3), "lineup": status or "n/a",
                        # value = model beats the vigged price AND is a coin-flip-or-better call
                        # (a big EV on a sub-50% longshot is model error per CLAUDE.md).
                        "value": ev > 0 and model_over >= 0.5})
    # sort: team, player, market (tiros before a puerta), line
    order = {"tiros": 0, "a puerta": 1}
    out.sort(key=lambda r: (r["team"], r["player"], order[r["market"]], r["line"]))
    # surface dropped-but-quoted players: a real striker mislabeled MF (e.g. Shomurodov) or an
    # uncovered league shows up here, not silently — so the FW filter's blind spots stay visible.
    note = None if out else "no forwards with a quoted prop line"
    return out, note, excluded

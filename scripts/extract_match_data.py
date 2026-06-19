#!/usr/bin/env python3
"""Extract granular stats from every WC match into model-ready datasets (ESPN, free).

The scoreline barely predicts the future; the underlying numbers do. This walks ESPN's
scoreboard day by day, and for each completed match writes two datasets:

  data/csv/derived/match_team_stats.csv   — per team per match, FOR and AGAINST:
      possession, shots_for/against, sot_for/against, corners, fouls, cards
  data/csv/derived/player_match_shots.csv — per player per match:
      minutes, shots, shots_on_target, shots_p90, sot_p90, goals, assists

'against' is the opponent-defense signal for props; per-90 normalises for minutes (the
dominant prop input). Rebuilt fresh each run (idempotent).

    .venv/bin/python scripts/extract_match_data.py --from 2026-06-11 --to 2026-06-30

No key needed (ESPN is open). xG is NOT here — ESPN doesn't carry it; that's the separate
heavier FBref/Sofascore decision.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.espn import (ESPNError, fetch_scoreboard, fetch_summary,  # noqa: E402
                         parse_player_shots, team_for_against)

TEAM_CSV = Path("data/csv/derived/match_team_stats.csv")
PLAYER_CSV = Path("data/csv/derived/player_match_shots.csv")
TEAM_FIELDS = ["date", "match", "team", "opponent", "side", "possession",
               "shots_for", "sot_for", "shots_against", "sot_against",
               "corners", "fouls", "yellow_cards", "red_cards"]
PLAYER_FIELDS = ["date", "match", "team", "side", "player", "minutes",
                 "shots", "on_target", "shots_p90", "sot_p90", "goals", "assists"]


def _dates(start: str, end: str):
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    while d0 <= d1:
        yield d0.isoformat()
        d0 += dt.timedelta(days=1)


def _completed(ev: dict) -> bool:
    comp = (ev.get("competitions") or [{}])[0]
    st = (comp.get("status") or ev.get("status") or {}).get("type", {})
    return bool(st.get("completed"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="start", default="2026-06-11")
    ap.add_argument("--to", dest="end", default=dt.date.today().isoformat())
    args = ap.parse_args()

    team_rows, player_rows, seen, n_matches = [], [], set(), 0
    for day in _dates(args.start, args.end):
        try:
            sb = fetch_scoreboard(day)
        except ESPNError:
            continue
        for ev in sb.get("events", []):
            if not _completed(ev) or ev["id"] in seen:
                continue
            seen.add(ev["id"])
            comps = (ev.get("competitions") or [{}])[0].get("competitors", [])
            names = {c.get("homeAway"): (c.get("team") or {}).get("displayName") for c in comps}
            home, away = names.get("home"), names.get("away")
            if not home or not away:
                continue
            try:
                s = fetch_summary(ev["id"])
                fa = team_for_against(s, home, away)
                ps = parse_player_shots(s, home, away)
            except ESPNError:
                continue
            match = f"{home} vs {away}"
            for side, opp in (("home", away), ("away", home)):
                team = home if side == "home" else away
                team_rows.append({"date": day, "match": match, "team": team, "opponent": opp,
                                  "side": side, **fa[side]})
            for p in ps:
                player_rows.append({"date": day, "match": match,
                                    **{k: p.get(k) for k in
                                       ("team", "side", "player", "minutes", "shots",
                                        "on_target", "shots_p90", "sot_p90", "goals", "assists")}})
            n_matches += 1

    _write(TEAM_CSV, TEAM_FIELDS, team_rows)
    _write(PLAYER_CSV, PLAYER_FIELDS, player_rows)
    print(f"Extracted {n_matches} matches: {len(team_rows)} team rows -> {TEAM_CSV}, "
          f"{len(player_rows)} player-shot rows -> {PLAYER_CSV}")
    if player_rows:
        top = sorted(player_rows, key=lambda r: -(r["sot_p90"] or 0))[:5]
        print("Top SoT/90 (single match, min-adjusted):")
        for r in top:
            print(f"  {r['player']:22s} {r['on_target']} OT in {r['minutes']:.0f}' "
                  f"-> {r['sot_p90']}/90  ({r['match']})")


def _write(path: Path, fields, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()

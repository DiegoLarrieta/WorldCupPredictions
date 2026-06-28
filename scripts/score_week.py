#!/usr/bin/env python3
"""Score a whole week of predictions against real results, in one shot.

    python scripts/score_week.py                       # predictions/week1, auto-fetch results
    python scripts/score_week.py predictions/week1 --stage group
    python scripts/score_week.py --no-refresh          # score but don't touch ratings

For every match folder under the week dir that has a prediction.json, this:
  1. pulls the finished result from The Odds API /scores (matched by team name),
  2. scores the FROZEN prediction (engine.feedback.record_outcome),
  3. feeds the result into the warehouse so the NEXT prediction's rating replay
     reflects it (idempotent; --no-refresh to skip),
and then refreshes the tournament monitor.

Needs ODDS_API_KEY. The /scores free tier only reaches ~3 days back, so run it close
to the matches. For a result outside that window, score it by hand with
scripts/record_match.py instead.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.espn import ESPNError, match_result
from engine.feedback import monitor, record_outcome
from engine.odds_api import OddsAPIError, fetch_scores, find_event, parse_score
from engine.warehouse import append_from_record


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("week_dir", nargs="?", default="predictions/week1")
    ap.add_argument("--stage", default=None,
                    help="round label written into each record (default auto: '16 knockout' "
                         "for predictions/16round/ paths, else 'group')")
    ap.add_argument("--days-from", type=int, default=3, help="/scores lookback (free tier max 3)")
    ap.add_argument("--source", default="oddsapi", choices=["oddsapi", "espn"],
                    help="result source: oddsapi /scores (~3d window) or espn (reaches back, "
                         "uses each prediction's as_of date)")
    ap.add_argument("--no-refresh", action="store_true", help="don't feed results into the warehouse")
    ap.add_argument("--no-monitor", action="store_true")
    args = ap.parse_args()

    week = Path(args.week_dir)
    # round label: explicit --stage wins; else derive from the path so knockout folders are
    # tagged "16 knockout" automatically (no flag to remember each round).
    stage = args.stage or ("16 knockout" if "16round" in str(week) else "group")
    # recurse: folders may be flat (week/<slug>) or nested by group (week/groupX/<slug>)
    folders = sorted(p.parent for p in week.glob("**/prediction.json"))
    if not folders:
        sys.exit(f"No prediction.json under {week}/")

    events = None
    if args.source == "oddsapi":
        try:
            events = fetch_scores(days_from=args.days_from)
        except OddsAPIError as e:
            sys.exit(f"Could not fetch scores: {e}")

    scored, skipped = 0, []
    for folder in folders:
        pred = json.loads((folder / "prediction.json").read_text())
        home, away = pred["match"].split(" vs ")
        try:
            if args.source == "espn":
                sc = match_result(home, away, pred["as_of"])
            else:
                sc = parse_score(find_event(events, home, away), home, away)
        except (OddsAPIError, ESPNError):
            skipped.append((folder.name, "no result found"))
            continue
        if not sc["completed"]:
            skipped.append((folder.name, "not finished yet"))
            continue

        rec = record_outcome(folder, sc["home_goals"], sc["away_goals"],
                             stage=stage, source=f"{args.source}-scores")
        s, fr = rec["scores"], rec["prediction"]
        print(f"{fr['match']}: {sc['home_goals']}-{sc['away_goals']} "
              f"({rec['outcome']['spine']['result']}) — we gave the actual outcome "
              f"{fr['ensemble'][s['y']]:.0%}, RPS {s['rps']:.4f}, surprisal {s['surprisal']:.2f}")
        if not args.no_refresh:
            append_from_record(rec)
        scored += 1

    print(f"\nScored {scored}/{len(folders)} match(es)"
          + (f"; ratings refreshed in the warehouse" if not args.no_refresh else ""))
    for name, why in skipped:
        print(f"  skipped {name}: {why}")

    if scored and not args.no_monitor:
        m = monitor()
        pm, base = m["per_model"], m["vs_baseline"]
        print(f"\nTournament so far: {m['n']} scored. Ensemble RPS {pm['ensemble']['rps']:.4f} "
              f"vs uniform {base['uniform']['rps']:.4f} "
              f"(beats components: {'yes' if m['ensemble_beats_components'] else 'NO'}). "
              f"See data/worldcupmatches/_monitor.md")


if __name__ == "__main__":
    main()

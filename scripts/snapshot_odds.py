#!/usr/bin/env python3
"""Snapshot current WC odds to a log — run repeatedly to capture open -> close movement.

Each run appends one timestamped row per (match, market, selection, book) for the SHARP
book (Pinnacle, the closing-line reference) and 'best' (where you'd actually place). Run it
on a schedule (e.g. daily, then again right before kickoff via /loop or cron); the last
snapshot before a match is its closing line. engine.clov grades bets against that close.

    .venv/bin/python scripts/snapshot_odds.py

Appends to data/csv/derived/odds_snapshots.csv. Needs ODDS_API_KEY.
This is the honest-CLOV plumbing: capture now, because the closing line can't be recovered
later (every kickoff missed is a CLOV data point gone for 4 years).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.odds_api import OddsAPIError, fetch_events, snapshot_rows

LOG = Path("data/csv/derived/odds_snapshots.csv")
FIELDS = ["match", "commence_time", "market", "selection", "book", "price", "captured_at"]


def main() -> None:
    try:
        events = fetch_events(markets="h2h,totals")
    except OddsAPIError as e:
        sys.exit(f"Could not fetch odds: {e}")

    rows = snapshot_rows(events, books=("pinnacle", "best"))
    if not rows:
        sys.exit("No odds rows captured (no fixtures listed, or no pinnacle/best prices).")

    LOG.parent.mkdir(parents=True, exist_ok=True)
    new = not LOG.exists()
    with open(LOG, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerows(rows)

    ts = rows[0]["captured_at"]
    matches = len({r["match"] for r in rows})
    print(f"Snapshotted {len(rows)} rows across {matches} fixtures at {ts} -> {LOG}")
    print("Run again closer to kickoff; the last snapshot before a match is its closing line.")


if __name__ == "__main__":
    main()

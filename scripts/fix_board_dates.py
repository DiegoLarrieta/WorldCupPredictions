#!/usr/bin/env python3
"""Rectify every board fixture's date from its authoritative source: the prediction's as_of.

The board used to guess each match's date by loose team-name overlap against the odds
snapshot, which mis-assigned dates (e.g. 'South Africa vs South Korea' inherited 'South Africa
vs Canada''s date — both share 'south africa'). The real date lives in each
predictions/**/prediction.json `as_of`. This walks the board, overwrites date/kickoff from the
matching prediction's as_of (keeping the time only when the old kickoff was already on the
right date), and rewrites daily_board.json. No API, no network — safe to re-run.
"""

from __future__ import annotations

import glob
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "data" / "csv" / "derived" / "daily_board.json"


def main() -> None:
    asof = {}
    for f in glob.glob(str(ROOT / "predictions/**/prediction.json"), recursive=True):
        d = json.loads(Path(f).read_text())
        if d.get("match") and d.get("as_of"):
            asof[d["match"]] = d["as_of"]

    board = json.loads(BOARD.read_text())
    fixed = []
    for r in board:
        a = asof.get(r["match"])
        if not a or r.get("date") == a:
            continue
        ko = r.get("kickoff", "")
        time = ko[11:16] if ko[:10] == a else ""        # keep time only if it was the right day
        fixed.append((r["match"], r.get("date"), a))
        r["date"] = a
        r["kickoff"] = f"{a} {time}".strip()

    BOARD.write_text(json.dumps(board, indent=1, ensure_ascii=False))
    print(f"Rectified {len(fixed)} date(s):")
    for m, old, new in fixed:
        print(f"  {old} -> {new}  {m}")


if __name__ == "__main__":
    main()

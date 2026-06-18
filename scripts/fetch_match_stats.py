#!/usr/bin/env python3
"""Backfill granular stats (team + per-player shots) onto scored matches, from ESPN.

    python scripts/fetch_match_stats.py                 # predictions/week1
    python scripts/fetch_match_stats.py predictions/week1

For every prediction in the week dir that already has a worldcupmatches record, this
pulls team stats (possession, shots, SoT, corners) and per-player shots/shots-on-target
from ESPN's open API, attaches them to the record's rich layer (engine.feedback.
backfill_rich, source='espn'), and rebuilds data/csv/derived/player_match_shots.csv —
the raw material for the player shots-on-target PROP model.

This data is for calibration + the prop/goals markets, NOT the 1X2 model (granular
stats were CI-disproven for the winner market). No key needed; ESPN is open.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.espn import ESPNError, fetch_match_stats
from engine.feedback import DATASET_DIR, backfill_rich, match_key

SHOTS_CSV = Path("data/csv/derived/player_match_shots.csv")
_SHOT_FIELDS = ["match_key", "date", "match", "side", "team", "player",
                "shots", "on_target", "goals", "assists", "starter"]


def _flatten_team(team: dict) -> dict:
    flat = {}
    for side in ("home", "away"):
        for k, v in team.get(side, {}).items():
            flat[f"{k}_{side}"] = v
    return flat


def rebuild_shots_csv(csv_path: Path = SHOTS_CSV) -> int:
    """Rebuild the player-shots table from every record's rich.player_shots (idempotent)."""
    rows = []
    for p in sorted(DATASET_DIR.glob("*.json")):
        if p.name.startswith("_"):
            continue
        rec = json.loads(p.read_text())
        rich = (rec.get("outcome") or {}).get("rich") or {}
        idn = rec["identity"]
        for ps in rich.get("player_shots", []):
            rows.append({"match_key": rec["match_key"], "date": idn.get("date"),
                         "match": rec["prediction"]["match"], **{k: ps.get(k) for k in
                         ("side", "team", "player", "shots", "on_target", "goals",
                          "assists", "starter")}})
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_SHOT_FIELDS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("week_dir", nargs="?", default="predictions/week1")
    args = ap.parse_args()

    folders = sorted(p.parent for p in Path(args.week_dir).glob("*/prediction.json"))
    if not folders:
        sys.exit(f"No prediction.json under {args.week_dir}/")

    done, skipped = 0, []
    for folder in folders:
        pred = json.loads((folder / "prediction.json").read_text())
        home, away = pred["match"].split(" vs ")
        date = pred["as_of"]
        key = match_key(date, home, away)
        if not (DATASET_DIR / f"{key}.json").exists():
            skipped.append((folder.name, "not scored yet — run score_week.py first"))
            continue
        try:
            st = fetch_match_stats(home, away, date)
        except ESPNError as e:
            skipped.append((folder.name, str(e)))
            continue
        backfill_rich(key, source="espn", espn_event_id=st["event_id"],
                      player_shots=st["player_shots"], **_flatten_team(st["team"]))
        t = st["team"]
        top = st["player_shots"][0] if st["player_shots"] else None
        print(f"{pred['match']}: shots {t['home'].get('shots')}-{t['away'].get('shots')}, "
              f"on target {t['home'].get('shots_on_target')}-{t['away'].get('shots_on_target')}, "
              f"poss {t['home'].get('possession')}-{t['away'].get('possession')}"
              + (f"  | top shooter: {top['player']} {top['shots']} ({top['on_target']} OT)" if top else ""))
        done += 1

    n = rebuild_shots_csv()
    print(f"\nBackfilled {done}/{len(folders)} match(es); {n} player-shot rows -> {SHOTS_CSV}")
    for name, why in skipped:
        print(f"  skipped {name}: {why}")


if __name__ == "__main__":
    main()

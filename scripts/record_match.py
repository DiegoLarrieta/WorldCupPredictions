#!/usr/bin/env python3
"""Live-night entry: score a finished match the moment it ends.

    python scripts/record_match.py predictions/ira-nor 0 2 --stage group --group E
    python scripts/record_match.py predictions/ira-nor 0 2 --stage group --group E \
        --xg-home 0.7 --xg-away 2.4 --poss-home 41 --monitor

Writes the canonical record under data/worldcupmatches/, fills actual_result in the
match folder, scores the prediction, and (with --monitor) refreshes the tournament roll-up.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.feedback import monitor, record_outcome


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("match_dir", help="prediction folder, e.g. predictions/ira-nor")
    ap.add_argument("home_goals", type=int)
    ap.add_argument("away_goals", type=int)
    ap.add_argument("--stage", required=True,
                    choices=["group", "r32", "r16", "qf", "sf", "final", "third_place"])
    ap.add_argument("--group", default=None, help="group letter A..L (group stage only)")
    ap.add_argument("--venue", default=None)
    ap.add_argument("--source", default="manual", choices=["manual", "martj42", "fbref"])
    # optional rich stats (everything you have to hand on the night)
    ap.add_argument("--xg-home", type=float, default=None)
    ap.add_argument("--xg-away", type=float, default=None)
    ap.add_argument("--poss-home", type=float, default=None)
    ap.add_argument("--poss-away", type=float, default=None)
    ap.add_argument("--monitor", action="store_true", help="refresh the tournament roll-up after")
    args = ap.parse_args()

    extra = {k: v for k, v in {
        "xg_home": args.xg_home, "xg_away": args.xg_away,
        "possession_home": args.poss_home, "possession_away": args.poss_away,
    }.items() if v is not None} or None

    rec = record_outcome(args.match_dir, args.home_goals, args.away_goals,
                         stage=args.stage, group=args.group, venue=args.venue,
                         extra=extra, source=args.source)
    sc, pr = rec["scores"], rec["prediction"]
    p_actual = pr["ensemble"][sc["y"]]
    print(f"{pr['match']}: {args.home_goals}-{args.away_goals} ({rec['outcome']['spine']['result']})")
    print(f"  we gave the actual outcome {p_actual:.0%}  |  "
          f"RPS {sc['rps']:.4f}  log-loss {sc['log_loss']:.4f}  "
          f"Brier {sc['brier']:.4f}  surprisal {sc['surprisal']:.2f}")
    print(f"  record: data/worldcupmatches/{rec['match_key']}.json")

    if args.monitor:
        s = monitor()
        print(f"\nTournament: {s['n']} scored. Ensemble RPS "
              f"{s['per_model']['ensemble']['rps']:.4f} "
              f"(uniform baseline {s['vs_baseline']['uniform']['rps']:.4f}). "
              f"See data/worldcupmatches/_monitor.md")


if __name__ == "__main__":
    main()

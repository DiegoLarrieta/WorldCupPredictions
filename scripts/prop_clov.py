#!/usr/bin/env python3
"""Pick the model's most confident shots-on-target OVERS for a fixture and (optionally)
log them as CLOV bets.

Why overs only: US/UK/EU books quote SoT props over-only (no under), so the line can't be
de-vigged and a pre-bet 'value' flag is impossible (a big EV on a one-sided longshot is
model error, not edge). The honest test is CLOV — bet the overs the model is most
CONFIDENT in (not the highest-EV longshots), capture the closing over-price, and let the
close judge us. Per the scorecard, CLOV is the leading edge indicator, no de-vig needed.

Selection: rows where the model is MORE bullish than the offered (vig-included) over
price — model_over * over_price > 1 (EV>0) — with guards against the one-sided-longshot
trap: a model_over floor (--min) and a line cap (--max-line). Betting a short favourite
the market rates above us is taking the worse side; we only bet where we disagree UPWARD.
Excludes players with no real club shot data (shot_rate_raw=NaN -> position prior only).
Sorted by EV at the taken price.

    .venv/bin/python scripts/prop_clov.py predictions/week3/groupD/sco-bra          # dry-run
    .venv/bin/python scripts/prop_clov.py predictions/week3/groupD/sco-bra --log --stake 1

Run prop_bets.py first (writes prop_compare.json). Closing capture: re-run prop_bets near
kickoff and settle with that over-price as closing_odds (engine.betlog.settle -> CLOV).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.betlog import log_bet
from scripts.prop_bets import _norm, _toks   # reuse the same name normaliser/tokeniser

RATES_CSV = Path("data/csv/derived/player_shot_rates.csv")


def _real_data_names() -> list[tuple[frozenset, bool]]:
    """[(token_set, has_real_shot_data)] — has_real = shot_rate_raw is not NaN."""
    df = pd.read_csv(RATES_CSV).sort_values("mins", ascending=False)
    return [(_toks(r["name"]), pd.notna(r["shot_rate_raw"])) for _, r in df.iterrows()]


def _has_real_data(player: str, table) -> bool:
    bt = _toks(player)
    if not bt:
        return False
    cands = [real for tk, real in table if tk and (tk <= bt or bt <= tk)]
    return bool(cands) and any(cands)        # matched a row that had real shot data


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("match_dir")
    ap.add_argument("--min", type=float, default=0.5, help="model P(over) floor (longshot guard)")
    ap.add_argument("--max-line", type=float, default=1.5, help="skip lines above this")
    ap.add_argument("--edge", type=float, default=0.0, help="min EV at the taken price (model>price)")
    ap.add_argument("--top", type=int, default=5, help="how many to take")
    ap.add_argument("--stake", type=float, default=1.0, help="paper stake per bet")
    ap.add_argument("--book", default="best")
    ap.add_argument("--log", action="store_true", help="actually write to the ledger")
    args = ap.parse_args()

    folder = Path(args.match_dir)
    cmp = json.loads((folder / "prop_compare.json").read_text())
    table = _real_data_names()

    cands = []
    for r in cmp["rows"]:
        if r.get("over_price") is None or r.get("model_over") is None:
            continue
        if r["model_over"] < args.min or r["line"] > args.max_line:
            continue
        ev = r["model_over"] * r["over_price"] - 1.0          # EV at the offered price
        if ev <= args.edge:                                   # model must beat the vigged price
            continue
        if not _has_real_data(r["player"], table):
            continue
        cands.append({**r, "ev_taken": ev})
    cands.sort(key=lambda r: -r["ev_taken"])
    cands = cands[: args.top]

    match = cmp["match"]
    if not cands:
        print(f"{match}: no confident overs among real-data players "
              f"(model_over >= {args.min}, line <= {args.max_line}).")
        return

    print(f"{match} — {len(cands)} CLOV over candidate(s) "
          f"({'LOGGING' if args.log else 'dry-run'}):")
    for r in cands:
        line = f"sot_o{r['line']}"
        sel = f"{r['player']} over {r['line']}"
        implied = 1.0 / r["over_price"]
        print(f"  {r['player']:22s} over {r['line']} @ {r['over_price']:.2f}  "
              f"model {r['model_over']:.0%} vs price {implied:.0%}  "
              f"EV +{r['ev_taken']:.2f}  SoT/90 {r['sot_per90']:.2f}")
        if args.log:
            bet = log_bet(match, line, sel, odds_taken=r["over_price"],
                          model_prob=r["model_over"], stake=args.stake, book=args.book)
            print(f"      -> logged bet #{bet['bet_id']}")
    if not args.log:
        print("  (dry-run — re-run with --log --stake N to record these as paper bets)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Player shots-on-target prop bets: model vs market, end to end.

Closes the prop loop. For a fixture it: pulls player shots-on-target prop odds (The Odds
API, US books), looks up each player's shrunk shot rate (the prop model), computes our
P(player goes over the line), de-vigs the market over/under, and reports edge + EV with
value flags. Writes prop_compare.{json,md} into the match folder.

    .venv/bin/python scripts/prop_bets.py predictions/week2/usa-aus

Needs ODDS_API_KEY and data/csv/derived/player_shot_rates.csv (run build_prop_model.py).

HONEST: these are CANDIDATE bets, not proven edge. US prop books are soft, which is why
this is worth doing — but the prop model is unvalidated against these lines. Log what you
bet (/log-bet) and let CLOV judge it. Expect mostly "no bet"; that's correct.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.market import prop_ev                                   # noqa: E402
from engine.odds_api import OddsAPIError, fetch_player_props        # noqa: E402
from engine.props import prop_at_least                              # noqa: E402

RATES_CSV = Path("data/csv/derived/player_shot_rates.csv")


def _norm(s: str) -> str:
    from unidecode import unidecode
    return unidecode(str(s)).strip().lower()


def _rate_lookup() -> dict[str, float]:
    """Name -> shrunk shots-on-target/90, keeping the highest-minutes row per player."""
    df = pd.read_csv(RATES_CSV)
    df = df.sort_values("mins", ascending=False)
    out = {}
    for _, r in df.iterrows():
        k = _norm(r["name"])
        if k not in out:                       # first = most minutes (most reliable)
            out[k] = float(r["sot_per90"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("match_dir", help="folder with prediction.json (gives home/away)")
    ap.add_argument("--book", default="best")
    ap.add_argument("--minutes", type=float, default=90.0, help="expected minutes (lower for subs)")
    ap.add_argument("--opp", type=float, default=1.0, help="opponent-defense factor (1.0=avg)")
    ap.add_argument("--threshold", type=float, default=0.03, help="EV threshold to flag value")
    args = ap.parse_args()

    folder = Path(args.match_dir)
    pred = json.loads((folder / "prediction.json").read_text())
    home, away = pred["match"].split(" vs ")

    if not RATES_CSV.exists():
        sys.exit(f"{RATES_CSV} missing — run scripts/build_prop_model.py first.")
    rates = _rate_lookup()

    try:
        props = fetch_player_props(home, away, book=args.book)
    except OddsAPIError as e:
        sys.exit(f"Could not fetch player props: {e}")
    if not props:
        sys.exit("No player shots-on-target props listed for this fixture yet.")

    rows, unmatched = [], []
    for p in props:
        rate = rates.get(_norm(p["player"]))
        if rate is None:
            unmatched.append(p["player"])
            continue
        if p["line"] is None or p["over_price"] is None:
            continue
        need = math.ceil(p["line"])                 # over 1.5 -> need >= 2 SoT
        model_over = prop_at_least(rate, need, expected_minutes=args.minutes, opponent_factor=args.opp)
        ev = prop_ev(model_over, p["over_price"], p.get("under_price"), ev_threshold=args.threshold)
        b = ev["best"]
        rows.append({"player": p["player"], "line": p["line"], "need_sot": need,
                     "sot_per90": round(rate, 2), "model_over": round(model_over, 3),
                     "over_price": p["over_price"], "under_price": p.get("under_price"),
                     "best_side": b["side"], "market_prob": b["market_prob"],
                     "edge": b["edge"], "ev_per_unit": b["ev_per_unit"], "value": ev["value"]})

    rows.sort(key=lambda r: r["ev_per_unit"], reverse=True)
    value = [r for r in rows if r["value"]]
    out = {"match": pred["match"], "market": "player_shots_on_target",
           "expected_minutes": args.minutes, "opponent_factor": args.opp,
           "rows": rows, "value_bets": value, "unmatched_players": unmatched}
    (folder / "prop_compare.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    (folder / "prop_compare.md").write_text(_md(out))

    print(f"{pred['match']} — {len(rows)} players priced, {len(value)} value bet(s):")
    for r in (value or rows[:5]):
        price = r["over_price"] if r["best_side"] == "over" else r["under_price"]
        mp = f"{r['market_prob']:.0%}" if r["market_prob"] is not None else "n/a"
        print(f"  {r['player']:22s} {r['best_side']} {r['line']} SoT @ {price:.2f}  "
              f"model {r['model_over']:.0%} mkt {mp}  EV {r['ev_per_unit']:+.2f}"
              f"{'  <-- VALUE' if r['value'] else ''}")
    if unmatched:
        print(f"  ({len(unmatched)} players had no shot-rate match: {', '.join(unmatched[:6])}"
              f"{'...' if len(unmatched) > 6 else ''})")
    print(f"  -> {folder}/prop_compare.md")


def _md(o: dict) -> str:
    L = [f"# Player shots-on-target props: {o['match']}", "",
         f"_Model P(over) from shrunk shot rates (expected {o['expected_minutes']:.0f} min, "
         f"opponent factor {o['opponent_factor']}). Market de-vigged (Shin). Value = EV >= 3%. "
         f"Candidate bets, not proven edge — log what you bet and let CLOV judge._", "",
         "| Player | Line | Model P(over) | Market | Edge | Over | Under | Best | EV/1u | Value |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in o["rows"]:
        flag = "✅" if r["value"] else ""
        mp = f"{r['market_prob']:.0%}" if r["market_prob"] is not None else "—"
        ed = f"{r['edge']:+.0%}" if r["edge"] is not None else "—"
        un = f"{r['under_price']:.2f}" if r["under_price"] is not None else "—"
        L.append(f"| {r['player']} | {r['line']} | {r['model_over']:.0%} | {mp} | {ed} | "
                 f"{r['over_price']:.2f} | {un} | {r['best_side']} | {r['ev_per_unit']:+.2f} | {flag} |")
    if o["value_bets"]:
        L += ["", "## Value bets", ""]
        for r in o["value_bets"]:
            price = r["over_price"] if r["best_side"] == "over" else r["under_price"]
            mp = f"{r['market_prob']:.0%}" if r["market_prob"] is not None else "n/a (one-sided)"
            L.append(f"- **{r['player']} {r['best_side']} {r['line']} SoT** @ {price:.2f} — "
                     f"model {r['model_over']:.0%} vs market {mp}, EV {r['ev_per_unit']:+.2f}/1u")
    else:
        one_sided = sum(1 for r in o["rows"] if r["market_prob"] is None)
        L += ["", f"_No value bets. {one_sided}/{len(o['rows'])} lines were one-sided "
              "(over-only, no under to de-vig) — shown but never flagged, since a big EV on an "
              "un-de-viggable longshot is almost always model error, not edge. Two-sided lines "
              "that cleared the threshold: none._"]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()

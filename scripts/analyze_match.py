#!/usr/bin/env python3
"""Analyze a fixture end-to-end into ONE readable analysis.md — the document you read to
decide what to bet and why.

It surfaces the model's probability for every market (1X2, goal lines O/U 1.5/2.5/3.5,
BTTS, player shots-on-target) next to the market price, applies the honest discipline
(sharp-vs-soft for 1X2/goals; CLOV-on-overs for props), and writes the recommendation +
the reasoning + the caveats.

    .venv/bin/python scripts/analyze_match.py predictions/<week>/<grp>/<slug>            # live
    .venv/bin/python scripts/analyze_match.py predictions/<...> --source snapshot         # backtest
    .venv/bin/python scripts/analyze_match.py predictions/<...> --source snapshot --reveal # + result

Modes:
  live (default) — fetch sharp (Pinnacle) + soft (best) odds and player props live.
  snapshot       — rebuild odds from the last PRE-KICKOFF snapshot in odds_snapshots.csv,
                   for a leakage-free backtest of a finished game (the model already only
                   sees data before as_of). Props weren't snapshotted, so they're skipped.
  --reveal       — also read the real result (ESPN) and grade what we'd have bet. Omit it
                   to keep the backtest blind.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.market import compare_lines               # noqa: E402
from scripts.prop_clov import _real_data_names, _has_real_data  # noqa: E402

SNAP = Path("data/csv/derived/odds_snapshots.csv")
GOAL_LINES = (1.5, 2.5, 3.5)


def poisson_over(total_lambda: float, line: float) -> float:
    """P(total goals > line) with total ~ Poisson(lh+la). Matches the published O/U 2.5."""
    need = math.floor(line) + 1                        # over 2.5 -> need >= 3
    cdf = sum(math.exp(-total_lambda) * total_lambda ** k / math.factorial(k)
              for k in range(need))
    return round(1.0 - cdf, 3)


def _snapshot_odds(match_key: str):
    """Rebuild {book: {market: {sel: price}}} from the last pre-kickoff snapshot."""
    rows = [r for r in csv.DictReader(open(SNAP)) if match_key in r["match"]]
    if not rows:
        return {}, {}, None
    last = max(r["captured_at"] for r in rows)
    rows = [r for r in rows if r["captured_at"] == last]
    books = defaultdict(lambda: defaultdict(dict))
    for r in rows:
        books[r["book"]][r["market"]][r["selection"]] = float(r["price"])
    return dict(books.get("pinnacle", {})), dict(books.get("best", {})), last


def _prop_candidates(folder: Path):
    """Run prop_bets live, then the CLOV-over selection. Returns (candidates, note)."""
    r = subprocess.run([sys.executable, "scripts/prop_bets.py", str(folder), "--lineups"],
                       capture_output=True, text=True)
    pc = folder / "prop_compare.json"
    if not pc.exists():
        return [], "no props listed for this fixture"
    cmp = json.loads(pc.read_text())
    table = _real_data_names()
    out = []
    for row in cmp["rows"]:
        if row.get("over_price") is None or row.get("model_over") is None:
            continue
        if row["model_over"] < 0.5 or row["line"] > 1.5:
            continue
        ev = row["model_over"] * row["over_price"] - 1.0
        if ev <= 0 or not _has_real_data(row["player"], table):
            continue
        out.append({**row, "ev": ev})
    out.sort(key=lambda r: -r["ev"])
    return out[:5], None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--source", choices=["live", "snapshot"], default="live")
    ap.add_argument("--reveal", action="store_true")
    args = ap.parse_args()

    folder = Path(args.folder)
    pred = json.loads((folder / "prediction.json").read_text())
    home, away = pred["match"].split(" vs ")
    e = pred["win_draw_loss"]["ENSEMBLE"]
    eg = pred["expected_goals"]
    tot_lambda = float(eg[home]) + float(eg[away])

    # --- odds ---
    snap_ts = None
    if args.source == "snapshot":
        key = home.split()[0] if len(home.split()[0]) > 3 else away.split()[0]
        sharp, soft, snap_ts = _snapshot_odds(key)
    else:
        from engine.odds_api import fetch_odds, OddsAPIError
        try:
            sharp = fetch_odds(home, away, book="pinnacle")
            soft = fetch_odds(home, away, book="best")
        except OddsAPIError as ex:
            sharp, soft = {}, {}
            print(f"odds fetch failed: {ex}")

    market = compare_lines(pred, sharp, soft) if sharp else None

    # --- props (live only) ---
    props, prop_note = ([], "skipped (snapshot backtest — props weren't captured)")
    if args.source == "live":
        props, prop_note = _prop_candidates(folder)

    # --- result (reveal) ---
    result = None
    if args.reveal:
        from engine.espn import match_result, ESPNError
        try:
            result = match_result(home, away, pred["as_of"])
        except ESPNError:
            result = None

    md = _render(pred, e, eg, tot_lambda, market, props, prop_note, result, args, snap_ts)
    (folder / "analysis.md").write_text(md)
    print(f"-> {folder/'analysis.md'}")
    print(md)


def _render(pred, e, eg, tot_lambda, market, props, prop_note, result, args, snap_ts) -> str:
    home, away = pred["match"].split(" vs ")
    L = [f"# Analysis — {pred['match']}", "",
         f"_as_of {pred['as_of']} · source: {args.source}"
         + (f" (snapshot {snap_ts})" if snap_ts else "") + "_", ""]

    # 1X2
    L += ["## 1X2 (match winner)", "",
          f"- Model: **{home} {e[home]:.0%}** · Draw {e['Draw']:.0%} · **{away} {e[away]:.0%}**"]
    if market and "1x2" in market["markets"]:
        L.append("")
        L.append("| sel | model | sharp fair | best | verdict |")
        L.append("|---|---|---|---|---|")
        for r in market["markets"]["1x2"]["selections"]:
            L.append(f"| {r['selection']} | {r['model_prob']:.0%} | {r['sharp_prob']:.0%} | "
                     f"{r['best_odds']:.2f} | **{r['verdict']}** |")
    L.append("")

    # Goals
    L += ["## Goals (total)", "",
          f"- Expected goals: {home} {eg[home]} – {eg[away]} {away}  (total λ {tot_lambda:.2f})",
          "", "| line | model P(over) | market (best over) | note |", "|---|---|---|---|"]
    ou_mkt = (market["markets"].get("ou_2.5") if market else None)
    for ln in GOAL_LINES:
        p_over = poisson_over(tot_lambda, ln)
        price = note = "—"
        if ln == 2.5 and ou_mkt:
            over_row = next((r for r in ou_mkt["selections"] if r["selection"] == "over"), None)
            if over_row:
                price = f"{over_row['best_odds']:.2f}"
                note = over_row["verdict"]
        L.append(f"| over {ln} | {p_over:.0%} | {price} | {note} |")
    L += ["", f"- BTTS (both score): model **{pred.get('btts'):.0%}**", ""]

    # Props
    L += ["## Player shots-on-target (CLOV-on-overs)", ""]
    if props:
        L.append("Overs where the model beats the offered (vig-included) price, real-data "
                 "players only. One-sided market → judged by CLOV, not de-vig.")
        L.append("")
        L.append("| player | line | over | model | price implies | EV |")
        L.append("|---|---|---|---|---|---|")
        for p in props:
            L.append(f"| {p['player']} | {p['line']} | {p['over_price']:.2f} | "
                     f"{p['model_over']:.0%} | {1/p['over_price']:.0%} | +{p['ev']:.2f} |")
    else:
        L.append(f"_No prop candidates — {prop_note}._")
    L.append("")

    # Recommendation
    L += ["## Recommendation", ""]
    recs = (market["recommend"] if market else [])
    if recs:
        for r in recs:
            L.append(f"- **{r['market']} {r['selection']}** @ {r['best_odds']:.2f} — soft price "
                     f"beats the sharp fair by {r['soft_edge']:+.1%} (prospective CLOV+).")
    else:
        L.append("- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair "
                 "(the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.")
    if props:
        L.append(f"- **Prop watch:** {', '.join(p['player'] for p in props)} — paper/CLOV only, "
                 "log small and let the close judge.")
    L += ["", "_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the "
          "sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot "
          "backtests use pre-kickoff odds, which may be stale if captured long before kickoff._", ""]

    # Reveal
    if args.reveal:
        L += ["## Result (revealed)", ""]
        if result and result.get("completed"):
            hg, ag = result["home_goals"], result["away_goals"]
            res = "home" if hg > ag else "away" if ag > hg else "draw"
            tot = hg + ag
            L.append(f"- **{home} {hg}–{ag} {away}** ({res}, {tot} goals)")
            L.append(f"  - 1X2: we gave {res} **{e[home] if res=='home' else e[away] if res=='away' else e['Draw']:.0%}**")
            for ln in GOAL_LINES:
                hit = "over" if tot > ln else "under"
                L.append(f"  - O/U {ln}: **{hit}** (model P(over) {poisson_over(tot_lambda, ln):.0%})")
        else:
            L.append("- result not available yet.")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()

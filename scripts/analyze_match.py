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
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.market import compare_lines               # noqa: E402
from scripts.prop_clov import _real_data_names, _has_real_data  # noqa: E402

SNAP = Path("data/csv/derived/odds_snapshots.csv")
README = Path("README.md")
BOARD_JSON = Path("data/csv/derived/daily_board.json")
GOAL_LINES = (1.5, 2.5, 3.5)


def _kickoff(match: str) -> str:
    """'YYYY-MM-DD HH:MM' kickoff for a match from the latest odds snapshot, else ''."""
    if not SNAP.exists():
        return ""
    want = set(match.lower().replace(" vs ", " ").split())
    best = ""
    for r in csv.DictReader(open(SNAP)):
        m = set(r["match"].lower().replace(" vs ", " ").replace("&", "").split())
        if want & m and len(want & m) >= 2:                # both teams present
            best = r["commence_time"]
    return best.replace("T", " ").replace("Z", "")[:16] if best else ""


def _update_board(folder: Path, pred: dict, market, props) -> None:
    """Upsert this fixture's row into README's daily board (sidecar JSON is the source)."""
    home, away = pred["match"].split(" vs ")
    e = pred["win_draw_loss"]["ENSEMBLE"]
    fav = max([(home, e[home]), ("Draw", e["Draw"]), (away, e[away])], key=lambda x: x[1])
    ou = "—"
    if market and "ou_2.5" in market["markets"]:
        ov = next((r for r in market["markets"]["ou_2.5"]["selections"] if r["selection"] == "over"), None)
        if ov:
            ou = f"over {ov['model_prob']:.0%} @ {ov['best_odds']:.2f} ({ov['verdict']})"
    prop = (f"{props[0]['player']} o{props[0]['line']} @ {props[0]['over_price']:.2f}"
            if props else "—")
    ko = _kickoff(pred["match"])
    row = {"match": pred["match"], "kickoff": ko, "date": ko[:10],
           "onex2": f"{fav[0]} {fav[1]:.0%}", "ou": ou, "prop": prop,
           "link": str(folder / "analysis.md")}

    rows = json.loads(BOARD_JSON.read_text()) if BOARD_JSON.exists() else []
    rows = [r for r in rows if r["match"] != row["match"]] + [row]
    today = row["date"] or max((r["date"] for r in rows), default="")
    rows = sorted([r for r in rows if r.get("date") == today], key=lambda r: r["kickoff"])
    BOARD_JSON.parent.mkdir(parents=True, exist_ok=True)
    BOARD_JSON.write_text(json.dumps(rows, indent=1, ensure_ascii=False))

    L = [f"## 📅 Tablero de hoy — {today or '(s/f)'}", "",
         "_Se actualiza partido por partido vía `/analyze-match`. Detalle en cada `analysis.md`._", "",
         "| Hora (UTC) | Partido | 1X2 (registro) | Total goles O/U 2.5 | Prop destacado | Análisis |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        hhmm = (r["kickoff"][11:16] + "Z") if len(r["kickoff"]) >= 16 else "—"
        L.append(f"| {hhmm} | {r['match']} | {r['onex2']} | {r['ou']} | {r['prop']} "
                 f"| [análisis]({r['link']}) |")
    if README.exists():
        txt = README.read_text()
        new = re.sub(r"<!-- DAILY-BOARD:START -->.*?<!-- DAILY-BOARD:END -->",
                     "<!-- DAILY-BOARD:START -->\n" + "\n".join(L) + "\n<!-- DAILY-BOARD:END -->",
                     txt, flags=re.S)
        README.write_text(new)


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
        # backfill the goals line (priority market) from the last snapshot if live missed it
        if "ou_2.5" not in sharp:
            key = home.split()[0] if len(home.split()[0]) > 3 else away.split()[0]
            s_sharp, s_soft, _ = _snapshot_odds(key)
            if s_sharp.get("ou_2.5"):
                sharp["ou_2.5"] = s_sharp["ou_2.5"]
                soft.setdefault("ou_2.5", s_soft.get("ou_2.5", s_sharp["ou_2.5"]))

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
    if args.source == "live":                       # publish to the README daily board
        _update_board(folder, pred, market, props)
        print("-> README daily board updated")
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

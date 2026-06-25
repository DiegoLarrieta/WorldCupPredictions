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

# --- Per-team shots model (Fase B): anchor on the team's expected goals (λ from DC). ---
# Validated on 44 WC team-matches: shots ≈ 2.6+8.4·λ (corr 0.69), SoT ≈ 0.6+3.1·λ (corr 0.59).
# Beats the sum-of-XI approach (corr -0.37, failed). Poisson on the fitted mean. Refit as n
# grows (fit lives in match_team_stats + each prediction's λ). NB could fit overdispersion later.
TEAM_SHOTS_COEF = (2.6, 8.4)
TEAM_SOT_COEF = (0.6, 3.1)


def team_over(lam_goals: float, line: float, coef) -> float:
    """P(a team's shots/SoT in the match > line), from Poisson(a + b·λ_goals)."""
    return poisson_over(max(coef[0] + coef[1] * float(lam_goals), 0.1), line)


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


def _update_board(folder: Path, pred: dict, market, props, extra=None) -> None:
    """Upsert this fixture's full market breakdown into README's daily board (sidecar JSON
    is the source). Every market we analyse gets its model prob + real odds where we have them."""
    extra = extra or {}
    home, away = pred["match"].split(" vs ")
    e = pred["win_draw_loss"]["ENSEMBLE"]
    eg = pred["expected_goals"]
    lam = float(eg[home]) + float(eg[away])
    x2 = {s["selection"]: s["best_odds"] for s in market["markets"]["1x2"]["selections"]} \
        if market and "1x2" in market["markets"] else {}
    NF = "_(no fetcheado)_"

    def od(v):
        return f"{v:.2f}" if v else NF

    # resultado (si se jugó) para los checks por mercado
    ar = pred.get("actual_result") or {}
    played, hg, ag, res_o = False, 0, 0, ""
    if ar.get("score") and "-" in str(ar["score"]):
        try:
            hg, ag = (int(x) for x in str(ar["score"]).split("-"))
            res_o, played = ar.get("result", ""), True
        except ValueError:
            played = False
    tot = hg + ag

    def h(cond):                       # ✅/❌ si jugado, ⏳ si no
        return bool(cond) if played else None

    # (mercado, prob, odds, ¿pasó?)
    mk = [
        (f"Gana {home}", e[home], od(x2.get("home")), h(res_o == "home")),
        ("Empate", e["Draw"], od(x2.get("draw")), h(res_o == "draw")),
        (f"Gana {away}", e[away], od(x2.get("away")), h(res_o == "away")),
        (f"Doble oport. {home}", e[home] + e["Draw"], od(extra.get("dc_home")), h(res_o in ("home", "draw"))),
        (f"Doble oport. {away}", e[away] + e["Draw"], od(extra.get("dc_away")), h(res_o in ("away", "draw"))),
        ("Over 1.5 goles", poisson_over(lam, 1.5), od((extra.get("ou_1.5") or {}).get("over")), h(tot > 1.5)),
        ("Over 2.5 goles", poisson_over(lam, 2.5), od((extra.get("ou_2.5") or {}).get("over")), h(tot > 2.5)),
        ("Over 3.5 goles", poisson_over(lam, 3.5), od((extra.get("ou_3.5") or {}).get("over")), h(tot > 3.5)),
        (f"Over 1.5 goles {home}", poisson_over(float(eg[home]), 1.5), od(extra.get("team_ov15_home")), h(hg >= 2)),
        (f"Over 1.5 goles {away}", poisson_over(float(eg[away]), 1.5), od(extra.get("team_ov15_away")), h(ag >= 2)),
        ("BTTS (ambos marcan)", float(pred.get("btts") or 0), od((extra.get("btts") or {}).get("yes")), h(hg > 0 and ag > 0)),
    ]
    tp = _board_prop(folder, props)        # top prop (live, o leído de prop_compare.json)
    if tp:
        player, line, price, mo = tp
        sot = _player_sot(pred["match"], player) if played else None
        mk.append((f"Prop: {player} o{line} SoT", mo, od(price),
                   h(sot > line) if sot is not None else None))

    # apuestas sugeridas (lectura sharp-vs-blando) + resultado
    sug = "; ".join(f"{r['selection']} @ {r['best_odds']:.2f} ({r['soft_edge']:+.0%})"
                    for r in (market.get("recommend") if market else []) or [])
    res = ""
    if played:
        res = f"✅ Jugado: **{ar['score']}** ({res_o})"
        am = folder / "analysis.md"
        if am.exists():
            m = re.search(r"Checks acertados: (\d+/\d+)", am.read_text())
            if m:
                res += f" · checks **{m.group(1)}**"
    ko = _kickoff(pred["match"])
    row = {"match": pred["match"], "kickoff": ko, "date": ko[:10], "result": res,
           "sug": sug, "link": str(folder / "analysis.md"),
           "markets": [(lab, round(pr, 3), o, hp) for lab, pr, o, hp in mk]}

    rows = json.loads(BOARD_JSON.read_text()) if BOARD_JSON.exists() else []
    rows = [r for r in rows if r.get("markets") is not None and r["match"] != row["match"]] + [row]
    rows = sorted(rows, key=lambda r: r.get("kickoff", ""), reverse=True)   # nuevos arriba
    BOARD_JSON.parent.mkdir(parents=True, exist_ok=True)
    BOARD_JSON.write_text(json.dumps(rows, indent=1, ensure_ascii=False))

    L = ["## 📅 Tablero de partidos", "",
         "_Acumula todo lo analizado (lo nuevo arriba). Prob = modelo · Odds = The Odds API · "
         "1X2/doble-oport = registro. Detalle + checks: `analysis.md`._", ""]
    for r in rows:
        hhmm = (r["kickoff"][11:16] + "Z") if len(r.get("kickoff", "")) >= 16 else "—"
        head = f"### {r['match']} — {r['kickoff'][:10]} {hhmm} · [análisis]({r['link']})"
        L += [head, ""]
        L += [r["result"] if r.get("result") else "⏳ Por jugarse", ""]
        if r.get("sug"):
            L += [f"🎯 **Apuestas sugeridas:** {r['sug']}", ""]
        else:
            L += ["🎯 **Apuestas sugeridas:** ninguna (sin edge soft-vs-sharp)", ""]
        L += ["| Mercado | Prob modelo | Odds | Check |", "|---|---|---|---|"]
        for m in r["markets"]:
            lab, pr, o = m[0], m[1], m[2]
            hp = m[3] if len(m) > 3 else None
            ck = "⏳" if hp is None else ("✅" if hp else "❌")
            L.append(f"| {lab} | {pr:.0%} | {o} | {ck} |")
        L.append("")
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
        # capture a FRESH snapshot now (part of the pipeline) — never analyse on stale odds,
        # and feed the CLOV log with this moment's prices. Run analyse near kickoff = the close.
        snap = subprocess.run([sys.executable, "scripts/snapshot_odds.py"], capture_output=True, text=True)
        print(snap.stdout.strip().split("\n")[0] if snap.stdout else "snapshot: (sin salida)")
        from engine.odds_api import fetch_odds, OddsAPIError
        try:
            sharp = fetch_odds(home, away, book="pinnacle")
            soft = fetch_odds(home, away, book="best")
        except OddsAPIError as ex:
            sharp, soft = {}, {}
            print(f"odds fetch failed: {ex}")
        # backfill the goals line (priority market) from the last snapshot if live missed it
        if "ou_2.5" not in sharp or "ou_2.5" not in soft:
            key = home.split()[0] if len(home.split()[0]) > 3 else away.split()[0]
            s_sharp, s_soft, _ = _snapshot_odds(key)
            if "ou_2.5" not in sharp and s_sharp.get("ou_2.5"):
                sharp["ou_2.5"] = s_sharp["ou_2.5"]
            if "ou_2.5" not in soft and s_soft.get("ou_2.5"):   # soft total even if sharp lacks it
                soft["ou_2.5"] = s_soft["ou_2.5"]

    market = compare_lines(pred, sharp, soft) if sharp else None

    # --- full market set (live only): double chance, O/U lines, team totals, BTTS ---
    extra = {}
    if args.source == "live":
        try:
            from engine.odds_api import fetch_all_markets
            extra = fetch_all_markets(home, away)
        except Exception:
            pass

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

    md = _render(pred, e, eg, tot_lambda, market, props, prop_note, result, args, snap_ts,
                 soft.get("ou_2.5") if isinstance(soft, dict) else None, extra)
    (folder / "analysis.md").write_text(md)
    _update_board(folder, pred, market, props, extra)   # accumulate in the README board
    print(f"-> {folder/'analysis.md'}")
    print(md)


def _render(pred, e, eg, tot_lambda, market, props, prop_note, result, args, snap_ts,
            soft_ou=None, extra=None) -> str:
    extra = extra or {}
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

    # Goals (model P(over) vs real odds + EV at the offered price)
    L += ["## Goals (total)", "",
          f"- Expected goals: {home} {eg[home]} – {eg[away]} {away}  (total λ {tot_lambda:.2f})",
          "", "| over | model P | odds | EV@odds |", "|---|---|---|---|"]
    for ln in GOAL_LINES:
        p = poisson_over(tot_lambda, ln)
        od = (extra.get(f"ou_{ln}") or {}).get("over")
        if not od and ln == 2.5 and soft_ou:
            od = soft_ou.get("over")
        ev = f"{p*od-1:+.2f}" if od else "—"
        L.append(f"| {ln} | {p:.0%} | {(f'{od:.2f}' if od else '—')} | {ev} |")
    L.append("")

    # Otros mercados (doble oportunidad, goles por equipo, BTTS) — model P vs odds + EV
    dc_h, dc_a = e[home] + e["Draw"], e[away] + e["Draw"]
    th = poisson_over(float(eg[home]), 1.5)
    ta = poisson_over(float(eg[away]), 1.5)
    rows = [
        (f"Doble oport. {home}", dc_h, extra.get("dc_home")),
        (f"Doble oport. {away}", dc_a, extra.get("dc_away")),
        (f"Over 1.5 goles {home}", th, extra.get("team_ov15_home")),
        (f"Over 1.5 goles {away}", ta, extra.get("team_ov15_away")),
        ("BTTS (ambos marcan)", float(pred.get("btts") or 0), (extra.get("btts") or {}).get("yes")),
        (f"Tiros {home} over 9.5", team_over(eg[home], 9.5, TEAM_SHOTS_COEF), None),
        (f"Tiros {away} over 9.5", team_over(eg[away], 9.5, TEAM_SHOTS_COEF), None),
        (f"TaP {home} over 2.5", team_over(eg[home], 2.5, TEAM_SOT_COEF), None),
        (f"TaP {away} over 2.5", team_over(eg[away], 2.5, TEAM_SOT_COEF), None),
    ]
    L += ["## Otros mercados", "",
          "_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes "
          "(1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._",
          "", "| mercado | model P | odds | EV@odds |", "|---|---|---|---|"]
    for lab, p, od in rows:
        ev = f"{p*od-1:+.2f}" if od else "—"
        L.append(f"| {lab} | {p:.0%} | {(f'{od:.2f}' if od else '—')} | {ev} |")
    L.append("")

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

    # Reveal — qué se cumplió (✅ si la inclinación del modelo, P>=50%, acertó)
    if args.reveal:
        L += ["## Resultado y checks (qué se cumplió)", ""]
        if result and result.get("completed"):
            hg, ag = result["home_goals"], result["away_goals"]
            res = "home" if hg > ag else "away" if ag > hg else "draw"
            tot = hg + ag
            ash = _actual_team_stats(pred["match"], home, away)
            L.append(f"- **{home} {hg}–{ag} {away}** ({res}, {tot} goles"
                     + (f"; tiros {ash['home'][0]}-{ash['away'][0]}, TaP {ash['home'][1]}-{ash['away'][1]}" if ash else "") + ")")
            L += ["", "| Mercado | model P | ¿Pasó? | check |", "|---|---|---|---|"]

            def chk(label, p, happened):
                ok = "✅" if (p >= 0.5) == bool(happened) else "❌"
                L.append(f"| {label} | {p:.0%} | {'sí' if happened else 'no'} | {ok} |")

            chk(f"Gana {home}", e[home], res == "home")
            chk("Empate", e["Draw"], res == "draw")
            chk(f"Gana {away}", e[away], res == "away")
            chk(f"Doble oport. {home}", e[home] + e["Draw"], res in ("home", "draw"))
            chk(f"Doble oport. {away}", e[away] + e["Draw"], res in ("away", "draw"))
            for ln in GOAL_LINES:
                chk(f"Over {ln} goles", poisson_over(tot_lambda, ln), tot > ln)
            chk(f"Over 1.5 goles {home}", poisson_over(float(eg[home]), 1.5), hg >= 2)
            chk(f"Over 1.5 goles {away}", poisson_over(float(eg[away]), 1.5), ag >= 2)
            chk("BTTS", float(pred.get("btts") or 0), hg > 0 and ag > 0)
            if ash:
                chk(f"Tiros {home} o9.5", team_over(eg[home], 9.5, TEAM_SHOTS_COEF), ash["home"][0] > 9.5)
                chk(f"Tiros {away} o9.5", team_over(eg[away], 9.5, TEAM_SHOTS_COEF), ash["away"][0] > 9.5)
                chk(f"TaP {home} o2.5", team_over(eg[home], 2.5, TEAM_SOT_COEF), ash["home"][1] > 2.5)
                chk(f"TaP {away} o2.5", team_over(eg[away], 2.5, TEAM_SOT_COEF), ash["away"][1] > 2.5)
            nok = sum(1 for x in L if x.endswith("✅ |"))
            ntot = sum(1 for x in L if x.endswith("✅ |") or x.endswith("❌ |"))
            L += ["", f"**Checks acertados: {nok}/{ntot}** (✅ = la inclinación del modelo coincidió con lo que pasó)."]
        else:
            L.append("- resultado no disponible aún.")
    return "\n".join(L) + "\n"


def _actual_team_stats(match: str, home: str, away: str):
    """{home:(shots,sot), away:(shots,sot)} from match_team_stats.csv, else None."""
    f = Path("data/csv/derived/match_team_stats.csv")
    if not f.exists():
        return None
    out = {}
    for r in csv.DictReader(open(f)):
        if r["match"] == match:
            side = "home" if _norm_team(r["team"]) == _norm_team(home) else "away" if _norm_team(r["team"]) == _norm_team(away) else None
            if side:
                try:
                    out[side] = (float(r["shots_for"]), float(r["sot_for"]))
                except (ValueError, TypeError):
                    pass
    return out if len(out) == 2 else None


def _norm_team(s):
    from unidecode import unidecode
    return unidecode(str(s)).strip().lower()


def _board_prop(folder, props):
    """Top prop for the board: from live `props`, else the top CLOV candidate in
    prop_compare.json. Returns (player, line, price, model_over) or None."""
    if props:
        p = props[0]
        return p["player"], p["line"], p.get("over_price"), p["model_over"]
    pc = folder / "prop_compare.json"
    if pc.exists():
        rows = [r for r in json.loads(pc.read_text()).get("rows", [])
                if r.get("over_price") and (r.get("model_over") or 0) >= 0.45 and r["line"] <= 1.5]
        rows.sort(key=lambda r: -(r["model_over"] * r["over_price"]))
        if rows:
            r = rows[0]
            return r["player"], r["line"], r["over_price"], r["model_over"]
    return None


def _player_sot(match, player):
    """A player's shots-on-target in a finished match (player_match_shots), else None."""
    f = Path("data/csv/derived/player_match_shots.csv")
    if not f.exists():
        return None
    pt = frozenset(_norm_team(player).replace("-", " ").split())
    for r in csv.DictReader(open(f)):
        if r.get("match") != match:
            continue
        rt = frozenset(_norm_team(r.get("player", "")).replace("-", " ").split())
        if rt and (rt <= pt or pt <= rt):
            try:
                return float(r.get("on_target") or 0)
            except (ValueError, TypeError):
                return None
    return None


if __name__ == "__main__":
    main()

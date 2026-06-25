"""Model vs market — turn a prediction into a bet decision.

A prediction alone is worthless for betting. The only thing that matters is whether
our probability disagrees with the *price* enough to have positive expected value.
This module takes the odds for a fixture (the ones you pull for that match), strips
the bookmaker margin, lines the de-vigged market probability up against the model,
and reports the edge + EV per outcome so a value bet is obvious.

    from engine.market import compare, save_comparison
    pred = json.loads((folder / "prediction.json").read_text())
    cmp = compare(pred, {
        "1x2":    {"home": 8.0, "draw": 5.5, "away": 1.33},
        "ou_2.5": {"over": 2.10, "under": 1.75},
    })
    save_comparison(cmp, folder)        # writes market_compare.{json,md}

No DuckDB / network import (CI-safe). De-vig is the same multiplicative method as
sql/implied_prob.sql, so SQL and Python agree.
"""

from __future__ import annotations

import json
from pathlib import Path

# A bet must clear this EV (per 1u stake) to be flagged as value. Covers model noise
# + the fact that the price you actually get is the vigged one. Tune as edge is proven.
DEFAULT_EV_THRESHOLD = 0.03

# How to strip the bookmaker margin. Multiplicative just scales proportionally, so it
# keeps the longshot's inflated share — but longshots are systematically OVERBET (the
# favourite-longshot bias), so their true probability sits BELOW the proportional one.
# Shin and power attribute more of the margin to longshots: they lift the favourite and
# trim the longshot/draw, which is the better-calibrated estimate. Using a method that
# corrects this matters most on exactly the underdog/draw calls our model likes to flag,
# so we don't mistake a de-vig artifact for edge. Default Shin.
DEFAULT_DEVIG = "shin"


def devig(odds: dict[str, float], method: str = "multiplicative") -> dict[str, float]:
    """Decimal odds -> de-vigged implied probabilities (sums to 1).

    method:
      'multiplicative' — raw/overround. Fast, but biased toward favourites.
      'shin'           — Shin (1992): solves for the share of margin attributable to
                         informed money; corrects the favourite-longshot bias.
      'power'          — each implied prob raised to a common exponent until they sum
                         to 1; also de-biases longshots, no insider-trade assumption.
    Works for any number of mutually-exclusive selections (1X2, O/U, BTTS).
    """
    raw = {k: 1.0 / float(v) for k, v in odds.items()}
    if method == "multiplicative":
        s = sum(raw.values())
        return {k: p / s for k, p in raw.items()}
    if method == "shin":
        return _devig_shin(raw)
    if method == "power":
        return _devig_power(raw)
    raise ValueError(f"unknown devig method '{method}' (multiplicative|shin|power)")


def _devig_shin(raw: dict[str, float]) -> dict[str, float]:
    """Shin's method. Solve z in [0, 0.5) so the implied probabilities sum to 1.

    p_i = (sqrt(z^2 + 4(1-z) b_i^2 / B) - z) / (2(1-z)), B = sum(b_i) overround.
    """
    import math
    b = list(raw.values())
    B = sum(b)

    def probs(z: float) -> list[float]:
        return [(math.sqrt(z * z + 4 * (1 - z) * bi * bi / B) - z) / (2 * (1 - z)) for bi in b]

    lo, hi = 0.0, 0.499
    f_lo = sum(probs(lo)) - 1.0
    f_hi = sum(probs(hi)) - 1.0
    if f_lo * f_hi > 0:                       # no bracket (≈no vig) -> multiplicative
        return {k: v / B for k, v in raw.items()}
    for _ in range(60):                       # bisection
        mid = (lo + hi) / 2
        if (sum(probs(mid)) - 1.0) * f_lo > 0:
            lo = mid
        else:
            hi = mid
    p = probs((lo + hi) / 2)
    s = sum(p)
    return {k: pi / s for k, pi in zip(raw, p)}


def _devig_power(raw: dict[str, float]) -> dict[str, float]:
    """Power method. Find c so sum(b_i^c) = 1, then p_i = b_i^c (c >= 1 shrinks longshots less)."""
    b = list(raw.values())
    lo, hi = 1.0, 10.0
    f = lambda c: sum(bi ** c for bi in b) - 1.0   # noqa: E731
    if f(lo) <= 0:                                   # already <=1 (no vig) -> multiplicative
        s = sum(b)
        return {k: v / s for k, v in raw.items()}
    for _ in range(60):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    c = (lo + hi) / 2
    return {k: bi ** c for k, bi in zip(raw, b)}


def vig_of(odds: dict[str, float]) -> float:
    """Bookmaker margin implied by a set of odds (overround - 1)."""
    return sum(1.0 / float(v) for v in odds.values()) - 1.0


def prop_ev(model_over_prob: float, over_price: float | None, under_price: float | None = None,
            *, ev_threshold: float = DEFAULT_EV_THRESHOLD, devig_method: str = DEFAULT_DEVIG) -> dict:
    """Model vs market for a two-way player prop (over/under a line).

    `model_over_prob` is our P(player exceeds the line) from engine.props. We de-vig the
    over/under pair (Shin) for the market's fair view, then take EV on each side at the
    offered price. Returns the best side and whether it clears the threshold. Either price
    may be missing (one-sided book) — de-vig is skipped then and EV uses the raw price.
    """
    p_over = float(model_over_prob)
    p_under = 1.0 - p_over
    market = None
    if over_price and under_price:
        market = devig({"over": over_price, "under": under_price}, devig_method)
    sides = []
    if over_price:
        sides.append({"side": "over", "price": float(over_price), "model_prob": round(p_over, 3),
                      "market_prob": round(market["over"], 3) if market else None,
                      "edge": round(p_over - market["over"], 3) if market else None,
                      "ev_per_unit": round(_ev(p_over, over_price), 3)})
    if under_price:
        sides.append({"side": "under", "price": float(under_price), "model_prob": round(p_under, 3),
                      "market_prob": round(market["under"], 3) if market else None,
                      "edge": round(p_under - market["under"], 3) if market else None,
                      "ev_per_unit": round(_ev(p_under, under_price), 3)})
    best = max(sides, key=lambda s: s["ev_per_unit"]) if sides else None
    # Only flag value when we have a two-sided line to de-vig against. A one-sided book
    # price (market_prob is None) can't be sanity-checked, so a big EV there is almost
    # always model error, not edge — show it, never flag it.
    return {"sides": sides, "best": best,
            "value": bool(best and best["ev_per_unit"] >= ev_threshold
                          and best["market_prob"] is not None)}


def _ev(model_prob: float, decimal_odds: float) -> float:
    """Expected value per 1u stake at the OFFERED (vigged) price: p*d - 1.

    Positive EV = the price pays more than our probability says it should. This is
    the real betting signal — it's measured against the price you actually get, not
    the de-vigged fair line.
    """
    return model_prob * float(decimal_odds) - 1.0


# Map a market key + selection to the model probability inside a prediction dict.
def _model_probs(prediction: dict, market: str, selections: list[str]) -> dict[str, float]:
    wdl = prediction["win_draw_loss"]["ENSEMBLE"]
    home, away = list(wdl.keys())[0], list(wdl.keys())[2]
    if market == "1x2":
        return {"home": wdl[home], "draw": wdl["Draw"], "away": wdl[away]}
    if market == "ou_2.5":
        ou = prediction["over_under_2_5"]
        return {"over": ou["over"], "under": ou["under"]}
    if market == "btts":
        y = prediction["btts"]
        return {"yes": y, "no": round(1.0 - y, 3)}
    raise ValueError(f"unsupported market '{market}' (have: 1x2, ou_2.5, btts)")


def compare(prediction: dict, odds: dict[str, dict[str, float]],
            ev_threshold: float = DEFAULT_EV_THRESHOLD,
            devig_method: str = DEFAULT_DEVIG) -> dict:
    """Line the model up against the offered odds for every market provided.

    `odds` maps a market key ('1x2', 'ou_2.5', 'btts') to its selections' decimal
    odds. Returns a structured comparison; selections clearing `ev_threshold` are
    flagged as value bets. `devig_method` controls how the market's fair probability
    is recovered (default Shin, which de-biases underdog/draw value calls).
    """
    markets = {}
    best = None
    for market, book in odds.items():
        model = _model_probs(prediction, market, list(book.keys()))
        mkt = devig(book, devig_method)
        rows = []
        for sel, price in book.items():
            p = float(model[sel])
            ev = _ev(p, price)
            row = {
                "selection": sel,
                "odds": float(price),
                "model_prob": round(p, 3),
                "market_prob": round(mkt[sel], 3),          # de-vigged fair
                "edge": round(p - mkt[sel], 3),             # where we disagree w/ fair line
                "ev_per_unit": round(ev, 3),                # signal vs the price you get
                "value": ev >= ev_threshold,
            }
            rows.append(row)
            if best is None or ev > best["ev_per_unit"]:
                best = {"market": market, **row}
        markets[market] = {"vig": round(vig_of(book), 4), "selections": rows}

    value_bets = [
        {"market": m, **r}
        for m, data in markets.items() for r in data["selections"] if r["value"]
    ]
    value_bets.sort(key=lambda r: r["ev_per_unit"], reverse=True)

    return {
        "match": prediction.get("match"),
        "as_of": prediction.get("as_of"),
        "ev_threshold": ev_threshold,
        "devig_method": devig_method,
        "markets": markets,
        "value_bets": value_bets,
        "best_ev": best,
    }


def compare_folder(folder: Path, odds: dict[str, dict[str, float]],
                   ev_threshold: float = DEFAULT_EV_THRESHOLD) -> dict:
    """Read a match folder's prediction.json, compare to odds, write the result."""
    folder = Path(folder)
    prediction = json.loads((folder / "prediction.json").read_text())
    cmp = compare(prediction, odds, ev_threshold)
    save_comparison(cmp, folder)
    return cmp


# --- sharp-vs-soft, the honest read ----------------------------------------
# A flag from compare() is naive: a big model-vs-market gap on 1X2 is usually US being
# wrong (the edge test proved we don't out-predict a sharp close). The defensible value
# is model-INDEPENDENT: a soft book offering a price BETTER than the sharp's de-vigged
# fair (best_odds * sharp_prob > 1) — that's a prospective CLOV+, beating the close before
# it closes. We surface the model-vs-sharp gap too, but label large ones SUSPECT.
SOFT_EDGE_THRESHOLD = 0.03      # best price must beat the sharp fair by this to recommend
                                # (< this is within de-vig noise — soft and sharp agree)
MODEL_DISAGREE_THRESHOLD = 0.05  # model_prob - sharp_prob above this = flagged suspect
MIN_SHARP_PROB = 0.20            # longshot guard: below this, best-of-books dispersion +
                                 # de-vig noise dominate -> a soft "edge" is unreliable
                                 # (this is what was flagging every draw/underdog as a bet)


def _verdict(soft_edge: float, model_gap: float, sharp_prob: float) -> tuple[str, str]:
    if soft_edge >= SOFT_EDGE_THRESHOLD:
        if sharp_prob < MIN_SHARP_PROB:
            return "pass", ("soft price beats the sharp, but it's a longshot "
                            f"(sharp {sharp_prob:.0%}) — best-of-books noise, not real edge")
        return "bet", "soft price beats the sharp's own price (prospective CLOV+)"
    if model_gap >= MODEL_DISAGREE_THRESHOLD:
        return "suspect", "model disagrees with the sharp close — edge test says we're usually wrong here"
    return "pass", "no edge vs the sharp"


def compare_lines(prediction: dict, sharp_odds: dict, soft_odds: dict,
                  devig_method: str = DEFAULT_DEVIG) -> dict:
    """Honest read using a SHARP book (Pinnacle, for the fair line) and a SOFT/best book
    (where you'd bet). Per selection: the best available price, the sharp's de-vigged fair,
    the soft-edge (does best beat the sharp fair -> recommend) and the model-vs-sharp gap
    (shown, but a big positive one is flagged SUSPECT, not value)."""
    markets, recommend = {}, []
    for market, sharp_book in sharp_odds.items():
        soft_book = soft_odds.get(market, {})
        model = _model_probs(prediction, market, list(sharp_book.keys()))
        fair = devig(sharp_book, devig_method)
        rows = []
        for sel, sharp_price in sharp_book.items():
            best = max(float(sharp_price), float(soft_book.get(sel, 0.0)))
            sp = fair[sel]
            soft_edge = best / float(sharp_price) - 1.0  # best vs the sharp's OWN price = CLOV+
            model_gap = float(model[sel]) - sp           # our disagreement with the sharp
            verdict, why = _verdict(soft_edge, model_gap, sp)
            row = {
                "selection": sel,
                "best_odds": round(best, 3),
                "sharp_odds": round(float(sharp_price), 3),
                "model_prob": round(float(model[sel]), 3),
                "sharp_prob": round(sp, 3),
                "soft_edge": round(soft_edge, 3),     # >0 => price beats the close (credible)
                "model_vs_sharp": round(model_gap, 3),
                "verdict": verdict, "why": why,
            }
            rows.append(row)
            if verdict == "bet":
                recommend.append({"market": market, **row})
        markets[market] = {"sharp_vig": round(vig_of(sharp_book), 4), "selections": rows}
    # Drop any market with >1 flagged selection: you can't have edge on both sides of a
    # 2-way (over+under) or every leg of a 3-way (home/draw/away). When 'best' (max across
    # books) beats a single sharp on most legs that's market DISPERSION, not edge — keep
    # only markets where exactly ONE selection is genuinely soft-priced.
    from collections import Counter
    per_market = Counter(r["market"] for r in recommend)
    recommend = [r for r in recommend if per_market[r["market"]] == 1]
    recommend.sort(key=lambda r: r["soft_edge"], reverse=True)
    return {
        "match": prediction.get("match"), "as_of": prediction.get("as_of"),
        "devig_method": devig_method, "markets": markets, "recommend": recommend,
    }


def compare_lines_folder(folder: Path, sharp_odds: dict, soft_odds: dict) -> dict:
    """Read a folder's prediction.json, do the sharp-vs-soft read, write market_compare.*"""
    folder = Path(folder)
    prediction = json.loads((folder / "prediction.json").read_text())
    cmp = compare_lines(prediction, sharp_odds, soft_odds)
    (folder / "market_compare.json").write_text(json.dumps(cmp, ensure_ascii=False, indent=2))
    (folder / "market_compare.md").write_text(_markdown_lines(cmp))
    return cmp


def _markdown_lines(cmp: dict) -> str:
    L = [f"# Market read (sharp vs soft): {cmp['match']}", "",
         "Recommend = a **soft book beats the sharp's own price** on a non-longshot (prospective CLOV+). A big "
         "model-vs-sharp gap is **suspect** (the edge test says we don't out-predict the "
         "sharp close), not value.", ""]
    for m, data in cmp["markets"].items():
        L.append(f"## {m}  (sharp vig {data['sharp_vig']:.1%})")
        L.append("| sel | best | sharp fair | model | soft edge | model vs sharp | verdict |")
        L.append("|---|---|---|---|---|---|---|")
        for r in data["selections"]:
            L.append(f"| {r['selection']} | {r['best_odds']:.2f} | {r['sharp_prob']:.0%} | "
                     f"{r['model_prob']:.0%} | {r['soft_edge']:+.1%} | {r['model_vs_sharp']:+.1%} "
                     f"| **{r['verdict']}** |")
        L.append("")
    if cmp["recommend"]:
        L.append("## ✅ Recommended (soft-price edge)")
        for r in cmp["recommend"]:
            L.append(f"- **{r['market']} {r['selection']}** @ {r['best_odds']:.2f} — "
                     f"{r['soft_edge']:+.1%} vs the sharp price ({r['why']})")
    else:
        L.append("## No soft-price edge — pass (the common, correct outcome)")
    return "\n".join(L) + "\n"


def save_comparison(cmp: dict, folder: Path) -> None:
    """Write market_compare.json + market_compare.md into a match folder."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "market_compare.json").write_text(json.dumps(cmp, indent=2, ensure_ascii=False))
    (folder / "market_compare.md").write_text(_markdown(cmp))


def _markdown(cmp: dict) -> str:
    L = [f"# Model vs market: {cmp['match']}", "",
         f"_Ensemble probabilities vs the offered odds. EV is per 1u stake at the "
         f"price shown; value bets clear EV ≥ {cmp['ev_threshold']:.0%}. Edge is model "
         f"minus the de-vigged fair line._", ""]
    for market, data in cmp["markets"].items():
        L += [f"## {market}  (vig {data['vig']:.1%})", "",
              "| Selection | Odds | Model | Market | Edge | EV/1u | Value |",
              "|---|---|---|---|---|---|---|"]
        for r in data["selections"]:
            flag = "✅" if r["value"] else ""
            L.append(f"| {r['selection']} | {r['odds']:.2f} | {r['model_prob']:.0%} | "
                     f"{r['market_prob']:.0%} | {r['edge']:+.0%} | {r['ev_per_unit']:+.2f} | {flag} |")
        L.append("")
    if cmp["value_bets"]:
        L += ["## Value bets", ""]
        for r in cmp["value_bets"]:
            L.append(f"- **{r['market']} / {r['selection']}** @ {r['odds']:.2f} — "
                     f"model {r['model_prob']:.0%} vs market {r['market_prob']:.0%}, "
                     f"EV {r['ev_per_unit']:+.2f}/1u")
    else:
        L += ["## Value bets", "", "_None clear the threshold. The market agrees with us "
              "(or beats us) on every selection — no bet._"]
    return "\n".join(L)

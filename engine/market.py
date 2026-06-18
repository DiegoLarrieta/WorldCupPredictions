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


def devig(odds: dict[str, float]) -> dict[str, float]:
    """Decimal odds -> de-vigged implied probabilities (multiplicative, sums to 1).

    Works for any number of mutually-exclusive selections (3-way 1X2, 2-way O/U,
    2-way BTTS). raw_prob = 1/price; normalise so the book's margin is removed.
    """
    raw = {k: 1.0 / float(v) for k, v in odds.items()}
    overround = sum(raw.values())          # > 1; the excess is the vig
    return {k: p / overround for k, p in raw.items()}


def vig_of(odds: dict[str, float]) -> float:
    """Bookmaker margin implied by a set of odds (overround - 1)."""
    return sum(1.0 / float(v) for v in odds.values()) - 1.0


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
            ev_threshold: float = DEFAULT_EV_THRESHOLD) -> dict:
    """Line the model up against the offered odds for every market provided.

    `odds` maps a market key ('1x2', 'ou_2.5', 'btts') to its selections' decimal
    odds. Returns a structured comparison; selections clearing `ev_threshold` are
    flagged as value bets.
    """
    markets = {}
    best = None
    for market, book in odds.items():
        model = _model_probs(prediction, market, list(book.keys()))
        mkt = devig(book)
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

"""The bet ledger — your proprietary closing-line-value (CLOV) dataset.

We have no historical odds for the markets you bet, so the only way to prove edge is
to capture it live: every bet you place this World Cup, logged with the price you took,
the model's probability at the time, and later the closing price + result. Over the
tournament this becomes a CLOV record nobody can buy — the real test of whether the
model beats the market.

    from engine.betlog import log_bet, settle, summary
    log_bet("Iraq vs Norway", "ou_2.5", "under", odds_taken=1.78,
            model_prob=0.62, stake=10, book="pinnacle")   # -> appends an open bet
    settle(3, result="win", closing_odds=1.70)            # -> P/L + CLOV filled in
    print(summary())                                      # -> ROI, avg CLOV, hit rate

Ledger: data/bets.csv (committed — money records belong in version control). Append-only
in spirit; settle() rewrites the one row it updates. Pure stdlib csv, CI-safe.

CLOV = odds_taken / closing_odds - 1. Positive means you beat the closing line (took a
better price than the market settled at) — the single best leading indicator of edge,
because closing lines are the market's sharpest estimate.
"""

from __future__ import annotations

import csv
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "data" / "bets.csv"

FIELDS = ["bet_id", "date", "match", "market", "selection", "odds_taken",
          "model_prob", "ev", "stake", "book", "result", "closing_odds",
          "clov", "pnl", "status"]


def _read(ledger: Path) -> list[dict]:
    if not Path(ledger).exists():
        return []
    with open(ledger, newline="") as f:
        return list(csv.DictReader(f))


def _write(rows: list[dict], ledger: Path) -> None:
    ledger = Path(ledger)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with open(ledger, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def _next_id(rows: list[dict]) -> int:
    return max((int(r["bet_id"]) for r in rows), default=0) + 1


def log_bet(match: str, market: str, selection: str, *, odds_taken: float,
            model_prob: float, stake: float, book: str = "", date: str = "",
            ledger: Path = LEDGER) -> dict:
    """Append an open bet. EV per 1u is recorded at the price you actually took."""
    import datetime as dt
    rows = _read(ledger)
    row = {
        "bet_id": _next_id(rows),
        "date": date or dt.date.today().isoformat(),
        "match": match, "market": market, "selection": selection,
        "odds_taken": round(float(odds_taken), 3),
        "model_prob": round(float(model_prob), 3),
        "ev": round(float(model_prob) * float(odds_taken) - 1.0, 3),
        "stake": round(float(stake), 2),
        "book": book,
        "result": "", "closing_odds": "", "clov": "", "pnl": "",
        "status": "open",
    }
    rows.append(row)
    _write(rows, ledger)
    return row


def settle(bet_id: int, *, result: str, closing_odds: float | None = None,
           ledger: Path = LEDGER) -> dict:
    """Settle a bet. result in {'win','loss','void'}; closing_odds enables CLOV.

    P/L is staked-money: win -> stake*(odds-1), loss -> -stake, void -> 0.
    """
    if result not in ("win", "loss", "void"):
        raise ValueError("result must be 'win', 'loss', or 'void'")
    rows = _read(ledger)
    for r in rows:
        if int(r["bet_id"]) == int(bet_id):
            odds, stake = float(r["odds_taken"]), float(r["stake"])
            r["result"] = result
            r["status"] = "settled"
            r["pnl"] = round(stake * (odds - 1) if result == "win"
                             else -stake if result == "loss" else 0.0, 2)
            if closing_odds:
                r["closing_odds"] = round(float(closing_odds), 3)
                r["clov"] = round(odds / float(closing_odds) - 1.0, 4)
            _write(rows, ledger)
            return r
    raise KeyError(f"no bet with id {bet_id}")


def summary(ledger: Path = LEDGER) -> dict:
    """Headline numbers: staked, P/L, ROI, settled hit rate, CLOV, beat-close %."""
    rows = _read(ledger)
    settled = [r for r in rows if r["status"] == "settled"]
    staked = sum(float(r["stake"]) for r in settled)
    pnl = sum(float(r["pnl"]) for r in settled if r["pnl"] != "")
    wins = sum(1 for r in settled if r["result"] == "win")
    decided = [r for r in settled if r["result"] in ("win", "loss")]
    clovs = [float(r["clov"]) for r in rows if r["clov"] not in ("", None)]
    beat = sum(1 for c in clovs if c > 0)
    return {
        "bets": len(rows),
        "open": sum(1 for r in rows if r["status"] == "open"),
        "settled": len(settled),
        "staked": round(staked, 2),
        "pnl": round(pnl, 2),
        "roi": round(pnl / staked, 4) if staked else None,
        "hit_rate": round(wins / len(decided), 4) if decided else None,
        "avg_clov": round(sum(clovs) / len(clovs), 4) if clovs else None,
        "beat_close_rate": round(beat / len(clovs), 4) if clovs else None,
    }

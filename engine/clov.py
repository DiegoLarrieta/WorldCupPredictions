"""Closing-line value, done honestly — against the sharp close, not best-price.

Beating the closing line is the only reliable leading indicator of edge on small samples.
But two things have to be right or the metric lies:
  1. Grade against a SHARP book's CLOSING price (Pinnacle), not the best price you could
     find across 41 books. Best-price flatters you; Pinnacle's close is the truth serum.
  2. Capture the line over time (open -> close) so 'closing' really is the last price
     before kickoff, and so we can see which way the market moved relative to our bet.

This module is pure (operates on a list of snapshot dicts), so it is CI-tested. The
capture that produces those snapshots lives in scripts/snapshot_odds.py; the bet ledger
(engine.betlog) records CLOV per bet at settle time.

Snapshot row shape: {match, market, selection, book, price, captured_at}  (captured_at ISO).
"""

from __future__ import annotations


def clov(odds_taken: float, closing_odds: float) -> float:
    """Closing-line value: odds_taken / closing_odds - 1. Positive = you beat the close."""
    return float(odds_taken) / float(closing_odds) - 1.0


def _series(rows, market, selection, book):
    """Snapshots for one book/market/selection, sorted by capture time."""
    xs = [r for r in rows if r["market"] == market and r["selection"] == selection
          and r["book"] == book]
    return sorted(xs, key=lambda r: r["captured_at"])


def closing_price(rows, market, selection, book="pinnacle"):
    """Last captured price before kickoff for the sharp book (the closing line)."""
    xs = _series(rows, market, selection, book)
    return float(xs[-1]["price"]) if xs else None


def opening_price(rows, market, selection, book="pinnacle"):
    """First captured price (the opening line)."""
    xs = _series(rows, market, selection, book)
    return float(xs[0]["price"]) if xs else None


def line_movement(rows, market, selection, book="pinnacle") -> dict:
    """Open -> close drift for a selection. drift_pct > 0 means the price drifted longer
    (the selection got less likely in the market's eyes); < 0 means it shortened.
    """
    op, cl = opening_price(rows, market, selection, book), closing_price(rows, market, selection, book)
    if op is None or cl is None:
        return {"open": op, "close": cl, "drift_pct": None, "n": 0}
    return {"open": op, "close": cl, "drift_pct": cl / op - 1.0,
            "n": len(_series(rows, market, selection, book))}


def grade_bet(odds_taken: float, rows, market, selection, book="pinnacle") -> dict:
    """Grade a placed bet against the sharp closing line: CLOV + whether we beat it.

    This is the honest scorecard: did the price we took beat where the sharp book closed?
    """
    close = closing_price(rows, market, selection, book)
    if close is None:
        return {"closing_odds": None, "clov": None, "beat_close": None, "ref_book": book}
    v = clov(odds_taken, close)
    return {"closing_odds": close, "clov": round(v, 4), "beat_close": v > 0, "ref_book": book}

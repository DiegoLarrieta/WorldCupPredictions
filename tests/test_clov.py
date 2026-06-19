"""Pure-logic tests for CLOV / line-movement (CI, no network) + snapshot flattening."""

from __future__ import annotations

import pytest

from engine.clov import (clov, closing_price, grade_bet, line_movement, opening_price)
from engine.odds_api import snapshot_rows


# open at t1, close at t2 (Pinnacle shortened the favourite from 1.90 -> 1.80)
ROWS = [
    {"match": "A vs B", "market": "1x2", "selection": "home", "book": "pinnacle",
     "price": 1.90, "captured_at": "2026-06-20T10:00:00"},
    {"match": "A vs B", "market": "1x2", "selection": "home", "book": "pinnacle",
     "price": 1.80, "captured_at": "2026-06-20T18:00:00"},
    {"match": "A vs B", "market": "1x2", "selection": "home", "book": "best",
     "price": 1.95, "captured_at": "2026-06-20T10:00:00"},
]


def test_clov_positive_when_you_beat_the_close():
    # took 1.95, sharp closed 1.80 -> positive CLOV
    assert clov(1.95, 1.80) == pytest.approx(1.95 / 1.80 - 1)
    assert clov(1.95, 1.80) > 0
    assert clov(1.70, 1.80) < 0          # took worse than close


def test_open_and_close_pick_first_and_last_by_time():
    assert opening_price(ROWS, "1x2", "home", "pinnacle") == 1.90
    assert closing_price(ROWS, "1x2", "home", "pinnacle") == 1.80   # last in time, not best


def test_line_movement_drift():
    mv = line_movement(ROWS, "1x2", "home", "pinnacle")
    assert mv["open"] == 1.90 and mv["close"] == 1.80
    assert mv["drift_pct"] == pytest.approx(1.80 / 1.90 - 1)        # shortened (negative)
    assert mv["n"] == 2


def test_grade_bet_uses_sharp_close_not_best():
    g = grade_bet(1.95, ROWS, "1x2", "home", book="pinnacle")
    assert g["closing_odds"] == 1.80      # graded vs Pinnacle close, NOT the 1.95 best
    assert g["beat_close"] is True
    assert g["clov"] == pytest.approx(1.95 / 1.80 - 1, abs=1e-4)


def test_grade_bet_missing_book_is_safe():
    g = grade_bet(2.0, ROWS, "1x2", "home", book="williamhill")
    assert g["closing_odds"] is None and g["beat_close"] is None


def test_snapshot_rows_flattens_pinnacle_and_best():
    event = {"home_team": "England", "away_team": "Croatia",
             "commence_time": "2026-06-20T20:00:00Z", "bookmakers": [
        {"key": "pinnacle", "title": "Pinnacle", "markets": [
            {"key": "h2h", "outcomes": [{"name": "England", "price": 1.50},
                                        {"name": "Croatia", "price": 7.0},
                                        {"name": "Draw", "price": 4.2}]}]},
        {"key": "bet365", "title": "Bet365", "markets": [
            {"key": "h2h", "outcomes": [{"name": "England", "price": 1.55},
                                        {"name": "Croatia", "price": 7.5},
                                        {"name": "Draw", "price": 4.3}]}]}]}
    rows = snapshot_rows([event], books=("pinnacle", "best"), captured_at="2026-06-20T10:00:00")
    books = {r["book"] for r in rows}
    assert books == {"pinnacle", "best"}
    home_best = next(r for r in rows if r["book"] == "best" and r["selection"] == "home")
    assert home_best["price"] == 1.55            # best across the two books
    home_pin = next(r for r in rows if r["book"] == "pinnacle" and r["selection"] == "home")
    assert home_pin["price"] == 1.50
    assert all(r["captured_at"] == "2026-06-20T10:00:00" for r in rows)

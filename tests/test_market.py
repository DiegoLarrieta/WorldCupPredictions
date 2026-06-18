"""Pure-logic tests for the model-vs-market comparison (run in CI, no database)."""

from __future__ import annotations

import pytest

from engine.market import compare, devig, vig_of, _ev


# ---- de-vig ----------------------------------------------------------------
def test_devig_sums_to_one_and_removes_margin():
    odds = {"home": 8.0, "draw": 5.5, "away": 1.33}
    p = devig(odds)
    assert sum(p.values()) == pytest.approx(1.0)
    # favourite stays the favourite after de-vig
    assert p["away"] > p["home"] > p["draw"] or p["away"] > p["draw"] > p["home"]
    assert p["away"] == max(p.values())


def test_vig_is_positive_for_real_book():
    # a real bookmaker's overround is > 0
    assert vig_of({"home": 8.0, "draw": 5.5, "away": 1.33}) > 0


def test_devig_matches_sql_method():
    # multiplicative de-vig == raw / overround, same as sql/implied_prob.sql
    odds = {"over": 2.10, "under": 1.75}
    raw = {k: 1 / v for k, v in odds.items()}
    over = sum(raw.values())
    assert devig(odds)["over"] == pytest.approx(raw["over"] / over)


# ---- EV --------------------------------------------------------------------
def test_ev_fair_coin_at_fair_odds_is_zero():
    assert _ev(0.5, 2.0) == pytest.approx(0.0)


def test_ev_positive_when_model_beats_price():
    # model says 60%, price implies 50% -> positive EV
    assert _ev(0.60, 2.0) == pytest.approx(0.20)


# ---- compare ---------------------------------------------------------------
def _prediction():
    return {
        "match": "Iraq vs Norway",
        "as_of": "2026-06-16",
        "win_draw_loss": {"ENSEMBLE": {"Iraq": 0.137, "Draw": 0.24, "Norway": 0.623}},
        "over_under_2_5": {"over": 0.385, "under": 0.615},
        "btts": 0.398,
    }


def test_compare_flags_value_when_model_beats_market():
    # Norway offered at 1.85 (fair ~1.61) while model says 62.3%; longshots priced
    # sharp (no value there) -> Norway is the only value bet, and the best EV.
    cmp = compare(_prediction(), {"1x2": {"home": 6.5, "draw": 3.9, "away": 1.85}})
    away = next(r for r in cmp["markets"]["1x2"]["selections"] if r["selection"] == "away")
    assert away["ev_per_unit"] > 0
    assert away["value"] is True
    assert [r["selection"] for r in cmp["value_bets"]] == ["away"]
    assert cmp["best_ev"]["selection"] == "away"


def test_compare_no_value_when_market_is_sharp():
    # every price sits at/below fair for our model -> no positive-EV selection
    cmp = compare(_prediction(), {"1x2": {"home": 6.5, "draw": 3.9, "away": 1.50}})
    assert cmp["value_bets"] == []


def test_compare_handles_over_under_and_btts():
    cmp = compare(_prediction(), {"ou_2.5": {"over": 3.0, "under": 1.4},
                                  "btts": {"yes": 2.6, "no": 1.5}})
    assert set(cmp["markets"]) == {"ou_2.5", "btts"}
    # model under = 61.5%; at 1.4 that's EV 0.615*1.4-1 = -0.139 -> no value
    under = next(r for r in cmp["markets"]["ou_2.5"]["selections"] if r["selection"] == "under")
    assert under["value"] is False

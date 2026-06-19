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


# ---- Shin / power de-vig ----------------------------------------------------
def test_shin_and_power_sum_to_one():
    odds = {"home": 8.0, "draw": 5.5, "away": 1.33}
    for m in ("shin", "power"):
        p = devig(odds, m)
        assert sum(p.values()) == pytest.approx(1.0, abs=1e-6)


def test_shin_trims_longshot_lifts_favourite():
    # favourite-longshot correction: Shin trims the overbet longshot, lifts the favourite
    odds = {"home": 8.0, "draw": 5.5, "away": 1.33}   # home = longshot, away = favourite
    mult, shin = devig(odds, "multiplicative"), devig(odds, "shin")
    assert shin["home"] < mult["home"]      # longshot gets less (it's overbet)
    assert shin["away"] > mult["away"]      # favourite gets more


def test_power_also_trims_longshot():
    odds = {"home": 8.0, "draw": 5.5, "away": 1.33}
    mult, power = devig(odds, "multiplicative"), devig(odds, "power")
    assert power["home"] < mult["home"]
    assert power["away"] > mult["away"]


def test_devig_methods_agree_when_no_vig():
    # fair two-way book (overround ~0) -> all methods nearly identical
    odds = {"over": 2.0, "under": 2.0}
    m, s, p = devig(odds, "multiplicative"), devig(odds, "shin"), devig(odds, "power")
    assert m["over"] == pytest.approx(0.5)
    assert s["over"] == pytest.approx(0.5, abs=1e-3)
    assert p["over"] == pytest.approx(0.5, abs=1e-3)


def test_unknown_devig_method_raises():
    with pytest.raises(ValueError):
        devig({"a": 2.0, "b": 2.0}, "bogus")


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


# ---- prop EV ---------------------------------------------------------------
def test_prop_ev_flags_over_value():
    from engine.market import prop_ev
    # model 55% over; offered 2.10 -> EV 0.55*2.10-1 = +0.155 -> value
    r = prop_ev(0.55, over_price=2.10, under_price=1.75)
    assert r["best"]["side"] == "over"
    assert r["best"]["ev_per_unit"] > 0
    assert r["value"] is True


def test_prop_ev_picks_under_when_model_is_low():
    from engine.market import prop_ev
    # model 30% over -> 70% under; under at 1.75 -> EV 0.70*1.75-1 = +0.225
    r = prop_ev(0.30, over_price=2.10, under_price=1.75)
    assert r["best"]["side"] == "under"
    assert r["value"] is True


def test_prop_ev_handles_one_sided_book():
    from engine.market import prop_ev
    r = prop_ev(0.5, over_price=2.0, under_price=None)
    assert [s["side"] for s in r["sides"]] == ["over"]
    assert r["sides"][0]["market_prob"] is None      # no de-vig without the pair


def test_prop_ev_does_not_flag_one_sided_even_with_huge_ev():
    from engine.market import prop_ev
    # one-sided longshot: model 9% at 23.0 -> EV +1.07, but no under to de-vig -> NOT value
    r = prop_ev(0.09, over_price=23.0, under_price=None)
    assert r["best"]["ev_per_unit"] > 1.0
    assert r["value"] is False

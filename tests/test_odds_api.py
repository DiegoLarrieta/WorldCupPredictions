"""Pure-parsing tests for the Odds API adapter (run in CI, no network/key)."""

from __future__ import annotations

import pytest

from engine.odds_api import OddsAPIError, extract_odds, find_event


# A trimmed Odds API event in the real v4 shape. Note: API's home_team is Norway
# (nominal) even though our prediction treats Iraq as home — mapping is by name.
EVENT = {
    "home_team": "Norway",
    "away_team": "Iraq",
    "bookmakers": [
        {"key": "pinnacle", "title": "Pinnacle", "markets": [
            {"key": "h2h", "outcomes": [
                {"name": "Norway", "price": 1.55},
                {"name": "Iraq", "price": 7.0},
                {"name": "Draw", "price": 4.2}]},
            {"key": "totals", "outcomes": [
                {"name": "Over", "price": 2.05, "point": 2.5},
                {"name": "Under", "price": 1.78, "point": 2.5}]}]},
        {"key": "bet365", "title": "Bet365", "markets": [
            {"key": "h2h", "outcomes": [
                {"name": "Norway", "price": 1.50},
                {"name": "Iraq", "price": 7.5},      # better price on Iraq here
                {"name": "Draw", "price": 4.3}]},     # better price on Draw here
            {"key": "totals", "outcomes": [
                {"name": "Over", "price": 2.10, "point": 2.5},
                {"name": "Under", "price": 1.75, "point": 2.5}]}]},
    ],
}


def test_find_event_is_order_and_accent_insensitive():
    assert find_event([EVENT], "Iraq", "Norway") is EVENT          # swapped order
    with pytest.raises(OddsAPIError):
        find_event([EVENT], "Brazil", "Norway")


def test_extract_maps_outcomes_to_our_home_away():
    # our home = Iraq even though the API's home_team = Norway
    odds = extract_odds(EVENT, "Iraq", "Norway", book="pinnacle")
    assert odds["1x2"]["home"] == 7.0      # Iraq
    assert odds["1x2"]["away"] == 1.55     # Norway
    assert odds["1x2"]["draw"] == 4.2
    assert odds["ou_2.5"] == {"over": 2.05, "under": 1.78}


def test_best_takes_highest_price_per_selection_across_books():
    odds = extract_odds(EVENT, "Iraq", "Norway", book="best")
    assert odds["1x2"]["home"] == 7.5      # Iraq best is bet365's 7.5
    assert odds["1x2"]["draw"] == 4.3      # Draw best is bet365's 4.3
    assert odds["1x2"]["away"] == 1.55     # Norway best is pinnacle's 1.55
    assert odds["ou_2.5"]["over"] == 2.10  # best over
    assert odds["ou_2.5"]["under"] == 1.78 # best under


def test_named_book_missing_market_raises():
    with pytest.raises(OddsAPIError):
        extract_odds(EVENT, "Iraq", "Norway", book="williamhill")


def test_totals_point_filter_omits_other_lines():
    # only a 3.5 line present -> ou_2.5 absent, but 1x2 still extracted
    ev = {"home_team": "A", "away_team": "B", "bookmakers": [
        {"key": "x", "title": "X", "markets": [
            {"key": "h2h", "outcomes": [
                {"name": "A", "price": 2.0}, {"name": "B", "price": 3.0},
                {"name": "Draw", "price": 3.5}]},
            {"key": "totals", "outcomes": [
                {"name": "Over", "price": 1.9, "point": 3.5},
                {"name": "Under", "price": 1.9, "point": 3.5}]}]}]}
    odds = extract_odds(ev, "A", "B", book="best", totals_point=2.5)
    assert "1x2" in odds and "ou_2.5" not in odds

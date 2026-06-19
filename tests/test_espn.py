"""Pure-parsing tests for the ESPN match-stats adapter (CI, no network)."""

from __future__ import annotations

import pytest

from engine.espn import (ESPNError, find_event_id, parse_player_shots, parse_team_stats,
                         player_minutes, team_for_against)


SCOREBOARD = {"events": [
    {"id": "760435", "competitions": [{"competitors": [
        {"team": {"displayName": "Portugal"}}, {"team": {"displayName": "Congo DR"}}]}]},
    {"id": "760437", "competitions": [{"competitors": [
        {"team": {"displayName": "England"}}, {"team": {"displayName": "Croatia"}}]}]},
]}

SUMMARY = {
    "boxscore": {"teams": [
        {"team": {"displayName": "England"}, "statistics": [
            {"name": "possessionPct", "displayValue": "51.7"},
            {"name": "totalShots", "displayValue": "22"},
            {"name": "shotsOnTarget", "displayValue": "11"},
            {"name": "wonCorners", "displayValue": "8"}]},
        {"team": {"displayName": "Croatia"}, "statistics": [
            {"name": "possessionPct", "displayValue": "48.3"},
            {"name": "totalShots", "displayValue": "9"},
            {"name": "shotsOnTarget", "displayValue": "4"}]},
    ]},
    "rosters": [
        {"team": {"displayName": "England"}, "roster": [
            {"athlete": {"id": "1", "displayName": "Harry Kane"}, "starter": True,
             "subbedOut": True, "stats": [
                {"name": "totalShots", "displayValue": "7"},
                {"name": "shotsOnTarget", "displayValue": "3"},
                {"name": "totalGoals", "displayValue": "2"}]},
            {"athlete": {"id": "2", "displayName": "Jordan Pickford"}, "starter": True,
             "stats": [{"name": "totalShots", "displayValue": "0"},
                       {"name": "saves", "displayValue": "3"}]},
            {"athlete": {"id": "3", "displayName": "Marcus Rashford"}, "starter": False,
             "subbedIn": True, "stats": [{"name": "totalShots", "displayValue": "2"},
                                         {"name": "shotsOnTarget", "displayValue": "1"}]}]},
        {"team": {"displayName": "Croatia"}, "roster": [
            {"athlete": {"id": "4", "displayName": "Petar Musa"}, "starter": True, "stats": [
                {"name": "totalShots", "displayValue": "1"},
                {"name": "shotsOnTarget", "displayValue": "1"}]}]},
    ],
    "keyEvents": [
        {"type": {"type": "substitution"}, "clock": {"value": 4320.0},   # 72'
         "participants": [{"athlete": {"id": "1"}}, {"athlete": {"id": "3"}}]},
    ],
}


def test_find_event_id_token_match_handles_word_order():
    # 'DR Congo' (ours) vs 'Congo DR' (ESPN) must still match
    assert find_event_id(SCOREBOARD, "Portugal", "DR Congo") == "760435"
    assert find_event_id(SCOREBOARD, "Croatia", "England") == "760437"   # order-independent
    with pytest.raises(ESPNError):
        find_event_id(SCOREBOARD, "Brazil", "England")


def test_team_stats_mapped_to_home_away():
    t = parse_team_stats(SUMMARY, "England", "Croatia")
    assert t["home"]["possession"] == 51.7
    assert t["home"]["shots"] == 22 and t["home"]["shots_on_target"] == 11
    assert t["home"]["corners"] == 8
    assert t["away"]["shots"] == 9


def test_player_shots_only_shooters_sorted_desc():
    ps = parse_player_shots(SUMMARY, "England", "Croatia")
    names = [p["player"] for p in ps]
    assert "Jordan Pickford" not in names          # 0 shots -> excluded
    assert names[0] == "Harry Kane"                # sorted by shots desc
    kane = ps[0]
    assert kane["shots"] == 7 and kane["on_target"] == 3 and kane["goals"] == 2
    assert kane["side"] == "home" and kane["starter"] is True
    musa = next(p for p in ps if p["player"] == "Petar Musa")
    assert musa["side"] == "away"


def test_team_stats_name_mismatch_raises():
    with pytest.raises(ESPNError):
        parse_team_stats(SUMMARY, "Spain", "Croatia")


def test_player_minutes_from_starter_and_sub_clock():
    m = player_minutes(SUMMARY)
    assert m["1"] == 72.0      # Kane started, subbed off at 72'
    assert m["2"] == 90.0      # Pickford played the whole match
    assert m["3"] == 18.0      # Rashford came on at 72' -> 90-72
    assert m["4"] == 90.0      # Musa full match


def test_player_shots_includes_minutes_and_per90():
    ps = parse_player_shots(SUMMARY, "England", "Croatia")
    kane = next(p for p in ps if p["player"] == "Harry Kane")
    assert kane["minutes"] == 72.0
    assert kane["shots_p90"] == pytest.approx(7 * 90 / 72, abs=0.01)   # rate scaled up
    rashford = next(p for p in ps if p["player"] == "Marcus Rashford")
    assert rashford["minutes"] == 18.0
    assert rashford["shots_p90"] == pytest.approx(2 * 90 / 18, abs=0.01)  # 2 in 18' -> high rate


def test_team_for_against():
    fa = team_for_against(SUMMARY, "England", "Croatia")
    assert fa["home"]["shots_for"] == 22 and fa["home"]["shots_against"] == 9
    assert fa["home"]["sot_for"] == 11 and fa["home"]["sot_against"] == 4
    assert fa["away"]["shots_for"] == 9 and fa["away"]["shots_against"] == 22

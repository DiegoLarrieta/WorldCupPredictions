"""Pure-parsing tests for the ESPN match-stats adapter (CI, no network)."""

from __future__ import annotations

import pytest

from engine.espn import (ESPNError, find_event_id, parse_player_shots, parse_team_stats)


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
            {"athlete": {"displayName": "Harry Kane"}, "starter": True, "stats": [
                {"name": "totalShots", "displayValue": "7"},
                {"name": "shotsOnTarget", "displayValue": "3"},
                {"name": "totalGoals", "displayValue": "2"}]},
            {"athlete": {"displayName": "Jordan Pickford"}, "starter": True, "stats": [
                {"name": "totalShots", "displayValue": "0"},
                {"name": "saves", "displayValue": "3"}]}]},
        {"team": {"displayName": "Croatia"}, "roster": [
            {"athlete": {"displayName": "Petar Musa"}, "starter": True, "stats": [
                {"name": "totalShots", "displayValue": "1"},
                {"name": "shotsOnTarget", "displayValue": "1"}]}]},
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

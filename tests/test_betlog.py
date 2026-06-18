"""Pure-logic tests for the bet ledger (run in CI, no database; uses a tmp ledger)."""

from __future__ import annotations

import pytest

from engine.betlog import log_bet, settle, summary


def test_log_assigns_ids_and_computes_ev(tmp_path):
    led = tmp_path / "bets.csv"
    a = log_bet("A vs B", "1x2", "home", odds_taken=2.0, model_prob=0.6,
                stake=10, ledger=led)
    b = log_bet("C vs D", "ou_2.5", "under", odds_taken=1.78, model_prob=0.62,
                stake=5, ledger=led)
    assert a["bet_id"] == 1 and b["bet_id"] == 2
    assert a["ev"] == pytest.approx(0.2)        # 0.6*2.0 - 1
    assert a["status"] == "open"


def test_settle_win_pnl_and_clov(tmp_path):
    led = tmp_path / "bets.csv"
    log_bet("A vs B", "1x2", "home", odds_taken=2.0, model_prob=0.6, stake=10, ledger=led)
    r = settle(1, result="win", closing_odds=1.80, ledger=led)
    assert r["pnl"] == pytest.approx(10.0)      # stake*(2.0-1)
    assert r["clov"] == pytest.approx(2.0 / 1.80 - 1, abs=1e-4)   # beat the close
    assert r["status"] == "settled"


def test_settle_loss_and_void(tmp_path):
    led = tmp_path / "bets.csv"
    log_bet("A vs B", "1x2", "home", odds_taken=2.0, model_prob=0.6, stake=10, ledger=led)
    log_bet("C vs D", "1x2", "away", odds_taken=3.0, model_prob=0.3, stake=10, ledger=led)
    assert settle(1, result="loss", ledger=led)["pnl"] == pytest.approx(-10.0)
    assert settle(2, result="void", ledger=led)["pnl"] == pytest.approx(0.0)


def test_settle_rejects_bad_result_and_missing_id(tmp_path):
    led = tmp_path / "bets.csv"
    log_bet("A vs B", "1x2", "home", odds_taken=2.0, model_prob=0.6, stake=10, ledger=led)
    with pytest.raises(ValueError):
        settle(1, result="pending", ledger=led)
    with pytest.raises(KeyError):
        settle(99, result="win", ledger=led)


def test_summary_rolls_up_roi_and_clov(tmp_path):
    led = tmp_path / "bets.csv"
    log_bet("A vs B", "1x2", "home", odds_taken=2.0, model_prob=0.6, stake=10, ledger=led)
    log_bet("C vs D", "1x2", "away", odds_taken=3.0, model_prob=0.3, stake=10, ledger=led)
    log_bet("E vs F", "ou_2.5", "over", odds_taken=2.0, model_prob=0.5, stake=10, ledger=led)
    settle(1, result="win", closing_odds=1.80, ledger=led)   # +10, clov>0
    settle(2, result="loss", closing_odds=3.30, ledger=led)  # -10, clov<0
    s = summary(ledger=led)
    assert s["bets"] == 3 and s["open"] == 1 and s["settled"] == 2
    assert s["staked"] == pytest.approx(20.0)
    assert s["pnl"] == pytest.approx(0.0)        # +10 -10
    assert s["roi"] == pytest.approx(0.0)
    assert s["hit_rate"] == pytest.approx(0.5)   # 1 win of 2 decided
    assert s["beat_close_rate"] == pytest.approx(0.5)   # 1 of 2 clovs positive


def test_summary_empty_ledger_is_safe(tmp_path):
    s = summary(ledger=tmp_path / "none.csv")
    assert s["bets"] == 0 and s["roi"] is None and s["avg_clov"] is None

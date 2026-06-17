"""Pure-logic tests for the feedback loop (run in CI, no database / network).

Covers the scoring numerics, the honest-scoring properties (RPS order, surprisal),
record build + round-trip on a tmp match folder, non-destructive rich backfill, and
the tournament monitor aggregation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from engine import feedback
from engine.feedback import (
    backfill_rich,
    match_key,
    monitor,
    record_outcome,
    result_to_y,
    score_prediction,
    team_code,
)


# ---- keys / outcome mapping ------------------------------------------------
def test_team_code_and_match_key():
    assert team_code("Iraq") == "ira"
    assert team_code("Norway") == "nor"
    assert match_key("2026-06-16", "Iraq", "Norway") == "2026-06-16-ira-nor"


def test_result_to_y():
    assert result_to_y(2, 0) == 0   # home win
    assert result_to_y(1, 1) == 1   # draw
    assert result_to_y(0, 2) == 2   # away win


# ---- scoring numerics ------------------------------------------------------
def test_score_perfect_and_worst():
    assert score_prediction([1.0, 0.0, 0.0], 0)["rps"] == pytest.approx(0.0, abs=1e-4)
    assert score_prediction([1.0, 0.0, 0.0], 2)["rps"] == pytest.approx(1.0, abs=1e-4)


def test_brier_is_multiclass_and_bounded():
    # perfect = 0; certain-and-wrong on the far class = 2.0
    assert score_prediction([1.0, 0.0, 0.0], 0)["brier"] == pytest.approx(0.0, abs=1e-4)
    assert score_prediction([0.0, 0.0, 1.0], 0)["brier"] == pytest.approx(2.0, abs=1e-4)


def test_surprisal_higher_when_more_wrong():
    confident_right = score_prediction([0.8, 0.15, 0.05], 0)["surprisal"]
    confident_wrong = score_prediction([0.8, 0.15, 0.05], 2)["surprisal"]
    assert confident_wrong > confident_right


def test_rps_order_property_via_scorer():
    """Home won: predicting the adjacent draw beats predicting the far away win."""
    adjacent = score_prediction([0.0, 1.0, 0.0], 0)["rps"]
    far = score_prediction([0.0, 0.0, 1.0], 0)["rps"]
    assert adjacent < far


# ---- record build + round-trip ---------------------------------------------
def _stub_prediction(home="Iraq", away="Norway"):
    """A minimal frozen-able prediction.json payload."""
    return {
        "match": f"{home} vs {away}",
        "competition": "World Cup",
        "venue": "neutral",
        "as_of": "2026-06-16",
        "model": "Elo + Dixon-Coles ensemble, temperature-calibrated",
        "ensemble_weight_on_dc": 0.481,
        "calibration_temperature": 0.906,
        "win_draw_loss": {
            "ENSEMBLE": {home: 0.137, "Draw": 0.24, away: 0.623},
            "dixon_coles": {home: 0.158, "Draw": 0.271, away: 0.571},
            "elo": {home: 0.146, "Draw": 0.233, away: 0.622},
        },
        "expected_goals": {home: 0.69, away: 1.54},
        "over_under_2_5": {"over": 0.385, "under": 0.615},
        "btts": 0.398,
        "top_scorelines": [{"score": "0-1", "prob": 0.158}],
        "actual_result": None,
    }


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    """Point the dataset dir at a tmp folder so tests never touch the real one."""
    ds = tmp_path / "worldcupmatches"
    monkeypatch.setattr(feedback, "DATASET_DIR", ds)
    return tmp_path, ds


def _make_match(tmp_path, home="Iraq", away="Norway"):
    mdir = tmp_path / "predictions" / f"{team_code(home)}-{team_code(away)}"
    mdir.mkdir(parents=True)
    (mdir / "prediction.json").write_text(json.dumps(_stub_prediction(home, away)))
    return mdir


def test_record_outcome_builds_record_and_fills_actual(sandbox):
    tmp_path, ds = sandbox
    mdir = _make_match(tmp_path)

    rec = record_outcome(mdir, 0, 2, stage="group", group="E")

    assert rec["match_key"] == "2026-06-16-ira-nor"
    assert rec["outcome"]["spine"]["result"] == "away"          # Norway won
    assert rec["scores"]["y"] == 2
    # we gave the actual outcome 62.3% -> a good (low) RPS
    assert rec["scores"]["rps"] < 0.2
    # per-model scores present for ensemble + both components
    assert set(rec["scores"]["per_model"]) == {"ensemble", "dixon_coles", "elo"}
    # record persisted, and actual_result written back into the match folder
    assert (ds / "2026-06-16-ira-nor.json").exists()
    written = json.loads((mdir / "prediction.json").read_text())
    assert written["actual_result"]["score"] == "0-2"
    assert written["actual_result"]["result"] == "away"


def test_frozen_prediction_carries_params_hash(sandbox):
    tmp_path, _ = sandbox
    mdir = _make_match(tmp_path)
    rec = record_outcome(mdir, 1, 1, stage="group", group="E")
    assert len(rec["prediction"]["params_hash"]) == 16
    assert rec["outcome"]["spine"]["result"] == "draw"


def test_backfill_rich_is_non_destructive(sandbox):
    tmp_path, _ = sandbox
    mdir = _make_match(tmp_path)
    rec = record_outcome(mdir, 0, 2, stage="group", group="E", extra={"xg_home": 0.7})
    key = rec["match_key"]

    updated = backfill_rich(key, xg_away=2.4, possession_home=41)

    # spine + frozen prediction untouched; rich layer merged with provenance
    assert updated["outcome"]["spine"]["result"] == "away"
    assert updated["prediction"]["ensemble"] == rec["prediction"]["ensemble"]
    assert updated["outcome"]["rich"]["xg_home"] == 0.7
    assert updated["outcome"]["rich"]["xg_away"] == 2.4
    assert updated["outcome"]["rich"]["source"] == "fbref"


# ---- monitor ---------------------------------------------------------------
def test_monitor_aggregates_and_beats_uniform(sandbox):
    tmp_path, _ = sandbox
    # two scored matches, both where the ensemble favourite (away, 62%) was right
    m1 = _make_match(tmp_path, "Iraq", "Norway")
    record_outcome(m1, 0, 2, stage="group", group="E")        # away (Norway) 62% -> right
    m2 = _make_match(tmp_path, "Sweden", "Tunisia")
    record_outcome(m2, 0, 1, stage="group", group="F")        # away win -> favourite right

    s = monitor(write=False)

    assert s["n"] == 2
    assert "ensemble" in s["per_model"]
    # a competent model beats the uniform 1/3 baseline on RPS
    assert s["per_model"]["ensemble"]["rps"] < s["vs_baseline"]["uniform"]["rps"]
    assert isinstance(s["ensemble_beats_components"], bool)
    assert len(s["most_surprising"]) <= 3


def test_monitor_empty_is_safe(sandbox):
    s = monitor(write=False)
    assert s == {"n": 0}

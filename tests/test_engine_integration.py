"""Integration tests that need the DuckDB warehouse. The warehouse is gitignored and
built by a slow scrape, so these AUTO-SKIP when it's absent (e.g. in CI) and run
locally after `make data`.
"""

from __future__ import annotations

import pytest

from engine.data import DB_PATH, load_internationals

pytestmark = pytest.mark.skipif(not DB_PATH.exists(),
                                reason="warehouse not built (run `make data`)")


def test_predict_match_structure_and_valid_probs():
    from engine import predict_match
    res = predict_match("Iraq", "Norway", neutral=True, as_of="2026-06-16")
    wdl = res["win_draw_loss"]["ENSEMBLE"]
    assert set(wdl) == {"Iraq", "Draw", "Norway"}
    assert sum(wdl.values()) == pytest.approx(1.0, abs=0.01)
    # all three sub-models present and each a valid distribution
    for key in ("ENSEMBLE", "dixon_coles", "elo"):
        assert sum(res["win_draw_loss"][key].values()) == pytest.approx(1.0, abs=0.01)
    assert res["expected_goals"]["Iraq"] >= 0
    assert 0 <= res["over_under_2_5"]["over"] <= 1


def test_predict_match_rejects_unknown_team():
    from engine import predict_match
    with pytest.raises(ValueError):
        predict_match("Nowhereland", "Norway", as_of="2026-06-16")


def test_no_leakage_in_loaded_window():
    """load_internationals(as_of) must never return a match dated on/after as_of."""
    as_of = "2024-01-01"
    df = load_internationals(as_of)
    assert len(df) > 0
    assert df["date"].max() < pytest.importorskip("pandas").Timestamp(as_of)

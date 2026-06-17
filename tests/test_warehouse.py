"""Integration tests for the rating-refresh warehouse write.

Needs the DuckDB warehouse (gitignored, built by `make data`), so these AUTO-SKIP when
it's absent (e.g. in CI). Every test cleans up its own rows with a unique sentinel source
so the real warehouse is never polluted.
"""

from __future__ import annotations

import pytest

from engine.data import DB_PATH

pytestmark = pytest.mark.skipif(not DB_PATH.exists(),
                                reason="warehouse not built (run `make data`)")

TEST_SOURCE = "pytest-rating-refresh"  # never collides with real wc2026-feedback rows


@pytest.fixture
def clean_source():
    """Guarantee the sentinel source is empty before and after each test."""
    from engine.warehouse import remove_results
    remove_results(TEST_SOURCE)
    yield TEST_SOURCE
    remove_results(TEST_SOURCE)


def _count(source: str) -> int:
    import duckdb
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        return con.execute("SELECT COUNT(*) FROM matches WHERE source = ?", [source]).fetchone()[0]
    finally:
        con.close()


def test_append_result_inserts_one_row(clean_source):
    from engine.warehouse import append_result
    info = append_result("2026-06-16", "Iraq", "Norway", 0, 2, source=clean_source)
    assert _count(clean_source) == 1
    assert info["match"] == "Iraq 0-2 Norway"
    assert isinstance(info["match_id"], int)


def test_append_is_idempotent(clean_source):
    """Re-scoring the same fixture replaces, never duplicates."""
    from engine.warehouse import append_result
    append_result("2026-06-16", "Iraq", "Norway", 0, 2, source=clean_source)
    append_result("2026-06-16", "Iraq", "Norway", 1, 1, source=clean_source)  # corrected score
    assert _count(clean_source) == 1


def test_unknown_team_raises(clean_source):
    from engine.warehouse import append_result
    with pytest.raises(ValueError, match="no history"):
        append_result("2026-06-16", "Nowhereland", "Norway", 0, 2, source=clean_source)
    assert _count(clean_source) == 0


def test_appended_result_changes_the_replay(clean_source):
    """The whole point: a result fed in must move the teams' Elo in the next replay.

    Replay BEFORE the match vs replay AFTER (as_of past the inserted date). The winner's
    rating must rise and the loser's must fall.
    """
    from engine.models.elo import replay_ratings
    from engine.warehouse import append_result

    before = replay_ratings("2026-06-16")
    h, a = "Iraq", "Norway"
    # use a real recent date the warehouse hasn't filled yet for these teams
    append_result("2026-06-15", h, a, 5, 0, source=clean_source)  # lopsided home win
    after = replay_ratings("2026-06-16")

    assert after[h] > before[h]   # big home win lifts the winner
    assert after[a] < before[a]   # and drops the loser


def test_feedback_rows_roundtrip(clean_source):
    from engine.warehouse import append_result, feedback_rows
    # feedback_rows reports the real FEEDBACK_SOURCE; here we just confirm it runs + shape
    append_result("2026-06-16", "Iraq", "Norway", 0, 2, source=clean_source)
    rows = feedback_rows()  # real wc2026-feedback rows (likely empty in test env)
    assert isinstance(rows, list)

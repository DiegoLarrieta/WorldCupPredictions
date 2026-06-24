---
name: score-week
description: Close the feedback loop for a played matchday — pull real results, score the frozen predictions, refresh ratings, extract granular stats, and rebuild the prop model. Use after games finish to "train" the model on what happened (e.g. "score week 2", "update the model with the latest results", "run the feedback loop for matchday 3").
---

# /score-week

The training/feedback step: turn played matches into model updates, in one pass. Wraps
`scripts/score_week.py`, `scripts/fetch_match_stats.py`, and `scripts/build_prop_model.py`.

**Honest scope (say this, don't oversell):** scoring a matchday updates the **ratings**
(Elo replays the results) and **refreshes the prop data** — it does NOT re-fit the model's
parameters (ensemble weight, DC coefficients, calibration temp are fixed on thousands of
games; ~20 results move them negligibly). The value is: ratings current for the next week,
fresher prop sample, and an honest **calibration** read — not "the model got smarter".

## Prereqs
- The week's fixtures exist as `predictions/<week>/**/prediction.json` (run /predict-match
  or the batch generator first). Predictions must be **frozen** (published before kickoff)
  — never re-predict after the result is known; that leaks the outcome into the ratings.
- `ODDS_API_KEY` only needed for `--source oddsapi`. **ESPN needs no key.**

## Steps (in order)
```bash
# 1. Results -> score frozen predictions -> feed warehouse (ratings) -> refresh monitor.
#    --source espn reaches arbitrarily far back; oddsapi /scores only ~3 days.
.venv/bin/python scripts/score_week.py predictions/<week> --source espn

# 2. Granular stats (team for/against + per-player shots) onto the scored records,
#    rebuilds data/csv/derived/player_match_shots.csv (the prop signal).
.venv/bin/python scripts/fetch_match_stats.py predictions/<week>

# 3. Rebuild the prop model on the richer shot sample.
.venv/bin/python scripts/build_prop_model.py
```
Pick `--source`: **espn** for any week more than ~3 days old (and as the no-key default);
**oddsapi** only for results in the last ~3 days if you prefer that feed. In-progress and
not-yet-played games skip cleanly — that's expected, re-run when they finish.

## Reporting
- Lead with the monitor line: matches scored, **ensemble RPS vs uniform** (are we beating
  naive?), and whether the ensemble beats its components. Point at `data/worldcupmatches/_monitor.md`.
- Frame proper scores honestly: beating uniform modestly is normal; 1X2 stays **record-only**
  per the edge test (`predictions/edge-test/`). This step does not create 1X2 edge.
- Note any games skipped (in-progress / no result) so the user knows the loop isn't complete.
- If a game won't match, it's usually a name variant (ESPN aliases live in `engine.espn`)
  or a wrong `as_of` (must equal the match date); fix and re-run, don't hand-wave.

## Reminders
- Scoring uses the **frozen** published prediction (`engine.feedback.record_outcome`), never
  a re-fit — a re-fit leaks the result through online-updated ratings.
- Idempotent: safe to re-run (e.g. to pick up late finishers); it overwrites the rich layer
  and re-appends to the warehouse without duplicating.
- After this, ratings reflect the new results on the next replay, and the prop model carries
  the latest shots — the inputs for the next matchday's /compare-market and /prop-bets.

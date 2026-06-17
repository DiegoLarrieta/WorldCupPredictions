# Design: Feedback Loop — the `worldcupmatches` ground-truth dataset (Step 3)

Branch: `feature/feedback-loop`
Status: PROPOSED — 2026-06-16
Builds on: the validated Elo + Dixon-Coles ensemble (engine/), CI + calibration (Step 2)

## Problem

We publish a probabilistic prediction for each World Cup 2026 match (`predictions/<m>/`).
Diego bets real money on them. The benchmark is **beating the betting line**, which means
we need an honest, running answer to one question: *were our published probabilities any
good?* — match by match and over the tournament.

A finished match we predicted is not "a score to type in." It is a **labeled example**:
the one piece of out-of-sample, real-stakes ground truth our model will ever see for
WC2026. We should capture it like one — richly, with provenance, frozen against what we
actually published — so it can (a) score the prediction, (b) update ratings, and (c)
accumulate into a dataset we mine later for feature validation (host advantage, xG-vs-goals).

## The artifact: `data/worldcupmatches/`

One canonical record per WC2026 match, append-only and versioned. JSON-per-match (human-
diffable, git-friendly) plus a combined CSV/parquet mirror under `data/csv/worldcupmatches/`
to match the existing warehouse-export convention. Records accrete in layers and are never
overwritten destructively — late-arriving xG backfills a record; it does not replace it.

### Schema — three layers that never mix

A record is one JSON object, `data/worldcupmatches/<match_key>.json`, where
`match_key = YYYY-MM-DD-<home_code>-<away_code>` (e.g. `2026-06-16-irq-nor`).

**1. `identity`** — what game this is.
```
match_key, date, home, away, neutral, venue, competition,
stage  (group | r32 | r16 | qf | sf | final | third_place),
group  (A..L, null in knockouts)
```

**2. `prediction`** — a FROZEN snapshot, copied verbatim from `prediction.json` at record
time. This is the immutable "what we published," and scoring uses *this*, never a re-fit.
Re-fitting after the result is in would leak the outcome through online-updated ratings and
flatter us dishonestly.
```
ensemble {home, draw, away},  model, ensemble_weight_on_dc,
calibration_temperature, params_hash (sha256 of engine/params.json),
as_of, xg {home, away}, over25, btts, top_scorelines,
components { dixon_coles{...}, elo{...} }   # to test ensemble vs parts on live data
```

**3. `outcome`** — ground truth, **source-tagged and partially fillable**. Spine lands the
night of the match (manual or martj42); the rich layer backfills from FBref later. Each
group carries `source` ∈ {manual, martj42, fbref} and `captured_at`.
```
spine:  home_goals, away_goals, result (home|draw|away),
        after_extra_time, penalties, decided_by_pens
rich:   xg_home, xg_away, shots_home/away, sot_home/away,
        possession_home/away, corners, cards, goal_timeline[], actual_xi{}
provenance: { spine: {source, captured_at}, rich: {source, captured_at} }
```

**4. `scores`** — computed from layers 2+3, recomputed whenever outcome changes.
```
y (0=home,1=draw,2=away), rps, log_loss, brier_multiclass,
per_model: { ensemble:{rps,ll,brier}, dixon_coles:{...}, elo:{...} },
surprisal  (−log p(actual) — how shocked the model was)
```

### Why this shape (statistician's notes)

- **Freeze the prediction.** Honest out-of-sample scoring compares the published vector to
  the realized outcome. Snapshotting `prediction` (incl. `params_hash`) makes every score
  reproducible and immune to later model changes.
- **Provenance + partial fill.** Live-night you know the score, not the xG. The record
  accepts the spine immediately and backfills rich stats later, each stamped with source and
  time. No field is ever silently of-unknown-origin.
- **Score the components, not just the ensemble.** We claimed the ensemble beats DC and Elo
  alone (CI on held-out internationals). WC2026 is fresh out-of-sample data — store all three
  scores so we can watch whether that holds live, instead of asserting it.
- **Store xG even when goals drive ratings today.** The replay currently updates Elo on
  goal-difference. The "update on xG (less noisy)" experiment needs xG sitting in a clean
  dataset to test against. We capture it now; we flip the rating signal later, gated by the
  validation harness — not in this step.
- **Surprisal as a bet-quality signal.** −log p(actual) flags the matches where the model
  was confidently wrong — exactly the bets worth a post-mortem.

## Modules

- `engine/feedback.py` (importable, unit-tested, CI-safe):
  - `score_prediction(probs_dict, y) -> {rps, log_loss, brier, surprisal}` — reuses
    `engine.evaluate.rps/log_loss`, adds multiclass Brier + surprisal.
  - `record_outcome(match_dir, home_goals, away_goals, *, stage, group=None, extra=None,
    source="manual") -> record` — reads the frozen prediction, builds/updates the
    `worldcupmatches` record, fills `actual_result` in `prediction.json`, computes scores.
  - `backfill_rich(match_key, **stats)` — adds the FBref layer to an existing record.
  - `load_tournament() -> DataFrame` / `monitor() -> writes _monitor.md + _monitor.json`:
    rolling RPS/log-loss/Brier, calibration reliability, ensemble-vs-components, and a
    skill comparison vs baselines (uniform 1/3/1/3, Elo-only) so "are we adding value?"
    has a number, not a vibe.
- `scripts/record_match.py` — thin CLI for live-night spine entry; wraps `record_outcome`.
- Rating refresh: appending a scored WC match into the warehouse `matches`
  (`source='wc2026-feedback'`) makes the next prediction's leakage-safe replay include it.
  `make spine` later re-pulls martj42 and reconciles (CREATE OR REPLACE rebuilds from the
  official source, harmlessly superseding the interim row). **This step builds the dataset +
  scoring + monitor; the warehouse-append and the xG-rating experiment are the next two
  commits**, each its own PR per the workflow.

## Out of scope (separate, harness-gated follow-ups)

- xG-driven rating updates (the experiment) — needs the dataset this step creates.
- Host-nation home advantage and missing-key-player delta (Step 4 features).
- Automated FBref scraping pipeline — `backfill_rich` takes stats; wiring the scrape is later.

## Test plan (CI-safe, no warehouse)

`tests/test_feedback.py`: `score_prediction` numerics (RPS/LL/Brier on hand-checked vectors,
ordering property: a draw-when-away-win scores better than home-when-away-win), record
build/round-trip on a tmp dir with a stub `prediction.json`, partial-fill provenance, and
`monitor` aggregation on two synthetic records.

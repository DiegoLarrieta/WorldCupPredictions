# World Cup Match Predictor

A football match predictor that outputs win/draw/loss probabilities, goal counts,
and over/under per match. Built to bet real money on — so the benchmark is **beating
the closing betting line**, not raw accuracy.

This repo is currently scoped to **Step 1: the data-gathering layer** (modeling and
edge-testing come later).

## Where we are

Design is **APPROVED** (`design/design-step1-data-layer.md`) and we were partway
through `/plan-eng-review` when work paused.

**Locked decisions (from eng review):**
- **Approach 1 — `soccerdata` for ingestion, thin slice first.** Don't build the
  full 9-table warehouse on spec; earn each layer with evidence.
- **`fact_odds` stays long-format** (holds 1X2 + over/under + handicap, and both a
  single closing row *and* multi-snapshot line movement with no schema change).
- **Odds strategy:**
  - Backfill closing odds from **football-data.co.uk** (free, club leagues) to prove
    the implied-probability harness end-to-end.
  - **Snapshot The Odds API live during the 2026 WC, starting now** — the line-movement
    data you'll wish you had for 2022 is the data to log today. ~64 matches × a few
    snapshots/day fits the free tier.
  - Defer the paid sharp-line (Pinnacle via OddsPapi / SportsGameOdds) until the
    backtest shows the harness finds *anything*.

**Open question we stopped on — Architecture issue 2 of 2:**
> The live WC odds-capture cron is a stateful, time-sensitive job (miss a window =
> data lost for 4 years), but the design treats ingestion as "no orchestration until
> there's pain." How robust should the Phase 0 capture job be?
>
> Your steer: **"very robust"** + **"can we scrape it"** (OddsPortal as a fallback
> source for WC closing odds). Research on the OddsPortal scrape path was in flight
> when we paused. **Decide this before relying on the live cron.**

## Phases

```
PHASE 0 (the slice — days)        <-- WE ARE HERE
  soccerdata.MatchHistory  -> results + closing odds  -> DuckDB
  soccerdata.ClubElo       -> team strength
  one SQL view: implied_prob = (1/odds) normalized (vig removed)
  GOAL: a query that, for any past match, shows
        my_naive_prob (Elo-based) vs market_implied_prob vs actual_result

PHASE 1 (formalize — only after the slice shows promise)
  medallion (bronze/silver/gold) + dbt-duckdb + reconciliation test + full star schema

PHASE 2 (richness — only if player form moves the backtest)
  soccerdata.FBref player season stats -> bridge_player_season
```

## The Assignment (next concrete step)

Pull one week of historical closing odds from football-data.co.uk for any league,
load it into a DuckDB `fact_odds` table next to the results, and write the single SQL
query that computes the market's vig-removed implied probability per match. That's
what `src/phase0/ingest.py` + `sql/implied_prob.sql` scaffold below.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python src/phase0/ingest.py        # loads MatchHistory + ClubElo into data/worldcup.duckdb
duckdb data/worldcup.duckdb < sql/implied_prob.sql
```

## Open questions (deferred)

1. Budget: one paid API (API-Football ~$15-30/mo) vs free multi-source?
2. Competition scope: World Cup only, or club leagues that feed player form?
3. The big deferred one: **what is the actual edge over the market?**

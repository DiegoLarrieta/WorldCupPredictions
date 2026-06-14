# Data-Gathering Plan — World Cup Match Predictor

Goal: end with the most complete, cleanest football dataset we can build — full match
history, per-match team stats, per-player stats, and bookmaker odds — structured so
**recency weighting is trivial** and we can always answer *"are we beating the market?"*

Guiding rules (so "gather everything" doesn't become "gather forever"):
1. **Spine first, richness later.** Build the skeleton, then hang muscle on it.
2. **Odds from day one.** They're the scoreboard; without them the rest is unverifiable.
3. **Down-weight, don't delete, old data.** Keep full history; fade it with `exp(-ξ·days_ago)`.
4. **Earn each layer with evidence.** Don't build the player pipeline until the backtest
   says it moves predictions.
5. **Library before scraper.** Use `soccerdata`; hand-roll a scraper only for a source
   we've *proven* we need and no library covers.

---

## Step 0 — Spine + the harness (the thin slice)  ← START HERE
**What:** Land the match backbone and prove the implied-probability query end to end.
- Pull **martj42/international_results** → `fact_match` (every international, the spine).
- **Compute our own Elo** from the martj42 results → `team_elo` (recency-aware national-team
  strength). [ENG REVIEW: ClubElo rates *club* teams only, not national teams — it can't rate
  Brazil/Morocco. We roll Elo from results we already have: `new = old + K·(result − expected)`,
  `K` scaled by match importance + goal margin. No new source, directly recency-tunable, and
  sanity-checkable against eloratings.net's published numbers.]
- Build the **~210-team ISO-keyed seed map** + a **reconciliation test** (0 unmatched teams
  after any join) BEFORE the first cross-source join. [ENG REVIEW: entity resolution isn't
  deferrable — it bites the instant two sources meet. Teams are bounded/stable, so the map is
  an afternoon done once; the test fails loudly on any silent drop.]
- Backfill **closing odds** from football-data.co.uk (via soccerdata, club leagues) → `fact_odds` (long format).
- Write the SQL: market's **vig-removed implied probability** per match (`sql/implied_prob.sql`).

**Why:** This is the cheapest thing that can kill or validate the project. It forces the
schema decision that matters (odds next to results) and gives a backtest target.

**Done when:** One query shows, for any past match: a naive Elo-based probability vs the
market's de-vigged probability vs the actual result.

---

## Step 1 — Recency weighting baked in
**What:** Add a real `date` to every fact (already there) and a computed
`recency_weight = exp(-ξ · days_ago)` at feature-build time. Seed half-life ≈ 12 months.
**Why:** Directly answers "50-year-old matches shouldn't count." Old matches fade toward
zero automatically; `ξ` (the decay rate) becomes a knob we tune against the backtest.
**Done when:** A feature query returns each match with its recency weight, and a match from
10 years ago carries weight ≈ 0.001 while last month's ≈ 1.0.

---

## Step 2 — Team match stats (the first real richness: xG)
**What:** Pull per-match team stats — **xG**, shots, shots on target, possession, pass %,
corners — from **FBref / Understat** (via soccerdata) → `fact_match_team_stats`.
**Why:** xG is the single biggest upgrade over raw goals — it measures chance *quality*
and predicts future results better than past goals. This is where predictions actually improve.
**Done when:** Every match we have stats for shows team xG-for / xG-against, and a query can
compute a team's recent (decay-weighted) average xG.

---

## Step 3 — Lineups + player club-form (the deep player layer)
**What:** Two joined pieces:
- `fact_lineup` — who started each (international) match.
- `bridge_player_season` — each player's **club**-season stats (goals, xG, minutes) from FBref.
- Join rule: a national match joins to the club season *containing or immediately preceding*
  its date — so a player's form reflects the season he was actually in.

**Why:** This is the "stats of each player" you want. Crucial insight: internationals are too
rare (~10/year) to measure a player's form — his real form lives in his **club** matches.
The value is the *join*, player → club season → national lineup.

**Done when:** For an upcoming match's lineup, a query returns each starter's recent club xG
and goals. (This is the layer where scraping may finally be worth the tax — only if Step 2's
backtest shows player form moves the needle.)

---

## Step 4 — Live odds capture (the data money can't buy later)
**What:** A robust cron that snapshots **The Odds API** (free tier, ~40 books) for every
2026 WC match a few times a day → append-only into `fact_odds` (partitioned by capture time).
**Why:** Historical WC line-movement is expensive/unavailable, but we can *record it free,
now*. Miss a window = data lost for 4 years — so this job must be **robust**. [ENG REVIEW
RESOLVED: idempotent re-runnable job + logs every capture + **dead-man alert** (push/email if
a scheduled window produces zero rows) + **OddsPortal scrape fallback** for closing odds if The
Odds API misses. This is the one job worth over-building because the cost of loss is irreversible.]
**Done when:** A scheduled job reliably logs multi-book odds snapshots for live WC matches,
and we can see a line move over time.

---

## Step 5 — Formalize into the warehouse (only once Steps 0–2 show promise)
**What:** Wrap the slice in the medallion pipeline:
- **Bronze** (raw, immutable, partitioned by source/date) → **Silver** (typed, deduped,
  entity-resolved canonical IDs) → **Gold** (feature tables: Elo, rolling form, recency weights).
- Add **dbt-duckdb** data-quality tests (`unique`, `not_null`, `relationships`) plus a
  **reconciliation test** (sum of player goals == match goals — guards against silent join
  bugs that would manufacture a *fake* edge and cost real money).
**Why:** Structure and trust, earned with evidence rather than paid up front.
**Done when:** `dbt test` passes including reconciliation; the gold layer rebuilds from bronze.

---

## Cross-cutting: entity resolution (the part that kills these projects)
The hard part isn't downloading — it's making "Netherlands"/"Holland"/"NED" and
"Vinicius Jr"/"Vinícius Júnior" line up across sources.
- **Teams** (~210): hand-built seed map keyed on ISO country code.
- **Players:** match on `normalize(name) + birthdate + nationality`, fuzzy-match with
  `rapidfuzz`, route low-confidence pairs to a **manual review queue** — never auto-merge
  ambiguous players. `source_id_map` is the crosswalk (each source's native ID → canonical ID).
- `soccerdata`'s cross-source matching IDs do a big chunk of this for free.

## Target end-state schema (where every step lands)
```
fact_match              spine: date, teams, goals, result, venue, neutral
fact_match_team_stats   per match/team: xG, shots, SoT, possession, pass %, corners
fact_lineup             per match/team: player, position, starter, minutes
bridge_player_season    per player/season: club, goals, xG, minutes  (the recency signal)
fact_odds (long)        per match/book/market/selection: price, line, captured_at
team_elo                recency-aware team strength
source_id_map           canonical_id ↔ (source, native_id) crosswalk
```

## What we are deliberately NOT doing yet
- `fact_player_match_stats` (per-player-per-match rows) — heaviest table, secondary signal.
- Paid sharp-line feed (Pinnacle via OddsPapi/SportsGameOdds) — defer until a backtest finds edge.
- The actual prediction model — this whole plan is Step 1 (data); modeling is a later session.
```

## Feasibility note (eng review)
`src/phase0/ingest.py` currently imports ClubElo and runs on Python 3.14. Two follow-ups:
the Elo path must be rewritten to compute national-team Elo from results (above), and
`soccerdata` should be verified against 3.14 (lxml/pandas pins) — fall back to a 3.12 venv if
imports fail.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | issues_resolved | 3 issues, 2 critical test gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

- **VERDICT:** ENG reviewed — 3 architecture issues raised, all 3 resolved with user decisions (own-Elo, robust odds cron + OddsPortal fallback, team seed map + reconciliation test). Ready to implement Phase 0.

NO UNRESOLVED DECISIONS

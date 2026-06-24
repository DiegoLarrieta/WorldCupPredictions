# WorldCupPrediction

A World Cup match predictor built to **make money betting**. The bar is **beating
the closing line (CLOV)**, not raw accuracy. Diego bets real money. Treat every
feature with that bar: a stat is only worth keeping if it produces edge against a
market price, not just a plausible-looking prediction.

## North star

> Beat the closing line on the markets Diego actually bets: **match winner (1X2),
> player shots-on-target (strikers), total goals**. "Interesting stat" is not the
> goal. "Edge vs a real market price" is.

See the approved redirect design doc:
`~/.gstack/projects/WorldCupPrediction/diego-main-design-20260618-160643.md`.

### EDGE TEST RESULT (2026-06-18) — read this before betting main markets
We ran the decisive experiment: a club-level Elo+DC trained on EPL 2023-24, tested
out-of-sample on 2024-25 (363 matches) vs Bet365 **closing** odds
(`predictions/edge-test/`). **The market out-predicts every model** (log-loss: market
0.975 < DC 0.979 < ensemble 1.000 < Elo 1.024). No betting strategy has a positive-ROI
CI above zero. Calibration-vs-market agrees: market ECE 0.019 vs ensemble 0.041, and on
the subset where we most disagree with the line, **we're the wrong one**.
**Conclusion: the model does NOT beat a soft closing line, so it will not beat the WC main
line. Do not treat model-vs-market disagreement on 1X2/O-U as edge.** The opportunity is
soft markets (props) + being faster to a soft price, not out-modeling the sharp close.

### Market tracks (priority order, post-edge-test)
1. **Player props (shots on target)** — now the **primary** target. Softer than main
   markets and where our granular data has a real role. **Full loop built**: model
   (`engine/props.py`) + prop odds (`engine.odds_api.fetch_player_props`, The Odds API US
   books) + EV (`engine.market.prop_ev`) + `scripts/prop_bets.py` (`/prop-bets`). Caveat:
   US books quote SoT props **over-only** (one-sided), which can't be de-vigged — those
   are shown but never flagged as value (a big EV on an un-de-viggable longshot is model
   error). Genuine flags need a two-sided line; still unvalidated, so log + grade via CLOV.
2. **Goals / Over-Under** — secondary. DC emits a goal distribution; softer than 1X2 but
   still efficient. Worth comparing live, not assuming edge.
3. **1X2** — headline bet only. Edge-test says we do NOT beat the close here. Bet it for
   fun/record, not as if the model has an edge over a sharp line.

## The validated model

**Elo + Dixon-Coles ensemble** (`engine/`). Weight w≈0.48 fitted on 2,195 held-out
internationals; beats both single models (log-loss gain +0.0069, 95% CI
[+0.0017, +0.0121]). Temperature calibration applied for honest confidence.
Public API:

```python
from engine import predict_match, save_match
res = predict_match("Iraq", "Norway", neutral=True, lineups=LINEUPS)
save_match(res, Path(__file__).parent)   # writes prediction.json + prediction.md
```

## DISPROVEN — do not rebuild these

These were tested on leakage-free held-out data and **failed**. Rebuilding them is
wasted work; if you think one deserves another look, say so explicitly and bring
new evidence.

- **Club-form layer** (squad form, extra leagues as 1X2 features) — added *zero*
  predictive value over the ensemble. CI-confirmed in `predictions/feature-lab/`.
  Club form does not transfer to internationals over the results-based rating.
- **Striker tilt** — tilting goals by squad attack-form gap *hurt* held-out
  log-loss; fitted coefficient ~0. Removed.
- Kept: possession tilt (tiny effect, passed a weaker ablation).

Lineups/club form are stored as **context** for the record + post-match feedback,
**not** as model inputs.

## Repo layout

- `engine/` — the single validated prediction engine (Elo, DC, ensemble,
  calibration, evaluate, feedback, warehouse). Every match folder calls it; no
  per-match model drift. New signals go live only after passing the validation
  harness.
- `src/phase0/` — the data pipeline (ingest → players → nationality → fbref →
  squads → bridge → backtest → export). Builds `data/worldcup.duckdb` (gitignored).
- `predictions/<match>/` — per-fixture folders (e.g. `ira-nor/`); each is just a
  `predict.py` config that calls the engine, plus generated `prediction.{json,md}`.
- `predictions/feature-lab/`, `predictions/ensemble/` — validation harnesses
  (ablation, permutation, bootstrap CI on leakage-free held-out data).
- `predictions/edge-test/` — **the edge-existence test** (`epl_closing_line.py`,
  `calibration_vs_market.py`) + its `RESULTS*.md`. The decisive "do we beat the close"
  experiment. Re-run if the model changes.
- `engine/props.py` — player shots-on-target prop model (Gamma-Poisson + Beta-Binomial
  shrinkage). `engine/clov.py` — honest CLOV vs the sharp close. `engine/market.py` —
  model-vs-market with Shin/power de-vig.
- `data/csv/` — exported tables, committed to the repo. `.duckdb` is gitignored.
- `sql/implied_prob.sql` — de-vig harness (proven: 760 club matches, vig 0.055,
  fav hit 0.572).
- `design/` — design docs (data model, feedback loop, this redirect).

## How to run

- Python **3.12** venv (soccerdata needs 3.12, not system 3.14): `.venv/bin/python`.
- Full data pipeline: `make data`. Individual stages are Makefile targets
  (`make spine`, `make players`, ...).
- A single match prediction: `cd predictions/<match> && python predict.py`.
- **Model vs market (the bet decision):**
  ```python
  from engine.odds_api import fetch_odds
  from engine.market import compare_folder
  compare_folder("predictions/<match>", fetch_odds("Home", "Away"))
  ```
  Writes `market_compare.{json,md}` beside the prediction: per-outcome model prob,
  de-vigged market prob, edge, and EV per 1u — value bets flagged. Odds come from
  The Odds API (`export ODDS_API_KEY=...`, free tier ~500 req/mo); `book="best"`
  takes the best price per selection, or pass a book key (e.g. `"pinnacle"`) for a
  sharp closing-line proxy. Or pass odds by hand: `compare_folder(folder, {"1x2":
  {"home":7.0,"draw":4.2,"away":1.55}})`.
- **Score a week + refresh ratings:** `python scripts/score_week.py predictions/week1`
  (pulls results from The Odds API `/scores`, scores frozen predictions, feeds results
  into the warehouse so the next week's rating replay reflects them). Single match by
  hand: `scripts/record_match.py`.
- **Granular match stats (team + per-player shots):**
  `python scripts/fetch_match_stats.py predictions/week1` — pulls possession/shots/SoT
  and per-player shots+shots-on-target from **ESPN's open API** (`engine/espn.py`, no
  key), attaches them to each scored record's rich layer, and rebuilds
  `data/csv/derived/player_match_shots.csv`. This is the raw material for the player
  shots-on-target PROP model + calibration — **not** a 1X2 feature (granular stats were
  CI-disproven for the winner market). ESPN is the source because Sofascore/Fotmob are
  Cloudflare-walled; ESPN gives per-player totalShots + shotsOnTarget free.
- **Edge-existence test:** `python predictions/edge-test/epl_closing_line.py` then
  `calibration_vs_market.py` (writes `RESULTS*.md`). Run after any model change to
  re-check whether we beat a real closing line.
- **Prop model:** `python scripts/build_prop_model.py` -> `data/csv/derived/player_shot_rates.csv`
  (shrunk shots/90, on-target rate, P(1+/2+ SoT); filter on `mins`).
- **CLOV capture (run on a schedule):** `python scripts/snapshot_odds.py` appends timestamped
  Pinnacle + best prices to `data/csv/derived/odds_snapshots.csv`. The last snapshot before
  kickoff is the closing line; `engine.clov.grade_bet(...)` scores a bet against the sharp
  close (Pinnacle), not best-price. Capture now — closing lines can't be recovered later.

## Gotchas / hard-won facts

- **football-data.co.uk** odds CSVs: download with a **browser User-Agent**.
  soccerdata's TLS fingerprint gets 503'd; a plain GET with a browser UA returns
  200. (We dropped soccerdata for odds entirely.)
- Elo is **not stored** — `engine.models.elo.replay_ratings` recomputes by
  replaying the whole `matches` table in date order. "Update ratings after a match"
  = insert the result into `matches`; the next replay includes it.
- During the live WC, martj42 (spine upstream) lags days behind. We insert interim
  results tagged `source='wc2026-feedback'`; `make spine` later supersedes them
  from the official source.
- Feedback scoring must use the **frozen** published prediction, never a re-fit
  (a re-fit leaks the result through online-updated ratings).
- Honest betting numbers: RPS (ordered outcomes) is the primary metric, not just
  log-loss.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool.
When in doubt, invoke the skill.

Project skills (in `.claude/skills/`):
- New fixture prediction → invoke **/predict-match**
- Odds / edge / value bet for a fixture → invoke **/compare-market** (honest sharp-vs-soft
  read: recommends only a soft book beating the sharp fair; big model-vs-sharp gaps are
  flagged *suspect*, not value, per the edge test)
- Player shots-on-target prop bets → invoke **/prop-bets** (CLOV-on-overs: SoT is one-sided
  / un-de-viggable, so bet overs where the model beats the vigged price and judge by CLOV)
- Record / settle a bet → invoke **/log-bet**
- Score a played matchday / "train" on results (results → ratings → stats → prop rebuild) →
  invoke **/score-week**
- "Are we profitable / show the scorecard" (CLOV + ROI-with-CI + calibration) → invoke
  **/bet-report**

gstack routing:
- Product ideas / direction / "is this worth building" → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Bugs/errors → invoke /investigate
- Code review/diff check → invoke /review or /code-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save / resume progress → invoke /context-save or /context-restore

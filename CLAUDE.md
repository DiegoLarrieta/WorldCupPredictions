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

### Market tracks (priority order)
1. **1X2** — the only market we currently hold odds for (4,560 rows in
   `match_odds`). So it is the immediate, zero-dependency proving ground for the
   beat-the-line harness. Efficient + hard to beat; we grind it mainly to shake
   down the CLOV machinery and as the headline bet.
2. **Goals / Over-Under** — provable soon. Free O/U + Asian odds exist on
   football-data.co.uk (never ingested yet); the Dixon-Coles model already emits a
   full goal distribution, so O/U probabilities are one transform away.
3. **Player props (shots on target)** — the real prize, **deferred**. Needs a new
   opponent-adjusted player-shot model + a prop-odds source (paid/scraped). Don't
   start until tracks 1-2 prove the harness.

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
- Odds / edge / value bet for a fixture → invoke **/compare-market**
- Record / settle a bet, or betting performance (ROI, CLOV) → invoke **/log-bet**

gstack routing:
- Product ideas / direction / "is this worth building" → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Bugs/errors → invoke /investigate
- Code review/diff check → invoke /review or /code-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save / resume progress → invoke /context-save or /context-restore

---
name: analyze-match
description: Full pre-match betting analysis of a fixture into one analysis.md — model probabilities for every market (1X2, goal lines, BTTS, player shots-on-target) vs the market price, with the honest verdict and what to bet + why. Use when the user says "analyze <match>", "what should we bet on <match>", "give me the read on <fixture>".
---

# /analyze-match

The deliverable: pass a fixture, get **one `analysis.md`** with every market's probability,
the market price, the honest verdict, and the recommendation + reasoning. Orchestrates the
engine prediction + `/compare-market` (sharp-vs-soft) + `/prop-bets` (CLOV-on-overs) and
synthesizes them. Wraps `scripts/analyze_match.py`.

## Prereqs
- A folder with `prediction.json` (run /predict-match first if missing).
- `ODDS_API_KEY` for live mode (1X2/goals odds + player props).

## Steps
```bash
# Live — upcoming fixture, fetch odds + props now:
ODDS_API_KEY=... .venv/bin/python scripts/analyze_match.py predictions/<week>/<grp>/<slug>

# Backtest — finished game, leakage-free (model only sees pre-as_of data); uses the last
# pre-kickoff odds snapshot; props skipped (not snapshotted):
.venv/bin/python scripts/analyze_match.py predictions/<...> --source snapshot
.venv/bin/python scripts/analyze_match.py predictions/<...> --source snapshot --reveal  # + grade
```
Writes `analysis.md` into the folder. The skill should run it, then **read the file back
to the user** as the headline answer.

## What analysis.md contains (and what to emphasise)
- **Probabilities up front** — 1X2, goal lines O/U 1.5/2.5/3.5 (Poisson on total λ), BTTS,
  prop overs. This is the core; the user wants to see the numbers, not just a verdict.
- **The market price** beside each, and the **verdict**: 1X2/goals via sharp-vs-soft
  (recommend only a soft book beating the sharp fair; big model-vs-sharp gaps = *suspect*);
  props via CLOV-on-overs (model beats the vigged price, real-data players only).
- **Recommendation + why**, then caveats.

## Reporting
- Lead with the **Recommendation** section, then walk the probabilities the user asked about.
- "No bet" is the common, correct answer — don't manufacture one. A *suspect* is not a bet.
- For a backtest with `--reveal`, give the honest grade: did our reads hold up? Remember
  **n=1 is noise** — one right/wrong call proves nothing; it's the framework + the CLOV
  record over many that matter.

## Reminders
- This is the pre-match window tool. A started/finished game can only be **backtested**
  (snapshot), never bet — pre-match odds closed at kickoff.
- After it recommends a real bet, capture the close (snapshot near kickoff) and log via
  /log-bet so CLOV can grade it. Then /bet-report rolls it up.
- Snapshot backtests are only as good as the snapshot's freshness — a 20h-old capture is
  stale; flag it. The fix is capturing odds ~30 min before kickoff going forward.

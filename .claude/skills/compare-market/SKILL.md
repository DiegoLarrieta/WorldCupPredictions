---
name: compare-market
description: Compare a match prediction against the betting market with an honest sharp-vs-soft read. Use when the user wants odds, edge, value bets, or "is there a bet here" for a fixture (e.g. "compare the market for Iraq-Norway", "any value on Brazil vs Croatia", "check the odds").
---

# /compare-market

Turn a prediction into an **honest** bet read for the 1X2 / goals markets. Wraps
`engine.market.compare_lines` + `engine.odds_api`.

## The discipline this skill enforces (read before reporting)
The edge test proved we do **NOT** out-predict a sharp close on 1X2/goals. So a big
**model-vs-market gap is NOT value — it's usually us being wrong.** The defensible,
model-independent signal is **soft-vs-sharp**: a soft/best book offering a price *better
than the sharp's de-vigged fair* (`best_odds * sharp_prob > 1`). That's a prospective
CLOV+ — beating the closing line before it closes. Per selection the skill emits a verdict:
- **bet** — best price beats the sharp fair by ≥ 3% (soft book lagging the sharp). The only
  thing to recommend.
- **suspect** — model is ≥5% more bullish than the sharp. Show it, **never recommend it**
  (this is the trap: e.g. our model loving a favourite the sharp prices lower).
- **pass** — no edge.

## Inputs
- A match folder with `prediction.json` (run /predict-match first), or two team names + slug.
- `ODDS_API_KEY` for live odds; else the manual path.

## Steps
1. Ensure the prediction exists (else /predict-match first).
2. **Sharp-vs-soft read** (default — needs `ODDS_API_KEY`):
   ```bash
   ODDS_API_KEY=... .venv/bin/python -c "
   from engine.odds_api import fetch_odds
   from engine.market import compare_lines_folder
   sharp = fetch_odds('<Home>', '<Away>', book='pinnacle')   # the fair line
   soft  = fetch_odds('<Home>', '<Away>', book='best')        # where you'd bet
   cmp = compare_lines_folder('predictions/<slug>', sharp, soft)
   print(open('predictions/<slug>/market_compare.md').read())
   "
   ```
   If `fetch_odds` raises `OddsAPIError` (no key / not listed / wrong sport), go manual.
3. **Manual odds** (paste both a sharp and a soft set):
   ```bash
   .venv/bin/python -c "
   from engine.market import compare_lines_folder
   compare_lines_folder('predictions/<slug>',
       {'1x2': {'home':1.95,'draw':4.05,'away':3.63}},   # sharp (Pinnacle)
       {'1x2': {'home':2.00,'draw':4.10,'away':3.95}})   # best
   "
   ```
   With only one price source, you can't separate soft-edge from model-disagreement — say
   so; don't fall back to naive EV flags.
4. **Report from `market_compare.md`.** Lead with the **recommend** list (soft-price edges)
   or "no soft-price edge — pass" (the common, correct answer). For any large model-vs-sharp
   gap, state plainly it's **suspect, not a bet**, and why (edge test). Don't manufacture a bet.

## Reminders
- Sanity-check a soft-edge before trusting it: tiny edges (~3%) can be de-vig noise or a
  single stale book; a real one is the soft book clearly lagging the sharp. Lineups/rotation
  can explain why the sharp rates a side lower than our model — that's context for the
  suspect call, not a reason to override the sharp.
- After placing a real bet, use /log-bet (capture the closing price → CLOV).
- This skill is 1X2/goals only. Player props are one-sided (un-de-viggable) → use /prop-bets.

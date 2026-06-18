---
name: compare-market
description: Compare a match prediction against the betting market to find value bets. Use when the user wants odds, edge, EV, value bets, or "is there a bet here" for a fixture (e.g. "compare the market for Iraq-Norway", "any value on Brazil vs Croatia", "check the odds").
---

# /compare-market

Turn a prediction into a bet decision: fetch the fixture's odds, de-vig them, line them
up against the ensemble, and surface the value bets. Wraps `engine.market` +
`engine.odds_api`.

## Inputs
- A predicted match folder (must already contain `prediction.json` — run /predict-match
  first if it doesn't), OR two team names + folder slug.
- Odds source: The Odds API by default (needs `ODDS_API_KEY` in the env). If no key, or
  the user pastes odds, use the manual path.

## Steps

1. Ensure the prediction exists. If not, run /predict-match first.

2. **Automated odds** (default — needs `ODDS_API_KEY`):
   ```bash
   ODDS_API_KEY=... .venv/bin/python -c "
   from engine.odds_api import fetch_odds
   from engine.market import compare_folder
   cmp = compare_folder('predictions/<slug>', fetch_odds('<Home>', '<Away>'))
   print(open('predictions/<slug>/market_compare.md').read())
   "
   ```
   `book='best'` (default) takes the best price per selection; pass `book='pinnacle'`
   for a sharp closing-line proxy.

   If `fetch_odds` raises `OddsAPIError` (no key, fixture not listed yet, wrong sport
   key), fall back to manual.

3. **Manual odds** (no key, or user supplies prices):
   ```bash
   .venv/bin/python -c "
   from engine.market import compare_folder
   compare_folder('predictions/<slug>', {
       '1x2':    {'home': 7.0, 'draw': 4.2, 'away': 1.55},
       'ou_2.5': {'over': 2.05, 'under': 1.78},
   })
   "
   ```

4. Report the value bets to the user from `market_compare.md`. Lead with the verdict:
   which selections (if any) clear the EV threshold, the EV per unit, and where the
   model disagrees with the market. **If nothing clears the threshold, say so plainly —
   "no bet" is the correct, common answer.** Don't manufacture a bet.

## Reminders
- The signal that matters is **EV at the price you can actually take**, not just a
  prediction. Edge vs the de-vigged fair line shows *where* we disagree; EV shows
  whether it's bettable.
- After placing a real bet, use /log-bet to record it for the CLOV dataset.
- Default EV threshold is 3% (`engine.market.DEFAULT_EV_THRESHOLD`). Mention it; the
  user can ask to loosen/tighten.

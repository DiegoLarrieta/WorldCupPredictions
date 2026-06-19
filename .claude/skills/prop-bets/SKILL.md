---
name: prop-bets
description: Find player shots-on-target prop bets for a fixture — model vs market EV. Use when the user wants player props, shots-on-target bets, "any prop value", or to check a striker's shot prop (e.g. "prop bets for USA-Australia", "is there value on Haaland shots on target").
---

# /prop-bets

Run the player shots-on-target prop loop for a fixture: pull prop odds (The Odds API, US
books), compare to the shrunk prop model, report EV + value bets. Wraps `engine.props`,
`engine.odds_api.fetch_player_props`, and `engine.market.prop_ev`.

## Prereqs
- `ODDS_API_KEY` set (US prop markets live under `regions=us`; cost a few credits/fixture).
- `data/csv/derived/player_shot_rates.csv` exists — if not, run `scripts/build_prop_model.py`.
- A match folder with `prediction.json` (run /predict-match first) — gives home/away.

## Steps
```bash
ODDS_API_KEY=... .venv/bin/python scripts/prop_bets.py predictions/<week>/<slug>
# options: --minutes 60 (likely sub), --opp 1.2 (leaky defence), --book fanduel, --threshold 0.05
```
Reads the model rates, fetches props, writes `prop_compare.{json,md}` into the folder.

## Reporting
- Lead with value bets if any; otherwise say "no value" plainly — that's the common,
  correct outcome (soft books still often price these right).
- **One-sided lines (over-only, no under) are shown but never flagged as value** — they
  can't be de-vigged, so a big EV there is almost always model error, not edge. Don't
  recommend them as if they're proven.
- Adjust `--minutes` for players unlikely to start; the default assumes a full 90.

## Reminders
- These are CANDIDATE bets, not proven edge. The 1X2 edge test showed the model doesn't
  beat a sharp close; props are softer but the prop model is unvalidated against these
  lines. After placing a bet, use /log-bet and let CLOV judge it over time.
- Players with no club shot data (e.g. A-League, smaller leagues) won't match and are
  skipped — that's a coverage gap, not an error.
- Cross-source names auto-resolve via aliases (United States/USA etc.); add to
  `engine.odds_api._ALIAS_GROUPS` if a fixture won't match.

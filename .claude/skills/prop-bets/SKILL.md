---
name: prop-bets
description: Find player shots-on-target prop bets for a fixture via the CLOV-on-overs loop. Use when the user wants player props, shots-on-target bets, "any prop value", or to check a striker's shot prop (e.g. "prop bets for USA-Australia", "is there value on Haaland shots on target").
---

# /prop-bets

Surface shots-on-target prop bets via **CLOV-on-overs**. Wraps `scripts/prop_bets.py`
(fetch + model) and `scripts/prop_clov.py` (the decision).

## The discipline this skill enforces (read before reporting)
US/UK/EU/AU books quote SoT props **over-only** — no `under`, so the line **can't be
de-vigged** and a pre-bet "value" flag is impossible (a big EV on a one-sided longshot is
**model error**, not edge). So we don't flag EV-value. Instead we bet overs where the
**model beats the offered, vig-included price** (`model_over * over_price > 1`) and let the
**closing price judge us (CLOV)** — no de-vig needed; this is "be faster to a soft price".
Hard rules, baked into `prop_clov.py`:
- **Skip players with no real club shot data** (`shot_rate_raw=NaN` → rate is just the
  position prior; we don't know their rate).
- **Longshot guard:** model_over floor + line cap, so it can't pick one-sided longshots.
- **Big gap = suspect, not value.** A model that's wildly more bullish than the price
  (e.g. +25pts on a one-sided line) is probably wrong — prefer moderate, credible gaps,
  especially for actual strikers over midfielders.

## Prereqs
- `ODDS_API_KEY` (props cost a few credits/fixture). `data/csv/derived/player_shot_rates.csv`
  (run /score-week or `build_prop_model.py` to refresh). A folder with `prediction.json`.

## Steps
```bash
# 1. Fetch props + model -> prop_compare.{json,md} (model_over, over_price per player).
ODDS_API_KEY=... .venv/bin/python scripts/prop_bets.py predictions/<week>/<slug> --lineups
#    --lineups: use ESPN's confirmed XI (~1h pre-kickoff) -> starter ~85 min, bench ~20,
#               so we never bet a non-starter. Falls back to each player's typical min/game
#               if the XI isn't posted yet. --minutes N overrides; --opp 1.2 (leaky defence)

# 2. Decision: the overs where the model beats the vigged price, guarded + real-data only.
.venv/bin/python scripts/prop_clov.py predictions/<week>/<slug>          # dry-run
.venv/bin/python scripts/prop_clov.py predictions/<week>/<slug> --log --stake 1
#    --min 0.5 (model_over floor), --max-line 1.5, --edge 0.0 (min EV at taken price)
```

## Reporting
- Lead with the CLOV candidates from `prop_clov.py` (model% vs price%, EV at the taken
  price). For each, apply judgment: is the gap **credible** (real striker, plausible
  minutes) or a **suspicious blowout** (likely model error)? Recommend only credible ones.
- **If nothing credible survives, say "no bet" plainly** — the common, correct outcome.
- Adjust `--minutes` for players unlikely to start a full 90 (rotation inflates SoT prob).
- Only log with the user's OK (paper bets are records — `data/bets.csv` is committed).

## Reminders
- Candidates are NOT proven edge. We bet small/paper and let **CLOV** (vs the closing
  over-price) judge over many bets — that's the whole point. Capture the close: re-run
  prop_bets.py near kickoff and settle via /log-bet with that over-price as `closing_odds`.
- Players with no club shot data (MLS/Championship/etc.) are skipped by the real-data
  filter — coverage gap, not an error. Names auto-resolve via token-subset matching
  ('Carlos Casemiro' → 'Casemiro'); genuinely unmatched stay out.

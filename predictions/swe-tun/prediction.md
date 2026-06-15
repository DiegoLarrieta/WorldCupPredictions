# Prediction: Sweden vs Tunisia

_World Cup, neutral venue. Model fit on internationals before 2026-06-15 (no leakage)._

## Headline

| Outcome | Probability |
|---|---|
| **Sweden win** | **46%** |
| Draw | 29% |
| **Tunisia win** | **25%** |

- **Expected goals:** Sweden 1.4 – 0.97 Tunisia
- **Over 2.5 goals:** 42%  ·  **BTTS:** 48%
- **Most likely scores:** 1-1 (14%), 1-0 (12%), 0-0 (10%), 2-0 (9%)

## How we got here

1. **Dixon-Coles goals model** (team attack/defence from time-decayed international results) gives base expected goals Sweden 1.18 – 1.2 Tunisia → base W/D/L 35%/30%/36%.
2. **Starting-XI form tilt:** Sweden attacker threat 0.43/90 vs Tunisia 0.06/90 -> +19% goal tilt to Sweden.
3. **Elo cross-check:** Sweden 1776 vs Tunisia 1739 (Sweden 2-way win prob 55%) — same direction, modest favourite.

## Model validation (held-out, leakage-free)

- 1087 held-out internationals · log-loss **0.839** vs base-rate 1.048 · accuracy 61%.
- Beating base-rate log-loss = the model learned real team strength, not noise.

## Lineups used

- Sweden XI: 8/11 players matched to club form.
- Tunisia XI: 7/11 players matched to club form.

## Honest limits

- No international betting odds to validate against — not a value/market call.
- Form coverage ~65% and asymmetric (xG vs goals-only); tilt is capped and supporting.
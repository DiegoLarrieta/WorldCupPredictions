# Prediction: Sweden vs Tunisia

_World Cup, neutral venue. Model fit on internationals before 2026-06-15 (no leakage)._

## Headline

| Outcome | Probability |
|---|---|
| **Sweden win** | **46%** |
| Draw | 29% |
| **Tunisia win** | **26%** |

- **Expected goals:** Sweden 1.39 – 0.98 Tunisia
- **Over 2.5 goals:** 42%  ·  **BTTS:** 48%
- **Most likely scores:** 1-1 (14%), 1-0 (12%), 0-0 (10%), 2-0 (9%)

## How we got here

1. **Dixon-Coles goals model** (team attack/defence from time-decayed international results) gives base expected goals Sweden 1.18 – 1.2 Tunisia → base W/D/L 35%/30%/36%.
2. **Adjustments (striker +19% + possession -0.8% = net +18% to Sweden):**
   - Striker form: Sweden attackers 0.43/90 vs Tunisia 0.06/90 -> +19%
   - Possession (coverage-scaled): Sweden 44% (n=19) vs Tunisia 48% (n=6), confidence 0.25 -> -0.8% (shrunk for thin data)
3. **Elo cross-check:** Sweden 1776 vs Tunisia 1739 (Sweden 2-way win prob 55%) — same direction, modest favourite.

## Data confidence (uneven data, handled honestly)

- Sweden: 8/11 XI matched to club form, 19 tournament matches of possession.
- Tunisia: 7/11 XI matched, 6 possession matches.
- Tunisia is thinner on both club form and possession, so its signals are down-weighted; the prediction leans more on Elo for Tunisia.

## Model validation (held-out, leakage-free)

- 1087 held-out internationals · log-loss **0.839** vs base-rate 1.048 · accuracy 61%.
- Beating base-rate log-loss = the model learned real team strength, not noise.

## Lineups used

- Sweden XI: 8/11 players matched to club form.
- Tunisia XI: 7/11 players matched to club form.

## Honest limits

- No international betting odds to validate against — not a value/market call.
- Form coverage ~65% and asymmetric (xG vs goals-only); tilt is capped and supporting.
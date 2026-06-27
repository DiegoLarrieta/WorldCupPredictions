# WC2026 prediction monitor — 56 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1704 | 0.8947 | 0.5369 |
| dixon_coles | 0.1669 | 0.8791 | 0.5253 |
| elo | 0.1786 | 0.9245 | 0.5564 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2361, log-loss 1.0986
- **Our ensemble**: RPS 0.1704, log-loss 0.8947
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

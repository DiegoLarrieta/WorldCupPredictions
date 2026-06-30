# WC2026 prediction monitor — 74 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1663 | 0.9120 | 0.5472 |
| dixon_coles | 0.1645 | 0.9000 | 0.5386 |
| elo | 0.1728 | 0.9374 | 0.5632 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2282, log-loss 1.0986
- **Our ensemble**: RPS 0.1663, log-loss 0.9120
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

# WC2026 prediction monitor — 70 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1677 | 0.9078 | 0.5449 |
| dixon_coles | 0.1655 | 0.8954 | 0.5360 |
| elo | 0.1742 | 0.9335 | 0.5608 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2302, log-loss 1.0986
- **Our ensemble**: RPS 0.1677, log-loss 0.9078
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

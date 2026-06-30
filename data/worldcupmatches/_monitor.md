# WC2026 prediction monitor — 75 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1665 | 0.9102 | 0.5458 |
| dixon_coles | 0.1653 | 0.9001 | 0.5385 |
| elo | 0.1726 | 0.9345 | 0.5609 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2289, log-loss 1.0986
- **Our ensemble**: RPS 0.1665, log-loss 0.9102
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

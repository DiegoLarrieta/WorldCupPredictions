# WC2026 prediction monitor — 73 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1669 | 0.9078 | 0.5445 |
| dixon_coles | 0.1652 | 0.8971 | 0.5367 |
| elo | 0.1733 | 0.9323 | 0.5599 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2298, log-loss 1.0986
- **Our ensemble**: RPS 0.1669, log-loss 0.9078
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

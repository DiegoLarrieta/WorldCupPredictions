# WC2026 prediction monitor — 3 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1463 | 0.8646 | 0.5366 |
| dixon_coles | 0.1406 | 0.8319 | 0.5018 |
| elo | 0.1591 | 0.9255 | 0.5789 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2222, log-loss 1.0986
- **Our ensemble**: RPS 0.1463, log-loss 0.8646
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Portugal vs DR Congo → draw (surprisal 1.50)
- England vs Croatia → home (surprisal 0.62)
- Iraq vs Norway → away (surprisal 0.47)

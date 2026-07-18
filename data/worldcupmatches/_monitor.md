# WC2026 prediction monitor — 97 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1625 | 0.8675 | 0.5130 |
| dixon_coles | 0.1674 | 0.8802 | 0.5219 |
| elo | 0.1654 | 0.8803 | 0.5202 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2365, log-loss 1.0986
- **Our ensemble**: RPS 0.1625, log-loss 0.8675
- Ensemble beats both single models so far: **yes**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

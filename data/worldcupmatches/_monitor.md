# WC2026 prediction monitor — 46 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1715 | 0.9323 | 0.5695 |
| dixon_coles | 0.1671 | 0.9105 | 0.5525 |
| elo | 0.1789 | 0.9612 | 0.5880 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2271, log-loss 1.0986
- **Our ensemble**: RPS 0.1715, log-loss 0.9323
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- Ecuador vs Curaçao → draw (surprisal 1.97)
- England vs Ghana → draw (surprisal 1.93)

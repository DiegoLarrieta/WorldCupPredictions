# WC2026 prediction monitor — 81 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1620 | 0.8820 | 0.5250 |
| dixon_coles | 0.1638 | 0.8840 | 0.5259 |
| elo | 0.1665 | 0.9002 | 0.5361 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2325, log-loss 1.0986
- **Our ensemble**: RPS 0.1620, log-loss 0.8820
- Ensemble beats both single models so far: **yes**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

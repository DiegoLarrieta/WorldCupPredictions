# WC2026 prediction monitor — 76 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1647 | 0.9015 | 0.5396 |
| dixon_coles | 0.1638 | 0.8929 | 0.5332 |
| elo | 0.1707 | 0.9253 | 0.5545 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2295, log-loss 1.0986
- **Our ensemble**: RPS 0.1647, log-loss 0.9015
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

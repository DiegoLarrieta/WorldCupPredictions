# WC2026 prediction monitor — 95 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1617 | 0.8680 | 0.5134 |
| dixon_coles | 0.1670 | 0.8820 | 0.5233 |
| elo | 0.1639 | 0.8791 | 0.5195 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2357, log-loss 1.0986
- **Our ensemble**: RPS 0.1617, log-loss 0.8680
- Ensemble beats both single models so far: **yes**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

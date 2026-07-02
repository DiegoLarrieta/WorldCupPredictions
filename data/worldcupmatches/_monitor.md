# WC2026 prediction monitor — 80 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1634 | 0.8887 | 0.5299 |
| dixon_coles | 0.1646 | 0.8886 | 0.5294 |
| elo | 0.1681 | 0.9077 | 0.5415 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2319, log-loss 1.0986
- **Our ensemble**: RPS 0.1634, log-loss 0.8887
- Ensemble beats both single models so far: **yes**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

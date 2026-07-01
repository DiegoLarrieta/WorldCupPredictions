# WC2026 prediction monitor — 77 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1657 | 0.9027 | 0.5403 |
| dixon_coles | 0.1659 | 0.8985 | 0.5368 |
| elo | 0.1709 | 0.9234 | 0.5530 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2302, log-loss 1.0986
- **Our ensemble**: RPS 0.1657, log-loss 0.9027
- Ensemble beats both single models so far: **yes**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

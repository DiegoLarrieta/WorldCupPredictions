# WC2026 prediction monitor — 52 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1747 | 0.9202 | 0.5562 |
| dixon_coles | 0.1710 | 0.9023 | 0.5429 |
| elo | 0.1819 | 0.9478 | 0.5740 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2329, log-loss 1.0986
- **Our ensemble**: RPS 0.1747, log-loss 0.9202
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- South Africa vs South Korea → home (surprisal 2.06)
- Ecuador vs Curaçao → draw (surprisal 1.97)

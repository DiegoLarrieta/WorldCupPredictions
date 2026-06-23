# WC2026 prediction monitor — 24 matches scored

_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we
actually published (frozen), on real out-of-sample matches._

## Proper scores by model

| Model | RPS | Log-loss | Brier |
|---|---|---|---|
| ensemble | 0.1973 | 1.0607 | 0.6602 |
| dixon_coles | 0.1881 | 1.0193 | 0.6299 |
| elo | 0.2048 | 1.0908 | 0.6798 |

## Are we beating naive?

- Uniform (1/3 each): RPS 0.2153, log-loss 1.0986
- **Our ensemble**: RPS 0.1973, log-loss 1.0607
- Ensemble beats both single models so far: **NO — investigate**

## Most surprising results (confidently-wrong watch)

- Spain vs Cape Verde → draw (surprisal 2.33)
- Ivory Coast vs Ecuador → home (surprisal 1.86)
- Qatar vs Switzerland → draw (surprisal 1.83)

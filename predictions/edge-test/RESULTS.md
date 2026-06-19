# EPL closing-line edge test — 363 out-of-sample matches (season 2024-25)

_Train: 2023-24. Test: 2024-25. Ensemble weight on DC = 0.35. Mean Bet365 overround (vig) = 5.5%. Market de-vigged with Shin._

## Predictive accuracy vs the market (lower is better)

| Model | Log-loss | RPS | Brier |
|---|---|---|---|
| market (Shin) | 0.9752 | 0.2005 | 0.5817 |
| market (mult) | 0.9750 | 0.2004 | 0.5813 |
| ensemble | 0.9999 | 0.2088 | 0.5996 |
| dixon_coles | 0.9788 | 0.2028 | 0.5851 |
| elo | 1.0243 | 0.2150 | 0.6140 |

**Does our best model beat the market as a predictor? NO** (ensemble log-loss 0.9999 vs market 0.9752).

## Flat-stake betting simulation (1u per qualifying selection, at Bet365 odds)

| Model | EV threshold | Bets | ROI | 95% CI |
|---|---|---|---|---|
| ensemble | 0% | 318 | -0.070 | [-0.214, +0.084] |
| ensemble | 3% | 263 | -0.084 | [-0.245, +0.088] |
| ensemble | 5% | 226 | -0.076 | [-0.246, +0.112] |
| dixon_coles | 0% | 369 | +0.081 | [-0.101, +0.264] |
| dixon_coles | 3% | 304 | +0.091 | [-0.111, +0.291] |
| dixon_coles | 5% | 270 | +0.145 | [-0.066, +0.362] |
| elo | 0% | 341 | -0.067 | [-0.194, +0.077] |
| elo | 3% | 293 | -0.092 | [-0.231, +0.060] |
| elo | 5% | 258 | -0.111 | [-0.260, +0.055] |

## Verdict

- Beats the closing line as a predictor: **NO**.
- Any positive-ROI strategy with CI above zero (real edge, not noise): **NO**.

_If both are NO: the approach does not beat a soft real market, so it will not beat the WC main line. Pivot to props / soft books — do not bet WC 1X2/O-U as if the model has edge._

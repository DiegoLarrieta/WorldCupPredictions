# Calibration vs market — 363 out-of-sample EPL matches (2024-25)

_ECE = expected calibration error (lower is better): average gap between the predicted probability and how often it actually happened._

## Overall calibration error

| Source | ECE |
|---|---|
| market (Shin) | 0.0190 |
| ensemble | 0.0406 |
| dixon_coles | 0.0178 |
| elo | 0.0653 |

## Per-outcome ECE (home / draw / away)

| Source | home | draw | away |
|---|---|---|---|
| market (Shin) | 0.0570 | 0.0121 | 0.0511 |
| ensemble | 0.0722 | 0.0312 | 0.0661 |
| dixon_coles | 0.0286 | 0.0275 | 0.0595 |

## Reliability — ensemble (predicted vs observed)

| Prob bin | n | mean predicted | observed |
|---|---|---|---|
| 0.0-0.1 | 80 | 0.067 | 0.100 |
| 0.1-0.2 | 218 | 0.158 | 0.220 |
| 0.2-0.3 | 337 | 0.238 | 0.243 |
| 0.3-0.4 | 110 | 0.346 | 0.373 |
| 0.4-0.5 | 108 | 0.446 | 0.435 |
| 0.5-0.6 | 79 | 0.546 | 0.557 |
| 0.6-0.7 | 61 | 0.645 | 0.508 |
| 0.7-0.8 | 68 | 0.742 | 0.574 |
| 0.8-0.9 | 25 | 0.844 | 0.800 |
| 0.9-1.0 | 3 | 0.917 | 1.000 |

## The subset check (where we disagree most with the line)

- Top-quartile disagreement: 91 matches.
- Ensemble log-loss there: 1.1010 vs market 1.0056.
- Better than the market on its own disagreement subset: **NO**.

## Verdict

- Better calibrated than the market overall: **NO** (ECE 0.0406 vs 0.0190).
- Better where we most disagree with the line: **NO**.

_Calibration confirms the edge test: the market is at least as well calibrated everywhere we looked, including where we disagree with it most. No subset edge on this market — reinforces pivoting to props / soft books rather than betting the main line._

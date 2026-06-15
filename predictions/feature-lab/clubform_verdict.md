# Does club form add ANYTHING to international predictions? (firmer test)

_Two leakage-clean windows (2024-25 form 2324, 2025-26 form 2425), DC refit per window, 226 held-out internationals, 5-fold CV, bootstrap CI. Current-squad proxy._

## Result

| Model | held-out log-loss |
|---|---|
| Dixon-Coles alone | 1.0271 |
| Dixon-Coles + club-attack tilt | 1.0330 |
| **Improvement** | **-0.0060** |
| **Bootstrap 95% CI** | **[-0.0108, -0.0012]** |

- Fitted tilt coefficient: **-0.00** (hand-tuned was 0.50). Per fold: [np.float64(-0.15), np.float64(-0.01), np.float64(-0.01), np.float64(-0.05), np.float64(0.23)]

## Verdict

Club attack form **HURTS — significantly worse**.

_If the CI spans zero, the international-results model (Elo / Dixon-Coles) already prices in attacking quality — the club-form layer adds no reliable predictive value on top, and we should not build more of it (e.g. defensive club form) expecting gains._
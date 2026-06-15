# Does the striker tilt actually help? (ablation)

_Dixon-Coles fit before 2025-06-01; tested on 154 later internationals between squad-form teams. 5-fold CV, leakage-aware. Current-squad proxy → directional._

## Result

| Model | held-out log-loss |
|---|---|
| Dixon-Coles alone | 1.0048 |
| Dixon-Coles + striker tilt | 1.0190 |
| **Improvement** | **-0.0142** |

- Fitted tilt coefficient (beta): **-0.06** (the hand-tuned value was 0.50).
- Per-fold betas: [np.float64(0.23), np.float64(-0.15), np.float64(0.03), np.float64(-0.16), np.float64(-0.23)]

## Verdict

The striker tilt is **HARMFUL — hurts held-out prediction**.

_If justified, we adopt the fitted beta and trust the Sweden lean. If not, the +19% that drove the prediction was overrated and should be cut or shrunk._
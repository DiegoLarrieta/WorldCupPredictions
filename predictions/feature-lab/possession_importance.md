# Does national-team possession help predict international results?

_International tournaments only (WC/Euro/Copa/AFCON/Nations League/Gold Cup/Asian Cup). Leakage-free pre-match rolling features. 247 matches, 75 held-out._

## Results

- Base-rate log-loss: **1.1415**
- Full model: **1.0981**

| Feature group | log-loss without it | damage (higher = more useful) |
|---|---|---|
| possession | 1.1240 | +0.0260 |
| attack form (goals for) | 1.0854 | -0.0126 |
| defence form (goals against) | 1.0585 | -0.0395 |

## Verdict on possession

Removing national possession changes held-out log-loss by **+0.0260** → possession **HELPS**.

_Possession correlates with winning, but most of that is already captured by goal-scoring form/strength. This measures what it adds **on top** — the only thing that matters for prediction. Caveat: national possession is tournament-only and sparse, so treat as directional._
# Does national-team possession help predict international results?

_International tournaments only (WC/Euro/Copa/AFCON/Nations League/Gold Cup/Asian Cup). Leakage-free pre-match rolling features. 922 matches, 277 held-out._

## Results

- Base-rate log-loss: **1.1005**
- Full model: **1.0281**

| Feature group | log-loss without it | damage (higher = more useful) |
|---|---|---|
| possession | 1.0389 | +0.0108 |
| attack form (goals for) | 1.0339 | +0.0058 |
| defence form (goals against) | 1.0328 | +0.0047 |

## Verdict on possession

Removing national possession changes held-out log-loss by **+0.0108** → possession **HELPS**.

_Possession correlates with winning, but most of that is already captured by goal-scoring form/strength. This measures what it adds **on top** — the only thing that matters for prediction. Caveat: national possession is tournament-only and sparse, so treat as directional._
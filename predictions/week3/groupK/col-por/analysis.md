# Analysis — Colombia vs Portugal

_as_of 2026-06-27 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Colombia 45%** · Draw 26% · **Portugal 28%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 45% | 19% | +900 | **pass** |
| draw | 26% | 54% | +235 | **bet** |
| away | 28% | 26% | +740 | **bet** |

## Goals (total)

- Expected goals: Colombia 1.47 – 1.17 Portugal  (total λ 2.64)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 74% | — | — |
| 2.5 | 49% | — | — |
| 3.5 | 27% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Colombia | 72% | — | — |
| Doble oport. Portugal | 55% | — | — |
| Over 1.5 goles Colombia | 43% | — | — |
| Over 1.5 goles Portugal | 33% | — | — |
| BTTS (ambos marcan) | 54% | — | — |
| Tiros Colombia over 9.5 | 93% | — | — |
| Tiros Portugal over 9.5 | 79% | — | — |
| TaP Colombia over 2.5 | 89% | — | — |
| TaP Portugal over 2.5 | 79% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Colombia 0–0 Portugal** (draw, 0 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Colombia | 45% | no | ✅ |
| Empate | 26% | sí | ❌ |
| Gana Portugal | 28% | no | ✅ |
| Doble oport. Colombia | 72% | sí | ✅ |
| Doble oport. Portugal | 55% | sí | ✅ |
| Over 1.5 goles | 74% | no | ❌ |
| Over 2.5 goles | 49% | no | ✅ |
| Over 3.5 goles | 27% | no | ✅ |
| Over 1.5 goles Colombia | 43% | no | ✅ |
| Over 1.5 goles Portugal | 33% | no | ✅ |
| BTTS | 54% | no | ❌ |

**Checks acertados: 8/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

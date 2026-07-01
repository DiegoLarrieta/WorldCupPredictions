# Analysis — Mexico vs Ecuador

_as_of 2026-07-01 · source: snapshot (snapshot 2026-06-30T18:10:45-06:00)_

## 1X2 (match winner)

- Model: **Mexico 37%** · Draw 33% · **Ecuador 30%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 37% | 43% | +132 | **pass** |
| draw | 33% | 34% | +194 | **pass** |
| away | 30% | 23% | +340 | **bet** |

## Goals (total)

- Expected goals: Mexico 0.65 – 0.78 Ecuador  (total λ 1.43)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 42% | — | — |
| 2.5 | 17% | +210 | -0.46 |
| 3.5 | 6% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Mexico | 70% | — | — |
| Doble oport. Ecuador | 63% | — | — |
| Over 1.5 goles Mexico | 14% | — | — |
| Over 1.5 goles Ecuador | 18% | — | — |
| BTTS (ambos marcan) | 27% | — | — |
| Tiros Mexico over 9.5 | 29% | — | — |
| Tiros Ecuador over 9.5 | 43% | — | — |
| TaP Mexico over 2.5 | 48% | — | — |
| TaP Ecuador over 2.5 | 58% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **1x2 away** @ +340 — soft price beats the sharp fair by +5.5% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Mexico 2–0 Ecuador** (home, 2 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Mexico | 37% | sí | ❌ |
| Empate | 33% | no | ✅ |
| Gana Ecuador | 30% | no | ✅ |
| Doble oport. Mexico | 70% | sí | ✅ |
| Doble oport. Ecuador | 63% | no | ❌ |
| Over 1.5 goles | 42% | sí | ❌ |
| Over 2.5 goles | 17% | no | ✅ |
| Over 3.5 goles | 6% | no | ✅ |
| Over 1.5 goles Mexico | 14% | sí | ❌ |
| Over 1.5 goles Ecuador | 18% | no | ✅ |
| BTTS | 27% | no | ✅ |

**Checks acertados: 7/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

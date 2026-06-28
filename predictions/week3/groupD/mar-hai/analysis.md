# Analysis — Morocco vs Haiti

_as_of 2026-06-24 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Morocco 75%** · Draw 18% · **Haiti 7%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 75% | 46% | +120 | **bet** |
| draw | 18% | 30% | +243 | **bet** |
| away | 7% | 24% | +300 | **pass** |

## Goals (total)

- Expected goals: Morocco 1.8 – 0.52 Haiti  (total λ 2.32)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 67% | — | — |
| 2.5 | 41% | +132 | -0.05 |
| 3.5 | 20% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Morocco | 93% | — | — |
| Doble oport. Haiti | 25% | — | — |
| Over 1.5 goles Morocco | 54% | — | — |
| Over 1.5 goles Haiti | 10% | — | — |
| BTTS (ambos marcan) | 34% | — | — |
| Tiros Morocco over 9.5 | 98% | — | — |
| Tiros Haiti over 9.5 | 17% | — | — |
| TaP Morocco over 2.5 | 95% | — | — |
| TaP Haiti over 2.5 | 38% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Morocco 4–2 Haiti** (home, 6 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Morocco | 75% | sí | ✅ |
| Empate | 18% | no | ✅ |
| Gana Haiti | 7% | no | ✅ |
| Doble oport. Morocco | 93% | sí | ✅ |
| Doble oport. Haiti | 25% | no | ✅ |
| Over 1.5 goles | 67% | sí | ✅ |
| Over 2.5 goles | 41% | sí | ❌ |
| Over 3.5 goles | 20% | sí | ❌ |
| Over 1.5 goles Morocco | 54% | sí | ✅ |
| Over 1.5 goles Haiti | 10% | sí | ❌ |
| BTTS | 34% | sí | ❌ |

**Checks acertados: 7/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

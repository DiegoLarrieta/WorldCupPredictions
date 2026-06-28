# Analysis — Scotland vs Brazil

_as_of 2026-06-24 · source: snapshot (snapshot 2026-06-24T16:00:07-06:00)_

## 1X2 (match winner)

- Model: **Scotland 15%** · Draw 22% · **Brazil 64%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 15% | 9% | +1050 | **pass** |
| draw | 22% | 18% | +510 | **pass** |
| away | 64% | 73% | -278 | **pass** |

## Goals (total)

- Expected goals: Scotland 0.76 – 2.13 Brazil  (total λ 2.89)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 78% | — | — |
| 2.5 | 55% | -112 | +0.04 |
| 3.5 | 33% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Scotland | 36% | — | — |
| Doble oport. Brazil | 85% | — | — |
| Over 1.5 goles Scotland | 18% | — | — |
| Over 1.5 goles Brazil | 63% | — | — |
| BTTS (ambos marcan) | 47% | — | — |
| Tiros Scotland over 9.5 | 41% | — | — |
| Tiros Brazil over 9.5 | 100% | — | — |
| TaP Scotland over 2.5 | 57% | — | — |
| TaP Brazil over 2.5 | 98% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Scotland 0–3 Brazil** (away, 3 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Scotland | 15% | no | ✅ |
| Empate | 22% | no | ✅ |
| Gana Brazil | 64% | sí | ✅ |
| Doble oport. Scotland | 36% | no | ✅ |
| Doble oport. Brazil | 85% | sí | ✅ |
| Over 1.5 goles | 78% | sí | ✅ |
| Over 2.5 goles | 55% | sí | ✅ |
| Over 3.5 goles | 33% | no | ✅ |
| Over 1.5 goles Scotland | 18% | no | ✅ |
| Over 1.5 goles Brazil | 63% | sí | ✅ |
| BTTS | 47% | no | ✅ |

**Checks acertados: 11/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

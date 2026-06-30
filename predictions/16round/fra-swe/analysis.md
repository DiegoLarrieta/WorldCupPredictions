# Analysis — France vs Sweden

_as_of 2026-06-30 · source: snapshot (snapshot 2026-06-30T14:51:48-06:00)_

## 1X2 (match winner)

- Model: **France 78%** · Draw 15% · **Sweden 7%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 78% | 76% | -312 | **pass** |
| draw | 15% | 16% | +540 | **pass** |
| away | 7% | 8% | +1150 | **pass** |

## Goals (total)

- Expected goals: France 2.54 – 0.98 Sweden  (total λ 3.52)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 87% | — | — |
| 2.5 | 68% | -217 | -0.00 |
| 3.5 | 47% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. France | 93% | — | — |
| Doble oport. Sweden | 22% | — | — |
| Over 1.5 goles France | 72% | — | — |
| Over 1.5 goles Sweden | 26% | — | — |
| BTTS (ambos marcan) | 58% | — | — |
| Tiros France over 9.5 | 100% | — | — |
| Tiros Sweden over 9.5 | 64% | — | — |
| TaP France over 2.5 | 99% | — | — |
| TaP Sweden over 2.5 | 70% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **France 3–0 Sweden** (home, 3 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana France | 78% | sí | ✅ |
| Empate | 15% | no | ✅ |
| Gana Sweden | 7% | no | ✅ |
| Doble oport. France | 93% | sí | ✅ |
| Doble oport. Sweden | 22% | no | ✅ |
| Over 1.5 goles | 87% | sí | ✅ |
| Over 2.5 goles | 68% | sí | ✅ |
| Over 3.5 goles | 47% | no | ✅ |
| Over 1.5 goles France | 72% | sí | ✅ |
| Over 1.5 goles Sweden | 26% | no | ✅ |
| BTTS | 58% | no | ❌ |

**Checks acertados: 10/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

# Analysis — Jordan vs Argentina

_as_of 2026-06-27 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Jordan 3%** · Draw 11% · **Argentina 86%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 3% | 5% | +2400 | **pass** |
| draw | 11% | 10% | +900 | **pass** |
| away | 86% | 85% | -588 | **pass** |

## Goals (total)

- Expected goals: Jordan 0.41 – 2.74 Argentina  (total λ 3.15)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 82% | — | — |
| 2.5 | 61% | -175 | -0.04 |
| 3.5 | 39% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Jordan | 14% | — | — |
| Doble oport. Argentina | 97% | — | — |
| Over 1.5 goles Jordan | 6% | — | — |
| Over 1.5 goles Argentina | 76% | — | — |
| BTTS (ambos marcan) | 32% | — | — |
| Tiros Jordan over 9.5 | 9% | — | — |
| Tiros Argentina over 9.5 | 100% | — | — |
| TaP Jordan over 2.5 | 29% | — | — |
| TaP Argentina over 2.5 | 99% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Jordan 1–3 Argentina** (away, 4 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Jordan | 3% | no | ✅ |
| Empate | 11% | no | ✅ |
| Gana Argentina | 86% | sí | ✅ |
| Doble oport. Jordan | 14% | no | ✅ |
| Doble oport. Argentina | 97% | sí | ✅ |
| Over 1.5 goles | 82% | sí | ✅ |
| Over 2.5 goles | 61% | sí | ✅ |
| Over 3.5 goles | 39% | sí | ❌ |
| Over 1.5 goles Jordan | 6% | no | ✅ |
| Over 1.5 goles Argentina | 76% | sí | ✅ |
| BTTS | 32% | sí | ❌ |

**Checks acertados: 9/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

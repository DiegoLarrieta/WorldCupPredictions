# Analysis — Netherlands vs Morocco

_as_of 2026-06-30 · source: snapshot (snapshot 2026-06-29T18:09:15-06:00)_

## 1X2 (match winner)

- Model: **Netherlands 37%** · Draw 30% · **Morocco 34%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 37% | 40% | +148 | **pass** |
| draw | 30% | 31% | +227 | **bet** |
| away | 34% | 29% | +300 | **bet** |

## Goals (total)

- Expected goals: Netherlands 0.98 – 1.1 Morocco  (total λ 2.08)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 62% | — | — |
| 2.5 | 34% | +130 | -0.21 |
| 3.5 | 16% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Netherlands | 66% | — | — |
| Doble oport. Morocco | 63% | — | — |
| Over 1.5 goles Netherlands | 26% | — | — |
| Over 1.5 goles Morocco | 30% | — | — |
| BTTS (ambos marcan) | 43% | — | — |
| Tiros Netherlands over 9.5 | 64% | — | — |
| Tiros Morocco over 9.5 | 74% | — | — |
| TaP Netherlands over 2.5 | 70% | — | — |
| TaP Morocco over 2.5 | 76% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Netherlands 1–1 Morocco** (draw, 2 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Netherlands | 37% | no | ✅ |
| Empate | 30% | sí | ❌ |
| Gana Morocco | 34% | no | ✅ |
| Doble oport. Netherlands | 66% | sí | ✅ |
| Doble oport. Morocco | 63% | sí | ✅ |
| Over 1.5 goles | 62% | sí | ✅ |
| Over 2.5 goles | 34% | no | ✅ |
| Over 3.5 goles | 16% | no | ✅ |
| Over 1.5 goles Netherlands | 26% | no | ✅ |
| Over 1.5 goles Morocco | 30% | no | ✅ |
| BTTS | 43% | sí | ❌ |

**Checks acertados: 9/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

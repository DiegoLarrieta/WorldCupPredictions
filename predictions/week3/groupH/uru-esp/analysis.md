# Analysis — Uruguay vs Spain

_as_of 2026-06-26 · source: snapshot (snapshot 2026-06-26T12:54:12-06:00)_

## 1X2 (match winner)

- Model: **Uruguay 18%** · Draw 27% · **Spain 55%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 18% | 15% | +560 | **pass** |
| draw | 27% | 27% | +270 | **pass** |
| away | 55% | 58% | -133 | **bet** |

## Goals (total)

- Expected goals: Uruguay 0.8 – 1.15 Spain  (total λ 1.95)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 58% | — | — |
| 2.5 | 31% | +136 | -0.27 |
| 3.5 | 13% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Uruguay | 45% | — | — |
| Doble oport. Spain | 82% | — | — |
| Over 1.5 goles Uruguay | 19% | — | — |
| Over 1.5 goles Spain | 32% | — | — |
| BTTS (ambos marcan) | 38% | — | — |
| Tiros Uruguay over 9.5 | 46% | — | — |
| Tiros Spain over 9.5 | 78% | — | — |
| TaP Uruguay over 2.5 | 59% | — | — |
| TaP Spain over 2.5 | 78% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **1x2 away** @ -133 — soft price beats the sharp fair by +3.6% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Uruguay 0–1 Spain** (away, 1 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Uruguay | 18% | no | ✅ |
| Empate | 27% | no | ✅ |
| Gana Spain | 55% | sí | ✅ |
| Doble oport. Uruguay | 45% | no | ✅ |
| Doble oport. Spain | 82% | sí | ✅ |
| Over 1.5 goles | 58% | no | ❌ |
| Over 2.5 goles | 31% | no | ✅ |
| Over 3.5 goles | 13% | no | ✅ |
| Over 1.5 goles Uruguay | 19% | no | ✅ |
| Over 1.5 goles Spain | 32% | no | ✅ |
| BTTS | 38% | no | ✅ |

**Checks acertados: 10/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

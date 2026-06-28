# Analysis — Panama vs England

_as_of 2026-06-27 · source: snapshot (snapshot 2026-06-27T14:51:19-06:00)_

## 1X2 (match winner)

- Model: **Panama 9%** · Draw 19% · **England 72%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 9% | 6% | +2300 | **pass** |
| draw | 19% | 10% | +900 | **pass** |
| away | 72% | 84% | -526 | **pass** |

## Goals (total)

- Expected goals: Panama 0.63 – 2.09 England  (total λ 2.72)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 76% | — | — |
| 2.5 | 51% | -250 | -0.28 |
| 3.5 | 29% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Panama | 28% | — | — |
| Doble oport. England | 91% | — | — |
| Over 1.5 goles Panama | 13% | — | — |
| Over 1.5 goles England | 62% | — | — |
| BTTS (ambos marcan) | 42% | — | — |
| Tiros Panama over 9.5 | 27% | — | — |
| Tiros England over 9.5 | 100% | — | — |
| TaP Panama over 2.5 | 47% | — | — |
| TaP England over 2.5 | 97% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Panama 0–2 England** (away, 2 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Panama | 9% | no | ✅ |
| Empate | 19% | no | ✅ |
| Gana England | 72% | sí | ✅ |
| Doble oport. Panama | 28% | no | ✅ |
| Doble oport. England | 91% | sí | ✅ |
| Over 1.5 goles | 76% | sí | ✅ |
| Over 2.5 goles | 51% | no | ❌ |
| Over 3.5 goles | 29% | no | ✅ |
| Over 1.5 goles Panama | 13% | no | ✅ |
| Over 1.5 goles England | 62% | sí | ✅ |
| BTTS | 42% | no | ✅ |

**Checks acertados: 10/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

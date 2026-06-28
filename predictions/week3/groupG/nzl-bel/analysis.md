# Analysis — New Zealand vs Belgium

_as_of 2026-06-26 · source: snapshot (snapshot 2026-06-26T12:54:12-06:00)_

## 1X2 (match winner)

- Model: **New Zealand 16%** · Draw 23% · **Belgium 62%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 16% | 6% | +1650 | **pass** |
| draw | 23% | 12% | +750 | **pass** |
| away | 62% | 82% | -455 | **pass** |

## Goals (total)

- Expected goals: New Zealand 0.86 – 1.95 Belgium  (total λ 2.81)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 77% | — | — |
| 2.5 | 53% | -323 | -0.30 |
| 3.5 | 31% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. New Zealand | 38% | — | — |
| Doble oport. Belgium | 84% | — | — |
| Over 1.5 goles New Zealand | 21% | — | — |
| Over 1.5 goles Belgium | 58% | — | — |
| BTTS (ambos marcan) | 50% | — | — |
| Tiros New Zealand over 9.5 | 52% | — | — |
| Tiros Belgium over 9.5 | 99% | — | — |
| TaP New Zealand over 2.5 | 63% | — | — |
| TaP Belgium over 2.5 | 96% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **New Zealand 1–5 Belgium** (away, 6 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana New Zealand | 16% | no | ✅ |
| Empate | 23% | no | ✅ |
| Gana Belgium | 62% | sí | ✅ |
| Doble oport. New Zealand | 38% | no | ✅ |
| Doble oport. Belgium | 84% | sí | ✅ |
| Over 1.5 goles | 77% | sí | ✅ |
| Over 2.5 goles | 53% | sí | ✅ |
| Over 3.5 goles | 31% | sí | ❌ |
| Over 1.5 goles New Zealand | 21% | no | ✅ |
| Over 1.5 goles Belgium | 58% | sí | ✅ |
| BTTS | 50% | sí | ✅ |

**Checks acertados: 10/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

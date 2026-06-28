# Analysis — Mexico vs Czech Republic

_as_of 2026-06-24 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Mexico 64%** · Draw 22% · **Czech Republic 14%**

## Goals (total)

- Expected goals: Mexico 1.63 – 0.84 Czech Republic  (total λ 2.47)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 71% | — | — |
| 2.5 | 45% | +157 | +0.15 |
| 3.5 | 24% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Mexico | 86% | — | — |
| Doble oport. Czech Republic | 36% | — | — |
| Over 1.5 goles Mexico | 48% | — | — |
| Over 1.5 goles Czech Republic | 21% | — | — |
| BTTS (ambos marcan) | 46% | — | — |
| Tiros Mexico over 9.5 | 96% | — | — |
| Tiros Czech Republic over 9.5 | 50% | — | — |
| TaP Mexico over 2.5 | 92% | — | — |
| TaP Czech Republic over 2.5 | 62% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Mexico 3–0 Czech Republic** (home, 3 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Mexico | 64% | sí | ✅ |
| Empate | 22% | no | ✅ |
| Gana Czech Republic | 14% | no | ✅ |
| Doble oport. Mexico | 86% | sí | ✅ |
| Doble oport. Czech Republic | 36% | no | ✅ |
| Over 1.5 goles | 71% | sí | ✅ |
| Over 2.5 goles | 45% | sí | ❌ |
| Over 3.5 goles | 24% | no | ✅ |
| Over 1.5 goles Mexico | 48% | sí | ❌ |
| Over 1.5 goles Czech Republic | 21% | no | ✅ |
| BTTS | 46% | no | ✅ |

**Checks acertados: 9/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

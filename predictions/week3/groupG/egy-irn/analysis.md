# Analysis — Egypt vs Iran

_as_of 2026-06-26 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Egypt 29%** · Draw 29% · **Iran 42%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 29% | 29% | +250 | **bet** |
| draw | 29% | 32% | +210 | **pass** |
| away | 42% | 38% | +160 | **bet** |

## Goals (total)

- Expected goals: Egypt 0.89 – 1.19 Iran  (total λ 2.08)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 62% | — | — |
| 2.5 | 34% | +180 | -0.03 |
| 3.5 | 16% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Egypt | 58% | — | — |
| Doble oport. Iran | 71% | — | — |
| Over 1.5 goles Egypt | 22% | — | — |
| Over 1.5 goles Iran | 33% | — | — |
| BTTS (ambos marcan) | 42% | — | — |
| Tiros Egypt over 9.5 | 55% | — | — |
| Tiros Iran over 9.5 | 81% | — | — |
| TaP Egypt over 2.5 | 65% | — | — |
| TaP Iran over 2.5 | 80% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Egypt 1–1 Iran** (draw, 2 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Egypt | 29% | no | ✅ |
| Empate | 29% | sí | ❌ |
| Gana Iran | 42% | no | ✅ |
| Doble oport. Egypt | 58% | sí | ✅ |
| Doble oport. Iran | 71% | sí | ✅ |
| Over 1.5 goles | 62% | sí | ✅ |
| Over 2.5 goles | 34% | no | ✅ |
| Over 3.5 goles | 16% | no | ✅ |
| Over 1.5 goles Egypt | 22% | no | ✅ |
| Over 1.5 goles Iran | 33% | no | ✅ |
| BTTS | 42% | sí | ❌ |

**Checks acertados: 9/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

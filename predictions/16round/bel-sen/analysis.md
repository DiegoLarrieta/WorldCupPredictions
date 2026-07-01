# Analysis — Belgium vs Senegal

_as_of 2026-07-01 · source: snapshot (snapshot 2026-07-01T13:23:15-06:00)_

## 1X2 (match winner)

- Model: **Belgium 45%** · Draw 27% · **Senegal 28%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 45% | 49% | +120 | **bet** |
| draw | 27% | 28% | +252 | **pass** |
| away | 28% | 23% | +335 | **bet** |

## Goals (total)

- Expected goals: Belgium 1.37 – 1.13 Senegal  (total λ 2.50)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 71% | — | — |
| 2.5 | 46% | -120 | -0.17 |
| 3.5 | 24% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Belgium | 72% | — | — |
| Doble oport. Senegal | 55% | — | — |
| Over 1.5 goles Belgium | 40% | — | — |
| Over 1.5 goles Senegal | 31% | — | — |
| BTTS (ambos marcan) | 51% | — | — |
| Tiros Belgium over 9.5 | 90% | — | — |
| Tiros Senegal over 9.5 | 77% | — | — |
| TaP Belgium over 2.5 | 86% | — | — |
| TaP Senegal over 2.5 | 78% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Belgium 3–2 Senegal** (home, 5 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Belgium | 45% | sí | ❌ |
| Empate | 27% | no | ✅ |
| Gana Senegal | 28% | no | ✅ |
| Doble oport. Belgium | 72% | sí | ✅ |
| Doble oport. Senegal | 55% | no | ❌ |
| Over 1.5 goles | 71% | sí | ✅ |
| Over 2.5 goles | 46% | sí | ❌ |
| Over 3.5 goles | 24% | sí | ❌ |
| Over 1.5 goles Belgium | 40% | sí | ❌ |
| Over 1.5 goles Senegal | 31% | sí | ❌ |
| BTTS | 51% | sí | ✅ |

**Checks acertados: 5/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

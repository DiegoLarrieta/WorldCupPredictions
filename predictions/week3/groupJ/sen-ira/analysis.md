# Analysis — Senegal vs Iraq

_as_of 2026-06-26 · source: snapshot (snapshot 2026-06-26T12:54:12-06:00)_

## 1X2 (match winner)

- Model: **Senegal 61%** · Draw 24% · **Iraq 15%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 61% | 79% | -417 | **pass** |
| draw | 24% | 13% | +700 | **pass** |
| away | 15% | 8% | +1500 | **pass** |

## Goals (total)

- Expected goals: Senegal 1.51 – 0.67 Iraq  (total λ 2.18)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 64% | — | — |
| 2.5 | 37% | -200 | -0.44 |
| 3.5 | 18% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Senegal | 85% | — | — |
| Doble oport. Iraq | 39% | — | — |
| Over 1.5 goles Senegal | 45% | — | — |
| Over 1.5 goles Iraq | 14% | — | — |
| BTTS (ambos marcan) | 39% | — | — |
| Tiros Senegal over 9.5 | 94% | — | — |
| Tiros Iraq over 9.5 | 31% | — | — |
| TaP Senegal over 2.5 | 90% | — | — |
| TaP Iraq over 2.5 | 50% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Senegal 5–0 Iraq** (home, 5 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Senegal | 61% | sí | ✅ |
| Empate | 24% | no | ✅ |
| Gana Iraq | 15% | no | ✅ |
| Doble oport. Senegal | 85% | sí | ✅ |
| Doble oport. Iraq | 39% | no | ✅ |
| Over 1.5 goles | 64% | sí | ✅ |
| Over 2.5 goles | 37% | sí | ❌ |
| Over 3.5 goles | 18% | sí | ❌ |
| Over 1.5 goles Senegal | 45% | sí | ❌ |
| Over 1.5 goles Iraq | 14% | no | ✅ |
| BTTS | 39% | no | ✅ |

**Checks acertados: 8/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

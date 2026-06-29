# Analysis — Brazil vs Japan

_as_of 2026-06-29 · source: snapshot (snapshot 2026-06-29T10:16:12-06:00)_

## 1X2 (match winner)

- Model: **Brazil 48%** · Draw 27% · **Japan 25%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 48% | 53% | -115 | **pass** |
| draw | 27% | 27% | +310 | **bet** |
| away | 25% | 20% | +440 | **pass** |

## Goals (total)

- Expected goals: Brazil 1.33 – 1.08 Japan  (total λ 2.41)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 69% | — | — |
| 2.5 | 43% | +127 | -0.02 |
| 3.5 | 22% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Brazil | 75% | — | — |
| Doble oport. Japan | 52% | — | — |
| Over 1.5 goles Brazil | 38% | — | — |
| Over 1.5 goles Japan | 29% | — | — |
| BTTS (ambos marcan) | 50% | — | — |
| Tiros Brazil over 9.5 | 88% | — | — |
| Tiros Japan over 9.5 | 73% | — | — |
| TaP Brazil over 2.5 | 85% | — | — |
| TaP Japan over 2.5 | 75% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **1x2 draw** @ +310 — soft price beats the sharp fair by +13.9% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Brazil 2–1 Japan** (home, 3 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Brazil | 48% | sí | ❌ |
| Empate | 27% | no | ✅ |
| Gana Japan | 25% | no | ✅ |
| Doble oport. Brazil | 75% | sí | ✅ |
| Doble oport. Japan | 52% | no | ❌ |
| Over 1.5 goles | 69% | sí | ✅ |
| Over 2.5 goles | 43% | sí | ❌ |
| Over 3.5 goles | 22% | no | ✅ |
| Over 1.5 goles Brazil | 38% | sí | ❌ |
| Over 1.5 goles Japan | 29% | no | ✅ |
| BTTS | 50% | sí | ❌ |

**Checks acertados: 6/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

# Analysis — Norway vs France

_as_of 2026-06-26 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Norway 26%** · Draw 26% · **France 49%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 26% | 26% | +300 | **bet** |
| draw | 26% | 27% | +273 | **bet** |
| away | 49% | 47% | +116 | **bet** |

## Goals (total)

- Expected goals: Norway 1.23 – 1.61 France  (total λ 2.84)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 78% | — | — |
| 2.5 | 54% | -105 | +0.05 |
| 3.5 | 32% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Norway | 51% | — | — |
| Doble oport. France | 74% | — | — |
| Over 1.5 goles Norway | 35% | — | — |
| Over 1.5 goles France | 48% | — | — |
| BTTS (ambos marcan) | 57% | — | — |
| Tiros Norway over 9.5 | 83% | — | — |
| Tiros France over 9.5 | 96% | — | — |
| TaP Norway over 2.5 | 82% | — | — |
| TaP France over 2.5 | 92% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **ou_2.5 under** @ +102 — soft price beats the sharp fair by +4.1% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Norway 1–4 France** (away, 5 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Norway | 26% | no | ✅ |
| Empate | 26% | no | ✅ |
| Gana France | 49% | sí | ❌ |
| Doble oport. Norway | 51% | no | ❌ |
| Doble oport. France | 74% | sí | ✅ |
| Over 1.5 goles | 78% | sí | ✅ |
| Over 2.5 goles | 54% | sí | ✅ |
| Over 3.5 goles | 32% | sí | ❌ |
| Over 1.5 goles Norway | 35% | no | ✅ |
| Over 1.5 goles France | 48% | sí | ❌ |
| BTTS | 57% | sí | ✅ |

**Checks acertados: 7/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

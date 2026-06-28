# Analysis — South Africa vs Canada

_as_of 2026-06-28 · source: snapshot (snapshot 2026-06-28T12:19:15-06:00)_

## 1X2 (match winner)

- Model: **South Africa 18%** · Draw 27% · **Canada 55%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 18% | 19% | +465 | **pass** |
| draw | 27% | 28% | +280 | **bet** |
| away | 55% | 53% | -114 | **pass** |

## Goals (total)

- Expected goals: South Africa 0.6 – 1.35 Canada  (total λ 1.95)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 58% | — | — |
| 2.5 | 31% | +136 | -0.27 |
| 3.5 | 13% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. South Africa | 45% | — | — |
| Doble oport. Canada | 82% | — | — |
| Over 1.5 goles South Africa | 12% | — | — |
| Over 1.5 goles Canada | 39% | — | — |
| BTTS (ambos marcan) | 34% | — | — |
| Tiros South Africa over 9.5 | 24% | — | — |
| Tiros Canada over 9.5 | 89% | — | — |
| TaP South Africa over 2.5 | 45% | — | — |
| TaP Canada over 2.5 | 86% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **1x2 draw** @ +280 — soft price beats the sharp fair by +10.1% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **South Africa 0–1 Canada** (away, 1 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana South Africa | 18% | no | ✅ |
| Empate | 27% | no | ✅ |
| Gana Canada | 55% | sí | ✅ |
| Doble oport. South Africa | 45% | no | ✅ |
| Doble oport. Canada | 82% | sí | ✅ |
| Over 1.5 goles | 58% | no | ❌ |
| Over 2.5 goles | 31% | no | ✅ |
| Over 3.5 goles | 13% | no | ✅ |
| Over 1.5 goles South Africa | 12% | no | ✅ |
| Over 1.5 goles Canada | 39% | no | ✅ |
| BTTS | 34% | no | ✅ |

**Checks acertados: 10/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

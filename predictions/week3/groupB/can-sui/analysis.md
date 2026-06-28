# Analysis — Canada vs Switzerland

_as_of 2026-06-24 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Canada 33%** · Draw 29% · **Switzerland 38%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 33% | 17% | +525 | **pass** |
| draw | 29% | 26% | +275 | **pass** |
| away | 38% | 57% | -133 | **pass** |

## Goals (total)

- Expected goals: Canada 1.04 – 1.15 Switzerland  (total λ 2.19)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 64% | — | — |
| 2.5 | 38% | +123 | -0.16 |
| 3.5 | 18% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Canada | 62% | — | — |
| Doble oport. Switzerland | 67% | — | — |
| Over 1.5 goles Canada | 28% | — | — |
| Over 1.5 goles Switzerland | 32% | — | — |
| BTTS (ambos marcan) | 45% | — | — |
| Tiros Canada over 9.5 | 70% | — | — |
| Tiros Switzerland over 9.5 | 78% | — | — |
| TaP Canada over 2.5 | 74% | — | — |
| TaP Switzerland over 2.5 | 78% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Canada 1–2 Switzerland** (away, 3 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Canada | 33% | no | ✅ |
| Empate | 29% | no | ✅ |
| Gana Switzerland | 38% | sí | ❌ |
| Doble oport. Canada | 62% | no | ❌ |
| Doble oport. Switzerland | 67% | sí | ✅ |
| Over 1.5 goles | 64% | sí | ✅ |
| Over 2.5 goles | 38% | sí | ❌ |
| Over 3.5 goles | 18% | no | ✅ |
| Over 1.5 goles Canada | 28% | no | ✅ |
| Over 1.5 goles Switzerland | 32% | sí | ❌ |
| BTTS | 45% | sí | ❌ |

**Checks acertados: 6/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

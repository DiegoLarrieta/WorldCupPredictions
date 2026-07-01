# Analysis — England vs DR Congo

_as_of 2026-07-01 · source: snapshot (snapshot 2026-07-01T09:13:44-06:00)_

## 1X2 (match winner)

- Model: **England 66%** · Draw 24% · **DR Congo 10%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 66% | 76% | -312 | **pass** |
| draw | 24% | 18% | +450 | **pass** |
| away | 10% | 6% | +1650 | **pass** |

## Goals (total)

- Expected goals: England 1.24 – 0.5 DR Congo  (total λ 1.74)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 52% | — | — |
| 2.5 | 25% | +113 | -0.46 |
| 3.5 | 10% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. England | 90% | — | — |
| Doble oport. DR Congo | 34% | — | — |
| Over 1.5 goles England | 35% | — | — |
| Over 1.5 goles DR Congo | 9% | — | — |
| BTTS (ambos marcan) | 28% | — | — |
| Tiros England over 9.5 | 84% | — | — |
| Tiros DR Congo over 9.5 | 15% | — | — |
| TaP England over 2.5 | 82% | — | — |
| TaP DR Congo over 2.5 | 36% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **ou_2.5 over** @ +113 — soft price beats the sharp fair by +3.9% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **England 2–1 DR Congo** (home, 3 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana England | 66% | sí | ✅ |
| Empate | 24% | no | ✅ |
| Gana DR Congo | 10% | no | ✅ |
| Doble oport. England | 90% | sí | ✅ |
| Doble oport. DR Congo | 34% | no | ✅ |
| Over 1.5 goles | 52% | sí | ✅ |
| Over 2.5 goles | 25% | sí | ❌ |
| Over 3.5 goles | 10% | no | ✅ |
| Over 1.5 goles England | 35% | sí | ❌ |
| Over 1.5 goles DR Congo | 9% | no | ✅ |
| BTTS | 28% | sí | ❌ |

**Checks acertados: 8/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

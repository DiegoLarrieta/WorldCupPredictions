# Analysis — Japan vs Sweden

_as_of 2026-06-25 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Japan 73%** · Draw 17% · **Sweden 10%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 73% | 57% | -135 | **suspect** |
| draw | 17% | 25% | +310 | **bet** |
| away | 10% | 18% | +500 | **pass** |

## Goals (total)

- Expected goals: Japan 2.57 – 0.81 Sweden  (total λ 3.38)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 85% | — | — |
| 2.5 | 66% | +108 | +0.36 |
| 3.5 | 44% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Japan | 90% | — | — |
| Doble oport. Sweden | 27% | — | — |
| Over 1.5 goles Japan | 73% | — | — |
| Over 1.5 goles Sweden | 20% | — | — |
| BTTS (ambos marcan) | 52% | — | — |
| Tiros Japan over 9.5 | 100% | — | — |
| Tiros Sweden over 9.5 | 47% | — | — |
| TaP Japan over 2.5 | 99% | — | — |
| TaP Sweden over 2.5 | 60% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **1x2 draw** @ +310 — soft price beats the sharp fair by +5.7% (prospective CLOV+).

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Japan 1–1 Sweden** (draw, 2 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Japan | 73% | no | ❌ |
| Empate | 17% | sí | ❌ |
| Gana Sweden | 10% | no | ✅ |
| Doble oport. Japan | 90% | sí | ✅ |
| Doble oport. Sweden | 27% | sí | ❌ |
| Over 1.5 goles | 85% | sí | ✅ |
| Over 2.5 goles | 66% | no | ❌ |
| Over 3.5 goles | 44% | no | ✅ |
| Over 1.5 goles Japan | 73% | no | ❌ |
| Over 1.5 goles Sweden | 20% | no | ✅ |
| BTTS | 52% | sí | ✅ |

**Checks acertados: 6/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

# Analysis — Paraguay vs Australia

_as_of 2026-06-25 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Paraguay 22%** · Draw 29% · **Australia 50%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 22% | 71% | -250 | **pass** |
| draw | 29% | 18% | +440 | **pass** |
| away | 50% | 10% | +900 | **pass** |

## Goals (total)

- Expected goals: Paraguay 0.79 – 1.07 Australia  (total λ 1.86)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 56% | — | — |
| 2.5 | 28% | -132 | -0.50 |
| 3.5 | 12% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Paraguay | 50% | — | — |
| Doble oport. Australia | 78% | — | — |
| Over 1.5 goles Paraguay | 19% | — | — |
| Over 1.5 goles Australia | 29% | — | — |
| BTTS (ambos marcan) | 37% | — | — |
| Tiros Paraguay over 9.5 | 44% | — | — |
| Tiros Australia over 9.5 | 72% | — | — |
| TaP Paraguay over 2.5 | 59% | — | — |
| TaP Australia over 2.5 | 75% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Paraguay 0–0 Australia** (draw, 0 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Paraguay | 22% | no | ✅ |
| Empate | 29% | sí | ❌ |
| Gana Australia | 50% | no | ✅ |
| Doble oport. Paraguay | 50% | sí | ✅ |
| Doble oport. Australia | 78% | sí | ✅ |
| Over 1.5 goles | 56% | no | ❌ |
| Over 2.5 goles | 28% | no | ✅ |
| Over 3.5 goles | 12% | no | ✅ |
| Over 1.5 goles Paraguay | 19% | no | ✅ |
| Over 1.5 goles Australia | 29% | no | ✅ |
| BTTS | 37% | no | ✅ |

**Checks acertados: 9/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

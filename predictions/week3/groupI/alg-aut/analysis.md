# Analysis — Algeria vs Austria

_as_of 2026-06-27 · source: snapshot (snapshot 2026-06-27T19:22:12-06:00)_

## 1X2 (match winner)

- Model: **Algeria 35%** · Draw 28% · **Austria 36%**

| sel | model | sharp fair | best | verdict |
|---|---|---|---|---|
| home | 35% | 28% | +275 | **bet** |
| draw | 28% | 46% | +114 | **pass** |
| away | 36% | 26% | +292 | **bet** |

## Goals (total)

- Expected goals: Algeria 1.18 – 1.12 Austria  (total λ 2.30)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 67% | — | — |
| 2.5 | 40% | +225 | +0.31 |
| 3.5 | 20% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. Algeria | 64% | — | — |
| Doble oport. Austria | 65% | — | — |
| Over 1.5 goles Algeria | 33% | — | — |
| Over 1.5 goles Austria | 31% | — | — |
| BTTS (ambos marcan) | 48% | — | — |
| Tiros Algeria over 9.5 | 80% | — | — |
| Tiros Austria over 9.5 | 76% | — | — |
| TaP Algeria over 2.5 | 80% | — | — |
| TaP Austria over 2.5 | 77% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **Algeria 3–3 Austria** (draw, 6 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana Algeria | 35% | no | ✅ |
| Empate | 28% | sí | ❌ |
| Gana Austria | 36% | no | ✅ |
| Doble oport. Algeria | 64% | sí | ✅ |
| Doble oport. Austria | 65% | sí | ✅ |
| Over 1.5 goles | 67% | sí | ✅ |
| Over 2.5 goles | 40% | sí | ❌ |
| Over 3.5 goles | 20% | sí | ❌ |
| Over 1.5 goles Algeria | 33% | sí | ❌ |
| Over 1.5 goles Austria | 31% | sí | ❌ |
| BTTS | 48% | sí | ❌ |

**Checks acertados: 5/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

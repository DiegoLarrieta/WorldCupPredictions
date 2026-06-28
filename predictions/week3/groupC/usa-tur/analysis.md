# Analysis — United States vs Turkey

_as_of 2026-06-25 · source: snapshot_

## 1X2 (match winner)

- Model: **United States 56%** · Draw 23% · **Turkey 21%**

## Goals (total)

- Expected goals: United States 1.85 – 1.24 Turkey  (total λ 3.09)

| over | model P | odds | EV@odds |
|---|---|---|---|
| 1.5 | 81% | — | — |
| 2.5 | 60% | — | — |
| 3.5 | 37% | — | — |

## Otros mercados

_EV@odds = P(modelo)×odds−1, al precio ofrecido (no de-vig). En mercados eficientes (1X2, doble oport.) un EV+ suele ser error nuestro (edge test); en goles es la señal viva._

| mercado | model P | odds | EV@odds |
|---|---|---|---|
| Doble oport. United States | 79% | — | — |
| Doble oport. Turkey | 44% | — | — |
| Over 1.5 goles United States | 55% | — | — |
| Over 1.5 goles Turkey | 35% | — | — |
| BTTS (ambos marcan) | 61% | — | — |
| Tiros United States over 9.5 | 99% | — | — |
| Tiros Turkey over 9.5 | 84% | — | — |
| TaP United States over 2.5 | 95% | — | — |
| TaP Turkey over 2.5 | 82% | — | — |

## Props de delanteros (tiros y tiros a puerta)

_Sin tabla de delanteros — skipped (snapshot backtest)._

## Recommendation

- **No 1X2/goals bet** — nothing where a soft book beats the sharp fair (the common, correct outcome). Big model-vs-sharp gaps are *suspect*, not value.

_Caveats: 1X2/goals edge requires beating a soft book, not out-predicting the sharp (edge test). Props are one-sided — un-de-viggable, graded by CLOV. Snapshot backtests use pre-kickoff odds, which may be stale if captured long before kickoff._

## Resultado y checks (qué se cumplió)

- **United States 2–3 Turkey** (away, 5 goles)

| Mercado | model P | ¿Pasó? | check |
|---|---|---|---|
| Gana United States | 56% | no | ❌ |
| Empate | 23% | no | ✅ |
| Gana Turkey | 21% | sí | ❌ |
| Doble oport. United States | 79% | no | ❌ |
| Doble oport. Turkey | 44% | sí | ❌ |
| Over 1.5 goles | 81% | sí | ✅ |
| Over 2.5 goles | 60% | sí | ✅ |
| Over 3.5 goles | 37% | sí | ❌ |
| Over 1.5 goles United States | 55% | sí | ✅ |
| Over 1.5 goles Turkey | 35% | sí | ❌ |
| BTTS | 61% | sí | ✅ |

**Checks acertados: 5/11** (✅ = la inclinación del modelo coincidió con lo que pasó).

# Analysis — France vs Morocco

_cuartos de final · as_of 2026-07-09 · **solo-modelo** (sin odds capturadas para esta ronda)_

> ⚠️ Se nos pasó la ventana pre-partido de este cuarto: no hay snapshot de línea de
> cierre (los únicos snapshots son de fase de grupos) y el partido ya se jugó. Por eso
> **no hay precio de mercado ni veredicto de apuesta** — esto queda como registro del
> modelo para completar la carpeta de 4round y para el feedback post-partido, no como
> una recomendación (una línea cerrada no se puede apostar retroactivamente).

## 1X2 (match winner)

- Model: **France 48%** · Draw 29% · **Morocco 23%**
- Elo: France 2211 vs Morocco 2063 (Δ 148)

| Modelo | France | Draw | Morocco |
|---|---|---|---|
| Dixon-Coles | 34% | 35% | 30% |
| Elo | 58% | 24% | 18% |
| **Ensemble** | **48%** | **29%** | **23%** |

⚠️ **Discrepancia grande DC↔Elo.** Elo ve a Francia claramente por encima (58%) por su
rating; Dixon-Coles, que pesa las tasas de gol recientes, ve un partido casi parejo
(Francia 34% / empate 35% / Marruecos 30%) — refleja el bajo λ ofensivo esperado de
Francia (0.94). El ensemble aterriza en 48%: Francia favorita, pero un partido cerrado
y de pocos goles con Marruecos muy vivo.

## Goals (total)

- Expected goals: France 0.94 – 0.86 Morocco  (total λ 1.80)
- Over 2.5: **27%**  ·  BTTS: **36%**

| over | model P (Poisson λ) |
|---|---|
| 1.5 | 54% |
| 2.5 | 27% |
| 3.5 | 11% |

Partido de **pocos goles** según el modelo (Under 2.5 73%): 0-0 es el marcador más
probable. Marruecos defensivamente sólido, Francia sin explosión ofensiva esperada.

## Marcadores más probables

| score | prob |
|---|---|
| 0-0 | 18% |
| 1-1 | 15% |
| 1-0 | 14% |
| 0-1 | 13% |
| 2-0 | 7% |

## Props de delanteros

_No cotizados: la ventana pre-partido se pasó y The Odds API no devuelve props de un
juego terminado (además del costo de créditos). Sin tabla de props para esta ronda._

## Recommendation

- **Sin apuesta** — no hay línea capturada; imposible medir edge o CLOV. Registro solo-modelo.
- Lectura del modelo: Francia favorita moderada (48%) pero con fuerte disenso interno
  DC↔Elo, y sobre todo un partido de **pocos goles** (Under 2.5 73%, 0-0 el resultado
  más probable). Si fuera pre-partido, el ángulo sería el Under contra un libro blando,
  no el 1X2 contra el sharp (edge test).

_Para la próxima: capturar snapshot ~30 min antes del kickoff de cada cuarto para no
perder la línea de cierre. Si me pasas el marcador real, cierro el feedback con
`/score-week` (resultado → ratings → stats)._

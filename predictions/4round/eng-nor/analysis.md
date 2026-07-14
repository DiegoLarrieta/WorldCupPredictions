# Analysis — England vs Norway

_cuartos de final · as_of 2026-07-11 · **solo-modelo** (sin odds capturadas para esta ronda)_

> ⚠️ Se nos pasó la ventana pre-partido de este cuarto: no hay snapshot de línea de
> cierre (los únicos snapshots son de fase de grupos) y el partido ya se jugó. Por eso
> **no hay precio de mercado ni veredicto de apuesta** — esto queda como registro del
> modelo para completar la carpeta de 4round y para el feedback post-partido, no como
> una recomendación (una línea cerrada no se puede apostar retroactivamente).

## 1X2 (match winner)

- Model: **England 52%** · Draw 25% · **Norway 22%**
- Elo: England 2151 vs Norway 2051 (Δ 100)

| Modelo | England | Draw | Norway |
|---|---|---|---|
| Dixon-Coles | 49% | 27% | 25% |
| Elo | 52% | 26% | 23% |
| **Ensemble** | **52%** | **25%** | **22%** |

Los dos modelos coinciden (poca discrepancia DC↔Elo): Inglaterra favorita clara pero
lejos de dominante — Noruega, con la ola tras eliminar a Brasil, tiene ~1 de cada 5.

## Goals (total)

- Expected goals: England 1.62 – 1.09 Norway  (total λ 2.71)
- Over 2.5: **51%**  ·  BTTS: **54%**

| over | model P (Poisson λ) |
|---|---|
| 1.5 | 75% |
| 2.5 | 51% |
| 3.5 | 29% |

Partido de goles esperado (λ alto, BTTS >50%): ambas ofensivas producen. Un mercado
más "vivo" que el 1X2 si hubiéramos tenido precio.

## Marcadores más probables

| score | prob |
|---|---|
| 1-1 | 13% |
| 1-0 | 10% |
| 2-1 | 9% |
| 2-0 | 9% |
| 0-0 | 8% |

## Props de delanteros

_No cotizados: la ventana pre-partido se pasó y The Odds API no devuelve props de un
juego terminado (además del costo de créditos). Sin tabla de props para esta ronda._

## Recommendation

- **Sin apuesta** — no hay línea capturada; imposible medir edge o CLOV. Registro solo-modelo.
- Lectura del modelo: Inglaterra favorita moderada (52%), partido abierto a goles
  (O2.5 51%, BTTS 54%). Si esto fuera pre-partido, el ángulo a mirar sería goles/BTTS
  contra un libro blando, nunca el 1X2 contra el sharp (edge test).

_Para la próxima: capturar snapshot ~30 min antes del kickoff de cada cuarto para no
perder la línea de cierre. Si me pasas el marcador real, cierro el feedback con
`/score-week` (resultado → ratings → stats)._

# Diseño — Desglose completo de mercados + sección apostable

## 🗺️ Estado y roadmap (leer primero)

Plan de 3 fases. **goles→tiros es el cimiento de B y C** (por eso va primero).

- **✅ FASE A — Goles-implícito (HECHA, en main, commit fd4e5d4).**
  Los ~5.3k jugadores sin datos de tiros (MLS/Saudi/Championship/Liga MX) SÍ tienen goles.
  Cascada en `build_prop_model.py`: tiros reales → `shots/90 ≈ a+b·goles/90` (fit por
  posición, corr 0.68-0.73 en 8k) → prior. Columna `rate_source` (shots/goals/prior).
  `prop_clov` apuesta `rate_source!='prior'`. Messi 0.89→1.51 SoT/90, ahora apostable.
  Validó (corr 0.637 vs 0.621 bland, n=21). **Esto desbloqueó B: ya no hay NaN que metan ruido.**

- **⏳ FASE B — Modelo de tiros POR EQUIPO (PENDIENTE).** Ver §3. Construir DOS versiones,
  validar contra los 56 team-matches (`match_team_stats.csv`), la que gane (o ninguna):
  1. **Sumar-el-XI:** Σ(tiros esperados del 11 titular, con las tasas ya arregladas en A) ×
     factor de defensa rival (`sot_against`/`shots_against`).
  2. **Anclar-en-λ_goles:** tiros del equipo como función del λ de goles del DC (50k partidos,
     nuestra señal más fuerte) + defensa rival, calibrando goles↔tiros con los 56.
  Abierto: **Poisson vs Negative-Binomial** (overdispersión de tiros) — probar ambos, valida.
  Cubre DOS mercados: tiros del equipo Y tiros a puerta del equipo (tenemos ambos: `shots_for`,
  `sot_for`). NaN ya resuelto por A.

- **⏳ FASE C — Desglose completo en `analysis.md` (PENDIENTE).** Ver §4. Dos secciones:
  📊 desglose completo (1X2, doble-oport, goles totales 0.5-4.5, goles por equipo, BTTS,
  props de tiros/TaP por jugador, tiros por equipo) + 🎯 apostable acotado (disciplina
  soft-vs-sharp). Mercado primario = **O/U goles** (señal viva de sub-predicción). Mostrar≠apostar.

**TODO Fase C — tablero del README (pedido 2026-06-25):** la fila del tablero hoy muestra
solo 1X2 + O/U2.5, y el O/U sale "—" porque `_update_board` lee del compare SHARP (que no
cotiza el total en partidos chicos). Pedido: tabla más rica (goles O 1.5/2.5/3.5, doble
oportunidad, goles por equipo, prop destacado) CON precios reales (blandos marcados). Fix:
(a) `_update_board` debe usar el mismo fallback soft que el `analysis.md`; (b) más columnas.

**Para retomar:** sesión nueva → "seguimos con Fase B/C del market-breakdown". Todo el detalle
está abajo. Datos: `match_team_stats.csv` (56 team-matches: shots_for/sot_for/against),
`player_shot_rates.csv` (con `rate_source`), `engine.models.dixon_coles.lambdas` (λ por equipo).

---

Estado original del doc: **DRAFT** (Fase A ya implementada). Objetivo: que `/analyze-match` produzca un
`analysis.md` con **dos secciones**:
1. **📊 Desglose completo** — probabilidad del modelo + lo que paga el mercado, para TODOS los
   mercados que se puedan calcular. Transparente (mostrar todo).
2. **🎯 Dónde es apostable** — el subconjunto **chico** que pasa la disciplina (recomendar poco).

Principio rector: **mostrar todo, recomendar poco.** Con más mercados, el sesgo de
*comparaciones múltiples* crece (por azar habrá mercados donde diferimos mucho del precio);
la recomendación queda restringida a (a) un libro blando que le gana al precio del sharp
(CLOV+), o (b) mercados blandos/granulares con divergencia creíble.

---

## 1. Qué mercado calculamos y de dónde sale

| Mercado | Prob del modelo viene de | ¿Precio en The Odds API? | Rol |
|---|---|---|---|
| 1X2 (Win A / Draw / Win B) | ensemble Elo+DC | h2h ✅ | registro |
| Doble oportunidad (1X / 12 / X2) | **derivado del 1X2** (suma de pares) | derivable de h2h | registro |
| Goles totales O/U 0.5…4.5 | DC: Poisson(λ_total), matriz de marcadores | totals (algunas líneas) ✅ | **primario — señal viva en overs** |
| Goles por equipo O 0.5…3.5 | DC: Poisson(λ_A), Poisson(λ_B) | team_totals (parcial) ⚠️ | medible, **más blando** |
| BTTS | DC | btts ✅ | secundario |
| **Tiros / TaP por jugador** O 0.5/1.5 | prop model (shot_rate, sot_per90) + minutos/alineación | player props (over-only) ⚠️ | soft (CLOV) |
| **Tiros / TaP por EQUIPO** O línea | **bottom-up (ver §3)** — modelo nuevo | a veces ⚠️ | a construir+validar |

Todo menos "tiros por equipo" sale de modelos que **ya tenemos**. El precio del mercado será
**parcial** (The Odds API no carga todos los mercados) — mostramos nuestra prob siempre, y el
precio donde exista. Sin precio → no es apostable, solo informativo.

---

## 2. Goles totales vs goles por equipo — la distinción y cómo mejorar

- **Goles totales:** *medible* (over/under, de-viggeable) **+ señal viva** — medimos que el
  modelo **sub-predice goles** este WC (5/6 fueron over). Hay hipótesis de edge concreta.
- **Goles por equipo:** *medible* y **más blando** (menos líquido → libros más flojos → más
  margen de error a favor o en contra) — **pero todavía sin señal medida** específica.

**Cómo mejorar el de goles por equipo:** el sesgo de sub-predicción de goles **probablemente
se descompone al nivel de equipo** (si subestimamos el total, subestimamos a cada equipo). Si
eso se confirma:
- El **mismo edge de overs** se puede expresar en el mercado **más blando** (team totals) →
  potencialmente **más fácil de capturar** que el total del partido.
- Acción: medir si los **team-overs** también baten su línea de cierre; si sí, **preferir el
  mercado más blando** para el mismo edge. (Validar antes de asumir.)

---

## 3. Modelo de tiros por equipo — la decisión a discutir

**El problema:** el engine predice goles, no tiros. No tenemos modelo de tiros por equipo, y
los datos directos son chicos (`match_team_stats`, ~2-3 partidos por equipo del WC) → un modelo
top-down sería casi todo prior (ruido).

**Propuesta — bottom-up, reutiliza lo que ya tenemos:**
> Tiros del equipo ≈ **suma de los tiros esperados del 11 titular** (player `shot_rate` ×
> minutos esperados), ajustado por la **defensa rival** (`sot_against` de `match_team_stats`).
> Igual para TaP con `sot_per90`. Luego modelar el total del equipo como Poisson(λ_equipo) →
> P(over línea).

Ventajas:
- Usa el **prop model validado** (tasas por jugador) + las **alineaciones** (que ya integramos)
  + el **factor de defensa rival** — nada frágil top-down.
- **Validable** contra `match_team_stats` (los tiros reales por equipo que ya registramos):
  ¿la suma bottom-up predice el total real held-out? Solo se sube si pasa.

Puntos abiertos a discutir:
1. ¿Poisson o Negative-Binomial (overdispersión) para el total del equipo?
2. ¿Cómo pesar el factor de defensa rival con muestra chica (shrinkage)?
3. ¿Qué hacer con jugadores del 11 sin tasa real (raw=NaN)? (¿prior de posición?)
4. ¿Validamos contra los ~52 team-matches que tenemos, o esperamos más n?

---

## 4. Estructura del `analysis.md` propuesta

```
# Analysis — A vs B   (as_of, source)

## 📊 Desglose completo (todas las probabilidades)
### 1X2 + Doble oportunidad
| sel | modelo | mercado | precio |
### Goles totales (O/U 0.5…4.5)
| línea | P(over) modelo | mercado | precio | de-vig |
### Goles por equipo
| A over 0.5/1.5/2.5 | ... | B over ... |
### Tiros por equipo (bottom-up)   [si el modelo pasa validación]
| A tiros oX | A TaP oX | B tiros oX | B TaP oX |
### Props por jugador (top N del 11)
| jugador | tiros oX | TaP oX | modelo | precio |

## 🎯 Dónde es apostable (el subconjunto disciplinado)
- Solo: soft-price que bate el sharp (CLOV+), o mercado blando con divergencia creíble.
- Cada uno con veredicto + por qué. "Sin apuesta" es la respuesta común y correcta.
```

---

## 5. Notas honestas de implementación
- **Comparaciones múltiples:** 20 mercados ⇒ algunos diferirán por azar. La sección apostable
  NO se llena por "donde más diferimos" — se llena por la disciplina soft-vs-sharp. Mostrar ≠ apostar.
- **Precio parcial:** sin precio de mercado, un renglón es informativo, no apostable.
- **Props one-sided:** se gradúan por CLOV, no por de-vig (como hoy).
- **Tiros por equipo:** no se muestra hasta pasar validación held-out contra `match_team_stats`.

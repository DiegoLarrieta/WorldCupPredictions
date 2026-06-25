# World Cup 2026 — Match Predictor & Betting Engine

A football prediction system built to **make money betting**, not to look accurate. The
benchmark is **beating the closing betting line (CLOV)** — the market's sharpest estimate —
on the markets we actually bet. Every feature earns its place by producing *edge against a
price*, validated on leakage-free held-out data, or it doesn't ship.

> **North star:** beat the closing line on **total goals (O/U)**, **player shots-on-target**,
> and — for the record — **1X2**. "Interesting stat" is not the goal. "Edge vs a real price" is.

---

<!-- DAILY-BOARD:START -->
## 📅 Tablero de partidos

_Acumula todo lo analizado (lo nuevo arriba). Prob = modelo · Odds = The Odds API · 1X2/doble-oport = registro. Detalle + checks: `analysis.md`._

### Japan vs Sweden — 2026-06-25 23:00Z · [análisis](predictions/week3/groupF/jpn-swe/analysis.md)

⏳ Por jugarse

🎯 **Apuestas sugeridas:** ninguna (sin edge soft-vs-sharp)

| Mercado | Prob modelo | Odds | Check |
|---|---|---|---|
| Gana Japan | 64% | 2.28 | ⏳ |
| Empate | 21% | 3.60 | ⏳ |
| Gana Sweden | 15% | 4.60 | ⏳ |
| Doble oport. Japan | 85% | 1.38 | ⏳ |
| Doble oport. Sweden | 36% | 1.76 | ⏳ |
| Over 1.5 goles | 80% | 1.32 | ⏳ |
| Over 2.5 goles | 57% | 1.97 | ⏳ |
| Over 3.5 goles | 35% | 3.50 | ⏳ |
| Over 1.5 goles Japan | 61% | 2.19 | ⏳ |
| Over 1.5 goles Sweden | 24% | 3.05 | ⏳ |
| BTTS (ambos marcan) | 53% | 1.82 | ⏳ |
| Prop: Alexander Isak o0.5 SoT | 64% | 1.60 | ⏳ |

### Ecuador vs Germany — 2026-06-25 20:00Z · [análisis](predictions/week3/groupE/ecu-ger/analysis.md)

✅ Jugado: **2-1** (home) · checks **6/11**

🎯 **Apuestas sugeridas:** home @ 4.20 (+10%)

| Mercado | Prob modelo | Odds | Check |
|---|---|---|---|
| Gana Ecuador | 34% | 4.20 | ✅ |
| Empate | 30% | 4.40 | ❌ |
| Gana Germany | 36% | 1.90 | ❌ |
| Doble oport. Ecuador | 64% | _(no fetcheado)_ | ✅ |
| Doble oport. Germany | 66% | _(no fetcheado)_ | ❌ |
| Over 1.5 goles | 58% | _(no fetcheado)_ | ✅ |
| Over 2.5 goles | 31% | _(no fetcheado)_ | ✅ |
| Over 3.5 goles | 13% | _(no fetcheado)_ | ❌ |
| Over 1.5 goles Ecuador | 29% | _(no fetcheado)_ | ✅ |
| Over 1.5 goles Germany | 22% | _(no fetcheado)_ | ❌ |
| BTTS (ambos marcan) | 39% | _(no fetcheado)_ | ✅ |

### Curaçao vs Ivory Coast — 2026-06-25 20:00Z · [análisis](predictions/week3/groupE/cuw-civ/analysis.md)

✅ Jugado: **0-2** (away) · checks **11/11**

🎯 **Apuestas sugeridas:** away @ 1.19 (+4%)

| Mercado | Prob modelo | Odds | Check |
|---|---|---|---|
| Gana Curaçao | 13% | 24.00 | ❌ |
| Empate | 22% | 9.50 | ❌ |
| Gana Ivory Coast | 65% | 1.19 | ✅ |
| Doble oport. Curaçao | 35% | _(no fetcheado)_ | ❌ |
| Doble oport. Ivory Coast | 87% | _(no fetcheado)_ | ✅ |
| Over 1.5 goles | 70% | _(no fetcheado)_ | ✅ |
| Over 2.5 goles | 44% | _(no fetcheado)_ | ❌ |
| Over 3.5 goles | 23% | _(no fetcheado)_ | ❌ |
| Over 1.5 goles Curaçao | 13% | _(no fetcheado)_ | ❌ |
| Over 1.5 goles Ivory Coast | 54% | _(no fetcheado)_ | ✅ |
| BTTS (ambos marcan) | 39% | _(no fetcheado)_ | ❌ |

<!-- DAILY-BOARD:END -->

---

## Lo que hay que saber primero (la verdad sobre el edge)

Corrimos el experimento decisivo (`predictions/edge-test/`): un Elo+Dixon-Coles entrenado
out-of-sample contra el **cierre** de Bet365. **El mercado le gana a todos nuestros modelos**
(log-loss: mercado 0.975 < DC 0.979 < ensemble 1.000 < Elo 1.024). Conclusión dura:

- **NO le ganamos a un cierre sharp en 1X2 ni en O/U.** Más datos no arreglan esto — para
  ganarle habría que predecir mejor que *todo el mercado junto*.
- El edge **no** está en out-modelar el cierre. Está en **mercados blandos/lentos** (props),
  en **ser más rápidos a un precio blando**, y en mercados de **dos lados medibles** (goles).
- Por eso la vara es **CLOV** (¿tomamos un precio mejor que el cierre?) + **ROI con intervalo
  de confianza**, no accuracy. Definición completa: `design/profitability-scorecard.md`.

**Mercados que apostamos (por prioridad):**

| Mercado | Dos lados / medible | Rol |
|---|---|---|
| **Total de goles O/U** | ✅ de-viggeable | **Primario.** Hay señal viva: el modelo sub-predice goles este WC (real ~3.3 vs modelo ~2.3). |
| **Player tiros a puerta (props)** | ❌ over-only | Especialidad; solo graduable por CLOV. Apostar chico. |
| **Total de goles por equipo** | ✅ | Secundario, medible. |
| **1X2 / doble oportunidad** | ✅ | **Solo registro** — sin edge probado vs el cierre. |

Disciplina: **foco > variedad.** Para *probar* edge necesitás una muestra de CLOV por mercado;
repartir en 6 mercados da ruido en todos. Apostamos fuerte 1–2, registramos el resto.

---

## Cómo funciona el modelo

El predictor es un **ensemble Elo + Dixon-Coles**, calibrado, en `engine/`. Una sola fuente
de verdad: cada carpeta de partido llama al mismo motor, sin drift por-partido.

```python
from engine import predict_match, save_match
res = predict_match("Iraq", "Norway", neutral=True, as_of="2026-06-16")  # leakage-free
save_match(res, folder)        # escribe prediction.json + prediction.md
```

- **Elo** (`engine/models/elo.py`): replay cronológico de toda la tabla `matches` hasta
  `as_of` → ratings actuales; un mapa Elo→W/D/L entrenado convierte la diferencia de rating
  en probabilidades. Ventaja de localía y base parametrizadas en `engine/params.json`.
- **Dixon-Coles** (`engine/models/dixon_coles.py`): modelo de goles Poisson bivariado con
  corrección de marcadores bajos (ρ). Emite la **matriz de marcadores** completa → de ahí
  salen 1X2, **distribución de goles** (O/U a cualquier línea vía Poisson sobre λ_total),
  BTTS y top scorelines.
- **Ensemble** (`engine/ensemble.py`): mezcla W/D/L con peso **w≈0.481 sobre DC**, ajustado
  en 2.195 internacionales held-out. Le gana a cada modelo solo (ganancia log-loss +0.0069,
  IC95% [+0.0017, +0.0121]).
- **Calibración** (`engine/calibration.py`): temperature scaling para que un 70% sea de
  verdad ~70% (confianza honesta).
- **Sin fuga:** `as_of` fija el corte temporal; el modelo solo ve partidos estrictamente
  anteriores al kickoff (`engine/data.py`).

**Qué NO usa (y por qué):** alineaciones, forma de club y "ligas extra" como features de 1X2
fueron **probadas y descartadas** en held-out (`predictions/feature-lab/`) — aporte cero o
negativo. Se guardan como **contexto**, no como input del modelo de ganador. (En **props** sí
importan los minutos/quién arranca — ahí son input legítimo.)

---

## Cómo medimos (métricas)

Scoreamos contra las probabilidades **congeladas** (publicadas pre-kickoff), nunca un re-fit
(eso filtra el resultado). Métricas en `engine/evaluate.py`, rollup en
`data/worldcupmatches/_monitor.md`:

- **RPS** (ranked probability score) — la métrica primaria; respeta el orden de los outcomes.
- **Log-loss / Brier** — castigan la confianza equivocada.
- **ECE / reliability** — calibración: ¿el X% predicho ocurrió X%?
- **CLOV** (`engine/clov.py`, `engine/betlog.py`) — la vara de apuestas: ¿batimos el cierre?
- **ROI con IC bootstrap** (`engine.betlog.report`) — el veredicto: profitable = IC inferior > 0.

**Estado actual** (52 partidos scoreados): ensemble RPS **0.175** vs naive 0.233 (le gana
~25%). *Honesto:* Dixon-Coles solo (0.171) viene empatando/ganándole al ensemble en este
sample — varianza esperable a n bajo, no re-ajustamos por eso. 1X2 sigue siendo registro.

---

## El loop: cómo predecimos, apostamos y aprendemos

```
1. PREDECIR   /predict-match  → engine (sin fuga) → prediction.json (1X2 + goles)
2. ANALIZAR   /analyze-match  → modelo vs mercado (sharp-vs-blando) + props (CLOV-overs)
                              → analysis.md (el doc que se lee) + fila en el tablero
3. CAPTURAR   snapshot_odds.py → odds_snapshots.csv; el último pre-kickoff = el CIERRE
4. APOSTAR    /log-bet        → registra precio tomado + prob del modelo (paper o real)
5. SCOREAR    /score-week     → resultado real (ESPN) → ratings + stats + prop model
6. GRADUAR    /bet-report     → CLOV + ROI-con-IC → ¿tenemos edge?
```

**Cómo "aprende":** scorear una jornada (5) re-inyecta los resultados a la tabla `matches`;
el próximo replay de Elo y el rebuild del prop model ya los incluyen. **No** re-ajusta los
parámetros del modelo (peso del ensemble, ρ, temperatura están fijados en miles de partidos;
~20 resultados no los mueven) — actualiza **ratings + muestra de props + calibración**.
Cualquier feature nueva entra **solo si pasa el harness de validación** (held-out, IC).

---

## Las skills (interfaz de uso)

Cada skill = un trabajo, con la disciplina **encodeada en el output** (no en la memoria):

| Skill | Qué hace |
|---|---|
| **/predict-match** | Arma la carpeta del fixture y corre el engine → el número del modelo (1X2 + goles). |
| **/compare-market** | Lectura honesta **sharp-vs-blando**: recomienda solo donde un libro blando le gana al precio del sharp (CLOV+); gap modelo-vs-sharp grande = *sospechoso*, no valor. |
| **/prop-bets** | **CLOV-sobre-overs**: SoT es over-only → apuesta overs donde el modelo le gana al precio con vig; usa alineación (titular ~85min / banca ~20) y matcheo por plantilla. |
| **/analyze-match** | Orquesta todo → **un `analysis.md`** con todas las probabilidades + veredicto + qué apostar, y publica la fila en el tablero. |
| **/score-week** | El feedback: resultado real → ratings → stats granulares → rebuild del prop model → monitor. |
| **/bet-report** | El scorecard: CLOV (indicador líder) + ROI con IC + calibración → ¿ganamos? |
| **/log-bet** | Registra/settlea una apuesta en `data/bets.csv` (el dataset propio de CLOV). |

---

## Estructura del repo

```
engine/                 El motor validado (única fuente de verdad)
  models/{elo,dixon_coles,base}.py   los dos modelos + interfaz común
  ensemble.py · calibration.py       blend + confianza honesta
  predict.py · data.py               API pública + acceso sin fuga
  market.py · odds_api.py · clov.py  modelo-vs-mercado, odds, CLOV
  props.py                           modelo de tiros a puerta (shrinkage jerárquico)
  feedback.py · warehouse.py         scoring congelado + escritura al spine
  espn.py · betlog.py                stats/alineaciones (ESPN) + ledger de apuestas
  evaluate.py                        RPS / log-loss / Brier / reliability
scripts/                Orquestadores (lo que envuelven las skills)
  predict / analyze_match / prop_bets / prop_clov / compare
  score_week · record_match · fetch_match_stats · build_prop_model · snapshot_odds
predictions/            Carpetas por fixture: weekN/groupX/<slug>/
  edge-test/ · feature-lab/ · ensemble/   harnesses de validación
data/
  worldcup.duckdb       fuente de verdad (gitignored)
  csv/                  espejo navegable (matches, derived/, reference/, ...)
  worldcupmatches/      registros ricos por partido + _monitor.{md,json}
  bets.csv              el ledger de CLOV (commiteado)
design/                 docs: data-model, feedback-loop, profitability-scorecard, redirect
.claude/skills/         las 7 skills
tests/                  12 archivos de test (engine puro, CI-safe)
```

**Datos:** DuckDB es la fuente de verdad; `data/csv/` es espejo. Tablas clave: `matches`
(~50k resultados, el spine del Elo/DC), `player_seasons` (forma de club: minutos, tiros, xG),
`wc_squads`/`wc_squad_form` (plantillas del Mundial con `player_id`), `match_odds`/`market_prob`
(histórico de cuotas + harness de de-vig). ERD completo: `design/data-model.md`.

---

## Quickstart

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt   # 3.12, no 3.14
make data                                          # construye data/worldcup.duckdb + csv
.venv/bin/python -m pytest -q                      # tests (engine puro, sin DB)

# Un partido, de punta a punta:
cd predictions/week3/groupE/ecu-ger && python predict.py    # predicción
ODDS_API_KEY=... .venv/bin/python scripts/analyze_match.py predictions/week3/groupE/ecu-ger
```

Tests de lógica pura corren en CI en cada push. Los de integración (necesitan el warehouse)
se auto-saltan si no existe `data/worldcup.duckdb`.

---

## Estado honesto y mejoras pendientes

Lo que está **sólido**: el engine validado + harness de no-fuga; el scorecard de CLOV;
el pipeline de props endurecido (minutos, alineaciones ESPN, matcheo por plantilla); el
feedback loop; el de-vig sharp-vs-blando con guard anti-longshot.

Lo que está **abierto / a mejorar**:
- **Señal de goles** — el modelo sub-predice goles este WC. Es la hipótesis de edge más viva;
  hay que **testearla vs el mercado** (P(over) del modelo vs la línea) y graduar por CLOV.
- **np_xg en props** — mejora el predictor en correlación cruda (0.52 vs 0.46) pero el blend
  quedó **inconcluso** (IC cruza cero, n~14). Re-testear a medida que crece el sample.
- **Captura de cierre** — depende de estar en la ventana pre-match; sin un snapshot cercano
  al kickoff no hay CLOV. Disciplina operativa, no código.
- **Matcheo de nombres** — resuelto por plantilla, pero idealmente por `player_id` de punta a
  punta (no por texto).
- **Mercados de tiros del partido** — atractivos pero **sin modelo validado** todavía.

🤖 Mantené este README al día: el tablero se autopublica vía `/analyze-match`; el resto se
actualiza cuando cambia la estructura.

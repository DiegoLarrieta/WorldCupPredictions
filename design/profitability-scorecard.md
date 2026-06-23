# Profitability scorecard — ¿cómo sabemos si estamos ganando?

> La vara NO es accuracy ni confianza. El mercado ya sabe quién es favorito y cuántos
> goles se esperan. Acertar un partido que el mercado también acertaba no da un peso.
> **Profitable = tomamos precios mejores que el cierre (CLOV) y, en el agregado, el ROI
> tiene su intervalo de confianza por encima de cero.** Nada más cuenta como evidencia.

Esto fija la definición para no auto-engañarnos. Léelo antes de decir "vamos ganando".

---

## 1. Las dos métricas (en este orden)

### a) CLOV — Closing Line Value · *el indicador líder, por apuesta*
¿El precio que tomamos batió el cierre del libro sharp (Pinnacle)?

```python
from engine.clov import grade_bet
import csv
rows = list(csv.DictReader(open("data/csv/derived/odds_snapshots.csv")))
grade_bet(odds_taken=1.85, rows=rows, market="totals", selection="Over 2.5")
# -> {"closing_odds": 1.72, "clov": 0.0756, "beat_close": True, "ref_book": "pinnacle"}
```

- `clov > 0` (`beat_close=True`) → tomamos valor respecto al cierre. **Es señal de edge
  aunque esa apuesta concreta pierda ese día.**
- A largo plazo, CLOV medio positivo y consistente predice ganancia mejor que cualquier
  resultado individual. Es lo único honesto que tenemos *apuesta a apuesta*.
- Requiere haber capturado el cierre: `scripts/snapshot_odds.py` corriendo hasta el
  kickoff. El último snapshot antes del partido = la línea de cierre. **Sin captura, no
  hay CLOV y estamos apostando a ciegas.**

### b) ROI con intervalo de confianza · *el veredicto final, agregado*
Sobre **muchas** apuestas (decenas → cientos), ¿el ROI tiene el IC inferior > 0?

- `ROI = (suma de retornos − suma de stakes) / suma de stakes`.
- IC por bootstrap sobre las apuestas (mismo método que `predictions/edge-test/`).
- **Profitable = IC inferior > 0.** Si el IC cruza cero, *todavía no lo sabemos* — no es
  "casi"; es "sin evidencia".

---

## 2. Qué mercados cuentan como edge (no todos)

| Mercado | ¿Edge plausible? | Para qué lo corremos |
|---|---|---|
| **Player props (tiros a puerta)** | **Sí** — mercado blando, nuestra data granular tiene rol | **El laboratorio de plata.** Apostar chico, loguear, graduar por CLOV |
| Goles / Over-Under | Marginal | Comparar vs cierre; no asumir edge |
| 1X2 (ganador) | **No** (edge test, 18-jun) | Solo para el registro / feedback |

Cuando discrepamos del cierre en 1X2/goles, **el que se equivoca somos nosotros** (probado
out-of-sample). Discrepancia modelo-vs-mercado en esos mercados **no es edge** — es error
nuestro. No apostar como si lo fuera.

⚠️ **Props one-sided:** los libros US cotizan SoT solo "over" (sin under), no se pueden
de-viggear. Un EV grande ahí casi siempre es error del modelo, no valor. Solo cuentan
líneas de dos lados.

---

## 3. El loop disciplinado (cada apuesta, sin excepción)

1. **Predecir** sin fuga: `predict_match(...)` con `as_of` = fecha del partido.
2. **Comparar con mercado:** `engine.market.compare_folder` (1X2/goles) o
   `scripts/prop_bets.py` (props). De-vig con Shin/power antes de calcular edge.
3. **Capturar cierre:** `scripts/snapshot_odds.py` en schedule hasta el kickoff.
4. **Apostar** (chico) solo donde hay valor de dos lados → registrar con `/log-bet`.
5. **Settlear** con el resultado real → `scripts/score_week.py`.
6. **Graduar por CLOV:** `grade_bet(...)` contra el cierre capturado.
7. Feedback al warehouse → la próxima réplica de ratings ya incluye el resultado.

---

## 4. Reglas de decisión

- **Escalar stake:** solo si CLOV medio > 0 con consistencia **y** el ROI agregado tiene
  IC inferior > 0 sobre N suficiente (≳ 30–50 apuestas del mismo tipo).
- **Parar un mercado:** si tras N apuestas el CLOV medio es ≤ 0, no tenemos edge ahí —
  dejar de apostarlo, por muy "seguros" que nos sintamos.
- **Tamaño:** fracción de Kelly (¼ o menos) sobre el edge de-viggeado, nunca sobre el EV
  de una línea one-sided.

---

## 5. Qué NO cuenta como evidencia (la lista de auto-engaños)

- ❌ "Acertamos el ganador" → el mercado también; no pagó nada.
- ❌ "Estábamos 90% seguros y pasó" → confianza ≠ edge.
- ❌ Un solo resultado, o un solo partido → varianza enorme, ruido puro.
- ❌ "El modelo dice 60% y el mercado 50% en el 1X2" → en main markets el equivocado
  somos nosotros (edge test). No es valor.
- ❌ ROI positivo con IC que cruza cero → todavía no sabemos.

**Sí cuenta:** tomar 2.10 en algo que cierra 1.90 (CLOV +), repetido, con ROI agregado de
IC > 0. Eso —y solo eso— es "estamos ganando".

---

*Herramientas: `engine/clov.py` (CLOV), `engine/market.py` (de-vig + EV),
`scripts/snapshot_odds.py` (captura de cierre), `scripts/prop_bets.py`, `scripts/score_week.py`.
Referencia del porqué: `predictions/edge-test/RESULTS*.md`.*

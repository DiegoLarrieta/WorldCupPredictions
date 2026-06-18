---
name: predict-match
description: Scaffold a new World Cup fixture prediction folder and run it through the validated engine. Use when the user wants to predict a match, add a fixture, or generate a prediction for two teams (e.g. "predict Brazil vs Croatia", "add the England-Spain match").
---

# /predict-match

Create a new `predictions/<home>-<away>/` folder that calls the shared engine, then
run it to produce `prediction.json` + `prediction.md`. Every match uses the identical
validated Elo + Dixon-Coles ensemble — no per-match model drift.

## Inputs to gather

- **Home team, away team** (exact names as they appear in the `matches`/`teams`
  table — national team names match martj42/Wikipedia, e.g. "Iraq", "Norway").
- **Neutral venue?** World Cup group/knockout games are usually `neutral=True`
  unless a host nation (USA/Canada/Mexico for 2026) is playing at home.
- **Lineups (optional)** — confirmed XIs if known. Stored as CONTEXT only; lineups
  are NOT model inputs (proven not to improve internationals). They're recorded for
  the post-match feedback loop.
- **Folder slug** — short `homeabbr-awayabbr` (e.g. `eng-cro`), matching the
  existing convention.

## Steps

1. Confirm the team names resolve. If unsure they exist in the warehouse, check:
   ```bash
   .venv/bin/python -c "import duckdb; c=duckdb.connect('data/worldcup.duckdb', read_only=True); print(c.execute(\"SELECT team_name FROM teams WHERE team_name ILIKE '%NAME%'\").fetchall())"
   ```
   A name that doesn't resolve silently drops the team to default ratings — catch it here.

2. Create `predictions/<slug>/predict.py` from this template (match the existing
   folders exactly — config only, all logic in the engine):

   ```python
   """<Home> vs <Away> — config only; all logic lives in the shared engine.

   Run:  python predict.py   (writes prediction.json + prediction.md here)
   """

   import sys
   from pathlib import Path

   sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
   from engine import predict_match, save_match

   HOME, AWAY, NEUTRAL = "<Home>", "<Away>", True

   LINEUPS = {
       # optional; context only, not a model input. Omit or fill confirmed XIs.
   }

   if __name__ == "__main__":
       res = predict_match(HOME, AWAY, neutral=NEUTRAL, lineups=LINEUPS or None)
       save_match(res, Path(__file__).resolve().parent)
       e = res["win_draw_loss"]["ENSEMBLE"]
       print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")
   ```

3. Run it:
   ```bash
   cd predictions/<slug> && python predict.py
   ```
   (Use the repo `.venv/bin/python` if the system python lacks deps.)

4. Read back `prediction.md` and report the ENSEMBLE line to the user, plus how the
   components (Elo vs DC) split — if they disagree sharply, say so (honest toss-up),
   don't hide it behind the blended number.

## Reminders

- North star is **beat the closing line**, not accuracy. If the user has the actual
  market odds for this fixture, note where the model disagrees with the implied
  probability — that disagreement is the only thing that matters for a bet.
- Do NOT add club form, striker tilt, or lineup strength as model inputs. They are
  disproven (see CLAUDE.md "DISPROVEN"). Lineups are context only.
- After the real match, use `engine.feedback.record_outcome(...)` to score the
  frozen prediction against the result.

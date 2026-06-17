"""Public prediction API — the one entry point every match folder uses.

    from engine import predict_match, save_match
    res = predict_match("Iraq", "Norway", neutral=True, lineups=LINEUPS)
    save_match(res, Path(__file__).parent)

The validated model is the Elo + Dixon-Coles ensemble. Club form / lineups are NOT
model inputs (proven not to improve internationals); lineups are stored as context
for the record and the post-match feedback loop.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from engine.models.dixon_coles import DixonColesModel
from engine.models.elo import EloModel
from engine.ensemble import Ensemble

DEFAULT_AS_OF = dt.date.today().isoformat()


def predict_match(home: str, away: str, *, neutral: bool = True,
                  as_of: str = DEFAULT_AS_OF, lineups: dict | None = None,
                  competition: str = "World Cup") -> dict:
    """Predict one match with the validated ensemble. Returns a result dict."""
    dc, elo = DixonColesModel(), EloModel()
    ens = Ensemble(dc, elo).fit(as_of)
    for t in (home, away):
        if not ens.can_rate(t):
            raise ValueError(f"'{t}' cannot be rated (unknown or too few matches). "
                             f"Check spelling against team_ratings.")

    comp = ens.components(home, away, neutral)
    detail = dc.predict_detail(home, away, neutral)

    def wdl(p):
        return {home: round(float(p[0]), 3), "Draw": round(float(p[1]), 3), away: round(float(p[2]), 3)}

    return {
        "match": f"{home} vs {away}",
        "competition": competition,
        "venue": "neutral" if neutral else f"{home} home",
        "as_of": as_of,
        "model": "Elo + Dixon-Coles ensemble (validated)",
        "ensemble_weight_on_dc": round(ens.w, 3),
        "win_draw_loss": {
            "ENSEMBLE": wdl(comp["ensemble"]),
            "dixon_coles": wdl(comp["dixon_coles"]),
            "elo": wdl(comp["elo"]),
        },
        "elo": {home: round(elo.rating(home)), away: round(elo.rating(away))},
        "expected_goals": {home: round(detail["xg_home"], 2), away: round(detail["xg_away"], 2)},
        "over_under_2_5": {"over": round(detail["over25"], 3), "under": round(detail["under25"], 3)},
        "btts": round(detail["btts"], 3),
        "top_scorelines": [{"score": f"{x}-{y}", "prob": round(p, 3)} for (x, y), p in detail["top_scores"]],
        "lineups": lineups,        # context only (not a model input)
        "actual_result": None,     # filled by the post-match feedback step
    }


def save_match(result: dict, folder: Path) -> None:
    """Write prediction.json + prediction.md into a match folder."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "prediction.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    (folder / "prediction.md").write_text(_markdown(result))


def _markdown(r: dict) -> str:
    wdl = r["win_draw_loss"]
    e, dc, el = wdl["ENSEMBLE"], wdl["dixon_coles"], wdl["elo"]
    home, away = list(e.keys())[0], list(e.keys())[2]
    eg = r["expected_goals"]
    L = [
        f"# Prediction: {r['match']}", "",
        f"_Validated Elo + Dixon-Coles ensemble (weight {r['ensemble_weight_on_dc']:.2f} on DC). "
        f"{r['competition']}, {r['venue']}, fit on internationals before {r['as_of']} (no leakage)._", "",
        "## Headline (ensemble)", "",
        "| Outcome | Probability |", "|---|---|",
        f"| **{home} win** | **{e[home]:.0%}** |",
        f"| Draw | {e['Draw']:.0%} |",
        f"| **{away} win** | **{e[away]:.0%}** |", "",
        f"- Expected goals: {home} {eg[home]} – {eg[away]} {away}",
        f"- Over 2.5: {r['over_under_2_5']['over']:.0%}  ·  BTTS: {r['btts']:.0%}",
        f"- Likely scores: " + ", ".join(f"{s['score']} ({s['prob']:.0%})" for s in r['top_scorelines'][:4]), "",
        "## The two models it blends", "",
        f"| Model | {home} | Draw | {away} |", "|---|---|---|---|",
        f"| Dixon-Coles | {dc[home]:.0%} | {dc['Draw']:.0%} | {dc[away]:.0%} |",
        f"| Elo | {el[home]:.0%} | {el['Draw']:.0%} | {el[away]:.0%} |",
        f"| **Ensemble** | **{e[home]:.0%}** | **{e['Draw']:.0%}** | **{e[away]:.0%}** |", "",
        f"Elo: {home} {r['elo'][home]} vs {away} {r['elo'][away]}.",
    ]
    if r.get("lineups"):
        L += ["", "## Confirmed lineups (context — not a model input)", ""]
        for team, ln in r["lineups"].items():
            L.append(f"**{team} ({ln['formation']}):** " + ", ".join(ln["xi"]))
            L.append("")
    L += ["## Actual result", "",
          "_Not yet played. The post-match step fills this in and scores the prediction (feedback loop)._"]
    return "\n".join(L)

"""Predict Iraq vs Norway (2026 WC, neutral) — validated Elo + Dixon-Coles ensemble.

Self-contained match folder (same pattern as swe-tun/): model.py + predict.py +
prediction.json + prediction.md. Team-level only — club form / lineups were shown to
add no predictive value over the international-results model (see feature-lab/clubform_verdict.md).
Writes prediction.json + prediction.md into this folder.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np

import model as M

HOME, AWAY, NEUTRAL = "Iraq", "Norway", True
AS_OF = "2026-06-16"
HERE = Path(__file__).resolve().parent
ENS = json.loads((HERE.parent / "ensemble" / "ensemble_params.json").read_text())


def elo_wdl(eh, ea, neutral):
    gap = (eh - ea + (0 if neutral else ENS["elo_home_adv"])) / 100.0
    z = np.array([c[0] * gap + b for c, b in zip(ENS["elo_wdl_coef"], ENS["elo_wdl_intercept"])])
    z -= z.max()
    return np.exp(z) / np.exp(z).sum()


def main():
    mdl = M.fit(AS_OF)
    lh, la = M.lambdas(mdl, HOME, AWAY, neutral=NEUTRAL)
    o = M.outcomes(M.score_matrix(lh, la, mdl["rho"]))
    p_dc = np.array([o["home"], o["draw"], o["away"]])

    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    eh = con.execute(f"SELECT elo FROM team_ratings WHERE team_name='{HOME}'").fetchone()[0]
    ea = con.execute(f"SELECT elo FROM team_ratings WHERE team_name='{AWAY}'").fetchone()[0]
    con.close()
    p_elo = elo_wdl(eh, ea, NEUTRAL)

    w = ENS["weight_dc"]
    p = w * p_dc + (1 - w) * p_elo

    result = {
        "match": f"{HOME} vs {AWAY}", "venue": "neutral (World Cup)", "as_of": AS_OF,
        "model": "Elo + Dixon-Coles ensemble (validated)", "ensemble_weight_on_dc": w,
        "win_draw_loss": {
            "ENSEMBLE": {HOME: round(float(p[0]), 3), "Draw": round(float(p[1]), 3), AWAY: round(float(p[2]), 3)},
            "dixon_coles": {HOME: round(float(p_dc[0]), 3), "Draw": round(float(p_dc[1]), 3), AWAY: round(float(p_dc[2]), 3)},
            "elo": {HOME: round(float(p_elo[0]), 3), "Draw": round(float(p_elo[1]), 3), AWAY: round(float(p_elo[2]), 3)},
        },
        "elo": {HOME: round(eh), AWAY: round(ea)},
        "expected_goals": {HOME: round(lh, 2), AWAY: round(la, 2)},
        "over_under_2_5": {"over": round(o["over25"], 3), "under": round(o["under25"], 3)},
        "btts": round(o["btts"], 3),
        "top_scorelines": [{"score": f"{x}-{y}", "prob": round(pr, 3)} for (x, y), pr in o["top_scores"][:5]],
        "actual_result": None,   # filled by the post-match step (the feedback loop)
    }
    (HERE / "prediction.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    _write_md(result, lh, la, o)

    print(f"=== {HOME} vs {AWAY} (neutral) ===  Elo {HOME} {eh:.0f} vs {AWAY} {ea:.0f}")
    print(f"  {'Dixon-Coles':<13}{HOME} {p_dc[0]:.0%} | Draw {p_dc[1]:.0%} | {AWAY} {p_dc[2]:.0%}")
    print(f"  {'Elo':<13}{HOME} {p_elo[0]:.0%} | Draw {p_elo[1]:.0%} | {AWAY} {p_elo[2]:.0%}")
    print(f"  >> ENSEMBLE  {HOME} {p[0]:.0%} | Draw {p[1]:.0%} | {AWAY} {p[2]:.0%}")
    print(f"  xG {HOME} {lh:.2f}-{la:.2f} {AWAY} | Over2.5 {o['over25']:.0%} | "
          f"likely " + ", ".join(f"{x}-{y}" for (x, y), _ in o['top_scores'][:3]))
    print("  saved -> prediction.json + prediction.md")


def _write_md(r, lh, la, o):
    e = r["win_draw_loss"]["ENSEMBLE"]; dc = r["win_draw_loss"]["dixon_coles"]; el = r["win_draw_loss"]["elo"]
    L = [
        f"# Prediction: {r['match']}", "",
        f"_Validated Elo + Dixon-Coles ensemble (weight {r['ensemble_weight_on_dc']:.2f} on DC). "
        f"{r['venue']}, fit on internationals before {r['as_of']} (no leakage)._", "",
        "## Headline (ensemble)", "",
        "| Outcome | Probability |", "|---|---|",
        f"| **{HOME} win** | **{e[HOME]:.0%}** |",
        f"| Draw | {e['Draw']:.0%} |",
        f"| **{AWAY} win** | **{e[AWAY]:.0%}** |", "",
        f"- Expected goals: {HOME} {r['expected_goals'][HOME]} – {r['expected_goals'][AWAY]} {AWAY}",
        f"- Over 2.5: {r['over_under_2_5']['over']:.0%}  ·  BTTS: {r['btts']:.0%}",
        f"- Likely scores: " + ", ".join(f"{s['score']} ({s['prob']:.0%})" for s in r['top_scorelines'][:4]), "",
        "## The two models it blends", "",
        f"| Model | {HOME} | Draw | {AWAY} |", "|---|---|---|---|",
        f"| Dixon-Coles | {dc[HOME]:.0%} | {dc['Draw']:.0%} | {dc[AWAY]:.0%} |",
        f"| Elo | {el[HOME]:.0%} | {el['Draw']:.0%} | {el[AWAY]:.0%} |",
        f"| **Ensemble** | **{e[HOME]:.0%}** | **{e['Draw']:.0%}** | **{e[AWAY]:.0%}** |", "",
        f"Elo: {HOME} {r['elo'][HOME]} vs {AWAY} {r['elo'][AWAY]}. Both models agree → confident {AWAY} lean.", "",
        "## Actual result", "",
        "_Not yet played. The post-match step fills this in and scores the prediction (feedback loop)._",
    ]
    (HERE / "prediction.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()

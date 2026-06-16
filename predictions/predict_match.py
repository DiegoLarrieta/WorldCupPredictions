"""Reusable match predictor — the VALIDATED model (Elo + Dixon-Coles ensemble).

Usage:  python predict_match.py "Iraq" "Norway" [--neutral]

Outputs W/D/L (ensemble headline + the two components), expected goals, Over/Under 2.5,
BTTS, and the most likely scorelines. No club form / lineups — those were shown to add
no predictive value over the international-results model (see clubform_verdict.md).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "predictions" / "swe-tun"))
import model as M  # noqa: E402

AS_OF = "2026-06-16"   # fit on internationals strictly before this (no leakage)
ENS = json.loads((ROOT / "predictions" / "ensemble" / "ensemble_params.json").read_text())


def elo_wdl(elo_h, elo_a, neutral):
    gap = (elo_h - elo_a + (0 if neutral else ENS["elo_home_adv"])) / 100.0
    z = np.array([c[0] * gap + b for c, b in zip(ENS["elo_wdl_coef"], ENS["elo_wdl_intercept"])])
    z -= z.max()
    return np.exp(z) / np.exp(z).sum()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("home"); ap.add_argument("away")
    ap.add_argument("--neutral", action="store_true")
    a = ap.parse_args()

    mdl = M.fit(AS_OF)
    for t in (a.home, a.away):
        if t not in mdl["attack"]:
            sys.exit(f"'{t}' not found / too few matches to rate. Check spelling vs team_ratings.")

    lh, la = M.lambdas(mdl, a.home, a.away, neutral=a.neutral)
    o = M.outcomes(M.score_matrix(lh, la, mdl["rho"]))
    p_dc = np.array([o["home"], o["draw"], o["away"]])

    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    eh = con.execute(f"SELECT elo FROM team_ratings WHERE team_name='{a.home}'").fetchone()[0]
    ea = con.execute(f"SELECT elo FROM team_ratings WHERE team_name='{a.away}'").fetchone()[0]
    con.close()
    p_elo = elo_wdl(eh, ea, a.neutral)

    w = ENS["weight_dc"]
    p = w * p_dc + (1 - w) * p_elo

    venue = "neutral" if a.neutral else f"{a.home} home"
    print(f"\n=== {a.home} vs {a.away}  ({venue}) ===")
    print(f"  Elo: {a.home} {eh:.0f}  vs  {a.away} {ea:.0f}\n")
    print(f"  {'model':<14}{a.home:>10}{'Draw':>8}{a.away:>10}")
    print(f"  {'Dixon-Coles':<14}{p_dc[0]:>10.0%}{p_dc[1]:>8.0%}{p_dc[2]:>10.0%}")
    print(f"  {'Elo':<14}{p_elo[0]:>10.0%}{p_elo[1]:>8.0%}{p_elo[2]:>10.0%}")
    print(f"  {'>> ENSEMBLE':<14}{p[0]:>10.0%}{p[1]:>8.0%}{p[2]:>10.0%}")
    print(f"\n  Expected goals: {a.home} {lh:.2f} - {la:.2f} {a.away}")
    print(f"  Over 2.5: {o['over25']:.0%}  ·  BTTS: {o['btts']:.0%}")
    print("  Likely scores: " + ", ".join(f"{x}-{y} ({pr:.0%})" for (x, y), pr in o["top_scores"][:4]))


if __name__ == "__main__":
    main()

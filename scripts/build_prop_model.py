#!/usr/bin/env python3
"""Build the player shots-on-target prop table, with hierarchical shrinkage.

Shot rate base = club seasons (engine warehouse player_seasons: shots + minutes), which is
the big sample. We Gamma-Poisson shrink each player's shots/90 toward their POSITION prior,
so thin samples regress to the mean instead of overfitting. On-target rate = Beta-Binomial
shrink of the World Cup shots-on-target / shots we've scraped (engine/espn), with a global
prior for players we have no SoT for yet. Expected SoT/90 = shot_rate * on_target_rate, and
we attach P(1+ SoT) / P(2+ SoT) over a full 90.

Writes data/csv/derived/player_shot_rates.csv (sorted by expected SoT/90).

This is the prop SIGNAL. It is NOT yet bettable: free odds feeds don't carry player props,
so there are no prices to compute EV against. Sourcing prop odds is the open blocker.

Run:  .venv/bin/python scripts/build_prop_model.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.props import (beta_binomial_eb, gamma_poisson_eb, posterior_p,  # noqa: E402
                          posterior_rate, prop_at_least, sot_per90)

DB = Path("data/worldcup.duckdb")
OUT = Path("data/csv/derived/player_shot_rates.csv")
WC_SHOTS = Path("data/csv/derived/player_match_shots.csv")


def _coarse_pos(p: str) -> str:
    p = (p if isinstance(p, str) else "").upper()
    if p.startswith("G"):
        return "GK"
    if p.startswith("D"):
        return "DF"
    if p.startswith("F") or p.startswith("S"):   # F / S(triker)
        return "FW"
    return "MF"


def _norm(s: str) -> str:
    from unidecode import unidecode
    return unidecode(str(s)).strip().lower()


def main() -> None:
    con = duckdb.connect(str(DB), read_only=True)
    ps = con.execute("""
        SELECT s.player_id, p.name, s.position,
               SUM(s.minutes) AS mins, SUM(s.shots) AS shots
        FROM player_seasons s JOIN players p USING(player_id)
        WHERE s.minutes > 0 GROUP BY 1,2,3 HAVING SUM(s.minutes) > 0
    """).df()
    con.close()

    ps["shots"] = pd.to_numeric(ps["shots"], errors="coerce").fillna(0.0)
    ps["pos"] = ps["position"].map(_coarse_pos)
    ps["nineties"] = ps["mins"] / 90.0

    # --- Gamma-Poisson shrink of shots/90, with a prior PER POSITION group ---
    priors = {}
    for pos, g in ps.groupby("pos"):
        priors[pos] = gamma_poisson_eb(g["shots"].to_numpy(), g["nineties"].to_numpy())
    ps["shot_rate_raw"] = ps["shots"] / ps["nineties"]
    ps["shot_rate"] = [posterior_rate(*priors[pos][:2], sh, ni)
                       for pos, sh, ni in zip(ps["pos"], ps["shots"], ps["nineties"])]

    # --- Beta-Binomial shrink of on-target rate from WC data (global prior) ---
    on_target_global = 0.35
    per_player_ot = {}
    if WC_SHOTS.exists():
        wc = pd.read_csv(WC_SHOTS)
        agg = wc.groupby("player").agg(sot=("on_target", "sum"), sh=("shots", "sum"))
        agg = agg[agg["sh"] > 0]
        if len(agg):
            a, b, on_target_global = beta_binomial_eb(agg["sot"].to_numpy(), agg["sh"].to_numpy())
            on_target_global = b and a / (a + b) or 0.35
            per_player_ot = {_norm(name): posterior_p(a, b, row.sot, row.sh)
                             for name, row in agg.iterrows()}

    ps["on_target_rate"] = [per_player_ot.get(_norm(n), on_target_global) for n in ps["name"]]
    ps["sot_per90"] = [sot_per90(sr, ot) for sr, ot in zip(ps["shot_rate"], ps["on_target_rate"])]
    ps["p_1plus_sot"] = [prop_at_least(r, 1) for r in ps["sot_per90"]]
    ps["p_2plus_sot"] = [prop_at_least(r, 2) for r in ps["sot_per90"]]

    out = ps[["player_id", "name", "pos", "mins", "shots", "shot_rate_raw",
              "shot_rate", "on_target_rate", "sot_per90", "p_1plus_sot", "p_2plus_sot"]]
    out = out.sort_values("sot_per90", ascending=False).round(3)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print(f"Built {len(out)} player shot-rate rows -> {OUT}")
    print(f"Position priors (shots/90 mean): "
          + ", ".join(f"{k} {v[2]:.2f}" for k, v in sorted(priors.items())))
    print(f"On-target prior (shrunk, from WC data): {on_target_global:.3f}")
    # trustworthy view: players with a real sample (>= 900 min ~ 10 full games)
    reliable = out[out["mins"] >= 900].head(12)
    print("\nTop 12 by expected shots-on-target / 90 (shrunk, >=900 min only):")
    print(reliable[["name", "pos", "mins", "shot_rate_raw", "shot_rate",
                    "sot_per90", "p_2plus_sot"]].to_string(index=False))
    print("\n(CSV keeps all players + a 'mins' column; low-minute rates are unreliable "
          "even after shrinkage — filter on minutes before betting.)")


if __name__ == "__main__":
    main()

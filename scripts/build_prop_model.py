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
    # Many leagues (MLS, Championship, BRA, Liga MX, Saudi, ...) carry minutes but NO
    # shots. NULL shots = "no data", NOT "zero shots" — counting those minutes as
    # zero-shot exposure both buries the player and drags the position prior down. So
    # exposure for the shot rate = ONLY minutes from seasons WITH a shot figure
    # (mins_known); total minutes (mins) are kept just for display/the betting filter.
    ps = con.execute("""
        SELECT s.player_id, p.name,
               arg_max(s.position, s.minutes) AS position,
               SUM(s.minutes) AS mins, SUM(s.appearances) AS apps,
               SUM(CASE WHEN s.shots IS NOT NULL THEN s.minutes ELSE 0 END) AS mins_known,
               SUM(s.shots) AS shots,         -- SUM ignores NULLs (NULL if all unknown)
               SUM(s.goals) AS goals          -- goals exist even where shots don't (39% of rows)
        FROM player_seasons s JOIN players p USING(player_id)
        WHERE s.minutes > 0 GROUP BY 1,2 HAVING SUM(s.minutes) > 0
    """).df()
    con.close()

    ps["shots"] = pd.to_numeric(ps["shots"], errors="coerce")   # keep NaN = no shot data
    ps["goals"] = pd.to_numeric(ps["goals"], errors="coerce").fillna(0.0)
    ps["pos"] = ps["position"].map(_coarse_pos)
    ps["nineties"] = ps["mins_known"] / 90.0                    # exposure = covered mins only
    ps["g90"] = ps["goals"] / (ps["mins"] / 90.0)              # goals/90 (goals are universal)
    ps["min_per_app"] = (ps["mins"] / ps["apps"].replace(0, np.nan)).round(1)  # typical game length
    has = ps["shots"].notna() & (ps["nineties"] > 0)

    # --- shot rate, in a cascade of best-to-worst data ---
    # 1) REAL shots -> Gamma-Poisson shrink toward the position prior (the big, clean signal).
    # 2) NO shots but goals -> ESTIMATE shots from goals: shots/90 ~ a + b*goals/90, fitted
    #    per position on players who have both (corr ~0.7). Recovers the ~5.3k players whose
    #    leagues (MLS/Saudi/Championship/...) report goals but not shots — Messi/Quiñones go
    #    from the bland FW prior (2.32) to a goals-implied ~4.6, instead of being buried.
    # 3) Neither -> position prior (rare; mostly GKs/defenders who barely shoot anyway).
    priors, gfit = {}, {}
    for pos, g in ps[has].groupby("pos"):
        priors[pos] = gamma_poisson_eb(g["shots"].to_numpy(), g["nineties"].to_numpy())
        if g["g90"].std() > 1e-6 and len(g) >= 30:            # b*goals/90 + a
            gfit[pos] = tuple(np.polyfit(g["g90"].to_numpy(), (g["shots"] / g["nineties"]).to_numpy(), 1))
    ps["shot_rate_raw"] = np.where(has, ps["shots"] / ps["nineties"], np.nan)

    def _rate(pos, sh, ni, h, g90):
        if h:
            return posterior_rate(*priors[pos][:2], sh, ni), "shots"
        if g90 > 0 and pos in gfit:                           # goals-implied estimate, clamped
            b, a = gfit[pos]
            return max(a + b * g90, priors[pos][2] * 0.5), "goals"
        return priors[pos][2], "prior"                        # position prior mean (a/b)

    out = [_rate(p, sh, ni, h, g) for p, sh, ni, h, g
           in zip(ps["pos"], ps["shots"], ps["nineties"], has, ps["g90"])]
    ps["shot_rate"] = [o[0] for o in out]
    ps["rate_source"] = [o[1] for o in out]

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

    out = ps[["player_id", "name", "pos", "mins", "min_per_app", "shots", "shot_rate_raw",
              "shot_rate", "rate_source", "on_target_rate", "sot_per90", "p_1plus_sot", "p_2plus_sot"]]
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

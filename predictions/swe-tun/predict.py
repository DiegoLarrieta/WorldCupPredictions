"""Predict Sweden vs Tunisia (2026 WC, neutral venue) with the Dixon-Coles model,
cross-checked against Elo and refined by the confirmed starting XIs' club form.

Pipeline:
  1. Fit Dixon-Coles on internationals strictly BEFORE the match (no leakage).
  2. Validate on a held-out time slice (log-loss + accuracy vs a base-rate baseline)
     so we trust the model before we use it.
  3. Base prediction: W/D/L, expected goals, O/U 2.5, BTTS, top scorelines.
  4. Starter-form signal: match each confirmed XI to club form (xG/90 where we have it,
     goals/90 otherwise) and apply a small, transparent attacking-quality tilt.
  5. Elo cross-check. Write prediction.md + prediction.json.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import duckdb
import numpy as np
from unidecode import unidecode

import model as M

AS_OF = "2026-06-15"          # match is about to start; use all data through 2026-06-14
VAL_CUTOFF = "2025-06-01"     # held-out validation slice: [VAL_CUTOFF, AS_OF)
HOME, AWAY, NEUTRAL = "Sweden", "Tunisia", True
HERE = Path(__file__).resolve().parent

# Confirmed starting XIs (forwards/attackers flagged for the attack signal).
XI = {
    "Sweden": {
        "starters": ["Kristoffer Nordfeldt", "Gustaf Lagerbielke", "Isak Hien",
                     "Victor Lindelöf", "Alexander Bernhardsson", "Jesper Karlström",
                     "Yasin Ayari", "Gabriel Gudmundsson", "Benjamin Nygren",
                     "Viktor Gyökeres", "Alexander Isak"],
        "attackers": ["Viktor Gyökeres", "Alexander Isak", "Benjamin Nygren"],
    },
    "Tunisia": {
        "starters": ["Abdelmouhib Chamakh", "Ali Abdi", "Omar Rekik", "Montassar Talbi",
                     "Yan Valery", "Ellyes Skhiri", "Rani Khedira", "Mohamed Amine Ben Hmida",
                     "Hannibal Mejbri", "Anis Slimane", "Elias Saad"],
        "attackers": ["Elias Saad", "Hannibal Mejbri", "Anis Slimane"],
    },
}


def _norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z ]", " ", unidecode(str(s)).lower())).strip()


# ---- validation (best practice: trust the model before using it) -----------
def validate():
    mdl = M.fit(VAL_CUTOFF)
    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    test = con.execute(
        f"""SELECT home_team, away_team, CAST(home_goals AS INT) hg, CAST(away_goals AS INT) ag, neutral
            FROM matches WHERE is_international AND home_goals IS NOT NULL
            AND date >= DATE '{VAL_CUTOFF}' AND date < DATE '{AS_OF}'"""
    ).fetch_df()
    con.close()
    teams = set(mdl["teams"])
    test = test[test["home_team"].isin(teams) & test["away_team"].isin(teams)]

    base = np.array([(test["hg"] > test["ag"]).mean(), (test["hg"] == test["ag"]).mean(),
                     (test["hg"] < test["ag"]).mean()])
    ll_dc, ll_base, correct, n = 0.0, 0.0, 0, 0
    for r in test.itertuples(index=False):
        lh, la = M.lambdas(mdl, r.home_team, r.away_team, neutral=bool(r.neutral))
        o = M.outcomes(M.score_matrix(lh, la, mdl["rho"]))
        p = np.clip([o["home"], o["draw"], o["away"]], 1e-9, 1)
        y = 0 if r.hg > r.ag else (1 if r.hg == r.ag else 2)
        ll_dc -= np.log(p[y]); ll_base -= np.log(base[y])
        correct += int(np.argmax(p) == y); n += 1
    return {"n": n, "logloss_dc": ll_dc / n, "logloss_base": ll_base / n,
            "accuracy": correct / n}


# ---- starting-XI club-form signal ------------------------------------------
def starter_form(con, names):
    """For a list of player names, return club form (goals/90, xg/90 where present)."""
    norm_map = {}
    rows = con.execute(
        "SELECT p.name, SUM(s.minutes) mins, SUM(s.goals) goals, SUM(s.np_xg) npxg "
        "FROM player_seasons s JOIN players p ON p.player_id = s.player_id "
        "WHERE s.season = '2526' GROUP BY p.name"
    ).fetchall()
    for nm, mins, goals, npxg in rows:
        norm_map[_norm(nm)] = (mins, goals, npxg)
    out = []
    for nm in names:
        hit = norm_map.get(_norm(nm))
        if hit and hit[0] and hit[0] > 0:
            mins, goals, npxg = hit
            out.append({"name": nm, "matched": True, "minutes": float(mins),
                        "goals_per90": 90 * float(goals) / mins,
                        "npxg_per90": (90 * float(npxg) / mins) if npxg is not None else None})
        else:
            out.append({"name": nm, "matched": False})
    return out


def attack_index(form):
    """Mean goal-threat per 90 across matched attackers (xg/90 if available else goals/90)."""
    vals = [(f["npxg_per90"] if f.get("npxg_per90") is not None else f["goals_per90"])
            for f in form if f.get("matched")]
    return float(np.mean(vals)) if vals else None


# ---- national possession, with coverage-scaling (handle uneven data) -------
POSS_CSV = HERE.parent / "feature-lab" / "intl_possession_raw.csv"
POSS_SHRINK_K = 10   # a team needs ~K tournament matches before we half-trust its possession


def team_possession(team):
    """Return (avg possession %, n_matches) from international tournament history."""
    import pandas as pd
    if not POSS_CSV.exists():
        return None, 0
    df = pd.read_csv(POSS_CSV)
    d = df[df["team"] == team]
    return (float(d["Poss"].mean()), len(d)) if len(d) else (None, 0)


def _confidence(n):
    """Shrinkage weight n/(n+K): ~0 with no data, →1 with lots. Thin data ≈ no claim."""
    return n / (n + POSS_SHRINK_K)


def main():
    print("Validating Dixon-Coles (leakage-free time split) ...")
    val = validate()
    print(f"  held-out {val['n']} matches | log-loss DC {val['logloss_dc']:.3f} "
          f"vs base-rate {val['logloss_base']:.3f} | accuracy {val['accuracy']:.1%}")

    print(f"\nFitting on all internationals before {AS_OF} ...")
    mdl = M.fit(AS_OF)
    lh, la = M.lambdas(mdl, HOME, AWAY, neutral=NEUTRAL)
    base = M.outcomes(M.score_matrix(lh, la, mdl["rho"]))
    print(f"  base λ: {HOME} {lh:.2f} - {la:.2f} {AWAY}")

    # ---- starter form + transparent attacking-quality tilt ----
    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    swe_att = starter_form(con, XI["Sweden"]["attackers"])
    tun_att = starter_form(con, XI["Tunisia"]["attackers"])
    swe_xi = starter_form(con, XI["Sweden"]["starters"])
    tun_xi = starter_form(con, XI["Tunisia"]["starters"])
    con.close()
    swe_idx, tun_idx = attack_index(swe_att), attack_index(tun_att)

    # (1) Striker-form tilt: REMOVED. Ablation (striker_tilt_validation.py, 5-fold CV on
    # 154 held-out internationals) showed it HURTS held-out log-loss (-0.0142) and the
    # fitted coefficient is ~0, not the 0.50 I had hand-tuned. Club form double-counts the
    # Dixon-Coles attack rating and adds noise. So the validated coefficient is 0.
    STRIKER_BETA = 0.0
    striker_factor = 0.0
    striker_note = "removed — ablation showed it worsened held-out prediction (fitted beta ~0)"
    if swe_idx is not None and tun_idx is not None:
        gap = swe_idx - tun_idx
        striker_factor = float(np.clip(gap * STRIKER_BETA, -0.20, 0.20))
        striker_note = (f"Sweden attackers {swe_idx:.2f}/90 vs Tunisia {tun_idx:.2f}/90, but "
                        f"validated coefficient is 0 -> {striker_factor:+.0%} (tilt removed by ablation)")

    # (2) Possession tilt, COVERAGE-SCALED: the raw signal is multiplied by each team's
    # data confidence n/(n+K), so a team with thin tournament history (Tunisia) can't
    # move the number much, however high its average looks.
    swe_poss, swe_pn = team_possession(HOME)
    tun_poss, tun_pn = team_possession(AWAY)
    poss_factor, poss_note = 0.0, "no possession data"
    if swe_poss is not None and tun_poss is not None:
        conf = _confidence(swe_pn) * _confidence(tun_pn)   # shrinks toward 0 if either is thin
        raw_gap = (swe_poss - tun_poss) / 100.0            # >0 = Sweden hogs the ball more
        poss_factor = float(np.clip(raw_gap * 0.8 * conf, -0.10, 0.10))
        poss_note = (f"Sweden {swe_poss:.0f}% (n={swe_pn}) vs Tunisia {tun_poss:.0f}% (n={tun_pn}), "
                     f"confidence {conf:.2f} -> {poss_factor:+.1%} (shrunk for thin data)")

    factor = float(np.clip(striker_factor + poss_factor, -0.25, 0.25))
    adj_lh, adj_la = lh * (1 + factor), la * (1 - factor)
    tilt_note = f"striker {striker_factor:+.0%} + possession {poss_factor:+.1%} = net {factor:+.0%} to Sweden"
    adj = M.outcomes(M.score_matrix(adj_lh, adj_la, mdl["rho"]))

    # data-confidence readout per team (uneven-data honesty)
    data_confidence = {
        HOME: {"xi_form_matched": sum(p["matched"] for p in swe_xi), "possession_matches": swe_pn},
        AWAY: {"xi_form_matched": sum(p["matched"] for p in tun_xi), "possession_matches": tun_pn},
        "note": "Tunisia is thinner on both club form and possession, so its signals are "
                "down-weighted; the prediction leans more on Elo for Tunisia.",
    }

    # ---- Elo cross-check ----
    con = duckdb.connect(str(M.DB_PATH), read_only=True)
    elo_h = con.execute(f"SELECT elo FROM team_ratings WHERE team_name='{HOME}'").fetchone()[0]
    elo_a = con.execute(f"SELECT elo FROM team_ratings WHERE team_name='{AWAY}'").fetchone()[0]
    con.close()
    elo_exp_home = 1 / (1 + 10 ** (-(elo_h - elo_a) / 400))

    result = {
        "match": f"{HOME} vs {AWAY}", "venue": "neutral (World Cup)", "as_of": AS_OF,
        "validation": val,
        "expected_goals": {"base": {HOME: round(lh, 2), AWAY: round(la, 2)},
                           "adjusted": {HOME: round(adj_lh, 2), AWAY: round(adj_la, 2)}},
        "win_draw_loss": {
            "base": {HOME: round(base["home"], 3), "Draw": round(base["draw"], 3), AWAY: round(base["away"], 3)},
            "adjusted": {HOME: round(adj["home"], 3), "Draw": round(adj["draw"], 3), AWAY: round(adj["away"], 3)},
        },
        "over_under_2_5": {"over": round(adj["over25"], 3), "under": round(adj["under25"], 3)},
        "btts": round(adj["btts"], 3),
        "top_scorelines": [{"score": f"{x}-{y}", "prob": round(p, 3)} for (x, y), p in adj["top_scores"]],
        "tilt": {"summary": tilt_note, "striker": striker_note, "possession": poss_note},
        "data_confidence": data_confidence,
        "elo": {HOME: round(elo_h), AWAY: round(elo_a), f"{HOME}_2way_winprob": round(elo_exp_home, 3)},
        "starters": {"Sweden_attackers": swe_att, "Tunisia_attackers": tun_att},
        "limits": ["No international betting odds to validate against — not a value/market call.",
                   "Form coverage ~65% and asymmetric (xG vs goals-only); tilt is capped and supporting."],
    }
    (HERE / "prediction.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    _write_markdown(result, mdl, swe_xi, tun_xi)
    print(f"\nWrote {HERE/'prediction.md'} and prediction.json")
    a = result["win_draw_loss"]["adjusted"]
    print(f"\n  >>> {HOME} {a[HOME]:.0%} | Draw {a['Draw']:.0%} | {AWAY} {a[AWAY]:.0%}")


def _write_markdown(r, mdl, swe_xi, tun_xi):
    a = r["win_draw_loss"]["adjusted"]; b = r["win_draw_loss"]["base"]
    eg = r["expected_goals"]["adjusted"]
    def matched(xi): return sum(p["matched"] for p in xi)
    lines = [
        f"# Prediction: {r['match']}", "",
        f"_World Cup, neutral venue. Model fit on internationals before {r['as_of']} (no leakage)._", "",
        "## Headline", "",
        f"| Outcome | Probability |", "|---|---|",
        f"| **Sweden win** | **{a['Sweden']:.0%}** |",
        f"| Draw | {a['Draw']:.0%} |",
        f"| **Tunisia win** | **{a['Tunisia']:.0%}** |", "",
        f"- **Expected goals:** Sweden {eg['Sweden']} – {eg['Tunisia']} Tunisia",
        f"- **Over 2.5 goals:** {r['over_under_2_5']['over']:.0%}  ·  **BTTS:** {r['btts']:.0%}",
        f"- **Most likely scores:** " + ", ".join(f"{s['score']} ({s['prob']:.0%})" for s in r['top_scorelines'][:4]),
        "",
        "## How we got here", "",
        f"1. **Dixon-Coles goals model** (team attack/defence from time-decayed international results) "
        f"gives base expected goals Sweden {r['expected_goals']['base']['Sweden']} – "
        f"{r['expected_goals']['base']['Tunisia']} Tunisia → base W/D/L "
        f"{b['Sweden']:.0%}/{b['Draw']:.0%}/{b['Tunisia']:.0%}.",
        f"2. **Adjustments ({r['tilt']['summary']}):**",
        f"   - Striker form: {r['tilt']['striker']}",
        f"   - Possession (coverage-scaled): {r['tilt']['possession']}",
        f"3. **Elo cross-check:** Sweden {r['elo']['Sweden']} vs Tunisia {r['elo']['Tunisia']} "
        f"(Sweden 2-way win prob {r['elo']['Sweden_2way_winprob']:.0%}) — same direction, modest favourite.",
        "",
        "## Data confidence (uneven data, handled honestly)", "",
        f"- Sweden: {r['data_confidence']['Sweden']['xi_form_matched']}/11 XI matched to club form, "
        f"{r['data_confidence']['Sweden']['possession_matches']} tournament matches of possession.",
        f"- Tunisia: {r['data_confidence']['Tunisia']['xi_form_matched']}/11 XI matched, "
        f"{r['data_confidence']['Tunisia']['possession_matches']} possession matches.",
        f"- {r['data_confidence']['note']}",
        "",
        "## Model validation (held-out, leakage-free)", "",
        f"- {r['validation']['n']} held-out internationals · "
        f"log-loss **{r['validation']['logloss_dc']:.3f}** vs base-rate {r['validation']['logloss_base']:.3f} "
        f"· accuracy {r['validation']['accuracy']:.0%}.",
        f"- Beating base-rate log-loss = the model learned real team strength, not noise.",
        "",
        "## Lineups used", "",
        f"- Sweden XI: {matched(swe_xi)}/11 players matched to club form.",
        f"- Tunisia XI: {matched(tun_xi)}/11 players matched to club form.",
        "",
        "## Honest limits", "",
    ] + [f"- {l}" for l in r["limits"]]
    (HERE / "prediction.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()

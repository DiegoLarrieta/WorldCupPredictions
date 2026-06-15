"""Feature-importance lab (INTERNATIONAL): does national-team possession help predict
international match results?

National possession exists only for major tournaments (FBref: WC, Euro, Copa América,
AFCON, Nations League, Gold Cup, Asian Cup) — no friendlies/qualifiers. So it's sparse,
and the answer here is suggestive, not definitive. But it's measured on the RIGHT domain:
national matches, not club games.

Method (leakage-free):
  1. Pull schedules (Poss + GF + GA + result) for every international tournament FBref
     exposes; combine into one national-team match log.
  2. Per team, build PRE-MATCH rolling averages (shift(1)) across tournaments: recent
     possession, goals for, goals against — a team's style/strength BEFORE the match.
  3. One row per match (neutral — oriented alphabetically, no home advantage).
  4. Time-split, fit multinomial logistic. ABLATION (drop a group, refit, measure
     held-out log-loss damage) + PERMUTATION importance. A feature is good iff removing
     or shuffling it makes held-out prediction worse.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import soccerdata as sd
from soccerdata import _config
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
ROLL = 6
TRAIN_FRAC = 0.7

# Register custom international tournaments (FBref names by best guess; failures skip).
_config.LEAGUE_DICT.update({
    "INT-Copa America": {"FBref": "Copa América", "season_start": "Jun", "season_end": "Jul"},
    "INT-AFCON": {"FBref": "Africa Cup of Nations", "season_start": "Jan", "season_end": "Feb"},
    "INT-Nations League": {"FBref": "UEFA Nations League", "season_start": "Sep", "season_end": "Jun"},
    "INT-Gold Cup": {"FBref": "CONCACAF Gold Cup", "season_start": "Jun", "season_end": "Jul"},
    "INT-Asian Cup": {"FBref": "Asian Cup", "season_start": "Jan", "season_end": "Feb"},
})

# (league, [seasons]) — only editions recent enough to carry possession (~2018+).
TOURNAMENTS = [
    ("INT-World Cup", ["2018", "2022"]),
    ("INT-European Championship", ["2020", "2024"]),
    ("INT-Copa America", ["2019", "2021", "2024"]),
    ("INT-AFCON", ["2019", "2021", "2023"]),
    ("INT-Nations League", ["2021", "2223", "2425"]),
    ("INT-Gold Cup", ["2019", "2021", "2023", "2025"]),
    ("INT-Asian Cup", ["2019", "2023"]),
]

FEATURES = {
    "possession": ["t_poss", "o_poss"],
    "attack form (goals for)": ["t_gf", "o_gf"],
    "defence form (goals against)": ["t_ga", "o_ga"],
}
ALL_COLS = [c for cols in FEATURES.values() for c in cols]


def pull_team_logs() -> pd.DataFrame:
    rows = []
    for league, seasons in TOURNAMENTS:
        for ssn in seasons:
            try:
                fb = sd.FBref(leagues=league, seasons=ssn)
                df = fb.read_team_match_stats(stat_type="schedule").reset_index()
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                if "Poss" not in df.columns:
                    print(f"  {league} {ssn}: no Poss, skip"); continue
                d = df[["team", "date", "opponent", "result", "GF", "GA", "Poss"]].copy()
                d["comp"] = f"{league} {ssn}"
                rows.append(d)
                print(f"  {league} {ssn}: {len(d)} team-matches")
            except Exception as e:
                print(f"  {league} {ssn}: skip ({type(e).__name__})")
    if not rows:
        raise SystemExit("no tournament data pulled")
    df = pd.concat(rows, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    for c in ("GF", "GA", "Poss"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["GF", "GA", "Poss", "result", "opponent"])
    df.to_csv(HERE / "intl_possession_raw.csv", index=False)
    return df.sort_values(["team", "date"])


def build(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("team", group_keys=False)
    df["r_poss"] = g["Poss"].apply(lambda s: s.shift(1).rolling(ROLL, min_periods=2).mean())
    df["r_gf"] = g["GF"].apply(lambda s: s.shift(1).rolling(ROLL, min_periods=2).mean())
    df["r_ga"] = g["GA"].apply(lambda s: s.shift(1).rolling(ROLL, min_periods=2).mean())

    team = df[["date", "team", "opponent", "result", "r_poss", "r_gf", "r_ga"]].rename(
        columns={"r_poss": "t_poss", "r_gf": "t_gf", "r_ga": "t_ga"})
    opp = df[["date", "team", "r_poss", "r_gf", "r_ga"]].rename(
        columns={"team": "opponent", "r_poss": "o_poss", "r_gf": "o_gf", "r_ga": "o_ga"})
    m = team.merge(opp, on=["date", "opponent"], how="inner").dropna(subset=ALL_COLS)
    # neutral venue: keep one row per match (team alphabetically first), no home term
    m = m[m["team"] < m["opponent"]].copy()
    m["y"] = m["result"].map({"W": 0, "D": 1, "L": 2})
    return m.dropna(subset=["y"]).sort_values("date").reset_index(drop=True)


def main():
    print("Pulling international tournament schedules (FBref) ...")
    m = build(pull_team_logs())
    cut = int(len(m) * TRAIN_FRAC)
    tr, te = m.iloc[:cut], m.iloc[cut:]
    print(f"\n  {len(m)} tournament matches with pre-match history | "
          f"train {len(tr)} / test {len(te)}")
    if len(te) < 40:
        print("  ! very small held-out sample — treat results as directional only")

    def fit_eval(cols):
        clf = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000))
        clf.fit(tr[cols], tr["y"])
        return clf, log_loss(te["y"], clf.predict_proba(te[cols]), labels=[0, 1, 2])

    base = np.tile(tr["y"].value_counts(normalize=True).sort_index().to_numpy(), (len(te), 1))
    ll_base = log_loss(te["y"], base, labels=[0, 1, 2])
    full, ll_full = fit_eval(ALL_COLS)
    print(f"\n  base-rate log-loss : {ll_base:.4f}")
    print(f"  full-model log-loss: {ll_full:.4f}  ({ll_base - ll_full:+.4f} vs base-rate)")

    print("\n=== ABLATION (drop group, refit, held-out log-loss damage) ===")
    rows = []
    for name, cols in FEATURES.items():
        keep = [c for c in ALL_COLS if c not in cols]
        _, ll = fit_eval(keep)
        rows.append((name, ll, ll - ll_full))
        print(f"  {name:<30} without -> {ll:.4f}   damage {ll - ll_full:+.4f}")

    print("\n=== PERMUTATION IMPORTANCE (shuffle in test, drop in log-loss) ===")
    r = permutation_importance(full, te[ALL_COLS], te["y"], n_repeats=30,
                               scoring="neg_log_loss", random_state=0)
    for col, imp, sd_ in sorted(zip(ALL_COLS, r.importances_mean, r.importances_std),
                                key=lambda t: -t[1]):
        print(f"  {col:<8} {imp:+.4f} ± {sd_:.4f}  {'█' * max(0, round(imp * 200))}")

    poss_dmg = dict((n, d) for n, _, d in rows)["possession"]
    verdict = ("HELPS" if poss_dmg > 0.002 else
               "no measurable help (within noise)" if poss_dmg <= 0.002 else "HURTS")
    print(f"\n  VERDICT: removing national possession changes held-out log-loss by "
          f"{poss_dmg:+.4f} -> possession {verdict}.")
    _write(ll_base, ll_full, rows, poss_dmg, verdict, len(m), len(te))
    print(f"  wrote {HERE/'possession_importance.md'}")


def _write(ll_base, ll_full, rows, poss_dmg, verdict, n, n_te):
    L = [
        "# Does national-team possession help predict international results?", "",
        f"_International tournaments only (WC/Euro/Copa/AFCON/Nations League/Gold Cup/Asian "
        f"Cup). Leakage-free pre-match rolling features. {n} matches, {n_te} held-out._", "",
        "## Results", "",
        f"- Base-rate log-loss: **{ll_base:.4f}**",
        f"- Full model: **{ll_full:.4f}**", "",
        "| Feature group | log-loss without it | damage (higher = more useful) |",
        "|---|---|---|",
    ] + [f"| {nm} | {ll:.4f} | {d:+.4f} |" for nm, ll, d in rows] + [
        "", "## Verdict on possession", "",
        f"Removing national possession changes held-out log-loss by **{poss_dmg:+.4f}** → "
        f"possession **{verdict}**.", "",
        "_Possession correlates with winning, but most of that is already captured by "
        "goal-scoring form/strength. This measures what it adds **on top** — the only thing "
        "that matters for prediction. Caveat: national possession is tournament-only and "
        "sparse, so treat as directional._",
    ]
    (HERE / "possession_importance.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()

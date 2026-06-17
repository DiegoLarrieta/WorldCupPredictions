"""Feedback loop — score published predictions against real results.

A finished World Cup match we predicted is a labeled, out-of-sample example. This
module turns it into a canonical record under ``data/worldcupmatches/`` and scores the
prediction we ACTUALLY published (a frozen snapshot) against the realized outcome.

Three honest-scoring rules, all enforced here:
  1. Score the frozen prediction, never a re-fit (a re-fit leaks the result through
     online-updated ratings and flatters the model).
  2. Tag every outcome field with its source + capture time; spine lands live-night,
     rich stats (xG, shots, ...) backfill later without overwriting the record.
  3. Score the ensemble AND its components, so "the ensemble beats its parts" is
     re-checked on live data instead of asserted.

CI-safe: no DuckDB / network import. Pure json + numpy. Match-folder I/O only.

    from engine.feedback import record_outcome, monitor
    record_outcome("predictions/ira-nor", home_goals=0, away_goals=2, stage="group", group="E")
    monitor()   # writes data/worldcupmatches/_monitor.{md,json}
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from pathlib import Path

import numpy as np

from engine.evaluate import log_loss, reliability, rps

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = REPO_ROOT / "data" / "worldcupmatches"
_PARAMS_PATH = REPO_ROOT / "engine" / "params.json"

_ORDER = ("home", "draw", "away")  # canonical outcome order for arrays / y


# --- helpers ----------------------------------------------------------------
def team_code(name: str) -> str:
    """Short slug used in match keys: 'Iraq' -> 'ira', 'Norway' -> 'nor'."""
    return re.sub(r"[^a-z]", "", name.lower())[:3]


def match_key(date: str, home: str, away: str) -> str:
    return f"{date}-{team_code(home)}-{team_code(away)}"


def result_to_y(home_goals: int, away_goals: int) -> int:
    """0 = home win, 1 = draw, 2 = away win (the regulation result)."""
    if home_goals > away_goals:
        return 0
    if home_goals == away_goals:
        return 1
    return 2


def _params_hash() -> str:
    return hashlib.sha256(_PARAMS_PATH.read_bytes()).hexdigest()[:16]


def _wdl_to_vec(wdl: dict, home: str, away: str) -> list[float]:
    """{home: p, 'Draw': p, away: p} -> [home, draw, away]."""
    return [float(wdl[home]), float(wdl["Draw"]), float(wdl[away])]


def _now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# --- scoring ----------------------------------------------------------------
def score_prediction(probs: list[float] | np.ndarray, y: int) -> dict:
    """Proper scores for one [home, draw, away] vector against outcome y.

    RPS (ordered, the proper metric here), log-loss, multiclass Brier, and surprisal
    (−log p(actual) — how shocked the model was; flags confidently-wrong bets).
    """
    p = np.clip(np.asarray(probs, dtype=float), 1e-12, 1.0)
    p = p / p.sum()
    onehot = np.eye(3)[y]
    return {
        "rps": round(rps(p[None, :], np.array([y])), 5),
        "log_loss": round(log_loss(p[None, :], np.array([y])), 5),
        "brier": round(float(np.sum((p - onehot) ** 2)), 5),  # multiclass, range 0..2
        "surprisal": round(float(-np.log(p[y])), 5),
    }


# --- record I/O -------------------------------------------------------------
def record_path(key: str) -> Path:
    return DATASET_DIR / f"{key}.json"


def _freeze_prediction(pred: dict) -> dict:
    """Snapshot the published prediction — the immutable 'what we said'."""
    wdl = pred["win_draw_loss"]
    home, away = pred["match"].split(" vs ")
    return {
        "match": pred["match"],
        "home": home,
        "away": away,
        "as_of": pred["as_of"],
        "model": pred["model"],
        "ensemble_weight_on_dc": pred["ensemble_weight_on_dc"],
        "calibration_temperature": pred["calibration_temperature"],
        "params_hash": _params_hash(),
        "ensemble": _wdl_to_vec(wdl["ENSEMBLE"], home, away),
        "components": {
            "dixon_coles": _wdl_to_vec(wdl["dixon_coles"], home, away),
            "elo": _wdl_to_vec(wdl["elo"], home, away),
        },
        "expected_goals": pred.get("expected_goals"),
        "over25": pred.get("over_under_2_5", {}).get("over"),
        "btts": pred.get("btts"),
        "top_scorelines": pred.get("top_scorelines"),
    }


def _score_all(frozen: dict, y: int) -> dict:
    """Score the ensemble and each component, plus surprisal — on the same outcome."""
    per_model = {"ensemble": score_prediction(frozen["ensemble"], y)}
    for name, vec in frozen["components"].items():
        per_model[name] = score_prediction(vec, y)
    top = per_model["ensemble"]
    return {"y": y, **top, "per_model": per_model}


def record_outcome(match_dir, home_goals: int, away_goals: int, *, stage: str,
                   group: str | None = None, venue: str | None = None,
                   extra: dict | None = None, source: str = "manual") -> dict:
    """Score a finished match and write/refresh its worldcupmatches record.

    Reads the FROZEN prediction from ``<match_dir>/prediction.json``, builds (or updates)
    the canonical record, fills ``actual_result`` back into prediction.json, and computes
    proper scores against the published probabilities. ``extra`` holds optional rich stats
    (xg_home, xg_away, possession_home, ...) tagged to the spine's source.
    """
    match_dir = Path(match_dir)
    pred = json.loads((match_dir / "prediction.json").read_text())
    frozen = _freeze_prediction(pred)
    home, away = frozen["home"], frozen["away"]
    y = result_to_y(home_goals, away_goals)
    key = match_key(pred["as_of"] if pred.get("as_of") else _now()[:10], home, away)

    spine = {
        "home_goals": int(home_goals),
        "away_goals": int(away_goals),
        "result": _ORDER[y],
        "source": source,
        "captured_at": _now(),
    }
    record = {
        "match_key": key,
        "schema_version": 1,
        "identity": {
            "match_key": key, "date": pred.get("as_of"), "home": home, "away": away,
            "neutral": pred.get("venue") == "neutral", "venue": venue or pred.get("venue"),
            "competition": pred.get("competition", "World Cup"),
            "stage": stage, "group": group,
        },
        "prediction": frozen,
        "outcome": {"spine": spine, "rich": (extra or None)},
        "scores": _score_all(frozen, y),
    }

    DATASET_DIR.mkdir(parents=True, exist_ok=True)
    record_path(key).write_text(json.dumps(record, indent=2, ensure_ascii=False))
    _write_actual_result(match_dir, pred, record)
    return record


def backfill_rich(key: str, *, source: str = "fbref", **stats) -> dict:
    """Add the rich stats layer (xG, shots, possession, ...) to an existing record.

    Non-destructive: the spine + frozen prediction are untouched; this only fills the
    later-arriving detail and stamps its provenance.
    """
    path = record_path(key)
    record = json.loads(path.read_text())
    rich = dict(record["outcome"].get("rich") or {})
    rich.update(stats)
    rich["source"] = source
    rich["captured_at"] = _now()
    record["outcome"]["rich"] = rich
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
    return record


def _write_actual_result(match_dir: Path, pred: dict, record: dict) -> None:
    """Fill actual_result in the match folder's prediction.json (closes the loop there)."""
    sp, sc = record["outcome"]["spine"], record["scores"]
    pred["actual_result"] = {
        "score": f"{sp['home_goals']}-{sp['away_goals']}",
        "result": sp["result"],
        "scored_at": sp["captured_at"],
        "rps": sc["rps"], "log_loss": sc["log_loss"], "brier": sc["brier"],
        "surprisal": sc["surprisal"],
    }
    (match_dir / "prediction.json").write_text(json.dumps(pred, indent=2, ensure_ascii=False))


# --- tournament monitor -----------------------------------------------------
def load_tournament() -> list[dict]:
    """All scored records, oldest match first."""
    if not DATASET_DIR.exists():
        return []
    recs = [json.loads(p.read_text()) for p in DATASET_DIR.glob("*.json")
            if not p.name.startswith("_")]
    return sorted(recs, key=lambda r: r["identity"].get("date") or "")


def _baseline_scores(probs_matrix: np.ndarray, ys: np.ndarray) -> dict:
    """Naive baselines so 'are we adding value?' is a number, not a vibe."""
    n = len(ys)
    uniform = np.full((n, 3), 1 / 3)
    return {
        "uniform": {"rps": round(rps(uniform, ys), 5), "log_loss": round(log_loss(uniform, ys), 5)},
        "ensemble": {"rps": round(rps(probs_matrix, ys), 5),
                     "log_loss": round(log_loss(probs_matrix, ys), 5)},
    }


def monitor(write: bool = True) -> dict:
    """Roll up tournament performance: per-model proper scores, calibration, vs baseline."""
    recs = load_tournament()
    if not recs:
        return {"n": 0}

    ys = np.array([r["scores"]["y"] for r in recs])
    models = ("ensemble", "dixon_coles", "elo")

    def vecs(m: str) -> np.ndarray:
        if m == "ensemble":
            return np.array([r["prediction"]["ensemble"] for r in recs])
        return np.array([r["prediction"]["components"][m] for r in recs])

    mats = {m: vecs(m) for m in models}
    per_model = {}
    for m in models:
        P = mats[m]
        per_model[m] = {"rps": round(rps(P, ys), 5), "log_loss": round(log_loss(P, ys), 5),
                        "brier": round(float(np.mean(np.sum(
                            (P - np.eye(3)[ys]) ** 2, axis=1))), 5)}

    ens = mats["ensemble"]
    worst = sorted(recs, key=lambda r: -r["scores"]["surprisal"])[:3]
    summary = {
        "n": len(recs),
        "per_model": per_model,
        "vs_baseline": _baseline_scores(ens, ys),
        "calibration": reliability(ens, ys, bins=5),
        "ensemble_beats_components": all(
            per_model["ensemble"]["rps"] <= per_model[m]["rps"] for m in ("dixon_coles", "elo")),
        "most_surprising": [{"match": r["prediction"]["match"],
                             "result": r["outcome"]["spine"]["result"],
                             "surprisal": r["scores"]["surprisal"]} for r in worst],
    }
    if write:
        DATASET_DIR.mkdir(parents=True, exist_ok=True)
        (DATASET_DIR / "_monitor.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        (DATASET_DIR / "_monitor.md").write_text(_monitor_md(summary))
    return summary


def _monitor_md(s: dict) -> str:
    pm = s["per_model"]
    L = [f"# WC2026 prediction monitor — {s['n']} matches scored", "",
         "_Lower RPS / log-loss / Brier is better. Scores are against the probabilities we",
         "actually published (frozen), on real out-of-sample matches._", "",
         "## Proper scores by model", "",
         "| Model | RPS | Log-loss | Brier |", "|---|---|---|---|"]
    for m in ("ensemble", "dixon_coles", "elo"):
        L.append(f"| {m} | {pm[m]['rps']:.4f} | {pm[m]['log_loss']:.4f} | {pm[m]['brier']:.4f} |")
    base = s["vs_baseline"]
    L += ["", "## Are we beating naive?", "",
          f"- Uniform (1/3 each): RPS {base['uniform']['rps']:.4f}, "
          f"log-loss {base['uniform']['log_loss']:.4f}",
          f"- **Our ensemble**: RPS {base['ensemble']['rps']:.4f}, "
          f"log-loss {base['ensemble']['log_loss']:.4f}",
          f"- Ensemble beats both single models so far: "
          f"**{'yes' if s['ensemble_beats_components'] else 'NO — investigate'}**", "",
          "## Most surprising results (confidently-wrong watch)", ""]
    for w in s["most_surprising"]:
        L.append(f"- {w['match']} → {w['result']} (surprisal {w['surprisal']:.2f})")
    return "\n".join(L) + "\n"

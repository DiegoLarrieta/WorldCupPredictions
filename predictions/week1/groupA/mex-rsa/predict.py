"""Mexico vs South Africa (matchday 1, 2026-06-11) — config only; logic in the engine.

Run:  python predict.py   (writes prediction.json + prediction.md here)

AS_OF is pinned to the match date so the model sees ONLY internationals strictly before
kickoff — even though this result is already in the warehouse, the leakage guard excludes
it. Re-run to verify the numbers are reproducible.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "Mexico", "South Africa", True
AS_OF = "2026-06-11"   # pinned to match date: leakage-free

LINEUPS = {
    "Mexico": {"formation": "4-1-2-3", "xi": [
        "1 Raul Rangel (GK)", "15 Israel Reyes", "3 C. Montes", "5 J. Vasquez",
        "23 J. Gallardo", "6 Erik Lira", "8 Alvaro Fidalgo", "26 Brian Gutierrez",
        "25 R. Alvarado", "9 R. Jimenez", "16 Julian Quinones"]},
    "South Africa": {"formation": "5-3-2", "xi": [
        "1 R. Williams (GK)", "6 A. Modiba", "14 Mbekezeli Mbokazi", "19 Nkosinathi Sibisi",
        "21 Ime Okon", "20 Khuliso Mudau", "4 T. Mokoena", "13 Siphephelo Sithole",
        "23 Jayden Adams", "15 Iqraam Rayners", "9 Lyle Foster"]},
}

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF, lineups=LINEUPS)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

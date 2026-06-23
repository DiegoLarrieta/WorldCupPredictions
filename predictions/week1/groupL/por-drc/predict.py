"""Portugal vs DR Congo — config only; all logic lives in the shared engine.

Run:  python predict.py   (writes prediction.json + prediction.md here)
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "Portugal", "DR Congo", True
AS_OF = "2026-06-17"   # pinned to match date: re-running stays leakage-free (model sees only matches strictly before this)

LINEUPS = {
    "Portugal": {"formation": "4-2-3-1", "xi": [
        "1 Diogo Costa (GK)", "20 João Cancelo", "4 Tomás Araújo", "13 Renato Veiga",
        "25 Nuno Mendes", "15 João Neves", "23 Vitinha", "10 Bernardo Silva",
        "8 Bruno Fernandes", "18 Pedro Neto", "7 Cristiano Ronaldo"]},
    "DR Congo": {"formation": "5-3-2", "xi": [
        "1 Lionel M'Pasi (GK)", "26 Arthur Masuaku", "3 Steve Kapuadi", "4 Axel Tuanzebe",
        "22 Chancel Mbemba", "2 Aaron Wan-Bissaka", "25 Edo Kayembe", "6 Ngal'ayel Mukau",
        "8 Samuel Moutoussamy", "20 Yoane Wissa", "17 Cédric Bakambu"]},
}

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF, lineups=LINEUPS)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

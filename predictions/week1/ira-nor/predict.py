"""Iraq vs Norway — config only; all logic lives in the shared engine.

Run:  python predict.py   (writes prediction.json + prediction.md here)
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "Iraq", "Norway", True
AS_OF = "2026-06-16"   # pinned to match date: re-running stays leakage-free (model sees only matches strictly before this)

LINEUPS = {
    "Iraq": {"formation": "4-4-2", "xi": [
        "12 Jalal Hasan (GK)", "3 Hussein Ali", "4 Zaid Tahseen", "5 A. Hashim",
        "23 Merchas Doski", "8 Ibrahim Bayesh", "16 Amir Al-Ammari", "24 Z. Ismael",
        "17 Ali Jasim", "18 Aymen Hussein", "9 Ali Al-Hamadi"]},
    "Norway": {"formation": "4-3-3", "xi": [
        "1 Ørjan Nyland (GK)", "5 David Møller Wolfe", "17 Torbjørn Heggem",
        "3 Kristoffer Ajer", "26 Julian Ryerson", "14 Fredrik Aursnes", "8 Sander Berge",
        "10 M. Ødegaard", "20 Antonio Nusa", "9 Erling Haaland", "7 Alexander Sørloth"]},
}

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF, lineups=LINEUPS)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

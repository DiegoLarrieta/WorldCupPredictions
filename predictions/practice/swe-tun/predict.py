"""Sweden vs Tunisia — config only; all logic lives in the shared engine.

Run:  python predict.py   (writes prediction.json + prediction.md here)

Note: earlier this folder carried experimental tilts (striker form, possession).
Those were validated out — striker tilt HURT held-out prediction; club form adds no
value over the results model. The validated model is the Elo + Dixon-Coles ensemble,
applied identically to every match via the engine.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "Sweden", "Tunisia", True
AS_OF = "2026-06-16"   # pinned to match date: re-running stays leakage-free (model sees only matches strictly before this)

LINEUPS = {
    "Sweden": {"formation": "3-4-1-2", "xi": [
        "23 Kristoffer Nordfeldt (GK)", "2 Gustaf Lagerbielke", "4 Isak Hien",
        "3 Victor Lindelöf", "21 Alexander Bernhardsson", "16 Jesper Karlström",
        "18 Yasin Ayari", "5 Gabriel Gudmundsson", "10 Benjamin Nygren",
        "17 Viktor Gyökeres", "9 Alexander Isak"]},
    "Tunisia": {"formation": "4-2-3-1", "xi": [
        "1 Abdelmouhib Chamakh (GK)", "2 Ali Abdi", "4 Omar Rekik", "3 Montassar Talbi",
        "20 Yan Valery", "17 Ellyes Skhiri", "13 Rani Khedira", "21 Mohamed Amine Ben Hmida",
        "10 Hannibal Mejbri", "25 Anis Slimane", "8 Elias Saad"]},
}

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF, lineups=LINEUPS)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

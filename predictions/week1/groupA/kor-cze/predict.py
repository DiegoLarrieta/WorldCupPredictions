"""South Korea vs Czech Republic (matchday 1, 2026-06-11) — config only; logic in engine.

Run:  python predict.py   (writes prediction.json + prediction.md here)

AS_OF pinned to the match date: the model sees ONLY internationals strictly before
kickoff, so the result already in the warehouse is excluded (leakage-free). Reproducible.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "South Korea", "Czech Republic", True
AS_OF = "2026-06-11"   # pinned to match date: leakage-free

LINEUPS = {
    "South Korea": {"formation": "3-4-3", "xi": [
        "1 Kim Seung-gyu (GK)", "2 Lee Han-beom", "4 Kim Min-jae", "3 Lee Gi-hyuk",
        "22 Seol Young-woo", "6 Hwang In-beom", "8 Paik Seung-ho", "13 Lee Tae-seok",
        "19 K. Lee", "7 Son Heung-Min", "10 Lee Jae-sung"]},
    "Czech Republic": {"formation": "3-4-3", "xi": [
        "1 Matej Kovar (GK)", "4 Robin Hranac", "7 Ladislav Krejci", "6 Stepan Chaloupek",
        "20 Jaroslav Zeleny", "24 Alexandr Sojka", "22 T. Soucek", "5 Vladimir Coufal",
        "15 Pavel Sulc", "10 Patrik Schick", "17 Lukas Provod"]},
}

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF, lineups=LINEUPS)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

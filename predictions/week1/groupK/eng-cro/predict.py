"""England vs Croatia — config only; all logic lives in the shared engine.

Run:  python predict.py   (writes prediction.json + prediction.md here)
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "England", "Croatia", True
AS_OF = "2026-06-17"   # pinned to match date: re-running stays leakage-free (model sees only matches strictly before this)

LINEUPS = {
    "England": {"formation": "4-2-3-1", "xi": [
        "1 Jordan Pickford (GK)", "24 Reece James", "2 Ezri Konsa", "5 John Stones",
        "3 Nico O'Reilly", "8 Elliot Anderson", "4 Declan Rice", "20 Noni Madueke",
        "10 Jude Bellingham", "18 Anthony Gordon", "9 Harry Kane"]},
    "Croatia": {"formation": "3-4-2-1", "xi": [
        "1 Dominik Livaković (GK)", "4 Joško Gvardiol", "22 Luka Vušković", "6 Josip Šutalo",
        "14 Ivan Perišić", "17 Petar Sučić", "10 Luka Modrić", "2 Josip Stanišić",
        "16 Martin Baturina", "15 Mario Pašalić", "26 Petar Musa"]},
}

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF, lineups=LINEUPS)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

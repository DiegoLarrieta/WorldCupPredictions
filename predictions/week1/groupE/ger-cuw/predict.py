"""Germany vs Curaçao (matchday 1, 2026-06-14) — config; lógica en el engine.

Run:  python predict.py   (escribe prediction.json + prediction.md aquí)

AS_OF fijado a la fecha del partido: el modelo ve SOLO internacionales estrictamente
antes del kickoff (sin fuga). Lineups omitidos (contexto, no input del modelo).
"""
import sys
from pathlib import Path
_root = Path(__file__).resolve()
while not (_root / "engine").is_dir():
    _root = _root.parent
sys.path.insert(0, str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "Germany", "Curaçao", True
AS_OF = "2026-06-14"

if __name__ == "__main__":
    res = predict_match(HOME, AWAY, neutral=NEUTRAL, as_of=AS_OF)
    save_match(res, Path(__file__).resolve().parent)
    e = res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

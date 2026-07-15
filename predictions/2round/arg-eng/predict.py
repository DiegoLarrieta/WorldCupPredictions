"""Argentina vs England (semifinal, 2026-07-15) — config; lógica en el engine. AS_OF sin fuga.

Alineaciones oficiales (ESPN, event 760515) — contexto para props + registro, NO input del modelo.
"""
import sys
from pathlib import Path
_root=Path(__file__).resolve()
while not (_root/"engine").is_dir(): _root=_root.parent
sys.path.insert(0,str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "England", "Argentina", True
AS_OF = "2026-07-15"

LINEUPS = {
    "England": {"formation": "4-2-3-1", "xi": [
        "1 Jordan Pickford (GK)", "24 Reece James", "5 John Stones", "6 Marc Guéhi",
        "25 Djed Spence", "4 Declan Rice", "8 Elliot Anderson", "17 Morgan Rogers",
        "10 Jude Bellingham", "18 Anthony Gordon", "9 Harry Kane"]},
    "Argentina": {"formation": "4-4-2", "xi": [
        "23 Emiliano Martínez (GK)", "26 Nahuel Molina", "13 Cristian Romero",
        "6 Lisandro Martínez", "3 Nicolás Tagliafico", "17 Giuliano Simeone",
        "5 Leandro Paredes", "20 Alexis Mac Allister", "24 Enzo Fernández",
        "10 Lionel Messi", "9 Julián Álvarez"]},
}

if __name__=="__main__":
    res=predict_match(HOME,AWAY,neutral=NEUTRAL,as_of=AS_OF,lineups=LINEUPS)
    save_match(res,Path(__file__).resolve().parent)
    e=res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

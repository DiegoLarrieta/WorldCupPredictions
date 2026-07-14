"""France vs Spain (semifinal / Semifinal, 2026-07-14) — config; lógica en el engine. AS_OF sin fuga.

Alineaciones oficiales (ESPN, event 760514) — contexto para props + registro, NO input del modelo.
"""
import sys
from pathlib import Path
_root=Path(__file__).resolve()
while not (_root/"engine").is_dir(): _root=_root.parent
sys.path.insert(0,str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "France", "Spain", True
AS_OF = "2026-07-14"

LINEUPS = {
    "France": {"formation": "4-2-3-1", "xi": [
        "16 Mike Maignan (GK)", "5 Jules Koundé", "4 Dayot Upamecano", "17 William Saliba",
        "3 Lucas Digne", "8 Aurélien Tchouaméni", "14 Adrien Rabiot", "7 Ousmane Dembélé",
        "11 Michael Olise", "12 Bradley Barcola", "10 Kylian Mbappé"]},
    "Spain": {"formation": "4-2-3-1", "xi": [
        "23 Unai Simón (GK)", "12 Pedro Porro", "22 Pau Cubarsí", "14 Aymeric Laporte",
        "24 Marc Cucurella", "16 Rodri", "8 Fabián Ruiz", "19 Lamine Yamal",
        "10 Dani Olmo", "15 Álex Baena", "21 Mikel Oyarzabal"]},
}

if __name__=="__main__":
    res=predict_match(HOME,AWAY,neutral=NEUTRAL,as_of=AS_OF,lineups=LINEUPS)
    save_match(res,Path(__file__).resolve().parent)
    e=res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

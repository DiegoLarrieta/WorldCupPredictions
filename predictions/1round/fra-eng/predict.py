"""France vs England (third place / 1round, 2026-07-18, Hard Rock Stadium Miami) — config; lógica en el engine.

Alineaciones prensa pre-partido (RotoWire/VoiceOfEmirates, rotación fuerte en ambos lados;
Saliba out por lesión, Samba duda) — contexto para props + registro, NO input del modelo.
"""
import sys
from pathlib import Path
_root=Path(__file__).resolve()
while not (_root/"engine").is_dir(): _root=_root.parent
sys.path.insert(0,str(_root))
from engine import predict_match, save_match

HOME, AWAY, NEUTRAL = "France", "England", True
AS_OF = "2026-07-18"

LINEUPS = {
    "France": {"formation": "4-2-3-1", "xi": [
        "Mike Maignan (GK)", "Malo Gusto", "Ibrahima Konaté", "Maxence Lacroix",
        "Théo Hernandez", "N'Golo Kanté", "Warren Zaïre-Emery", "Ousmane Dembélé",
        "Rayan Cherki", "Bradley Barcola", "Kylian Mbappé"]},
    "England": {"formation": "4-2-3-1", "xi": [
        "Jordan Pickford (GK)", "Djed Spence", "Marc Guéhi", "Ezri Konsa",
        "Nico O'Reilly", "Kobbie Mainoo", "Eberechi Eze", "Noni Madueke",
        "Morgan Rogers", "Marcus Rashford", "Harry Kane"]},
}

if __name__=="__main__":
    res=predict_match(HOME,AWAY,neutral=NEUTRAL,as_of=AS_OF,lineups=LINEUPS)
    save_match(res,Path(__file__).resolve().parent)
    e=res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

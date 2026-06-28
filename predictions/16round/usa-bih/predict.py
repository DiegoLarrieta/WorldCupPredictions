"""United States vs Bosnia and Herzegovina (16avos de final / Round of 32, 2026-07-02) — config; lógica en el engine. AS_OF sin fuga."""
import sys
from pathlib import Path
_root=Path(__file__).resolve()
while not (_root/"engine").is_dir(): _root=_root.parent
sys.path.insert(0,str(_root))
from engine import predict_match, save_match
HOME, AWAY, NEUTRAL = "United States", "Bosnia and Herzegovina", True
AS_OF = "2026-07-02"
if __name__=="__main__":
    res=predict_match(HOME,AWAY,neutral=NEUTRAL,as_of=AS_OF)
    save_match(res,Path(__file__).resolve().parent)
    e=res["win_draw_loss"]["ENSEMBLE"]
    print(f"{res['match']}: {HOME} {e[HOME]:.0%} | Draw {e['Draw']:.0%} | {AWAY} {e[AWAY]:.0%}")

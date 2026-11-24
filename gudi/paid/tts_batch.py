"""The week's narration takes, one per episode, in batch order. Run on the Mac (it holds the key).

python3 -m gudi.paid.tts_batch week-1 ep03-vemulavada [ep04-... ...] --cap 6668

For each episode, in the order given:
  - its take is reused if already on disk or in Speech History (gudi.paid.tts_once rules: never paid twice);
  - otherwise, before the one paid request, the live ElevenLabs balance must cover the script and the
    batch cap must still have room for it; if either fails, that episode and the rest are held.
Takes land in episodes/<slug>/takes/<slug>-take.mp3 with the character timings beside them.
Prints one JSON line per episode and a summary line. The key is read from .env.local, never printed.
"""
import argparse
import json

from ..paths import ROOT
from . import tts_once
from .elevenlabs import _get


def remaining():
    s = _get("/user/subscription")
    return int(s["character_limit"]) - int(s["character_count"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("batch")
    ap.add_argument("episodes", nargs="+")
    ap.add_argument("--cap", type=int, required=True, help="most characters this batch may spend")
    a = ap.parse_args(argv)
    spent, held = 0, []
    for slug in a.episodes:
        if held:
            held.append(slug)
            continue
        text_path = f"episodes/{slug}/voice.te.txt"
        chars = len((ROOT / text_path).read_text(encoding="utf-8").strip())
        dest = ROOT / "episodes" / slug / "takes" / f"{slug}-take.mp3"
        if not dest.exists():
            left = remaining()
            if left < chars or spent + chars > a.cap:
                print(json.dumps({"episode": slug, "result": "held", "characters": chars, "balance_left": left,
                                  "batch_spent": spent, "cap": a.cap}, ensure_ascii=False))
                held.append(slug)
                continue
        tts_once.main(text_path, str(dest))
        r = dict(tts_once.LAST)
        if r.get("result") == "new take":
            spent += chars
        print(json.dumps({"episode": slug, **r}, ensure_ascii=False))
        if r.get("result", "").startswith(("error", "stopped")):
            held.append(slug)
    print(json.dumps({"summary": True, "batch_spent_characters": spent, "cap": a.cap, "held": held}, ensure_ascii=False))
    return 0 if not held else 1


if __name__ == "__main__":
    raise SystemExit(main())

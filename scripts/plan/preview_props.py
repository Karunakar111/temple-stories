#!/usr/bin/env python3
"""Build Remotion props for an episode technical preview from shots.json.

Every picture is either TEMPORARY ART (an EP01 painting standing in, never Kolanupaka) or a
local PLATE (lamps / stone drawn in code). Typesetting (titles, names, date card, questions,
reminders) is the real local work and renders as it would in the final film.

Usage: python3 scripts/plan/preview_props.py ep02-kolanupaka > build/ep02-preview/props.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# EP02: what stands in for each shot until the paid stills exist.
ART = {
    "S01": ("plate", "lamps", None),
    "S02": ("plate", "lamps", None),
    "S03": ("temp", "scenes/p2-08-jatara-crowd.png", "50% 70%"),
    "S04": ("plate", "lamps", None),
    "S05": ("temp", "scenes/p2-08-jatara-crowd.png", "50% 95%"),
    "S06": ("temp", "exp01/hill-sky.jpg", "50% 30%"),
    "S07": ("temp", "scenes/p1-02-hill-dawn.png", "50% 40%"),
    "S08": ("temp", "scenes/p1-02-hill-dawn.png", "50% 80%"),
    "S09": ("temp", "scenes/p1-07-gardener.png", "50% 60%"),
    "S10": ("temp", "scenes/p1-07-gardener.png", "45% 75%"),
    "S11": ("temp", "scenes/p2-06-oggu-priest.png", "50% 40%"),
    "S12": ("temp", "scenes/p2-06-oggu-priest.png", "50% 30%"),
    "S13": ("temp", "scenes/p2-06-oggu-priest.png", "50% 30%"),
    "S14": ("plate", "lamps", None),
    "S15": ("plate", "lamps", None),
    "S16a": ("temp", "scenes/p1-02-hill-dawn.png", "50% 95%"),
    "S16b": ("plate", "stone", None),
    "S16c": ("plate", "lamps", None),
    "S17": ("temp", "scenes/p1-02-hill-dawn.png", "50% 95%"),
}

# Typesetting that is part of the final film (local work, not temporary).
TYPE = {
    "S01": {"kind": "title", "lines": ["కొలనుపాక", "సోమేశ్వరుడు"]},
    "S03": {"kind": "card", "lines": ["‘సిద్ధాంత శిఖామణి’"], "at": 2.2},
    "S05": {"kind": "name", "lines": ["రేణుకాచార్యుడు"], "at": 4.6},
    "S13": {"kind": "questions", "lines": ["భక్తుని ప్రయాణం ఎక్కడ మొదలవుతుంది?", "శివుడితో ఐక్యం కావడమంటే ఏంటి?"], "at": 0.3},
    "S16b": {"kind": "date", "lines": ["క్రీ.శ. 1067", "పూజలకు దానం"], "at": 0.4},
    "S17": {"kind": "reminders", "lines": ["1 · లింగం దగ్గర రేణుకాచార్యుడి కథ", "2 · ఆవరణలోని శాసనం, పూజలకు దానం"], "at": 2.6},
}

# Local light effects that the final film also uses (emergence, return into light).
FX = {"S02": "emerge", "S15": "return", "S16c": "arati"}


def main(slug):
    ep = ROOT / "episodes" / slug
    doc = json.loads((ep / "shots.json").read_text(encoding="utf-8"))
    timing = ep / "timing.json"
    timed = json.loads(timing.read_text(encoding="utf-8")) if timing.exists() else None
    shots = []
    for s in doc["shots"]:
        if s["est_dur_s"] <= 0:
            continue
        kind, src, pos = ART[s["id"]]
        clips = [c["settings"].get("duration") for c in s["paid"] if c["asset_type"] == "clip"]
        if timed:
            clips = [timed["clips"].get(s["id"], {}).get("duration", d) for d in clips]
        shots.append({
            "id": s["id"], "start": s["est_start_s"], "dur": s["est_dur_s"],
            "hold": s.get("hold_after_s", 0.0), "text": s["text"], "picture": s["picture"],
            "cls": s["class"], "clip_s": clips[0] if clips else None,
            "reuse": s.get("media_from"),
            "art": {"kind": kind, "src": src, "pos": pos},
            "type": TYPE.get(s["id"]), "fx": FX.get(s["id"]),
        })
    total = max(x["start"] + x["dur"] for x in shots) + 1.0
    print(json.dumps({
        "episode": slug, "revision": doc.get("revision"),
        "timing": "take" if timed else "estimate (no narration yet)",
        "total_s": round(total, 2), "music": "preview/ep01-music-bed.mp3", "shots": shots,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ep02-kolanupaka")

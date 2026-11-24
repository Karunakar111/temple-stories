#!/usr/bin/env python3
"""Zero-spend pipeline test: rebuild EP01 through gudi/film.py from footage already on disk.

Uses the EP01 edit list (scripts/ep01_full/edl.py), the approved narration take, and the
phrase timings measured from that take. Writes ONLY to exports/pipeline-test/; the approved
EP01 export and publishing/ep01/ are never read for writing. Nothing is generated or bought.

The picture follows the EDL's clips, source offsets and speeds. Simplifications, labelled on
screen as PIPELINE TEST: no per-beat zoom moves; the EDL's hand-drawn cards (map, patnam,
comment, end) become a still plus typeset text; the n10 beat (EP01 painted out a red stump
frame by frame) uses the hill clip instead.

Run (Mac or cloud): python3 scripts/plan/ep01_pipeline_test.py [--scale 1.0] [--substitute-missing]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "ep01_full"))

from edl import AUDIO, BEATS, CAPTIONS, DURATION  # noqa: E402
from gudi.audio_mix import ff  # noqa: E402
from gudi.film import make_film  # noqa: E402

NAMES = ["మల్లన్న", "మేడలమ్మ", "ఎల్లమ్మ", "గంగమ్మ", "బండారి", "కొమురవెల్లి", "ఒగ్గు", "పట్నం"]
CARD_STILL = {"map": "assets/ep01/a3-hill.png", "comment": "assets/ep01/a4-hand.png", "end": "assets/ep01/a2-throw.png"}
CARD_TEXT = {
    "hilltitle": {"kind": "title", "lines": ["కొమురవెల్లి", "సిద్దిపేట జిల్లా"]},
    "map": {"kind": "title", "lines": ["కొమురవెల్లి", "సిద్దిపేట జిల్లా"]},
    "datecard": {"kind": "date", "lines": ["సంక్రాంతి నుంచి ఉగాది", "ప్రతి ఆదివారం జాతర"]},
    "end": {"kind": "title", "lines": ["కొమురవెల్లి మల్లన్నకు", "కోటి దండాలు!"]},
}
SKIP = {"exports/ep01-full/n10-hand.mp4": "exports/ep01/a3-hill.mp4"}


def build_spec(scale, substitute):
    segs, overlays, missing = [], [], []
    for a, b, s in BEATS:
        if "card" in s:
            src = CARD_STILL.get(s["card"], "assets/ep01/a3-hill.png")
            seg = {"kind": "still", "src": str(ROOT / src), "start": a, "end": b, "push": 0.04}
        else:
            clip = SKIP.get(s["clip"], s["clip"])
            p = ROOT / clip
            if not p.exists():
                missing.append(clip)
                if substitute:
                    p = ROOT / "exports/ep01-full/n01-oggu.mp4"
            seg = {"kind": "clip", "src": str(p), "start": a, "end": b, "ss": s.get("ss", 0.0),
                   "speed": s.get("speed", 1.0) if not s.get("hold") else 1.0}
            if s.get("hold"):
                seg["speed"] = 0.25  # a held frame: slow it right down instead of freezing
        segs.append(seg)
        name = s.get("card") or s.get("overlay")
        if name in CARD_TEXT:
            overlays.append(dict(CARD_TEXT[name], start=a + 0.15, end=b - 0.05))
    if missing and not substitute:
        raise SystemExit("missing footage (run on the Mac, or pass --substitute-missing):\n  " + "\n  ".join(sorted(set(missing))))
    out = ROOT / "exports" / "pipeline-test"
    bg = out / "cover-bg.jpg"
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([ff("ffmpeg"), "-v", "error", "-y", "-ss", "1.5", "-i", str(ROOT / "exports/ep01-full/n01-oggu.mp4"),
                    "-frames:v", "1", "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920", "-q:v", "2", str(bg)], check=True)
    spec = {
        "slug": "ep01-pipeline-test", "tag": "gudi:ep01-pipeline-test:edl", "fps": 30, "scale": scale,
        "out_dir": str(out), "total_s": DURATION, "narration": str(ROOT / AUDIO), "narration_start": 0.0,
        "segments": segs, "phrases": [{"start": a, "end": b, "text": t} for a, b, t in CAPTIONS], "names": NAMES,
        "overlays": overlays, "label": "PIPELINE TEST · not the approved cut",
        "cover": {"bg_src": str(bg), "title": ["కొమురవెల్లి", "మల్లన్న"], "line": "దాని వెనుక కథ తెలుసా?", "badge": "PIPELINE TEST"},
    }
    return spec, sorted(set(missing))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--substitute-missing", action="store_true")
    a = ap.parse_args()
    spec, missing = build_spec(a.scale, a.substitute_missing)
    if missing:
        print(f"note: {len(missing)} clips not on this machine; n01-oggu stands in for them")
    mp4, report, problems = make_film(spec)
    if problems:
        print("FAILED:", problems)
        return 1
    from gudi.render import verify_outputs
    checks, vp = verify_outputs(mp4, spec["narration"], spec["tag"], (round(1080 * a.scale) // 2 * 2, round(1920 * a.scale) // 2 * 2),
                                srt=report["outputs"]["srt"], cover=report["outputs"]["cover"])
    report["final_check"] = {"checks": checks, "problems": vp}
    Path(spec["out_dir"], "ep01-pipeline-test.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"final_check": report["final_check"], "machine_s": report["machine_s"], "outputs": report["outputs"]}, ensure_ascii=False, indent=1))
    return 0 if not vp else 1


if __name__ == "__main__":
    sys.exit(main())

"""Shorter YouTube cut of a finished film from whole-sentence ranges (no paid calls).

  python3 scripts/ops/short_cut.py FILM.mp4 OUT.mp4 "a-b,c-d,..."
Each range is film time in seconds; cut points sit in the gaps between captions so no caption is split.
Each range is cut frame-accurately on its own (20 ms audio fades so joins do not click), then joined.
"""
import subprocess
import sys
from pathlib import Path

film, out, spec = sys.argv[1:4]
rng = [tuple(float(x) for x in r.split("-")) for r in spec.split(",")]
work = Path(out).parent / "cut-parts"; work.mkdir(exist_ok=True)
parts = []
for i, (a, b) in enumerate(rng):
    d = b - a; p = work / f"p{i}.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", film, "-t", f"{d:.3f}",
                    "-af", f"afade=t=in:d=0.02,afade=t=out:st={d - 0.02:.3f}:d=0.02",
                    "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", str(p)], check=True)
    parts.append(p)
lst = work / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy",
                "-movflags", "+faststart", out], check=True)
print(round(sum(b - a for a, b in rng), 2), "s")

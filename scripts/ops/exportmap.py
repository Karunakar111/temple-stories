"""exportmap.py SLUG [FILM_DIR] : what is actually on screen for every caption cue of an exported film.

Prints one row per SRT cue (film time, Telugu text, the picture(s) under it) and writes
/home/claude/work/<slug>-map.jpg: two frames per cue (just after it starts, just before it ends),
so a held composition across several story events is visible at a glance.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gudi.cli import _cfg, _ledger  # noqa: E402
from gudi.episodes import Episode  # noqa: E402
from gudi.render import film_spec  # noqa: E402

slug = sys.argv[1]
film_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("exports/films") / slug
mp4 = film_dir / f"{slug}.mp4"
srt = film_dir / f"{slug}.te.srt"

ep = Episode(slug)
spec, _ = film_spec(ep, _ledger(), _cfg(), tempfile.mkdtemp())
segs = spec["segments"]


def ts(s):
    h, m, r = s.split(":")
    sec, ms = r.split(",")
    return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000


cues = []
for block in srt.read_text(encoding="utf-8").strip().split("\n\n"):
    lines = block.strip().split("\n")
    a, b = [ts(x.strip()) for x in lines[1].split("-->")]
    cues.append((a, b, " ".join(lines[2:])))


def name(sg):
    n = Path(sg["src"]).stem.replace(f"{slug[:4]}-", "")
    f = "+focus" if sg.get("focus") else ""
    return f"{n}{f}"


rows = []
for a, b, text in cues:
    under = [name(sg) for sg in segs if sg["start"] < b - 0.05 and sg["end"] > a + 0.05]
    rows.append((a, b, text, under))
    print(f"{a:6.1f}-{b:5.1f}  {' / '.join(under):38s}  {text}")

tmp = Path(tempfile.mkdtemp())
for i, (a, b, text, under) in enumerate(rows):
    for j, t in enumerate((a + 0.25, max(a + 0.3, b - 0.25))):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", f"scale=150:-1,drawtext=text='{i + 1} {t:.1f}s':x=3:y=3:fontsize=13:fontcolor=yellow:box=1:boxcolor=black",
                        str(tmp / f"{i:03d}_{j}.png")], check=True)
n = len(rows)
cols = 8  # 4 cues per row, 2 frames each
r = -(-2 * n // cols)
out = Path("/home/claude/work") / f"{slug}-map.jpg"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(tmp / "*.png"),
                "-vf", f"tile={cols}x{r}:padding=4:color=white", "-frames:v", "1", str(out)], check=True)
print(out)

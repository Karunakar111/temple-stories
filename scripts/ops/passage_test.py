"""EP04 spider-cobra-elephant passage test: one fixed clearing, three animated actions, cut to the existing take.

  python3 scripts/ops/passage_test.py OUT_DIR

Window: 17.10 s to 39.95 s of the EP04 take (narration "అడవిలో ఒక శివలింగం" .. "మణులు అక్కడే ఉంటాయా?").
Each shot is retimed to fill exactly the span of its line (cut 0.12 s before the line starts).
Writes <out>/ep04-passage-mute.mp4 (no sound, no text) and <out>/ep04-passage-narrated.mp4
(the film's own mix for that window, captions rendered by the channel's caption style).
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gudi import assemble  # noqa: E402

EP = ROOT / "episodes/ep04-srikalahasti"
A, B, LEAD, FPS = 17.10, 39.95, 0.12, 30
CAP_DY = 400  # captions sit lower, over the ferns and stream, so the ledge, web and gem stay clear
AST = EP / "assets"
# (picture, kind, starts at narration time)
SHOTS = [("P01", "still", 17.15), ("PSPIDER", "clip", 18.96), ("PCOBRA", "clip", 26.11), ("PELEPHANT", "clip", 30.61)]
MIX = ROOT / "exports/films/ep04-srikalahasti-hook/ep04-srikalahasti.mp4"
SRT = ROOT / "exports/films/ep04-srikalahasti-hook/ep04-srikalahasti.te.srt"


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def secs(t):
    h, m, s = t.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    starts = [max(0.0, t - LEAD - A) for _, _, t in SHOTS] + [B - A]
    starts[0] = 0.0
    parts = []
    for i, (name, kind, _) in enumerate(SHOTS):
        span = starts[i + 1] - starts[i]
        p = out / f"part{i}.mp4"
        if kind == "still":
            src = AST / f"ep04-{name}-still.png"
            n = round(span * FPS)
            run("-loop", "1", "-framerate", str(FPS), "-t", f"{span:.3f}", "-i", str(src), "-vf",
                f"scale=2160:3840,zoompan=z='1+0.035*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps={FPS},format=yuv420p",
                "-frames:v", str(n), "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(p))
        else:
            src = AST / f"ep04-{name}-clip.mp4"
            k = span / dur(src)  # stretch factor to fill the line exactly
            run("-i", str(src), "-vf", f"setpts={k:.5f}*PTS,fps={FPS},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
                "-t", f"{span:.3f}", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium", str(p))
        parts.append(p)
    lst = out / "parts.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
    pic = out / "picture.mp4"
    run("-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(pic))
    mute = out / "ep04-passage-mute.mp4"
    run("-i", str(pic), "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-an", "-movflags", "+faststart", str(mute))

    # captions from the film's SRT inside the window, in the channel's caption style
    cues = []
    for b in re.split(r"\n\s*\n", SRT.read_text(encoding="utf-8").strip()):
        ln = b.splitlines(); s, e = [secs(x.strip()) for x in ln[1].split("-->")]
        if s >= A - 0.05 and s < B:
            cues.append((s - A, min(e, B) - A, " ".join(ln[2:])))
    (out / "caps").mkdir(exist_ok=True)
    pngs = assemble.render_overlays([{"kind": "caption", "text": t, "names": []} for _, _, t in cues], out / "caps", 1.0)
    inputs, chain, last = ["-i", str(pic), "-ss", f"{A:.3f}", "-t", f"{B - A:.3f}", "-i", str(MIX)], "", "0:v"
    for j, (png, (s, e, _)) in enumerate(zip(pngs, cues)):
        inputs += ["-i", str(png)]
        nxt = cues[j + 1][0] if j + 1 < len(cues) else B - A
        end = min(e + 0.25, nxt - 0.06)  # never two captions at once
        chain += f"[{last}][{j + 2}:v]overlay=0:{CAP_DY}:enable='between(t,{max(0, s - 0.05):.3f},{end:.3f})'[v{j}];"
        last = f"v{j}"
    nar = out / "ep04-passage-narrated.mp4"
    run(*inputs, "-filter_complex", chain + f"[{last}]format=yuv420p[v];[1:a]afade=t=in:d=0.15,afade=t=out:st={B - A - 0.3:.3f}:d=0.3[a]",
        "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", "-t", f"{B - A:.3f}", str(nar))
    print(json.dumps({"mute": str(mute), "narrated": str(nar), "length_s": round(dur(nar), 2),
                      "cuts_s": [round(x, 2) for x in starts], "captions": len(cues)}, ensure_ascii=False))


if __name__ == "__main__":
    main()

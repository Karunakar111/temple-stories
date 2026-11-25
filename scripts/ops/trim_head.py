"""Start a finished film later, so it opens on the action instead of the opening question.

  python3 scripts/ops/trim_head.py FILM.mp4 OUT.mp4 SECONDS [--srt IN.srt OUT.srt]

Re-encodes from SECONDS (frame-accurate), fades the sound in over 0.12 s so the cut does not click,
and shifts the SRT by the same amount (cues that end before the cut are dropped).
"""
import argparse
import re
import subprocess


def ts(s):
    s = max(0.0, s)
    h, m = int(s // 3600), int(s % 3600 // 60)
    return f"{h:02d}:{m:02d}:{s % 60:06.3f}".replace(".", ",")


def secs(t):
    h, m, s = t.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def shift_srt(src, dst, cut):
    blocks, n = [], 0
    for b in re.split(r"\n\s*\n", open(src, encoding="utf-8").read().strip()):
        lines = b.splitlines()
        a, z = [secs(x.strip()) for x in lines[1].split("-->")]
        if z <= cut + 0.05:
            continue
        n += 1
        blocks.append(f"{n}\n{ts(a - cut)} --> {ts(z - cut)}\n" + "\n".join(lines[2:]))
    open(dst, "w", encoding="utf-8").write("\n\n".join(blocks) + "\n")
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film"); ap.add_argument("out"); ap.add_argument("seconds", type=float)
    ap.add_argument("--srt", nargs=2)
    a = ap.parse_args()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.film, "-ss", f"{a.seconds:.3f}",
                    "-af", "afade=t=in:d=0.12", "-map_metadata", "0",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-r", "30",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.out], check=True)
    if a.srt:
        print("srt cues:", shift_srt(a.srt[0], a.srt[1], a.seconds))


if __name__ == "__main__":
    main()

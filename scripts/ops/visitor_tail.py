"""Append a spoken visitor line over a looping lamp close-up to a finished film (before the blessing ending).

  python3 scripts/ops/visitor_tail.py FILM.mp4 LAMP_CLIP.mp4 VOICE.mp3 PHRASES_JSON OUT.mp4 [--gain-db -0.9] [--zoom 1.3 --cx 0.47 --cy 0.5]

PHRASES_JSON: [[start_s, end_s, "text"], ...] in the voice file's own time.
The lamp clip plays forward and back (ping-pong) as long as needed, cropped closer on the flame;
the film cross-fades into it (0.4 s); the voice starts 0.5 s into the lamp; a low Sa drone sits under it;
captions use the channel's caption style.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gudi import assemble  # noqa: E402

FPS, XF, PRE, POST = 30, 0.4, 0.5, 0.6


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def main():
    ap = argparse.ArgumentParser()
    for k in ("film", "lamp", "voice", "phrases", "out"):
        ap.add_argument(k)
    ap.add_argument("--gain-db", type=float, default=-0.9)
    ap.add_argument("--zoom", type=float, default=1.3); ap.add_argument("--cx", type=float, default=0.47); ap.add_argument("--cy", type=float, default=0.5)
    a = ap.parse_args()
    out = Path(a.out); work = out.parent / (out.stem + "-visitor-work"); shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)
    film_s, vo_s = dur(a.film), dur(a.voice)
    T = round(PRE + vo_s + POST, 3)  # length of the lamp section
    # lamp: forward + reverse until long enough, cropped on the flame
    W, H = 1080, 1920; cw, ch = round(W / a.zoom / 2) * 2, round(H / a.zoom / 2) * 2
    x0 = int(max(0, min(W - cw, a.cx * W - cw / 2))); y0 = int(max(0, min(H - ch, a.cy * H - ch / 2)))
    pp = work / "pingpong.mp4"
    run("-i", a.lamp, "-filter_complex",
        f"[0:v]fps={FPS},scale={W}:{H},crop={cw}:{ch}:{x0}:{y0},scale={W}:{H},split[f][r0];[r0]reverse[r];[f][r]concat=n=2:v=1[v]",
        "-map", "[v]", "-c:v", "libx264", "-crf", "16", "-preset", "medium", str(pp))
    loop = work / "lamp.mp4"
    run("-stream_loop", "-1", "-i", str(pp), "-t", f"{T:.3f}", "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", str(loop))
    # captions
    phrases = json.loads(Path(a.phrases).read_text(encoding="utf-8"))
    (work / "caps").mkdir()
    pngs = assemble.render_overlays([{"kind": "caption", "text": t, "names": []} for _, _, t in phrases], work / "caps", 1.0)
    # voice section audio: drone + voice
    sec = work / "section.wav"
    run("-f", "lavfi", "-i", f"aevalsrc='0.035*sin(2*PI*146.83*t)+0.02*sin(2*PI*220*t)':s=48000:c=stereo:d={T:.3f}",
        "-i", a.voice, "-filter_complex",
        f"[0:a]afade=t=in:d=0.8,afade=t=out:st={T - 0.8:.3f}:d=0.8[d];[1:a]volume={a.gain_db}dB,aresample=48000,aformat=channel_layouts=stereo,adelay={int(PRE * 1000)}|{int(PRE * 1000)}[v];"
        f"[d][v]amix=inputs=2:normalize=0:duration=first", str(sec))
    total = round(film_s + T - XF, 3)
    inputs = ["-i", a.film, "-i", str(loop), "-i", str(sec)] + sum((["-i", str(p)] for p in pngs), [])
    off = film_s - XF
    chain = f"[0:v][1:v]xfade=transition=fade:duration={XF}:offset={off:.3f},format=yuv420p[x0];"
    last = "x0"
    for j, (s, e, _) in enumerate(phrases):
        t0, t1 = off + PRE + s - 0.05, off + PRE + e + 0.25
        if j + 1 < len(phrases):
            t1 = min(t1, off + PRE + phrases[j + 1][0] - 0.06)
        chain += f"[{last}][{j + 3}:v]overlay=0:0:enable='between(t,{t0:.3f},{t1:.3f})'[x{j + 1}];"
        last = f"x{j + 1}"
    ms = int(off * 1000)
    chain += f"[2:a]adelay={ms}|{ms}[s];[0:a]apad=whole_dur={total}[f];[f][s]amix=inputs=2:normalize=0:duration=first[a]"
    run(*inputs, "-filter_complex", chain, "-map", f"[{last}]", "-map", "[a]", "-map_metadata", "0", "-t", f"{total:.3f}",
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out))
    shift = off + PRE
    print(json.dumps({"out": str(out), "film_s": film_s, "lamp_s": T, "total_s": round(dur(out), 3),
                      "voice_starts_at": round(shift, 3)}, ensure_ascii=False))
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()

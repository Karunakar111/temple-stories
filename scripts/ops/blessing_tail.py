"""Append the closing blessing frame to a finished film (no paid calls, the approved picture is untouched).

  python3 scripts/ops/blessing_tail.py IN.mp4 BG_STILL.png OUT.mp4 "ఓం నమః శివాయ" "వేములవాడ రాజన్న" [--seconds 2.5]

The film cross-fades (0.4 s) into the temple still, dimmed, with a slow push; the blessing fades in over it.
Sound: the film's own ending, then one soft temple bell in D (matches the bed's Sa) over a low Sa that fades.
Checked after: length, decode, -14 LUFS +-1, true peak <= -1 dBTP.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gudi import assemble  # noqa: E402

FPS, W, H, XF = 30, 1080, 1920, 0.4


def run(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]))


def loudness(p):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    j = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    return float(j["input_i"]), float(j["input_tp"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("film"); ap.add_argument("bg"); ap.add_argument("out"); ap.add_argument("lines", nargs="+")
    ap.add_argument("--seconds", type=float, default=2.5)
    a = ap.parse_args()
    out = Path(a.out); work = out.parent / (out.stem + "-tail-work")
    shutil.rmtree(work, ignore_errors=True); work.mkdir(parents=True)

    png = assemble.render_overlays([{"kind": "blessing", "lines": a.lines}], work, 1.0)[0]
    shade = work / "shade.png"  # soft dark band behind the text, feathered top and bottom
    from PIL import Image
    im = Image.new("RGBA", (W, H))
    px = [(0, 0, 0, int(150 * max(0.0, 1 - abs(y - 1010) / 520) ** 0.8)) for y in range(H)]
    for y in range(H):
        im.paste(px[y], (0, y, W, y + 1))
    im.save(shade)
    film_s, T = dur(a.film), a.seconds
    n = round(T * FPS)

    # picture of the tail: still, cover-cropped, slow push, dimmed toward the centre band, blessing fades in
    tail = work / "tail.mp4"
    run("-loop", "1", "-framerate", str(FPS), "-t", f"{T:.3f}", "-i", a.bg,
        "-loop", "1", "-framerate", str(FPS), "-t", f"{T:.3f}", "-i", str(png),
        "-loop", "1", "-framerate", str(FPS), "-t", f"{T:.3f}", "-i", str(shade),
        "-filter_complex",
        f"[0:v]scale={W * 2}:{H * 2}:force_original_aspect_ratio=increase,crop={W * 2}:{H * 2},"
        f"zoompan=z='1+0.04*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS},"
        f"eq=brightness=-0.08:saturation=0.85,vignette=PI/4[b0];[b0][2:v]overlay=0:0[bg];"
        f"[1:v]format=rgba,fade=t=in:st={XF * 0.6:.2f}:d=0.45:alpha=1[tx];"
        f"[bg][tx]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(tail))

    # bell: inharmonic partials on D5 with a slow decay, a soft low Sa underneath; starts with the cross-fade
    total = round(film_s + T - XF, 3)
    bell = (f"0.20*exp(-1.1*t)*(sin(2*PI*587.3*t)+0.55*sin(2*PI*1174.7*t)*exp(-0.8*t)+0.35*sin(2*PI*1409*t)*exp(-1.5*t)"
            f"+0.22*sin(2*PI*1761*t)*exp(-2.2*t)+0.12*sin(2*PI*2466*t)*exp(-3*t))*min(1,t/0.004)"
            f"+0.05*sin(2*PI*146.83*t)*min(1,t/0.3)")
    tail_a = work / "tail.wav"
    run("-f", "lavfi", "-i", f"aevalsrc='{bell}':s=48000:c=stereo:d={T:.3f}",
        "-af", f"afade=t=out:st={T - 0.9:.3f}:d=0.9", str(tail_a))

    run("-i", a.film, "-i", str(tail), "-i", str(tail_a),
        "-filter_complex",
        f"[0:v][1:v]xfade=transition=fade:duration={XF}:offset={film_s - XF:.3f},format=yuv420p[v];"
        f"[2:a]adelay={int((film_s - XF) * 1000)}|{int((film_s - XF) * 1000)}[b];"
        f"[0:a]apad=whole_dur={total}[f];[f][b]amix=inputs=2:normalize=0:duration=first[a]",
        "-map", "[v]", "-map", "[a]", "-map_metadata", "0", "-t", f"{total:.3f}",
        "-r", str(FPS), "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(out))

    d = dur(out)
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(out), "-f", "null", "-"], check=True)
    i, tp = loudness(out)
    ok = abs(d - total) < 0.1 and abs(i + 14) <= 1 and tp <= -1.0
    print(json.dumps({"out": str(out), "film_s": film_s, "total_s": round(d, 3), "lufs": i, "true_peak": tp, "ok": ok}, ensure_ascii=False))
    shutil.rmtree(work, ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

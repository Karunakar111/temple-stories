"""Render Episode 1 (full) picture track frame-exact from the EDL.

python3 scripts/ep01_full/render.py  ->  build/ep01-full/picture.mp4 (no audio)
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from edl import BEATS, CAPTIONS, DURATION, PATNAM_TIMES, END_SECOND_LINE
import cards

W, H, FPS = 1080, 1920, 30
ROOT = "build/ep01-full"
TOTAL = round(DURATION * FPS)
CAP_Y = 1290  # caption block centre; clear of the Reels/Shorts bottom UI


def fr(t):
    return round(t * FPS)


def read_clip(path, ss, n, speed=1.0, hold=False):
    # slowed windows are frame-blended so they do not stutter
    rate = f"framerate=fps={FPS}" if speed < 0.8 else f"fps={FPS}"
    vf = f"setpts=(PTS-STARTPTS)/{speed},{rate},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
    cmd = ["ffmpeg", "-v", "error", "-ss", str(ss), "-i", path, "-vf", vf,
           "-frames:v", str(1 if hold else n), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    k = len(raw) // (W * H * 3)
    frames = [np.frombuffer(raw[i * W * H * 3:(i + 1) * W * H * 3], np.uint8).reshape(H, W, 3) for i in range(k)]
    if not frames:
        raise RuntimeError(f"no frames from {path}")
    short = n - len(frames)
    if short > 0:
        if not hold and short > 2:
            print(f"  note: {os.path.basename(path)} short by {short} frames, holding last")
        frames += [frames[-1]] * short
    return frames[:n]


def zoom_frame(arr, z, cx, cy):
    if abs(z - 1.0) < 1e-3:
        return arr
    im = Image.fromarray(arr)
    w, h = W / z, H / z
    x0 = min(max(cx * W - w / 2, 0), W - w)
    y0 = min(max(cy * H - h / 2, 0), H - h)
    return np.asarray(im.transform((W, H), Image.EXTENT, (x0, y0, x0 + w, y0 + h), Image.BICUBIC))


def decolor_red(arr, box):
    """Turn red, wound-like pixels inside box into water-white light."""
    x0, y0, x1, y1 = box
    a = arr.copy()
    sub = a[y0:y1, x0:x1].astype(np.int32)
    r, g, b = sub[..., 0], sub[..., 1], sub[..., 2]
    m = (r > 90) & (r > g * 1.35) & (r > b * 1.35)
    if not m.any():
        return arr
    mk = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
    k = np.asarray(mk).astype(np.float32)[..., None] / 255
    white = np.array([228, 238, 248], np.float32)
    a[y0:y1, x0:x1] = (sub * (1 - k) + white * k).astype(np.uint8)
    return a


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def load_seq(name):
    d = f"{ROOT}/cards/{name}"
    return [Image.open(f"{d}/{f}") for f in sorted(os.listdir(d))]


def build_cards():
    spec = []
    for a, b, s in BEATS:
        n = fr(b) - fr(a)
        name = s.get("card") or s.get("overlay")
        if not name:
            continue
        if name == "map": cards.map_card(n)
        elif name == "hilltitle": cards.hill_title(n)
        elif name == "patnam": cards.patnam(n, *PATNAM_TIMES)
        elif name == "datecard": cards.date_card(n)
        elif name == "comment": cards.comment_card(n, "assets/ep01/a4-hand.png")
        elif name == "end": cards.end_card(n, END_SECOND_LINE)
        print("card", name, n)
    os.makedirs(f"{ROOT}/captions", exist_ok=True)
    caps = []
    for i, (s, e, text) in enumerate(CAPTIONS):
        p = f"{ROOT}/captions/c{i:02d}.png"
        cards.caption_png(text, p)
        nxt = CAPTIONS[i + 1][0] if i + 1 < len(CAPTIONS) else DURATION
        caps.append((s - 0.05, min(e + 0.30, nxt - 0.06), Image.open(p)))
    return caps


def main():
    os.makedirs(ROOT, exist_ok=True)
    caps = build_cards()
    out = f"{ROOT}/picture.mp4"
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "17", "-pix_fmt", "yuv420p", out],
                           stdin=subprocess.PIPE)
    written = 0
    for bi, (a, b, s) in enumerate(BEATS):
        f0, f1 = fr(a), fr(b)
        n = f1 - f0
        print(f"beat {bi+1:2d} {a:6.2f}-{b:6.2f} {n:3d}f {s.get('clip', s.get('card'))}")
        if "card" in s:
            frames = [np.asarray(im.convert("RGB")) for im in load_seq(s["card"])][:n]
        else:
            frames = read_clip(s["clip"], s.get("ss", 0.0), n, s.get("speed", 1.0), s.get("hold", False))
        overlay = load_seq(s["overlay"]) if "overlay" in s else None
        for k in range(n):
            arr = frames[k]
            t = k / FPS
            if "decolor" in s:
                arr = decolor_red(arr, s["decolor"])
            if "zoom" in s:
                z0, z1, cx, cy, t0, t1 = s["zoom"]
                z = z0 + (z1 - z0) * smooth((t - t0) / max(t1 - t0, 1e-6))
                arr = zoom_frame(arr, z, cx, cy)
            if s.get("reveal"):
                # the gift arriving: a gold flash that settles, with a slow push
                arr = zoom_frame(arr, 1.0 + 0.05 * t / (n / FPS), 0.5, 0.45)
                g = max(0.0, 1.0 - t / 0.9) ** 1.6
                if g > 0:
                    glow = np.zeros_like(arr, dtype=np.float32)
                    glow[:] = (255, 232, 170)
                    arr = (arr.astype(np.float32) * (1 - g * 0.85) + glow * g * 0.85).astype(np.uint8)
            im = Image.fromarray(arr).convert("RGBA")
            if overlay is not None:
                im.alpha_composite(overlay[min(k, len(overlay) - 1)].convert("RGBA"))
            gt = (f0 + k) / FPS
            for cs, ce, cim in caps:
                if cs <= gt < ce:
                    a_in = smooth((gt - cs) / 0.12)
                    a_out = smooth((ce - gt) / 0.12)
                    al = min(a_in, a_out)
                    c = cim if al >= 0.999 else cim.copy()
                    if al < 0.999:
                        c.putalpha(c.split()[3].point(lambda v: int(v * al)))
                    im.alpha_composite(c, (0, int(CAP_Y - cim.height / 2)))
            enc.stdin.write(im.convert("RGB").tobytes())
            written += 1
    enc.stdin.close()
    enc.wait()
    print("frames", written, "expected", TOTAL)


if __name__ == "__main__":
    main()

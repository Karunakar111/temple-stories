"""Fix the order of the web tear in the EP04 elephant shot, using the existing intact-web artwork (no paid calls).

In the generated clip the web turns grey and splits as the trunk arrives, before the water reaches it.
Until the snap, this puts the intact web from keyframe P03b back behind the trunk and the water
(the trunk and the water are kept from the clip; thin torn strands are not), then dissolves to the
clip's own torn web in a few frames at the chosen snap time, with a small shake so the snap reads on a phone.

The clip is also retimed piecewise so its beats land on the narration:
  python3 scripts/ops/web_tear_fix.py OUT.mp4 MAP_JSON
MAP_JSON: {"points": [[out_s, src_s], ...], "snap_out": s, "duration": s}
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
AST = ROOT / "episodes/ep04-srikalahasti/assets"
CLIP = AST / "ep04-PELEPHANT-clip.mp4"
INTACT = AST / "ep04-P03b-still.png"
FPS = 30
SNAP_FRAMES = 4  # dissolve length


def frames(path):
    cap = cv2.VideoCapture(str(path)); out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f)
    return out, cap.get(cv2.CAP_PROP_FPS)


def interp(points, t):
    xs, ys = zip(*points)
    return float(np.interp(t, xs, ys))


def build(out_path, spec):
    src, sfps = frames(CLIP)
    h, w = src[0].shape[:2]
    intact = cv2.resize(cv2.imread(str(INTACT)), (w, h), interpolation=cv2.INTER_LANCZOS4)
    # where the web hangs: from the branch down to the back of the ledge, feathered
    region = np.zeros((h, w), np.float32)
    cv2.rectangle(region, (int(0.10 * w), int(0.16 * h)), (int(0.94 * w), int(0.575 * h)), 1.0, -1)
    region = cv2.GaussianBlur(region, (0, 0), 18)
    k5, k15 = np.ones((5, 5), np.uint8), np.ones((15, 15), np.uint8)
    n = round(spec["duration"] * FPS)
    snap = spec["snap_out"]
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(FPS),
                             "-i", "-", "-vf", "scale=1080:1920,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                             str(out_path)], stdin=subprocess.PIPE)
    for i in range(n):
        t = i / FPS
        s = interp(spec["points"], t)
        f = src[min(len(src) - 1, max(0, round(s * sfps)))].astype(np.float32)
        a = 1.0 if t < snap else max(0.0, 1.0 - (t - snap) * FPS / SNAP_FRAMES)  # weight of the intact web
        if a > 0:
            d = np.abs(f - intact.astype(np.float32)).max(axis=2) > 60
            b, g, r = f[..., 0], f[..., 1], f[..., 2]
            trunk = (d & (f.max(axis=2) < 95)).astype(np.uint8) * 255
            trunk = cv2.morphologyEx(trunk, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))  # thin dark torn strands drop out
            water = (d & (((b - r) > 30) & (b > 140) | (f.min(axis=2) > 205))).astype(np.uint8) * 255
            water = cv2.morphologyEx(water, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
            fg = cv2.morphologyEx(np.maximum(trunk, water), cv2.MORPH_CLOSE, k15)
            fg = cv2.dilate(fg, np.ones((9, 9), np.uint8))
            fga = cv2.GaussianBlur(fg.astype(np.float32) / 255, (0, 0), 3)
            wgt = (region * (1 - fga) * a)[..., None]
            f = f * (1 - wgt) + intact.astype(np.float32) * wgt
        if snap <= t < snap + 4 / FPS:  # small shake as the strand snaps
            dx = (3, -3, 2, -1)[int(round((t - snap) * FPS)) % 4]
            f = np.roll(f, dx, axis=1)
        proc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close(); proc.wait()


if __name__ == "__main__":
    build(Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text()))

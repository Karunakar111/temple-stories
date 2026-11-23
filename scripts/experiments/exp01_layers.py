"""Experiment 01: prepare layers from EXISTING approved paintings (no generation).

Outputs to public/exp01/. Everything here is classical image processing:
segmentation (GrabCut / thresholds), inpainting of hidden plate areas, a homography
to register two existing paintings, and lamp-flame detection.
"""
import json, cv2, numpy as np
from pathlib import Path
OUT = Path("public/exp01"); OUT.mkdir(parents=True, exist_ok=True)
meta = {}

def save_rgba(path, rgb, alpha):
    rgba = cv2.cvtColor(rgb, cv2.COLOR_BGR2BGRA); rgba[:, :, 3] = alpha
    cv2.imwrite(str(path), rgba, [cv2.IMWRITE_PNG_COMPRESSION, 6])

def inpaint_full(img, mask, scale=0.25):
    """Fill masked area (255) with plausible plate colour; done small, then upscaled."""
    small = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    ms = cv2.resize(mask, (small.shape[1], small.shape[0]), interpolation=cv2.INTER_NEAREST)
    ms = cv2.dilate(ms, np.ones((5, 5), np.uint8))
    fill = cv2.inpaint(small, ms, 9, cv2.INPAINT_TELEA)
    fill = cv2.resize(fill, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_CUBIC)
    fill = cv2.GaussianBlur(fill, (0, 0), 6)
    m = (cv2.GaussianBlur(mask, (0, 0), 3).astype(np.float32) / 255)[..., None]
    return (img * (1 - m) + fill * m).astype(np.uint8)

def grabcut_sky(img, sure_sky_rows, sure_fg_rows, scale=0.35, extra_fg=None):
    h, w = img.shape[:2]
    s = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    sh, sw = s.shape[:2]
    m = np.full((sh, sw), cv2.GC_PR_BGD, np.uint8)
    m[: int(sure_sky_rows * sh)] = cv2.GC_BGD
    m[int(sure_fg_rows * sh):] = cv2.GC_FGD
    if extra_fg is not None:
        ef = cv2.resize(extra_fg, (sw, sh), interpolation=cv2.INTER_NEAREST) > 0
        m[ef] = cv2.GC_FGD
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(s, m, None, bg, fg, 8, cv2.GC_INIT_WITH_MASK)
    sky = np.where((m == cv2.GC_BGD) | (m == cv2.GC_PR_BGD), 255, 0).astype(np.uint8)
    # keep only sky connected to the top edge
    n, lab = cv2.connectedComponents(sky)
    top = set(np.unique(lab[0])) - {0}
    sky = np.isin(lab, list(top)).astype(np.uint8) * 255
    sky = cv2.resize(sky, (w, h), interpolation=cv2.INTER_LINEAR)
    return cv2.GaussianBlur(sky, (0, 0), 1.2)

# ---------------- 1. Location: a3 hill -> sky / mid / foreground rocks
img = cv2.imread("assets/ep01/a3-hill.png"); h, w = img.shape[:2]
temple = np.zeros((h, w), np.uint8); cv2.rectangle(temple, (int(.58*w), int(.33*h)), (int(.72*w), int(.42*h)), 255, -1)
sky = grabcut_sky(img, 0.22, 0.62, extra_fg=temple)
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
# front rocks: dark blue-grey (hue 95-170, low value), touching the frame edge, below 60% height
rock = ((hsv[:, :, 2] < 95) & (hsv[:, :, 0] >= 95) & (hsv[:, :, 0] <= 170)).astype(np.uint8) * 255
rock[: int(0.6 * h)] = 0
rock = cv2.morphologyEx(rock, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(rock)
fg = np.zeros_like(rock)
for i in range(1, n):
    x, y, ww, hh, a = st[i]
    if a > 0.003 * h * w and (x == 0 or x + ww >= w - 1 or y + hh >= h - 1):
        fg[lab == i] = 255
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
ff = fg.copy(); fm = np.zeros((h + 2, w + 2), np.uint8); cv2.floodFill(ff, fm, (w // 2, int(.7 * h)), 255); fg = fg | (~ff)
fg = cv2.GaussianBlur(fg, (0, 0), 1.5)
hill_area = cv2.dilate((255 - sky), np.ones((61, 61), np.uint8))  # reach well past the soft edge
sky_plate = inpaint_full(img, hill_area)          # sky continues behind the hill, no edge remnants
mid_plate = inpaint_full(img, fg)                 # ground continues behind the front rocks
cv2.imwrite(str(OUT / "hill-sky.jpg"), sky_plate, [cv2.IMWRITE_JPEG_QUALITY, 92])
save_rgba(OUT / "hill-mid.png", mid_plate, 255 - sky)
save_rgba(OUT / "hill-front.png", img, fg)
cv2.imwrite(str(OUT / "hill-skymask.png"), sky)
# temple lamp: brightest pixel cluster in the shrine doorway
roi = cv2.cvtColor(img[int(.33*h):int(.42*h), int(.58*w):int(.72*w)], cv2.COLOR_BGR2GRAY)
meta["hill"] = {"w": w, "h": h, "temple": [int(.65*w), int(.385*h)]}

# ---------------- 2. Passing time: a10 garden -> sky mask
img = cv2.imread("assets/ep01/a10-garden.png"); h, w = img.shape[:2]
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
bright = ((hsv[:, :, 2] > 205) & (hsv[:, :, 1] < 80)).astype(np.uint8) * 255
bright[int(0.30 * h):] = 0
bright = cv2.morphologyEx(bright, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
n, lab = cv2.connectedComponents(bright)
top = set(np.unique(lab[0])) - {0}
sky = np.isin(lab, list(top)).astype(np.uint8) * 255
sky = cv2.morphologyEx(sky, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
sky = cv2.GaussianBlur(sky, (0, 0), 1.2)
cv2.imwrite(str(OUT / "garden-skymask.png"), sky)
cv2.imwrite(str(OUT / "garden.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 93])
ys, xs = np.where(sky > 128)
meta["garden"] = {"w": w, "h": h, "skyBox": [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())] if len(xs) else None}

# ---------------- 3. Key poses: n04 (palms joined) and n12 (offering), registered
a = cv2.imread("assets/ep01-full/n04-yellamma.png"); b = cv2.imread("assets/ep01-full/n12-share.png")
H = np.load("/home/claude/work/H_n12_to_n04.npy")
bw = cv2.warpPerspective(b, H, (a.shape[1], a.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
# colour-match the offering painting to the first one (LAB mean/std from the lower 60%, i.e. stone,
# floor and figures, not the differing sky); applied at 70% so the drawing's own light survives
def lab_stats(x):
    l = cv2.cvtColor(x, cv2.COLOR_BGR2LAB).astype(np.float32)[int(.4 * x.shape[0]):]
    return l.reshape(-1, 3).mean(0), l.reshape(-1, 3).std(0)
ma, sa = lab_stats(a); mb, sb = lab_stats(bw)
lb = cv2.cvtColor(bw, cv2.COLOR_BGR2LAB).astype(np.float32)
lt = (lb - mb) / sb * sa + ma
lb = np.clip(lb * 0.3 + lt * 0.7, 0, 255).astype(np.uint8)
bm = cv2.cvtColor(lb, cv2.COLOR_LAB2BGR)
cv2.imwrite(str(OUT / "pose-a.jpg"), a, [cv2.IMWRITE_JPEG_QUALITY, 93])
cv2.imwrite(str(OUT / "pose-b.jpg"), bm, [cv2.IMWRITE_JPEG_QUALITY, 93])

def flames(x, box=None, min_a=40, max_a=6000):
    hsv = cv2.cvtColor(x, cv2.COLOR_BGR2HSV)
    m = ((hsv[:, :, 2] > 240) & (hsv[:, :, 1] < 170)).astype(np.uint8) * 255
    if box is not None:
        bb = np.zeros_like(m); cv2.rectangle(bb, box[:2], box[2:], 255, -1); m &= bb
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    pts = [[int(cen[i][0]), int(cen[i][1]), int(st[i][4])] for i in range(1, n) if min_a <= st[i][4] <= max_a]
    return pts
meta["poses"] = {"w": a.shape[1], "h": a.shape[0], "flamesA": flames(a), "flamesB": flames(bm)}

# ---------------- 4. Close: deity close-up
d = cv2.imread("assets/pilot/shot2-deity-close.png")
cv2.imwrite(str(OUT / "deity.jpg"), d, [cv2.IMWRITE_JPEG_QUALITY, 93])
meta["deity"] = {"w": d.shape[1], "h": d.shape[0], "flames": flames(d)}

json.dump(meta, open(OUT / "meta.json", "w"), indent=1)
print(json.dumps({k: (v if k != "poses" else {kk: (vv if not isinstance(vv, list) else vv[:12]) for kk, vv in v.items()}) for k, v in meta.items()}, indent=0)[:2500])

# CSS mask-image reads alpha, so write the sky masks as white-with-alpha PNGs too
for n in ["garden-skymask", "hill-skymask"]:
    m = cv2.imread(str(OUT / f"{n}.png"), 0)
    rgba = np.zeros((m.shape[0], m.shape[1], 4), np.uint8); rgba[..., :3] = 255; rgba[..., 3] = m
    cv2.imwrite(str(OUT / f"{n}-alpha.png"), rgba)

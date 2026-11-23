"""Code-drawn cards and caption images for Episode 1 (full).

Renders PNG frame sequences into build/ep01-full/cards/<name>/f%04d.png
and caption PNGs into build/ep01-full/captions/. Run from the repo root.
"""
import math, os, random, json
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
ROOT = "build/ep01-full"
FB = "assets/fonts/NotoSansTelugu_700Bold.ttf"
FX = "assets/fonts/NotoSansTelugu_900Black.ttf"
GOLD = (255, 197, 61)
CREAM = (255, 246, 228)
INK = (38, 22, 10)
RAQM = ImageFont.Layout.RAQM


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=RAQM)


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def paper(seed=3):
    random.seed(seed)
    im = Image.new("RGB", (W, H), (226, 204, 160))
    px = im.load()
    noise = Image.effect_noise((W // 4, H // 4), 22).resize((W, H), Image.BICUBIC)
    im = Image.blend(im, Image.merge("RGB", [noise] * 3), 0.10)
    # vignette
    v = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(v)
    d.ellipse((-300, -200, W + 300, H + 200), fill=255)
    v = v.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", (W, H), (120, 80, 40))
    return Image.composite(im, dark, v)


def text_c(d, xy, s, f, fill, stroke=6, sfill=INK, anchor="mm"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=sfill)


def out_dir(name):
    p = f"{ROOT}/cards/{name}"
    os.makedirs(p, exist_ok=True)
    return p


# ---------------------------------------------------------------- map card
def map_card(nframes):
    p = out_dir("map")
    base = paper()
    d0 = ImageDraw.Draw(base)
    # faint hill contours for texture
    random.seed(11)
    for _ in range(14):
        cx, cy = random.randint(0, W), random.randint(300, 1700)
        r = random.randint(60, 220)
        for k in range(3):
            d0.arc((cx - r - k * 26, cy - r * 0.6 - k * 18, cx + r + k * 26, cy + r * 0.6 + k * 18),
                   0, 360, fill=(190, 160, 115), width=2)
    hyd = (290, 1330)
    kom = (790, 640)
    ctrl = (360, 820)
    def bez(t):
        x = (1 - t) ** 2 * hyd[0] + 2 * (1 - t) * t * ctrl[0] + t * t * kom[0]
        y = (1 - t) ** 2 * hyd[1] + 2 * (1 - t) * t * ctrl[1] + t * t * kom[1]
        return x, y
    fT = font(FX, 64); fL = font(FB, 54); fS = font(FB, 40); fK = font(FX, 92)
    for i in range(nframes):
        t = i / FPS
        im = base.copy()
        d = ImageDraw.Draw(im)
        prog = ease((t - 0.25) / 1.9)
        # route, dashed, drawn progressively
        n = 120
        last = None
        for k in range(int(n * prog) + 1):
            pt = bez(k / n)
            if last is not None and (k // 3) % 2 == 0:
                d.line([last, pt], fill=(150, 40, 20), width=9)
            last = pt
        # Hyderabad pin
        d.ellipse((hyd[0] - 20, hyd[1] - 20, hyd[0] + 20, hyd[1] + 20), fill=(150, 40, 20), outline=INK, width=4)
        text_c(d, (hyd[0], hyd[1] + 70), "హైదరాబాద్", fL, CREAM)
        # travelling marker
        if 0 < prog < 1:
            mx, my = bez(prog)
            d.ellipse((mx - 14, my - 14, mx + 14, my + 14), fill=GOLD, outline=INK, width=4)
        # Komuravelli pin appears on arrival
        a = ease((t - 2.0) / 0.35)
        if a > 0:
            r = 26 * a
            glow = Image.new("L", (W, H), 0)
            ImageDraw.Draw(glow).ellipse((kom[0] - 90, kom[1] - 90, kom[0] + 90, kom[1] + 90), fill=int(170 * a))
            glow = glow.filter(ImageFilter.GaussianBlur(40))
            im.paste(Image.new("RGB", (W, H), GOLD), (0, 0), glow)
            d = ImageDraw.Draw(im)
            d.ellipse((kom[0] - r, kom[1] - r, kom[0] + r, kom[1] + r), fill=GOLD, outline=INK, width=5)
            text_c(d, (kom[0] - 10, kom[1] - 95), "కొమురవెల్లి", fL, GOLD)
        # distance counter beside the route
        km = int(round(85 * prog))
        mx, my = bez(0.5)
        text_c(d, (mx + 230, my + 40), f"{km} కి.మీ", fK, CREAM, stroke=8)
        im.save(f"{p}/f{i:04d}.png")


# ------------------------------------------------- title over the hill shot
def hill_title(nframes):
    p = out_dir("hilltitle")
    fK = font(FX, 120); fS = font(FB, 56)
    for i in range(nframes):
        t = i / FPS
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        a = ease(t / 0.4)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        y = 430 - 20 * (1 - a)
        text_c(d, (W // 2, y), "కొమురవెల్లి", fK, GOLD + (255,), stroke=10)
        text_c(d, (W // 2, y + 120), "సిద్దిపేట జిల్లా", fS, CREAM + (255,), stroke=7)
        alpha = layer.split()[3].point(lambda v: int(v * a))
        layer.putalpha(alpha)
        im.alpha_composite(layer)
        im.save(f"{p}/f{i:04d}.png")


# ---------------------------------------------------- patnam, overhead fill
def patnam(nframes, t_yellow, t_red, t_white, t_centre):
    """Overhead patnam: many thin nested straight square borders, mostly
    turmeric yellow and white, minimal red, yellow centre. Each colour
    appears as its powder is named."""
    p = out_dir("patnam")
    random.seed(5)
    floor = Image.new("RGB", (W, H), (46, 40, 52))
    noise = Image.effect_noise((W // 3, H // 3), 30).resize((W, H), Image.BICUBIC)
    floor = Image.blend(floor, Image.merge("RGB", [noise] * 3), 0.12)
    fd = ImageDraw.Draw(floor)
    for x in range(0, W, 270):
        fd.line([(x, 0), (x, H)], fill=(30, 26, 34), width=4)
    for y in range(0, H, 270):
        fd.line([(0, y), (W, y)], fill=(30, 26, 34), width=4)
    cx, cy = W // 2, H // 2 - 40
    outer = 470
    YEL = (244, 182, 28); WHT = (246, 240, 226); RED = (186, 38, 30)
    # border list from outside in: (half-size, colour)
    seq = []
    s = outer
    k = 0
    while s > 120:
        if k in (5, 13):
            col = RED
        elif k % 2 == 0:
            col = YEL
        else:
            col = WHT
        seq.append((s, col))
        s -= 18
        k += 1
    def appear(col):
        return {YEL: t_yellow, RED: t_red, WHT: t_white}[col]
    lamps = [(cx - outer - 70, cy - outer - 70), (cx + outer + 70, cy - outer - 70),
             (cx - outer - 70, cy + outer + 70), (cx + outer + 70, cy + outer + 70)]
    for i in range(nframes):
        t = i / FPS
        im = floor.copy()
        # lamp glows
        glow = Image.new("L", (W, H), 0)
        gd = ImageDraw.Draw(glow)
        flick = 0.85 + 0.15 * math.sin(t * 9.0)
        for lx, ly in lamps:
            gd.ellipse((lx - 150, ly - 150, lx + 150, ly + 150), fill=int(140 * flick))
        glow = glow.filter(ImageFilter.GaussianBlur(70))
        im.paste(Image.new("RGB", (W, H), (255, 170, 70)), (0, 0), glow)
        d = ImageDraw.Draw(im)
        for lx, ly in lamps:
            d.ellipse((lx - 26, ly - 12, lx + 26, ly + 12), fill=(120, 60, 30), outline=INK, width=3)
            d.ellipse((lx - 7, ly - 34, lx + 7, ly - 8), fill=(255, 210, 90))
        for j, (hs, col) in enumerate(seq):
            t0 = appear(col) + 0.035 * j
            a = ease((t - t0) / 0.35)
            if a <= 0:
                continue
            c = tuple(int(46 + (v - 46) * a) for v in col)
            d.rectangle((cx - hs, cy - hs, cx + hs, cy + hs), outline=c, width=7)
        a = ease((t - t_centre) / 0.6)
        if a > 0:
            hs = 112
            c = tuple(int(46 + (v - 46) * a) for v in YEL)
            d.rectangle((cx - hs, cy - hs, cx + hs, cy + hs), fill=c, outline=WHT, width=6)
        # slow push in
        z = 1.0 + 0.05 * (t / (nframes / FPS))
        if z > 1.0:
            nw, nh = int(W * z), int(H * z)
            im = im.resize((nw, nh), Image.BICUBIC).crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
        im.save(f"{p}/f{i:04d}.png")


# ----------------------------------------------------- festival date card
def date_card(nframes):
    p = out_dir("datecard")
    fA = font(FX, 86); fB = font(FB, 58)
    for i in range(nframes):
        t = i / FPS
        a = ease((t - 0.15) / 0.4)
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        y0 = 1170 + 30 * (1 - a)
        box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.rounded_rectangle((90, y0 - 40, W - 90, y0 + 290), radius=34, fill=(24, 12, 6, int(200 * a)), outline=GOLD + (int(255 * a),), width=5)
        im.alpha_composite(box)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        text_c(ld, (W // 2, y0 + 60), "సంక్రాంతి నుంచి ఉగాది", font(FX, 74), GOLD + (255,), stroke=7)
        text_c(ld, (W // 2, y0 + 190), "ప్రతి ఆదివారం జాతర", fB, CREAM + (255,), stroke=6)
        layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
        im.alpha_composite(layer)
        im.save(f"{p}/f{i:04d}.png")


# ------------------------------------------------------- comment prompt
def comment_card(nframes, bg_path):
    p = out_dir("comment")
    bg = Image.open(bg_path).convert("RGB").resize((W, H)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (20, 10, 4)), 0.45)
    fA = font(FX, 70); fB = font(FB, 52)
    for i in range(nframes):
        t = i / FPS
        a = ease(t / 0.3)
        im = bg.copy().convert("RGBA")
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        y = 760 + 40 * (1 - a)
        d.rounded_rectangle((110, y, W - 110, y + 330), radius=40, fill=(255, 248, 232, 245), outline=GOLD + (255,), width=6)
        d.polygon([(260, y + 330), (330, y + 330), (240, y + 410)], fill=(255, 248, 232, 245))
        text_c(d, (W // 2, y + 105), "మీ ఊరు:", fA, (120, 40, 10, 255), stroke=0)
        # blinking cursor line
        d.line([(300, y + 240), (780, y + 240)], fill=(160, 120, 80, 255), width=5)
        if int(t * 2.2) % 2 == 0:
            d.line([(310, y + 190), (310, y + 232)], fill=(120, 40, 10, 255), width=6)
        # bouncing arrow toward the comments
        by = 1290 + 26 * math.sin(t * 7)
        d.polygon([(W // 2 - 70, by), (W // 2 + 70, by), (W // 2, by + 90)], fill=GOLD + (255,), outline=INK + (255,))
        d.rectangle((W // 2 - 26, by - 110, W // 2 + 26, by), fill=GOLD + (255,), outline=INK + (255,))
        layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
        im.alpha_composite(layer)
        im.convert("RGB").save(f"{p}/f{i:04d}.png")


# --------------------------------------------------------------- end card
def end_card(nframes, t_second):
    p = out_dir("end")
    fA = font(FX, 92); fB = font(FX, 128)
    random.seed(9)
    motes = [(random.uniform(0, W), random.uniform(0, H), random.uniform(1.5, 4.5), random.uniform(20, 70)) for _ in range(140)]
    for i in range(nframes):
        t = i / FPS
        im = Image.new("RGB", (W, H), (8, 4, 2))
        d = ImageDraw.Draw(im)
        for x, y, r, sp in motes:
            yy = (y - sp * t) % H
            d.ellipse((x - r, yy - r, x + r, yy + r), fill=(200, 140, 30))
        im = im.filter(ImageFilter.GaussianBlur(1.2))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        a1 = ease(t / 0.35)
        a2 = ease((t - t_second) / 0.3)
        l1 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text_c(ImageDraw.Draw(l1), (W // 2, 820), "కొమురవెల్లి మల్లన్నకు", fA, CREAM + (255,), stroke=6)
        l1.putalpha(l1.split()[3].point(lambda v: int(v * a1)))
        layer.alpha_composite(l1)
        if a2 > 0:
            l2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sc = 1.0 + 0.15 * (1 - a2)
            text_c(ImageDraw.Draw(l2), (W // 2, 1000), "కోటి దండాలు!", font(FX, int(128 * sc)), GOLD + (255,), stroke=9)
            l2.putalpha(l2.split()[3].point(lambda v: int(v * a2)))
            layer.alpha_composite(l2)
        im = im.convert("RGBA")
        im.alpha_composite(layer)
        im.convert("RGB").save(f"{p}/f{i:04d}.png")


# --------------------------------------------------------------- captions
NAMES = ["మల్లన్న", "మేడలమ్మ", "ఎల్లమ్మ", "గంగమ్మ", "బండారి", "కొమురవెల్లి", "ఒగ్గు", "పట్నం"]


def caption_png(text, path, size=60, maxw=930):
    f = font(FB, size)
    words = text.split()
    lines, cur = [], []
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    for w in words:
        trial = " ".join(cur + [w])
        if cur and probe.textlength(trial, font=f) > maxw:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    lh = int(size * 1.55)
    hgt = lh * len(lines) + 40
    im = Image.new("RGBA", (W, hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    space = probe.textlength(" ", font=f)
    # soft dark band behind the words so they read over busy frames
    widest = max(sum(probe.textlength(w, font=f) for w in ws) + space * (len(ws) - 1) for ws in lines)
    band = Image.new("RGBA", (W, hgt), (0, 0, 0, 0))
    ImageDraw.Draw(band).rounded_rectangle(((W - widest) / 2 - 34, 8, (W + widest) / 2 + 34, hgt - 8), radius=28, fill=(10, 5, 2, 120))
    im.alpha_composite(band.filter(ImageFilter.GaussianBlur(10)))
    for li, ws in enumerate(lines):
        total = sum(probe.textlength(w, font=f) for w in ws) + space * (len(ws) - 1)
        x = (W - total) / 2
        y = 20 + li * lh + lh / 2
        for w in ws:
            col = GOLD if any(w.startswith(n) for n in NAMES) else CREAM
            d.text((x, y), w, font=f, fill=col, anchor="lm", stroke_width=7, stroke_fill=(20, 10, 4))
            x += probe.textlength(w, font=f) + space
    im.save(path)
    return hgt


if __name__ == "__main__":
    import sys
    spec = json.load(open(sys.argv[1]))
    for c in spec["cards"]:
        kind, n = c["kind"], c["frames"]
        if kind == "map": map_card(n)
        elif kind == "hilltitle": hill_title(n)
        elif kind == "patnam": patnam(n, *c["times"])
        elif kind == "datecard": date_card(n)
        elif kind == "comment": comment_card(n, c["bg"])
        elif kind == "end": end_card(n, c["t_second"])
        print("card", kind, n)
    os.makedirs(f"{ROOT}/captions", exist_ok=True)
    for i, cap in enumerate(spec["captions"]):
        h = caption_png(cap["text"], f"{ROOT}/captions/c{i:02d}.png")
        cap["h"] = h
    json.dump(spec, open(sys.argv[1], "w"), ensure_ascii=False, indent=1)
    print("captions", len(spec["captions"]))

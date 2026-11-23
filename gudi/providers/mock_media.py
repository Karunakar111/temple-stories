"""Playable stand-in media for rehearsals (GUDI_MOCK_MEDIA=1). Clearly marked MOCK in the picture.

- still: 1536x2752 PNG, warm gradient and the beat name
- clip:  540x960 H.264 of the requested length, a slow push on a still
- narration: an MP3 with speech-like syllable bursts, as long as the script at EP01's rate
  (14.68 characters a second plus 0.5 s per paragraph), so retiming and the narration check
  run on a real take-shaped file
"""
import hashlib
import math
import subprocess
import wave
from pathlib import Path

from ..paths import ROOT

CPS, PARA = 14.68, 0.5


def _png(path, label, seed):
    from PIL import Image, ImageDraw

    h = hashlib.sha1(seed.encode()).digest()
    c1, c2 = (60 + h[0] % 80, 30 + h[1] % 50, 20 + h[2] % 40), (180 + h[3] % 60, 110 + h[4] % 70, 50 + h[5] % 50)
    im = Image.new("RGB", (1536, 2752))
    d = ImageDraw.Draw(im)
    for y in range(0, 2752, 8):
        t = y / 2752
        d.rectangle([0, y, 1536, y + 8], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    for k in range(6):
        x, y, r = h[6 + k] * 6, 400 + h[12 + k] * 9, 80 + h[k] % 120
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 230, 180), width=6)
    d.rectangle([60, 60, 1476, 260], fill=(194, 65, 12))
    d.text((100, 120), f"MOCK {label}", fill=(255, 255, 255), font_size=96)
    im.save(path)


def _narration(path, seconds, seed):
    import numpy as np

    rate = 22050
    rng = np.random.default_rng(int(hashlib.sha1(seed.encode()).hexdigest()[:8], 16))
    n = int(seconds * rate)
    env = np.zeros(n)
    t = 0.05
    while t < seconds - 0.2:  # syllables ~0.13 s, with word and sentence gaps
        d = rng.uniform(0.08, 0.18)
        a, b = int(t * rate), int(min(seconds, t + d) * rate)
        env[a:b] = np.sin(np.linspace(0, math.pi, b - a)) * rng.uniform(0.4, 1.0)
        t += d + (rng.uniform(0.25, 0.6) if rng.random() < 0.12 else rng.uniform(0.01, 0.06))
    x = np.arange(n) / rate
    sig = env * (0.6 * np.sin(2 * math.pi * 140 * x) + 0.3 * np.sin(2 * math.pi * 280 * x) + 0.1 * rng.standard_normal(n))
    pcm = (np.clip(sig, -1, 1) * 20000).astype(np.int16)
    wav = Path(str(path) + ".wav")
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm.tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "96k", str(path)], check=True)
    wav.unlink()


def make(job, job_id, dest):
    at = job["asset_type"]
    if at == "still":
        _png(dest, f"{job['beat']} still", job_id)
    elif at == "clip":
        png = Path(str(dest) + ".png")
        _png(png, f"{job['beat']} clip", job_id)
        d = int(job.get("duration") or 5)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-t", str(d), "-r", "30",
                        "-vf", "scale=540:966,crop=540:960:0:'3*t'", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
                        str(dest)], check=True)
        png.unlink()
    elif at == "narration":
        text = (ROOT / job["text_path"]).read_text(encoding="utf-8").strip()
        secs = len(text.replace("\n\n", "")) / CPS + PARA * text.count("\n\n")
        _narration(dest, secs, job_id)
    else:
        dest.write_bytes(job_id.encode())

"""Experiment 01 sound: approved narration + Episode 1's own music/effects stems, re-cut.

No new narration, music or effects are generated, except one soft bell at the
key-pose cut, synthesised with Episode 1's own bell() function.
Mix chain = Episode 1's (music 0.42, effects 0.32, bed sidechain-ducked under the voice,
loudnorm I=-14). Writes public/exp01/exp01-mix.wav.
"""
import os, subprocess, sys, json
import numpy as np

sys.path.insert(0, "scripts/ep01_full")
import importlib.util
spec = importlib.util.spec_from_file_location("ep_audio", "scripts/ep01_full/audio.py")
ep = importlib.util.module_from_spec(spec); spec.loader.exec_module(ep)

SR = 48000
DUR = 22.8
N = int(DUR * SR)
XF = 8 / 30  # crossfade, seconds (matches the picture)
BEATS = [  # out a, out b, master start, master end, out time of master start
    (0.0, 6.4, 5.16, 10.21, 0.6),
    (6.4, 13.9, 37.49, 43.66, 6.7),
    (13.9, 19.3, 69.72, 72.14, 14.9),
    (19.3, DUR, 105.21, 107.84, 19.6),
]
CUT = 71.10 + (14.9 - 69.72)


def load(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2).copy()


nar_m = load("audio/01-mallanna-full-paced.mp3")
mus_m = load("build/ep01-full/music.wav")
sfx_m = load("build/ep01-full/sfx.wav")
nar, mus, sfx = (np.zeros((N, 2), np.float32) for _ in range(3))


def place(dst, src, out_a, out_b, master_a, fade_in, fade_out):
    i0, i1 = int(out_a * SR), int(out_b * SR)
    m0 = int(master_a * SR)
    n = i1 - i0
    seg = np.zeros((n, 2), np.float32)
    lo, hi = max(0, m0), min(len(src), m0 + n)
    if hi > lo:
        seg[lo - m0: hi - m0] = src[lo:hi]
    env = np.ones(n, np.float32)
    fi, fo = int(fade_in * SR), int(fade_out * SR)
    if fi: env[:fi] = np.sin(np.linspace(0, np.pi / 2, fi)) ** 2
    if fo: env[-fo:] = np.cos(np.linspace(0, np.pi / 2, fo)) ** 2
    dst[i0:i1] += seg * env[:, None]


for k, (a, b, ma, mb, at) in enumerate(BEATS):
    off = at - ma
    # narration: exactly the approved line, 25 ms edges
    place(nar, nar_m, at, at + (mb - ma), ma, 0.025, 0.025)
    # music + effects: the same master moment, overlapping the neighbours by XF
    a2 = max(0.0, a - XF / 2) if k else 0.0
    b2 = min(DUR, b + XF / 2)
    first, last = k == 0, k == len(BEATS) - 1
    place(mus, mus_m, a2, b2, a2 - off, 0.0 if first else XF, 0.6 if last else XF)
    place(sfx, sfx_m, a2, b2, a2 - off, 0.0 if first else XF, 0.6 if last else XF)

bell = ep.bell(f=1174.7, decay=1.4, n_s=2.5).astype(np.float32)
i = int((CUT - 0.02) * SR)
sfx[i:i + len(bell)] += np.stack([bell, bell], 1)[: N - i] * 1.6

os.makedirs("build/exp01", exist_ok=True)
for name, x in (("nar", nar), ("mus", mus), ("sfx", sfx)):
    with open(f"build/exp01/{name}.f32", "wb") as fh:
        fh.write(x.astype(np.float32).tobytes())

graph = (
    "[0:a]volume=1.0,asplit=2[nar][key];"
    "[1:a]volume=0.42[mus];[2:a]volume=0.32[fx];"
    "[mus][fx]amix=inputs=2:normalize=0[bed];"
    "[bed][key]sidechaincompress=threshold=0.02:ratio=9:attack=8:release=300[duck];"
    "[nar][duck]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.5:LRA=9[out]"
)
raw = ["-f", "f32le", "-ar", str(SR), "-ac", "2", "-i"]
subprocess.run(["ffmpeg", "-v", "error", "-y", *raw, "build/exp01/nar.f32", *raw, "build/exp01/mus.f32", *raw,
                "build/exp01/sfx.f32", "-filter_complex", graph, "-map", "[out]", "-ar", str(SR), "-c:a", "pcm_s16le",
                "public/exp01/exp01-mix.wav"], check=True)
print("wrote public/exp01/exp01-mix.wav")

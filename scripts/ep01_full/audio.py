"""Synthesised music bed and sound effects for Episode 1 (full), then the final mix.

Everything is generated here (no samples, no licences): a tanpura-style drone in D,
a dolu-style drum and cymbals that follow the story sections, and effects at story
moments. The music is ducked under the narration with a sidechain compressor.

python3 scripts/ep01_full/audio.py -> build/ep01-full/{music,sfx}.wav, mix.wav
"""
import math, subprocess, sys, os
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from edl import AUDIO, DURATION

SR = 48000
N = int(DURATION * SR)
ROOT = "build/ep01-full"
rng = np.random.default_rng(7)
SA = 146.83  # D


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def add(buf, start, sig, gain=1.0):
    i = int(start * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def lowpass(x, cutoff):
    a = math.exp(-2 * math.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for k in range(len(x)):
        acc = (1 - a) * x[k] + a * acc
        y[k] = acc
    return y


def lp_fast(x, cutoff):
    # one-pole low-pass via FFT-free vectorised approximation (repeated box filter)
    w = max(1, int(SR / (cutoff * 2.2)))
    k = np.ones(w) / w
    y = np.convolve(x, k, mode="same")
    return np.convolve(y, k, mode="same")


def bandnoise(n, lo, hi):
    x = rng.standard_normal(n)
    return lp_fast(x, hi) - lp_fast(x, lo)


# ------------------------------------------------------------------ instruments
def tanpura_pluck(f, dur=2.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for h in range(1, 16):
        amp = (1.0 / h) * (1.25 if h % 2 else 0.8)  # jawari: odd partials buzz brighter
        s += amp * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h)) * np.exp(-t * (0.9 + 0.22 * h))
    att = np.minimum(1, t / 0.01)
    return s * att * 0.18


def drum(f0=110, f1=52, decay=0.32, click=0.25):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t / 0.05)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t / decay)
    s += click * rng.standard_normal(n) * np.exp(-t / 0.012)
    return s * 0.9


def cymbal(decay=0.35):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (2430, 3710, 5120, 6330, 7890))
    s = s / 5 + 0.3 * rng.standard_normal(n)
    return s * np.exp(-t / decay) * 0.12


def bell(f=880, decay=1.8, n_s=3.5):
    n = int(n_s * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for r, a in ((1.0, 1.0), (2.0, 0.5), (2.76, 0.4), (5.40, 0.25), (8.93, 0.12)):
        s += a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * r ** 0.5 / decay)
    return s * np.minimum(1, t / 0.003) * 0.12


def flute(notes, start, buf, gain=0.05):
    # notes: list of (offset s, freq, dur s)
    for off, f, d in notes:
        n = int(d * SR)
        t = np.arange(n) / SR
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.minimum(1, t / 0.4)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        s = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.05 * rng.standard_normal(n)
        e = np.minimum(1, t / 0.12) * np.minimum(1, (d - t) / 0.25)
        add(buf, start + off, s * np.clip(e, 0, 1), gain)


# ------------------------------------------------------------------ music
def music():
    m = np.zeros(N)
    # drone throughout, Pa Sa' Sa' Sa cycle
    cyc = [SA * 1.5, SA * 2, SA * 2, SA]
    t = 0.0
    k = 0
    while t < DURATION - 1.0:
        add(m, t, tanpura_pluck(cyc[k % 4]), 1.0)
        t += 0.62
        k += 1
    # section dynamics for the drone: hold under the blow, open for the festival
    ga = np.ones(N)
    def ramp(a, b, g0, g1):
        i, j = int(a * SR), int(b * SR)
        ga[i:j] = np.linspace(g0, g1, j - i)
    ramp(0, 1.0, 0.0, 1.0)
    ramp(105.2, DURATION, 1.0, 0.0)
    ramp(62.9, 63.2, 1.0, 0.22)   # the drone drops away under the blow
    ramp(66.0, 66.4, 0.22, 1.0)
    m *= ga

    def pattern(a, b, bpm, steps, f0=110, gain=1.0, cym=None):
        beat = 60 / bpm
        t = a
        i = 0
        while t < b:
            v = steps[i % len(steps)]
            if v:
                add(m, t, drum(f0=f0 * (1.15 if v == 2 else 1.0)), gain * (1.0 if v == 2 else 0.6))
            if cym and cym[i % len(cym)]:
                add(m, t, cymbal(), gain)
            t += beat
            i += 1

    pattern(0.0, 10.0, 76, [2, 0, 1, 0], gain=0.55)                      # opening heartbeat
    pattern(10.21, 18.0, 112 * 2, [2, 0, 1, 1, 0, 1], cym=[1, 0, 0, 1, 0, 0], gain=0.6)   # Oggu 6/8
    pattern(18.13, 52.0, 72, [1, 0, 0, 0], gain=0.45)                     # story, sparse
    pattern(52.08, 62.9, 150 * 2, [2, 1, 1, 1], cym=[1, 0, 0, 0, 0, 0, 0, 0], gain=0.38)   # chase
    pattern(66.0, 74.7, 84, [2, 0, 1, 0], gain=0.5)                       # return, wedding
    pattern(74.78, 90.3, 116 * 2, [2, 0, 1, 1, 0, 1], cym=[1, 0, 0, 1, 0, 0], gain=0.6)  # festival today
    pattern(90.4, 105.0, 72, [1, 0, 0, 0], gain=0.4)
    add(m, 105.39, drum(f0=90, f1=40, decay=0.6), 1.2)
    add(m, 106.87, drum(f0=90, f1=40, decay=0.8), 1.4)
    add(m, 106.87, cymbal(decay=1.2), 2.0)
    # a small flute phrase (Mohanam: S R G P D) at the open and the close
    S, R, G, P, D = SA * 2, SA * 2 * 9 / 8, SA * 2 * 5 / 4, SA * 3, SA * 3 * 10 / 9
    flute([(0, G, 0.5), (0.5, P, 0.5), (1.0, D, 0.9), (1.9, P, 1.2)], 0.4, m, 0.05)
    flute([(0, P, 0.5), (0.5, G, 0.5), (1.0, R, 0.5), (1.5, S, 1.6)], 100.7, m, 0.05)
    return m


# ------------------------------------------------------------------ effects
def sfx():
    s = np.zeros(N)
    def swell(n_s, lo, hi, att=0.05, dec=0.5):
        n = int(n_s * SR)
        t = np.arange(n) / SR
        return bandnoise(n, lo, hi) * np.minimum(1, t / att) * np.exp(-np.maximum(0, t - att) / dec)
    def whoosh(n_s=0.8):
        n = int(n_s * SR)
        t = np.arange(n) / SR
        x = rng.standard_normal(n)
        lo = lp_fast(x, 600) * np.sin(np.pi * t / n_s) ** 2
        return lo * 1.4
    add(s, 0.20, swell(0.9, 200, 3000, 0.04, 0.35), 0.5)          # turmeric thrown
    add(s, 5.10, whoosh(0.6), 0.25)                                # to the map
    for k in range(6):                                             # the gift arriving: rising bells
        add(s, 33.95 + k * 0.12, bell(660 * (1.12 ** k), 0.9, 2.0), 0.6)
    add(s, 36.05, whoosh(0.9), 0.6)                                # wings
    add(s, 36.55, whoosh(0.7), 0.4)
    add(s, 50.25, drum(f0=150, f1=70, decay=0.2, click=0.6), 0.8)  # spotted
    add(s, 50.45, drum(f0=150, f1=70, decay=0.2, click=0.6), 0.8)
    for k in range(10):                                            # dissolve shimmer
        add(s, 52.1 + k * 0.05, bell(1400 + 90 * k, 0.4, 0.8), 0.25)
    t = 52.5
    while t < 57.9:                                                # paws
        add(s, t, drum(f0=70, f1=40, decay=0.05, click=0.4), 0.18)
        t += 0.17
    add(s, 56.55, swell(1.1, 150, 2500, 0.02, 0.4), 0.7)          # river leap splash
    add(s, 58.15, swell(2.2, 80, 1200, 0.9, 0.9), 0.8)            # Gangamma rises
    add(s, 63.05, drum(f0=70, f1=32, decay=0.22, click=0.8), 1.2)  # the blow
    add(s, 63.05, swell(1.0, 1500, 7000, 0.01, 0.3), 0.25)        # spray of light
    add(s, 65.95, whoosh(1.0), 0.5)                                # return flight
    for k, f in enumerate((1180, 1320, 1180, 1480)):              # wedding bells
        add(s, 72.2 + k * 0.28, bell(f, 0.5, 1.2), 0.5)
    n = int(3.9 * SR)                                              # festival crowd bed
    tt = np.arange(n) / SR
    crowd = bandnoise(n, 250, 1800) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.7 * tt) ** 2)
    crowd *= np.minimum(1, tt / 0.3) * np.minimum(1, (3.9 - tt) / 0.5)
    add(s, 0.0, crowd[: int(3.0 * SR)] * np.minimum(1, np.arange(int(3.0 * SR)) / (0.2 * SR)), 0.35)  # festival open
    add(s, 96.69, crowd, 0.35)                                                                      # festival dates
    add(s, 74.85, bell(587, 2.0, 3.0), 0.5)                                                         # today, at the shrine
    for t0 in (85.40, 86.12, 86.78):                              # each powder laid down
        add(s, t0, swell(0.6, 400, 5000, 0.03, 0.25), 0.35)
    add(s, 103.43, bell(1760, 0.15, 0.4), 0.5)                     # comment prompt pop
    add(s, 105.25, bell(392, 2.6, 2.6), 1.6)                       # temple bell
    return s


def write_wav(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], axis=1)
    pcm = (st * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-", path],
                   input=pcm, check=True)


def main():
    os.makedirs(ROOT, exist_ok=True)
    m = music(); m = m / np.abs(m).max() * 0.8
    e = sfx(); e = e / np.abs(e).max() * 0.8
    write_wav(f"{ROOT}/music.wav", m)
    write_wav(f"{ROOT}/sfx.wav", e)
    # mix: narration on top, music ducked by the narration, effects underneath
    # music and effects are summed into one bed, and the whole bed ducks under the voice
    fc = ("[0:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.0,asplit=2[nar][key];"
          "[1:a]volume=0.42[mus];"
          "[2:a]volume=0.32[fx];"
          "[mus][fx]amix=inputs=2:normalize=0[bed];"
          "[bed][key]sidechaincompress=threshold=0.02:ratio=9:attack=8:release=300[duck];"
          "[nar][duck]amix=inputs=2:normalize=0:duration=first,"
          "loudnorm=I=-14:TP=-1.5:LRA=9[out]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", AUDIO, "-i", f"{ROOT}/music.wav", "-i", f"{ROOT}/sfx.wav",
                    "-filter_complex", fc, "-map", "[out]", "-ar", "48000", f"{ROOT}/mix.wav"], check=True)
    print("mix written")


if __name__ == "__main__":
    main()

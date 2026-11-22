#!/usr/bin/env python3
"""
Derive shot timings from the real narration waveform.

The audio is the clock. This reads the narration paragraphs out of the locked script,
measures the actual recording, and snaps each shot boundary to the nearest real pause
in the read — so cuts land in the gaps the voice already leaves, not on a guess.

Usage:  python3 scripts/timing.py <part-number>
Writes: src/episodes/01-part<N>-timing.json
"""
import array, json, re, subprocess, sys, os

FF = "node_modules/ffmpeg-static/ffmpeg"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "script/01-komuravelli-bandari.md")
SR, WINS = 4000, 0.04
FPS = 30

def narration(part):
    """Telugu narration cell of each shot row, in order, for one part."""
    s = open(SCRIPT, encoding="utf-8").read()
    body = s.split(f"# PART {part}")[1]
    if part == 1:
        body = body.split("# PART 2")[0]
    rows, out = [l for l in body.split("\n") if l.startswith("| ")], []
    for r in rows:
        c = [x.strip() for x in r.split("|")]
        if len(c) > 3 and re.search(r"[ఀ-౿]", c[3]):
            out.append(re.sub(r"\*\*", "", c[3]))
    return out

def envelope(path):
    raw = subprocess.run([FF, "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    a = array.array("h"); a.frombytes(raw)
    w = int(SR * WINS)
    rms = [ (sum(x*x for x in a[i*w:(i+1)*w]) / w) ** 0.5 for i in range(len(a)//w) ]
    peak = max(rms) or 1.0
    return [r / peak for r in rms], len(a) / SR

def gaps(norm, floor=0.12, minlen=0.12):
    out, start = [], None
    for i, v in enumerate(norm):
        if v < floor:
            if start is None: start = i
        else:
            if start is not None and (i - start) * WINS >= minlen:
                out.append(((start) * WINS, i * WINS))
            start = None
    if start is not None:
        out.append((start * WINS, len(norm) * WINS))
    return out

# Boundaries the word-count heuristic gets wrong, set from the measured pause map.
# The chant is only four words but is *delivered* slowly, so proportional allocation
# starves it. These are the pause midpoints where the chant audibly ends.
# Adjust by ear after the first preview render — that is cheaper than arguing with
# the heuristic.
OVERRIDES = {
    1: {1: 5.08},   # part 1, end of shot 1 (chant) — pause at 4.68-5.48
    2: {1: 10.36},  # part 2, shot 1 is chant + two lines — pause at 9.96-10.76
}

def main(part):
    audio = os.path.join(ROOT, f"audio/01-part{part}.mp3")
    shots = narration(part)
    norm, dur = envelope(audio)
    g = gaps(norm)
    # Candidate cut points: the midpoint of every pause >= 400ms.
    cands = [ (s + e) / 2 for s, e in g if (e - s) >= 0.40 ]

    # Walk the shots in order. Each boundary takes its proportional share of the
    # time that is actually *left*, based on the words that are actually left, then
    # snaps to the nearest real pause. Doing it sequentially means an override (or a
    # snap that moves a long way) re-flows everything after it instead of crushing
    # the next shot against a clamp.
    words = [len(t.split()) for t in shots]
    ov = OVERRIDES.get(part, {})
    fixed, cursor = [], 0.0
    for i in range(len(shots) - 1):
        if (i + 1) in ov:
            cursor = ov[i + 1]
            fixed.append(round(cursor, 2))
            continue
        remaining_words = sum(words[i:])
        target = cursor + (dur - cursor) * words[i] / remaining_words
        pool = [c for c in cands if c > cursor + 0.5]
        snap = min(pool, key=lambda c: abs(c - target)) if pool else target
        cursor = snap
        fixed.append(round(cursor, 2))

    edges = [0.0] + fixed + [round(dur, 2)]

    out = {
        "part": part,
        "audio": f"audio/01-part{part}.mp3",
        "durationSeconds": round(dur, 2),
        "fps": FPS,
        "durationInFrames": round(dur * FPS),
        "wordsPerSecond": round(sum(words) / dur, 2),
        "shots": [
            {"n": i + 1,
             "startSec": edges[i], "endSec": edges[i + 1],
             "startFrame": round(edges[i] * FPS), "endFrame": round(edges[i + 1] * FPS),
             "durationInFrames": round((edges[i + 1] - edges[i]) * FPS),
             "words": words[i],
             "telugu": shots[i]}
            for i in range(len(shots))
        ],
    }
    dest = os.path.join(ROOT, f"src/episodes/01-part{part}-timing.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    json.dump(out, open(dest, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"part {part}: {dur:.2f}s, {out['durationInFrames']} frames, "
          f"{out['wordsPerSecond']} words/s, {len(shots)} shots -> {os.path.relpath(dest, ROOT)}")
    for sh in out["shots"]:
        print(f"  shot {sh['n']}: {sh['startSec']:6.2f}–{sh['endSec']:6.2f}s "
              f"({sh['durationInFrames']:4d}f)  {sh['telugu'][:46]}…")

if __name__ == "__main__":
    main(int(sys.argv[1]))

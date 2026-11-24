"""Phrase-level Telugu captions and the SRT.

Timing comes from the narration take itself:
- ElevenLabs /with-timestamps returns a start and end time for every character of the script;
  phrases are cut at punctuation and at word boundaries (at most MAX_CHARS each) and timed from
  their first and last spoken character.
- A take without alignment (EP01) supplies its phrases directly (measured from speech-to-text).
"""
import json
import re
from pathlib import Path

MAX_CHARS = 30          # one caption block, two short lines at most on a phone
BREAK = re.compile(r"([.?!,;:…]+)")
DROP_END = ".,;:…"      # end punctuation not shown; '?' and '!' are kept


def _split_long(words, limit):
    out, cur = [], []
    for w in words:
        if cur and len(" ".join(cur + [w])) > limit:
            out.append(cur)
            cur = [w]
        else:
            cur.append(w)
    if cur:
        out.append(cur)
    # avoid a lonely last word
    if len(out) > 1 and len(out[-1]) == 1 and len(" ".join(out[-2] + out[-1])) <= limit + 8:
        last = out.pop()
        out[-1] += last
    return out


def phrase_spans(text, lo=0, hi=None):
    """[(char_start, char_end_exclusive)] over text[lo:hi], offsets into the original text."""
    hi = len(text) if hi is None else hi
    sub = text[lo:hi]
    return [(a + lo, b + lo) for a, b in _spans(sub)]


def _spans(text):
    spans, i = [], 0
    for m in BREAK.finditer(text + "."):
        if text.count("‘", i, m.start()) > text.count("’", i, m.start()):
            continue  # punctuation inside a quotation
        seg_end = min(m.end(), len(text))
        seg = text[i:seg_end]
        # a quoted title stays in one piece
        words = [(w.start() + i, w.end() + i) for w in re.finditer(r"‘[^’]*’\S*|\S+", seg)]
        if words:
            groups = _split_long([text[a:b] for a, b in words], MAX_CHARS)
            k = 0
            for g in groups:
                a = words[k][0]
                b = words[k + len(g) - 1][1]
                spans.append((a, b))
                k += len(g)
        i = seg_end
    return spans


def from_alignment(text, alignment, ranges=None):
    """ranges: [(lo, hi)] character ranges (one per shot) so no caption straddles a cut."""
    chars = alignment["characters"]
    st, en = alignment["character_start_times_seconds"], alignment["character_end_times_seconds"]
    if "".join(chars) != text:
        raise ValueError("alignment does not match the script text")
    out = []
    spans = [sp for lo, hi in (ranges or [(0, len(text))]) for sp in phrase_spans(text, lo, hi)]
    for a, b in spans:
        words = text[a:b].strip().rstrip(DROP_END).strip()
        if words:
            out.append({"start": round(st[a], 3), "end": round(en[b - 1], 3), "text": words})
    return out


def estimated_alignment(text, seconds, pause=0.35):
    """Uniform speaking rate with pauses at punctuation (mock takes, or a take whose alignment was lost)."""
    weights = [pause * 14.68 if c in ".?!" else (pause * 7 if c in ",;:" else (0.0 if c == "\n" else 1.0)) for c in text]
    total = sum(weights) or 1.0
    t, st, en = 0.05, [], []
    scale = (seconds - 0.25) / total
    for wgt in weights:
        st.append(round(t, 4))
        t += wgt * scale
        en.append(round(t, 4))
    return {"characters": list(text), "character_start_times_seconds": st, "character_end_times_seconds": en}


def _ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(phrases, path):
    lines = []
    for i, p in enumerate(phrases, 1):
        lines += [str(i), f"{_ts(p['start'])} --> {_ts(p['end'])}", p["text"], ""]
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def load_alignment(narration_path):
    f = Path(str(narration_path) + ".alignment.json")
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def pause_alignment(text, narration_path, noise="-35dB", min_pause=0.16):
    """Zero-cost timing for a take without character alignment: the narrator pauses at
    punctuation, so punctuation-delimited chunks are matched, in order, to the speech runs
    between detected pauses (by character count), and characters are spread evenly inside
    each chunk. Phrase-level accurate when the take pauses where the script punctuates."""
    from .audio_mix import silences

    sil, total = silences(narration_path, noise, min_pause)
    runs, t = [], 0.0
    for s, e in sil:
        if s - t > 0.05:
            runs.append((t, s))
        t = e
    if total - t > 0.05:
        runs.append((t, total))
    # chunks at punctuation
    chunks, i = [], 0
    for m in BREAK.finditer(text + "."):
        j = min(m.end(), len(text))
        if text[i:j].strip():
            chunks.append((i, j))
        i = j
    weights = [len(text[a:b].strip()) for a, b in chunks]
    # merge speech runs until counts match (runs >= chunks), else fall back to proportional spread
    if not runs:
        return estimated_alignment(text, total)
    while len(runs) > len(chunks):
        k = min(range(len(runs) - 1), key=lambda q: runs[q + 1][0] - runs[q][1])
        runs[k:k + 2] = [(runs[k][0], runs[k + 1][1])]
    if len(runs) < len(chunks):
        return estimated_alignment(text, total)
    st, en = [0.0] * len(text), [0.0] * len(text)
    for (a, b), (r0, r1) in zip(chunks, runs):
        n = max(1, b - a)
        for q in range(a, b):
            st[q] = round(r0 + (r1 - r0) * (q - a) / n, 4)
            en[q] = round(r0 + (r1 - r0) * (q - a + 1) / n, 4)
    for q in range(len(text)):  # characters between chunks (newlines) take the previous time
        if en[q] == 0.0 and q:
            st[q] = en[q] = en[q - 1]
    return {"characters": list(text), "character_start_times_seconds": st, "character_end_times_seconds": en, "method": "pauses"}

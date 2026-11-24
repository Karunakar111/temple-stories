"""Named re-edits of an episode, built from assets that already exist (no paid calls).

episodes/<slug>/edits/<name>.json lists the picture in order. Each cut and card is anchored to words in the
narration ("at": a phrase from voice.te.txt, searched forward from the previous anchor, plus an optional
"offset" in seconds), so the edit follows the real take's character timestamps. A cut lands 0.12 s before
its anchor word, as in the automatic cut.

  {"assets": {"S02": "<what a viewer sees in this picture>", ...},
   "segments": [{"at": "...", "asset": "S02", "kind": "still"|"clip", "focus": {"from": [cx, cy, z], "to": [...]},
                 "lead": 0.0, "ss": 0.0, "sees": "...", "flag": "..."}],
   "overlays": [{"at": "...", "until": "...", "kind": "title"|"card"|"name"|"questions"|"date"|"reminders", "lines": [...]}]}

Text rule: one readable text block at a time. While a title or card is up, no caption is drawn; a caption
that would run into a card is cut short before it.

phrase_map(spec, ...) lists every narration phrase with the time, the picture on screen and what a viewer
sees, so a missing scene is visible before anyone watches the film.
"""
import hashlib
import json
from pathlib import Path

from .captions import from_alignment, load_alignment
from .render import film_spec

LEAD = 0.12


def _asset_path(ep, name, kind):
    d = ep.dir / "assets"
    p = d / f"{ep.slug.split('-')[0]}-{name}-{kind}.{'mp4' if kind == 'clip' else 'png'}"
    if not p.exists():
        raise FileNotFoundError(f"{p.name} is not downloaded")
    return p


class Anchors:
    def __init__(self, voice, al):
        self.voice, self.st, self.pos = voice, al["character_start_times_seconds"], 0

    def time(self, words, offset=0.0, lead=LEAD):
        if not words:
            return 0.0
        i = self.voice.find(words, self.pos)
        if i < 0:
            raise ValueError(f"anchor {words!r} not found after character {self.pos}")
        self.pos = i
        return round(max(0.0, self.st[i] - lead + offset), 3)


def edit_doc(ep, name):
    return json.loads((ep.dir / "edits" / f"{name}.json").read_text(encoding="utf-8"))


def edit_spec(ep, ledger, cfg, out_dir, name):
    base, missing = film_spec(ep, ledger, cfg, out_dir)
    if missing:
        return None, missing
    doc = edit_doc(ep, name)
    voice = base["script_text"]
    al = load_alignment(base["narration"])
    if al is None:
        return None, ["a re-edit needs the take's character timestamps"]
    total = base["total_s"]

    an = Anchors(voice, al)
    segs = []
    for s in doc["segments"]:
        t = an.time(s.get("at", ""), s.get("offset", 0.0))
        seg = {"kind": s["kind"], "src": str(_asset_path(ep, s["asset"], s["kind"])), "start": t,
               "asset": s["asset"], "sees": s.get("sees") or doc.get("assets", {}).get(s["asset"], ""), "flag": s.get("flag")}
        for k in ("focus", "lead", "ss", "push", "speed"):
            if k in s:
                seg[k] = s[k]
        segs.append(seg)
    for a, b in zip(segs, segs[1:]):
        if b["start"] <= a["start"]:
            raise ValueError(f"cut at {b['start']} s is not after {a['start']} s ({b['asset']})")
        a["end"] = b["start"]
    segs[-1]["end"] = total

    an = Anchors(voice, al)
    overlays = []
    for o in doc.get("overlays", []):
        a = an.time(o.get("at", ""), o.get("offset", 0.0), lead=0.05)
        pos = an.pos
        b = an.time(o["until"], o.get("until_offset", 0.0), lead=0.10) if o.get("until") else total - 0.04
        an.pos = pos
        overlays.append({"kind": o["kind"], "lines": o["lines"], "start": a, "end": round(min(b, total - 0.04), 3)})
    overlays.sort(key=lambda o: o["start"])

    # one text block at a time: drop captions under a card, cut short any caption that runs into one
    phrases = []
    blocks = [o for o in overlays if o["kind"] != "mark"]  # a small disclosure mark is not a text block
    for p in from_alignment(voice, al, _ranges(ep, voice)):
        if any(o["start"] - 0.05 <= p["start"] < o["end"] for o in blocks):
            continue
        nxt = [o["start"] for o in blocks if o["start"] > p["start"]]
        q = dict(p)
        if nxt and q["end"] + 0.30 > nxt[0] - 0.06:
            q["end"] = round(nxt[0] - 0.40, 3)
        if q["end"] > q["start"] + 0.3:
            phrases.append(q)

    spec = dict(base, segments=[{k: v for k, v in s.items() if k not in ("asset", "sees", "flag")} for s in segs],
                overlays=overlays, phrases=phrases, out_dir=str(out_dir),
                tag=f"{base['tag']}:{name}-{hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:8]}")
    if doc.get("cover_shot"):
        spec["cover"] = dict(spec["cover"], bg_src=str(_asset_path(ep, doc["cover_shot"], "still")))
    spec["_timeline"] = segs
    return spec, []


def _ranges(ep, voice):
    out, pos = [], 0
    for s in ep.shots_doc["shots"]:
        if s.get("text"):
            a = voice.index(s["text"], pos)
            out.append((a, a + len(s["text"])))
            pos = a + len(s["text"])
    return out


def phrase_map(ep, timeline, overlays, al, describe):
    """Rows of (start, end, words, picture, what a viewer sees, text on screen, flag) for every spoken phrase."""
    voice = ep.voice_text()
    rows = []
    for p in from_alignment(voice, al, _ranges(ep, voice)):
        mid = (p["start"] + p["end"]) / 2
        on = [s for s in timeline if s["start"] <= mid < s["end"]] or [timeline[-1]]
        s = on[0]
        txt = [" / ".join(o["lines"]) for o in overlays if o["start"] <= mid < o["end"]]
        rows.append({"start": p["start"], "end": p["end"], "words": p["text"], "picture": s["asset"],
                     "sees": describe(s), "text_on_screen": txt[0] if txt else "caption",
                     "flag": s.get("flag") or ""})
    return rows

"""Phrase-to-visual check on a storyboard, before anything is generated or rendered.

For every narration phrase it lists the estimated time, the picture planned for that moment and what moves,
then raises a flag where the voice brings in a new person, action or idea while the screen still shows the
previous picture. Two sources of flags:

  auto      rules over shots.json: a reused picture, a clip that runs out before its narration does,
            one start image asked to become two scenes, one still held over many phrases
  reviewed  episodes/<slug>/visual_check.json, a person's (or Claude's) read of the storyboard, with the
            missing visual, its narration time and its quoted cost

`python3 -m gudi.visual_check ep03-vemulavada` prints the table; the weekly review shows it per episode.
"""
import json
import re
import sys
from pathlib import Path

from .captions import phrase_spans
from .episodes import Episode

CLIP_RATE = 1.5  # Higgsfield credits per second of Kling 3.0 pro, as quoted
STILL = 2


def _paid(shot, kind):
    return [c for c in shot.get("paid", []) if c["asset_type"] == kind]


def _clip_s(shot):
    c = _paid(shot, "clip")
    return float(c[0]["settings"].get("duration") or c[0].get("max_s") or 0) if c else 0.0


def rows(ep):
    doc = ep.shots_doc
    by = {s["id"]: s for s in doc["shots"]}
    on = [s for s in doc["shots"] if s.get("text")]
    reviewed = (json.loads((ep.dir / "visual_check.json").read_text(encoding="utf-8"))
                if (ep.dir / "visual_check.json").exists() else {"notes": []})
    notes = reviewed.get("notes", [])

    # how long each clip has to cover: its own shot plus shots that continue it
    cover = {}
    for s in on:
        src = s["id"] if _paid(s, "clip") else (s.get("media_from") if "covered by" in (s.get("class") or "") else None)
        if src:
            cover[src] = cover.get(src, 0.0) + (s.get("est_dur_s") or 0.0)

    out = []
    for s in on:
        text, t0, dur = s["text"], s.get("est_start_s") or 0.0, s.get("est_dur_s") or 0.0
        spans = phrase_spans(text)
        n = len(text) or 1
        src = s.get("media_from")
        cut = s.get("cut_to")
        own_still, own_clip = bool(_paid(s, "still")), bool(_paid(s, "clip"))
        auto = []
        if src and not own_still and not own_clip:
            auto.append(("check", f"Screen repeats {src} ({by[src].get('picture', '')[:70]}) while the voice moves on."))
        if own_clip and cover.get(s["id"], 0) > _clip_s(s) + 1.0:
            hold = cover[s["id"]] - _clip_s(s)
            auto.append(("check", f"{_clip_s(s):.0f} s clip under {cover[s['id']]:.1f} s of narration: last frame held about {hold:.1f} s."))
        if own_still and own_clip and re.search(r";\s*then\b|\bthen the\b", s.get("picture", "")) and not cut:
            auto.append(("check", "Picture describes two scenes but the clip starts from one still."))
        if own_still and not own_clip and not cut and len(spans) >= 4 and dur >= 9:
            auto.append(("check", f"One still over {len(spans)} phrases ({dur:.0f} s)."))
        for k, (a, b) in enumerate(spans):
            words = text[a:b]
            pic = s.get("picture", "")
            asset = s["id"]
            if src and not own_still and not own_clip:
                asset, pic = src, f"(reuses {src}) " + by[src].get("picture", "")
            if cut and a / n >= min(1.0, cut[1] / max(dur, 0.1)):
                asset, pic = cut[0], f"(cut to {cut[0]}) " + by[cut[0]].get("picture", "")
            flags = [(sev, msg) for sev, msg in auto] if k == 0 else []
            for nt in notes:
                if nt["shot"] == s["id"] and nt["phrase"] in words:
                    flags.append((nt["severity"], nt["note"] + (f" Fix: {nt['fix']}" if nt.get("fix") else "")
                                  + (f" Quote: {nt['quote']} credits." if nt.get("quote") is not None else "")))
            out.append({"shot": s["id"], "t": round(t0 + dur * a / n, 1), "words": words, "asset": asset,
                        "picture": pic, "moves": s.get("what_changes") or "", "flags": flags})
    return out, reviewed


def summary(ep):
    r, rev = rows(ep)
    missing = [n for n in rev.get("notes", []) if n["severity"] == "missing"]
    checks = sum(1 for x in r for f in x["flags"] if f[0] == "check")
    return {"phrases": len(r), "missing": missing, "checks": checks,
            "quote_if_fixed": sum(n.get("quote") or 0 for n in missing), "reviewed_by": rev.get("reviewed_by")}


def main(argv):
    for slug in argv:
        ep = Episode(slug)
        r, _ = rows(ep)
        print(f"== {slug}: {len(r)} phrases")
        for x in r:
            mark = "  " if not x["flags"] else ("!!" if any(f[0] == "missing" for f in x["flags"]) else " ?")
            print(f"{mark} {x['t']:5.1f}  {x['shot']:5s} {x['words']}\n         sees: {x['picture'][:110]}")
            for sev, msg in x["flags"]:
                print(f"         [{sev}] {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

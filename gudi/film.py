"""Make one finished film from a spec: narration check, picture, Telugu text layers, sound bed,
mix, mix check, mux, SRT and cover. Used for every episode (gudi/render.py builds the spec
from shots.json and the episode's own assets) and for the zero-spend EP01 pipeline test.

spec = {
  "slug", "tag", "fps", "scale", "out_dir", "total_s",
  "narration", "narration_start", "script_text" (optional),
  "segments": [{"kind": "clip"|"still", "src", "start", "end", "ss", "speed", "push"}],
  "phrases": [{"start", "end", "text"}], "names": [...],
  "overlays": [{"kind", "lines"|"text", "start", "end"}],
  "label": optional text shown top-left for the whole film,
  "cover": {"bg_src", "title": [...], "line", "badge"},
}
"""
import hashlib
import json
import shutil
import time
from pathlib import Path

from . import assemble, audio_mix
from .captions import write_srt

CODE = Path(__file__).resolve().parent.parent


def caption_items(phrases, names, total_s):
    out = []
    for i, p in enumerate(phrases):
        nxt = phrases[i + 1]["start"] if i + 1 < len(phrases) else total_s
        out.append({"kind": "caption", "text": p["text"], "names": names,
                    "start": max(0.0, p["start"] - 0.05), "end": min(p["end"] + 0.30, nxt - 0.06, total_s)})
    return out


def make_film(spec, say=print):
    t0 = time.monotonic()
    fps, scale = spec.get("fps", 30), spec.get("scale", 1.0)
    size = (round(1080 * scale) // 2 * 2, round(1920 * scale) // 2 * 2)
    out = Path(spec["out_dir"])
    work = out / "work"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    slug, total = spec["slug"], spec["total_s"]
    report = {"slug": slug, "steps": {}}
    try:
        # 1. the narration stem, before anything is mixed
        stem, problems = audio_mix.verify_stem(spec["narration"], spec.get("script_text"))
        report["steps"]["narration_stem"] = {"checks": stem, "problems": problems}
        say(f"  stem   {slug}: {'ok' if not problems else 'FAILED'} {stem}")
        if problems:
            return None, report, ["narration stem: " + "; ".join(problems)]

        # 2. picture: one FFmpeg pass
        segs, prev = [], 0
        for s in spec["segments"]:
            f0, f1 = assemble.frames(s["start"], fps), assemble.frames(s["end"], fps)
            if f0 != prev:
                raise ValueError(f"segment gap/overlap at {s['start']} s")
            segs.append(dict(s, frames=f1 - f0))
            prev = f1
        if prev != assemble.frames(total, fps):
            raise ValueError(f"segments end at {prev / fps:.2f} s, film is {total:.2f} s")
        t = time.monotonic()
        picture = assemble.build_picture(segs, work / "picture.mp4", size, fps)
        report["steps"]["picture_s"] = round(time.monotonic() - t, 1)
        say(f"  picture {slug}: {len(segs)} segments, {prev} frames in {report['steps']['picture_s']} s")

        # 3. text layers: one PNG per caption phrase / card
        items = caption_items(spec["phrases"], spec.get("names", []), total) + list(spec.get("overlays", []))
        if spec.get("label"):
            items.append({"kind": "label", "text": spec["label"], "start": 0.0, "end": total})
        t = time.monotonic()
        pngs = assemble.render_overlays(items, work, scale)
        report["steps"]["text_layers"] = {"pngs": len(pngs), "seconds": round(time.monotonic() - t, 1)}
        say(f"  text   {slug}: {len(pngs)} transparent PNGs ({sum(1 for i in items if i['kind'] == 'caption')} caption phrases)")

        # 4. sound: bed, mix, then the mix is checked on its own
        seed = int(hashlib.sha1(slug.encode()).hexdigest()[:6], 16)
        bed = audio_mix.make_bed(work / "bed.wav", total, seed)
        mixf = audio_mix.mix(spec["narration"], bed, work / "mix.wav", total, spec.get("narration_start", 0.0))
        mchecks, mproblems = audio_mix.verify_mix(mixf, spec["narration"], total, spec.get("narration_start", 0.0))
        report["steps"]["mix"] = {"checks": mchecks, "problems": mproblems}
        say(f"  mix    {slug}: {'ok' if not mproblems else 'FAILED'} {mchecks}")
        if mproblems:
            return None, report, ["mix: " + "; ".join(mproblems)]

        # 5. mux, SRT, cover
        mp4 = out / f"{slug}.mp4"
        assemble.mux(picture, list(zip(pngs, items)), mixf, mp4, total, fps, spec["tag"])
        srt = out / f"{slug}.te.srt"
        write_srt(spec["phrases"], srt)
        cover = spec.get("cover")
        cover_jpg = None
        if cover:
            stage = CODE / "public" / "render-stage" / hashlib.sha1(str(out).encode()).hexdigest()[:8]
            stage.mkdir(parents=True, exist_ok=True)
            bg = stage / ("cover-bg" + Path(cover["bg_src"]).suffix)
            shutil.copy2(cover["bg_src"], bg)
            cover_jpg = assemble.render_cover({"bg": str(bg.relative_to(CODE / "public")), "title": cover["title"], "line": cover["line"],
                                               "badge": cover.get("badge")}, out / f"{slug}-cover.jpg", work, 1.0)
            shutil.rmtree(stage, ignore_errors=True)
        report["outputs"] = {"mp4": str(mp4), "srt": str(srt), "cover": str(cover_jpg) if cover_jpg else None}
        report["machine_s"] = round(time.monotonic() - t0, 1)
        return mp4, report, []
    finally:
        (out / f"{slug}.report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        shutil.rmtree(work, ignore_errors=True)

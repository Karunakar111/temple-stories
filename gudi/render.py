"""Render an episode's film from its own assets, then decide whether it may be reviewed.

The film is made by gudi/film.py (FFmpeg assembly + Remotion text layers; identical on the Mac
and in the cloud). It is READY FOR REVIEW only when verify_outputs passes:
  1. the MP4 carries this episode's id and revision in its metadata,
  2. H.264 video at the expected size and an AAC audio stream,
  3. it decodes end to end with no decoder error,
  4. it lasts as long as the narration take (take <= film <= take + end hold),
  5. its sound is phone-ready (-14 LUFS +-1, true peak <= -1 dBTP) and still carries the take
     (envelope correlation >= 0.6 with the bed ducked underneath, sync within 60 ms),
  6. the SRT parses, is in order and ends inside the film; the cover is a 1080x1920 JPEG.
The narration stem is checked before mixing and the mix on its own (gudi/audio_mix.py).
On failure: one free automatic re-render, then an exception for that episode only.
One film at a time (file lock); disk check first; intermediates are removed.
"""
import fcntl
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from . import audio_mix
from .captions import from_alignment, load_alignment, pause_alignment
from .episodes import load_json, request_key
from .paths import ROOT, ensure_state

MIN_FREE_GB = 3
TAIL_S = 3.5
NAMES_DEFAULT = []


def _asset(ep, ledger, beat, asset_type):
    for c in ep.paid_calls():
        if c["beat"] == beat and c["asset_type"] == asset_type:
            j = ledger.job(request_key(ep, c))
            if j and j["state"] == "downloaded" and j["local_path"] and Path(j["local_path"]).exists():
                return Path(j["local_path"])
    return None


def _picture(ep, ledger, shot_id, by_id):
    """A shot's own clip, else its own still, else the shot it reuses."""
    s = by_id[shot_id]
    for at in ("clip", "still"):
        if any(c["asset_type"] == at for c in s["paid"]):
            p = _asset(ep, ledger, shot_id, at)
            if p:
                return p, ("clip" if at == "clip" else "still")
    if s.get("media_from"):
        return _picture(ep, ledger, s["media_from"], by_id)
    return None, None


def film_spec(ep, ledger, cfg, out_dir):
    """Spec for gudi/film.py from shots.json, the downloaded assets, the take and its alignment."""
    rc = cfg.get("render", {})
    doc, timing = ep.shots_doc, ep.timing or {}
    scale_t = timing.get("scale", 1.0)
    by_id = {s["id"]: s for s in doc["shots"]}
    narr = _asset(ep, ledger, "VO", "narration")
    missing, segs, notes = [], [], []
    if not narr:
        missing.append("narration take")
    voice = ep.voice_text()
    on = [s for s in doc["shots"] if s.get("text")]
    ranges, pos = [], 0
    for s in on:
        a = voice.index(s["text"], pos)
        ranges.append((a, a + len(s["text"])))
        pos = a + len(s["text"])
    take_s = audio_mix.duration(narr) if narr else 0.0
    total = round(max(take_s + 1.0, (on[-1]["est_start_s"] + on[-1]["est_dur_s"]) * scale_t + 1.0), 3) if on else 1.0
    for i, s in enumerate(on):
        start = 0.0 if i == 0 else round(s["est_start_s"] * scale_t, 3)
        end = round(on[i + 1]["est_start_s"] * scale_t, 3) if i + 1 < len(on) else total
        path, kind = _picture(ep, ledger, s["id"], by_id)
        if not path:
            missing.append(f"picture for {s['id']}")
            continue
        cut = s.get("cut_to")
        if cut:
            cp, ck = _picture(ep, ledger, cut[0], by_id)
            if not cp:
                missing.append(f"picture for {cut[0]}")
                continue
            mid = round(start + cut[1] * scale_t, 3)
            segs.append({"kind": kind, "src": str(path), "start": start, "end": mid})
            segs.append({"kind": ck, "src": str(cp), "start": mid, "end": end})
        else:
            segs.append({"kind": kind, "src": str(path), "start": start, "end": end})
    if missing:
        return None, missing
    al = load_alignment(narr)
    if al is None:
        al = pause_alignment(voice, narr)
        notes.append("caption timing from the take's pauses (no character alignment returned)")
    phrases = from_alignment(voice, al, ranges)
    ov = load_json(ep.dir / "overlays.json", {}) or {}
    starts = {s["id"]: (seg_start, seg_end) for s, seg_start, seg_end in
              ((s, 0.0 if i == 0 else round(s["est_start_s"] * scale_t, 3),
                round(on[i + 1]["est_start_s"] * scale_t, 3) if i + 1 < len(on) else total) for i, s in enumerate(on))}
    overlays, no_caption = [], []
    for o in ov.get("items", []):
        a, b = starts[o["shot"]]
        item = {k: v for k, v in o.items() if k not in ("shot", "at", "for")}
        item["start"] = round(a + o.get("at", 0.0) * scale_t, 3)
        item["end"] = round(min(b, item["start"] + o["for"]) if o.get("for") else b, 3) - 0.04
        overlays.append(item)
        if o["kind"] == "title":
            no_caption.append((a, b))
    phrases = [p for p in phrases if not any(a <= p["start"] < b for a, b in no_caption)]
    # a card that already shows the spoken words replaces their caption (EP01 rule)
    def shown(p):
        words = p["text"].rstrip("?!").strip()
        return any(o["start"] - 0.5 <= p["start"] <= o["end"] and any(words and words in l for l in o.get("lines", []))
                   for o in overlays)
    phrases = [p for p in phrases if not shown(p)]
    cover_shot = ov.get("cover_shot", on[0]["id"])
    cbg, _ = _picture(ep, ledger, cover_shot, by_id)
    if cbg and cbg.suffix == ".mp4":
        still = Path(out_dir) / "cover-bg.jpg"
        subprocess.run([audio_mix.ff("ffmpeg"), "-v", "error", "-y", "-ss", "0.5", "-i", str(cbg), "-frames:v", "1", str(still)], check=True)
        cbg = still
    title = ep.meta.get("title_te", "").split(" ", 1)
    spec = {"slug": ep.slug, "tag": f"gudi:{ep.slug}:{ep.revision()}", "fps": 30, "scale": float(rc.get("scale", 1.0)),
            "out_dir": str(out_dir), "total_s": total, "narration": str(narr), "narration_start": 0.0, "script_text": voice,
            "segments": segs, "phrases": phrases, "names": ov.get("names", NAMES_DEFAULT), "overlays": overlays,
            "label": rc.get("label"), "notes": notes,
            "cover": {"bg_src": str(cbg), "title": title if len(title) == 2 else [ep.meta.get("title_te", "")],
                      "line": ov.get("cover_line") or ep.meta.get("cover_te", ""), "badge": rc.get("label")}}
    return spec, []


def _srt_ok(path, total):
    if not path or not Path(path).exists():
        return False, "SRT missing"
    txt = Path(path).read_text(encoding="utf-8").strip()
    times = re.findall(r"(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)", txt)
    if not times:
        return False, "SRT has no cues"
    prev = -1.0
    for t in times:
        a = int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2]) + int(t[3]) / 1000
        b = int(t[4]) * 3600 + int(t[5]) * 60 + int(t[6]) + int(t[7]) / 1000
        if a < prev - 1e-3 or b <= a or b > total + 0.01:
            return False, f"SRT cue out of order or outside the film at {a:.2f} s"
        prev = a
    return True, f"{len(times)} cues"


def verify_outputs(mp4, narration, tag, size, srt=None, cover=None):
    checks, problems = {}, []
    mp4 = Path(mp4)
    if not mp4.exists() or mp4.stat().st_size == 0:
        return {"exists": False}, ["MP4 missing"]
    info = audio_mix.probe(mp4)
    streams = info.get("streams", [])
    v = [s for s in streams if s.get("codec_type") == "video"]
    a = [s for s in streams if s.get("codec_type") == "audio"]
    found = info.get("format", {}).get("tags", {}).get("comment", "")
    checks["episode_tag"] = found
    if found != tag:
        problems.append(f"MP4 is not tagged {tag!r} (found {found!r})")
    if not v or v[0].get("codec_name") != "h264" or (v[0].get("width"), v[0].get("height")) != tuple(size):
        problems.append(f"video stream not H.264 {size[0]}x{size[1]}")
    if not a or a[0].get("codec_name") != "aac":
        problems.append("no AAC audio stream")
    dec = subprocess.run([audio_mix.ff("ffmpeg"), "-v", "error", "-xerror", "-i", str(mp4), "-f", "null", "-"], capture_output=True, text=True)
    checks["full_decode"] = dec.returncode == 0 and not dec.stderr.strip()
    if not checks["full_decode"]:
        problems.append("full decode failed: " + (dec.stderr.strip().splitlines() or ["exit %d" % dec.returncode])[-1][:160])
    dur = float(info.get("format", {}).get("duration") or 0)
    take = audio_mix.duration(narration)
    checks.update(duration_s=round(dur, 2), narration_s=round(take, 2))
    if not (take - 0.1 <= dur <= take + TAIL_S):
        problems.append(f"length {dur:.2f} s does not match the {take:.2f} s narration (allowed {take:.2f}-{take + TAIL_S:.2f})")
    if a:
        i, tp = audio_mix.loudness(mp4)
        c, lag = audio_mix.correlation(audio_mix.envelope(narration, take), audio_mix.envelope(mp4, take))
        checks.update(loudness_lufs=i, true_peak_dbtp=tp, narration_corr=round(c, 3), sync_offset_ms=lag * 20)
        if abs(i - audio_mix.TARGET_I) > 1.0:
            problems.append(f"loudness {i} LUFS (target -14 +-1)")
        if tp > -1.0:
            problems.append(f"true peak {tp} dBTP above -1.0")
        if c < 0.6:
            problems.append(f"sound does not carry the narration (correlation {c:.2f} < 0.60)")
        if abs(lag) > 3:
            problems.append(f"narration out of sync by {lag * 20} ms")
    if srt is not None:
        ok, msg = _srt_ok(srt, dur)
        checks["srt"] = msg
        if not ok:
            problems.append(msg)
    if cover is not None:
        ci = audio_mix.probe(cover) if cover and Path(cover).exists() else {}
        cv = [s for s in ci.get("streams", []) if s.get("codec_type") == "video"]
        checks["cover"] = f"{cv[0].get('width')}x{cv[0].get('height')}" if cv else "missing"
        if not cv or (cv[0].get("width"), cv[0].get("height")) != (1080, 1920):
            problems.append("cover missing or not 1080x1920")
    return checks, problems


def render_and_verify(ep, ledger, cfg, say=print, fault=None):
    """Make this episode's film one at a time; mark it ready only if verify_outputs passes."""
    from .film import make_film

    rc = cfg.get("render", {})
    scale = float(rc.get("scale", 1.0))
    size = (round(1080 * scale) // 2 * 2, round(1920 * scale) // 2 * 2)
    out_dir = ROOT / "exports" / "films" / ep.slug
    mp4 = out_dir / f"{ep.slug}.mp4"
    prev = ledger.film(ep.slug)
    if prev and prev["status"] == "ready for review" and prev["revision"] == ep.revision() and mp4.exists() \
            and hashlib.sha256(mp4.read_bytes()).hexdigest() == prev["sha256"]:
        say(f"  film   {ep.slug}: already verified ({mp4.name}); not re-rendered")
        return "ready for review"
    out_dir.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(str(out_dir)).free / 1e9
    if free_gb < MIN_FREE_GB:
        ledger.set_film(ep.slug, revision=ep.revision(), status="held", reason=f"disk: {free_gb:.1f} GB free")
        say(f"  film   {ep.slug}: held, only {free_gb:.1f} GB free")
        return "held"
    spec, missing = film_spec(ep, ledger, cfg, out_dir)
    if missing:
        ledger.set_film(ep.slug, revision=ep.revision(), status="waiting", reason="; ".join(missing))
        say(f"  film   {ep.slug}: waiting for {', '.join(missing)}")
        return "waiting"
    lock_f = open(ensure_state() / "render.lock", "w")
    fcntl.flock(lock_f, fcntl.LOCK_EX)  # one film at a time
    try:
        attempts = (prev or {}).get("attempts") or 0
        checks, problems = {}, []
        for attempt in (1, 2):
            attempts += 1
            made, report, problems = make_film(spec, say=say)
            if made:
                if fault and attempt == 1:  # rehearsal only: damage the first export to prove the gate
                    fault(made)
                checks, problems = verify_outputs(made, spec["narration"], spec["tag"], size,
                                                  srt=report["outputs"]["srt"], cover=report["outputs"]["cover"])
                checks["stem"] = report["steps"]["narration_stem"]["checks"]
                checks["mix"] = report["steps"]["mix"]["checks"]
                checks["notes"] = spec.get("notes", [])
            if made and not problems:
                ledger.set_film(ep.slug, revision=ep.revision(), mp4=str(made), sha256=hashlib.sha256(made.read_bytes()).hexdigest(),
                                status="ready for review", reason=None, checks_json=json.dumps(checks, ensure_ascii=False), attempts=attempts)
                say(f"  film   {ep.slug}: READY FOR REVIEW  {checks['duration_s']} s vs take {checks['narration_s']} s, decode ok, "
                    f"{checks.get('loudness_lufs')} LUFS, TP {checks.get('true_peak_dbtp')}, narration corr {checks.get('narration_corr')}, "
                    f"sync {checks.get('sync_offset_ms')} ms, SRT {checks.get('srt')}, cover {checks.get('cover')}")
                return "ready for review"
            say(f"  film   {ep.slug}: attempt {attempt} failed the check: {'; '.join(problems)}"
                + (" -> free automatic re-render" if attempt == 1 else ""))
            if problems and problems[0].startswith("narration stem"):
                break  # a bad take is not fixed by re-rendering
        ledger.set_film(ep.slug, revision=ep.revision(), mp4=str(mp4), status="exception", reason="; ".join(problems),
                        checks_json=json.dumps(checks, ensure_ascii=False), attempts=attempts)
        return "exception"
    finally:
        fcntl.flock(lock_f, fcntl.LOCK_UN)
        lock_f.close()

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
    """An approved amendment's picture, else the shot's own clip, else its own still, else the shot it reuses."""
    swap = (load_json(ep.dir / "amendments.json", {}) or {}).get("picture", {})
    if shot_id in swap:
        return _picture(ep, ledger, swap[shot_id], by_id)
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
    al = load_alignment(narr) if narr else None
    if narr and al is None:
        al = pause_alignment(voice, narr)
        notes.append("caption and cut timing from the take's pauses (no character alignment returned)")
    if al is not None:
        # cuts follow the real take: a shot starts 0.12 s before its first spoken character
        st = al["character_start_times_seconds"]
        starts_t = [0.0] + [max(0.0, round(st[a] - 0.12, 3)) for a, _ in ranges[1:]]
        total = round(max(take_s + 1.0, al["character_end_times_seconds"][-1] + 1.0), 3)
    else:
        starts_t = [0.0] + [round(s["est_start_s"] * scale_t, 3) for s in on[1:]]
        total = round(max(take_s + 1.0, (on[-1]["est_start_s"] + on[-1]["est_dur_s"]) * scale_t + 1.0), 3) if on else 1.0
    shot_win = {}
    for i, s in enumerate(on):
        start = starts_t[i]
        end = starts_t[i + 1] if i + 1 < len(on) else total
        shot_win[s["id"]] = (start, end)
        path, kind = _picture(ep, ledger, s["id"], by_id)
        if not path:
            missing.append(f"picture for {s['id']}")
            continue
        cuts = s.get("cut_to")
        if cuts:
            cuts = [cuts] if not isinstance(cuts[0], (list, tuple)) else cuts
            pts = [(start, path, kind)]
            bad = False
            for cid, off in cuts:
                cp, ck = _picture(ep, ledger, cid, by_id)
                if not cp:
                    missing.append(f"picture for {cid}")
                    bad = True
                    break
                if isinstance(off, str):  # anchor on words in this shot's text, timed by the real take
                    i_w = voice.find(off, ranges[i][0])
                    if i_w < 0 or al is None:
                        missing.append(f"cut anchor {off!r} in {s['id']}")
                        bad = True
                        break
                    t = round(min(end - 0.5, max(start, al["character_start_times_seconds"][i_w] - 0.12)), 3)
                else:
                    t = start if off <= 0 else round(min(end - 0.5, start + off * scale_t), 3)
                if t <= pts[-1][0]:
                    pts[-1] = (pts[-1][0], cp, ck)
                else:
                    pts.append((t, cp, ck))
            if bad:
                continue
            for k, (t, cp, ck) in enumerate(pts):
                segs.append({"kind": ck, "src": str(cp), "start": t, "end": pts[k + 1][0] if k + 1 < len(pts) else end,
                             "own": cp == path and k == 0 and not s.get("media_from")})
        else:
            segs.append({"kind": kind, "src": str(path), "start": start, "end": end, "own": not s.get("media_from")})
    if missing:
        return None, missing
    # amendments.json "focus": {shot: {"from": [cx, cy, z], "to": [...]}} reframes a still at no cost
    am_focus = (load_json(ep.dir / "amendments.json", {}) or {}).get("focus", {})
    for sid, fz in am_focus.items():
        if sid in shot_win:
            a0, b0 = shot_win[sid]
            for sg in segs:
                if sg["kind"] == "still" and a0 - 1e-6 <= sg["start"] < b0:
                    sg["focus"] = fz
    notes += _finish_actions(segs)
    phrases = from_alignment(voice, al, ranges)
    ov = load_json(ep.dir / "overlays.json", {}) or {}
    starts = shot_win
    overlays, no_caption = [], []
    sh_rng = {s["id"]: r for s, r in zip(on, ranges)}

    def _at(o, key, default):
        words = o.get(key + "_words")
        if words and al is not None:
            i_w = voice.find(words, sh_rng[o["shot"]][0])
            if i_w < 0:
                raise ValueError(f"overlay anchor {words!r} not found in {o['shot']}")
            return round(max(0.0, al["character_start_times_seconds"][i_w] - 0.05), 3)
        return default

    for o in ov.get("items", []):
        a, b = starts[o["shot"]]
        item = {k: v for k, v in o.items() if k not in ("shot", "at", "for", "at_words", "until_words", "until_shot")}
        item["start"] = _at(o, "at", round(a + o.get("at", 0.0) * scale_t, 3))
        end = b if not o.get("until_shot") else starts[o["until_shot"]][1]
        item["end"] = round(_at(o, "until", min(end, item["start"] + o["for"]) if o.get("for") else end), 3) - 0.04
        overlays.append(item)
        if o["kind"] == "title":
            no_caption.append((item["start"], item["end"] + 0.04))
    # a hook that starts under the title still gets its caption once the title fades (muted viewers need the question)
    for p in phrases:
        for a, b in no_caption:
            if a <= p["start"] < b and p["end"] - b >= 1.2:
                p["start"] = round(b + 0.05, 3)
    phrases = [p for p in phrases if not any(a <= p["start"] < b for a, b in no_caption)]
    # one readable text block at a time (EP02 rule): no caption under a card; a caption running into one stops short
    blocks = [o for o in overlays if o["kind"] != "mark"]
    phrases = [p for p in phrases if not any(o["start"] - 0.05 <= p["start"] < o["end"] for o in blocks)]
    for p in phrases:
        nxt = [o["start"] for o in blocks if o["start"] > p["start"]]
        if nxt and p["end"] + 0.30 > nxt[0] - 0.06:
            p["end"] = round(nxt[0] - 0.40, 3)
    phrases = [p for p in phrases if p["end"] > p["start"] + 0.3]
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
    elif cbg and cover_shot in am_focus:
        # the cover keeps the same reframing as the film ("from" framing)
        cx, cy, z = am_focus[cover_shot]["from"]
        still = Path(out_dir) / "cover-bg.jpg"
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        crop = (f"crop=iw/{z}:ih/{z}:'max(0,min(iw-iw/{z},iw*{cx}-iw/{z}/2))':"
                f"'max(0,min(ih-ih/{z},ih*{cy}-ih/{z}/2))'")
        subprocess.run([audio_mix.ff("ffmpeg"), "-v", "error", "-y", "-i", str(cbg), "-vf", crop, "-q:v", "2", str(still)], check=True)
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


def render_and_verify(ep, ledger, cfg, say=print, fault=None, edit=None):
    """Make this episode's film one at a time; mark it ready only if verify_outputs passes.

    edit: name of episodes/<slug>/edits/<name>.json; rendered beside the automatic cut, which is left untouched."""
    from .film import make_film

    rc = cfg.get("render", {})
    scale = float(rc.get("scale", 1.0))
    size = (round(1080 * scale) // 2 * 2, round(1920 * scale) // 2 * 2)
    key = f"{ep.slug}-{edit}" if edit else ep.slug
    out_dir = ROOT / "exports" / "films" / key
    mp4 = out_dir / f"{ep.slug}.mp4"
    rev = ep.revision()
    if edit:
        rev += ":" + hashlib.sha256((ep.dir / "edits" / f"{edit}.json").read_bytes()).hexdigest()[:8]
    prev = ledger.film(key)
    if prev and prev["status"] == "ready for review" and prev["revision"] == rev and mp4.exists() \
            and hashlib.sha256(mp4.read_bytes()).hexdigest() == prev["sha256"]:
        say(f"  film   {key}: already verified ({mp4.name}); not re-rendered")
        return "ready for review"
    out_dir.mkdir(parents=True, exist_ok=True)
    free_gb = shutil.disk_usage(str(out_dir)).free / 1e9
    if free_gb < MIN_FREE_GB:
        ledger.set_film(key, revision=rev, status="held", reason=f"disk: {free_gb:.1f} GB free")
        say(f"  film   {key}: held, only {free_gb:.1f} GB free")
        return "held"
    if edit:
        from .edit import edit_spec
        spec, missing = edit_spec(ep, ledger, cfg, out_dir, edit)
    else:
        spec, missing = film_spec(ep, ledger, cfg, out_dir)
    if missing:
        ledger.set_film(key, revision=rev, status="waiting", reason="; ".join(missing))
        say(f"  film   {key}: waiting for {', '.join(missing)}")
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
                ledger.set_film(key, revision=rev, mp4=str(made), sha256=hashlib.sha256(made.read_bytes()).hexdigest(),
                                status="ready for review", reason=None, checks_json=json.dumps(checks, ensure_ascii=False), attempts=attempts)
                say(f"  film   {key}: READY FOR REVIEW  {checks['duration_s']} s vs take {checks['narration_s']} s, decode ok, "
                    f"{checks.get('loudness_lufs')} LUFS, TP {checks.get('true_peak_dbtp')}, narration corr {checks.get('narration_corr')}, "
                    f"sync {checks.get('sync_offset_ms')} ms, SRT {checks.get('srt')}, cover {checks.get('cover')}")
                return "ready for review"
            say(f"  film   {key}: attempt {attempt} failed the check: {'; '.join(problems)}"
                + (" -> free automatic re-render" if attempt == 1 else ""))
            if problems and problems[0].startswith("narration stem"):
                break  # a bad take is not fixed by re-rendering
        ledger.set_film(key, revision=rev, mp4=str(mp4), status="exception", reason="; ".join(problems),
                        checks_json=json.dumps(checks, ensure_ascii=False), attempts=attempts)
        return "exception"
    finally:
        fcntl.flock(lock_f, fcntl.LOCK_UN)
        lock_f.close()


def _finish_actions(segs, keep=1.5, reach=1.6, tail=0.6):
    """EP02 lesson (the water hand-over was cut before Lopamudra let go): a shot's own clip plays to its end.
    The missing time comes from the next picture if it is a still, otherwise from the previous still, each
    keeping at least `keep` seconds and moving at most `reach` seconds. Returns notes for any clip that still
    cannot finish."""
    notes = []
    for k, sg in enumerate(segs):
        if sg["kind"] != "clip" or not sg.get("own"):
            continue
        need = round(audio_mix.duration(sg["src"]) - (sg["end"] - sg["start"]) - 0.05, 3)
        if need <= 0:
            continue
        nxt = segs[k + 1] if k + 1 < len(segs) else None
        if nxt and nxt["kind"] == "still":
            d = max(0.0, min(need, reach, nxt["end"] - nxt["start"] - keep))
            sg["end"] = nxt["start"] = round(sg["end"] + d, 3)
            need -= d
        prv = segs[k - 1] if k else None
        if need > 0.05 and prv and prv["kind"] == "still":
            d = max(0.0, min(need, reach, prv["end"] - prv["start"] - keep))
            sg["start"] = prv["end"] = round(sg["start"] - d, 3)
            need -= d
        # then the settled tail of a neighbouring clip (EP02 v2 took 0.5 s from Agastya rising)
        for nb, side in ((prv, "prev"), (nxt, "next")):
            if need > 0.05 and nb and nb["kind"] == "clip":
                d = max(0.0, min(need, tail, nb["end"] - nb["start"] - 2.0))
                if side == "prev":
                    sg["start"] = nb["end"] = round(sg["start"] - d, 3)
                else:
                    sg["end"] = nb["start"] = round(sg["end"] + d, 3)
                need -= d
        if need > 0.05:
            notes.append(f"clip {Path(sg['src']).name} is cut {need:.1f} s before its end")
    for sg in segs:
        sg.pop("own", None)
    return notes

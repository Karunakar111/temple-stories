"""Render an episode's film from its own assets, then decide whether it may be reviewed.

A film is READY FOR REVIEW only when its episode-specific MP4
  1. exists and carries this episode's id and revision in its metadata,
  2. has an H.264 video stream at the expected size and an audio stream,
  3. decodes end to end with no decoder error,
  4. lasts as long as the narration take (at least the take, at most the take plus the end hold),
  5. carries that narration: the MP4's sound envelope follows the take's (correlation and sync).
Otherwise it gets one free automatic re-render; a second failure is an exception for that
episode only. One render at a time (file lock); a disk check runs first; staged copies of the
assets are removed after verification (they are reproducible).
"""
import fcntl
import hashlib
import json
import math
import shutil
import subprocess
import sys
import wave
from pathlib import Path

from .episodes import request_key
from .paths import ROOT, ensure_state

CODE = Path(__file__).resolve().parent.parent  # the Remotion project (src/, public/, node_modules)
MIN_FREE_GB = 3
TAIL_S = 3.5  # allowed picture after the last word (end hold)


def _ff(name):
    exe = shutil.which(name)
    if exe:
        return exe
    alt = CODE / "node_modules" / f"{name}-static" / ("bin/darwin/x64/" + name if name == "ffprobe" else name)
    return str(alt) if alt.exists() else name


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
                return p, ("video" if at == "clip" else "image")
    if s.get("media_from"):
        return _picture(ep, ledger, s["media_from"], by_id)
    return None, None


def film_props(ep, ledger, stage_rel, label=None):
    """Props for EpisodeFilm. Returns (props, files to stage, missing)."""
    doc, timing = ep.shots_doc, ep.timing or {}
    scale = timing.get("scale", 1.0)
    by_id = {s["id"]: s for s in doc["shots"]}
    narr = _asset(ep, ledger, "VO", "narration")
    files, missing, shots = {}, [], []
    if not narr:
        missing.append("narration take")

    def stage(path):
        name = path.name
        files[name] = path
        return f"{stage_rel}/{name}"

    on = [s for s in doc["shots"] if s.get("text")]
    for i, s in enumerate(on):
        start = s["est_start_s"] * scale
        end = on[i + 1]["est_start_s"] * scale if i + 1 < len(on) else (s["est_start_s"] + s["est_dur_s"]) * scale + 1.0
        path, kind = _picture(ep, ledger, s["id"], by_id)
        if not path:
            missing.append(f"picture for {s['id']}")
            continue
        cut = None
        if s.get("cut_to"):
            cp, ck = _picture(ep, ledger, s["cut_to"][0], by_id)
            if not cp:
                missing.append(f"picture for {s['cut_to'][0]}")
                continue
            cut = {"at": round(s["cut_to"][1] * scale, 3), "pic": {"kind": ck, "src": stage(cp)}}
        shots.append({"id": s["id"], "start": round(start, 3), "end": round(end, 3),
                      "capEnd": round(start + (s["est_dur_s"] - s.get("hold_after_s", 0)) * scale + 0.1, 3),
                      "text": s["text"], "pic": {"kind": kind, "src": stage(path)}, "cut": cut})
    total = shots[-1]["end"] if shots else 1.0
    title = ep.meta.get("title_te", "").split(" ", 1)
    props = {"episode": ep.slug, "title": title if len(title) == 2 else [ep.meta.get("title_te", "")], "total_s": round(total, 3),
             "narration": stage(narr) if narr else "", "music": None, "label": label, "shots": shots}
    return props, files, missing


def _probe(path):
    r = subprocess.run([_ff("ffprobe"), "-v", "error", "-show_entries",
                        "stream=codec_type,codec_name,width,height:format=duration:format_tags=comment",
                        "-of", "json", str(path)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def _envelope(path, seconds, rate=8000, hop=0.02):
    """Mono RMS envelope, one value per 20 ms."""
    import numpy as np

    r = subprocess.run([_ff("ffmpeg"), "-v", "error", "-i", str(path), "-t", f"{seconds:.3f}", "-ac", "1", "-ar", str(rate),
                        "-f", "s16le", "-"], capture_output=True)
    x = np.frombuffer(r.stdout, dtype=np.int16).astype(float)
    n = int(rate * hop)
    k = len(x) // n
    return np.sqrt((x[: k * n].reshape(k, n) ** 2).mean(axis=1)) if k else np.zeros(1)


def verify_film(ep, mp4, narration, size):
    import numpy as np

    checks, problems = {}, []
    if not mp4.exists() or mp4.stat().st_size == 0:
        return {"exists": False}, ["MP4 missing"]
    info = _probe(mp4)
    streams = info.get("streams", [])
    v = [s for s in streams if s.get("codec_type") == "video"]
    a = [s for s in streams if s.get("codec_type") == "audio"]
    tag = info.get("format", {}).get("tags", {}).get("comment", "")
    checks["episode_tag"] = tag
    if tag != f"gudi:{ep.slug}:{ep.revision()}":
        problems.append(f"MP4 is not tagged as {ep.slug} revision {ep.revision()} (found {tag!r})")
    if not v or v[0].get("codec_name") != "h264" or (v[0].get("width"), v[0].get("height")) != size:
        problems.append(f"video stream not H.264 {size[0]}x{size[1]}: {v[0] if v else 'none'}")
    if not a:
        problems.append("no audio stream")
    dec = subprocess.run([_ff("ffmpeg"), "-v", "error", "-xerror", "-i", str(mp4), "-f", "null", "-"], capture_output=True, text=True)
    checks["full_decode"] = dec.returncode == 0 and not dec.stderr.strip()
    if not checks["full_decode"]:
        problems.append("full decode failed: " + (dec.stderr.strip().splitlines() or ["exit %d" % dec.returncode])[-1][:160])
    dur = float(info.get("format", {}).get("duration") or 0)
    take = float(_probe(narration).get("format", {}).get("duration") or 0)
    checks.update(duration_s=round(dur, 2), narration_s=round(take, 2))
    if not (take - 0.1 <= dur <= take + TAIL_S):
        problems.append(f"length {dur:.2f} s does not match the {take:.2f} s narration (allowed {take:.2f}-{take + TAIL_S:.2f})")
    if a and take > 0:
        e1, e2 = _envelope(narration, take), _envelope(mp4, take)
        m = min(len(e1), len(e2))
        e1, e2 = e1[:m], e2[:m]
        corr = float(np.corrcoef(e1, e2)[0, 1]) if m > 10 and e1.std() > 0 and e2.std() > 0 else 0.0
        lags = range(-10, 11)  # +-200 ms
        best = max(lags, key=lambda L: float(np.dot(np.roll(e2, L), e1)))
        checks.update(narration_corr=round(corr, 3), sync_offset_ms=best * 20)
        if corr < 0.85:
            problems.append(f"sound does not follow the narration (envelope correlation {corr:.2f} < 0.85)")
        if abs(best) > 3:
            problems.append(f"narration out of sync by {best * 20} ms")
    return checks, problems


def _render(props_path, out, scale):
    backend = "render.mjs" if sys.platform == "darwin" else "remotion-cli"
    if backend == "render.mjs":  # macOS 12: image sequence + static ffmpeg (no video decode: clips need pre-extraction)
        cmd = ["node", "scripts/render.mjs", "EpisodeFilm", "--entry", "src/preview/index.ts", "--props", str(props_path), "--out", str(out)]
    else:
        cmd = ["npx", "remotion", "render", "src/preview/index.ts", "EpisodeFilm", str(out), f"--props={props_path}",
               f"--scale={scale}", "--crf=23", "--log=error"]
        chrome = shutil.which("google-chrome")
        if chrome:
            cmd.append(f"--browser-executable={chrome}")
    r = subprocess.run(cmd, cwd=str(CODE), capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr)[-600:]


def render_and_verify(ep, ledger, cfg, say=print, fault=None):
    """Render this episode's film one at a time; mark it ready only if verify_film passes."""
    rc = cfg.get("render", {})
    scale = float(rc.get("scale", 1.0))
    size = (round(1080 * scale), round(1920 * scale))
    out_dir = ROOT / "exports" / "films" / ep.slug
    mp4 = out_dir / f"{ep.slug}.mp4"
    narr = _asset(ep, ledger, "VO", "narration")
    prev = ledger.film(ep.slug)
    if prev and prev["status"] == "ready for review" and prev["revision"] == ep.revision() and mp4.exists() \
            and hashlib.sha256(mp4.read_bytes()).hexdigest() == prev["sha256"]:
        say(f"  film   {ep.slug}: already verified ({mp4.name}); not re-rendered")
        return "ready for review"
    free_gb = shutil.disk_usage(str(out_dir.parent if out_dir.parent.exists() else ROOT)).free / 1e9
    if free_gb < MIN_FREE_GB:
        ledger.set_film(ep.slug, revision=ep.revision(), status="held", reason=f"disk: {free_gb:.1f} GB free")
        say(f"  film   {ep.slug}: held, only {free_gb:.1f} GB free")
        return "held"
    stage_rel = f"render-stage/{hashlib.sha1(str(ROOT).encode()).hexdigest()[:8]}/{ep.slug}"
    props, files, missing = film_props(ep, ledger, stage_rel, label=rc.get("label"))
    if missing:
        ledger.set_film(ep.slug, revision=ep.revision(), status="waiting", reason="; ".join(missing))
        say(f"  film   {ep.slug}: waiting for {', '.join(missing)}")
        return "waiting"
    out_dir.mkdir(parents=True, exist_ok=True)
    lock_f = open(ensure_state() / "render.lock", "w")
    fcntl.flock(lock_f, fcntl.LOCK_EX)  # one film at a time
    stage_dir = CODE / "public" / stage_rel
    try:
        stage_dir.mkdir(parents=True, exist_ok=True)
        for name, src in files.items():
            shutil.copy2(src, stage_dir / name)
        props_path = out_dir / "props.json"
        props_path.write_text(json.dumps(props, ensure_ascii=False, indent=1), encoding="utf-8")
        attempts = (prev or {}).get("attempts") or 0
        for attempt in (1, 2):
            raw = out_dir / "render.mp4"
            code, log = _render(props_path, raw, scale)
            if code != 0:
                checks, problems = {}, [f"renderer exited {code}: {log.strip().splitlines()[-1] if log.strip() else ''}"]
            else:
                tagged = out_dir / "tagged.mp4"
                subprocess.run([_ff("ffmpeg"), "-v", "error", "-y", "-i", str(raw), "-c", "copy", "-metadata",
                                f"comment=gudi:{ep.slug}:{ep.revision()}", str(tagged)], check=True)
                tagged.replace(mp4)
                raw.unlink(missing_ok=True)
                if fault and attempt == 1:  # rehearsal only: damage the first export to prove the gate
                    fault(mp4)
                checks, problems = verify_film(ep, mp4, narr, size)
            attempts += 1
            if not problems:
                ledger.set_film(ep.slug, revision=ep.revision(), mp4=str(mp4), sha256=hashlib.sha256(mp4.read_bytes()).hexdigest(),
                                status="ready for review", reason=None, checks_json=json.dumps(checks), attempts=attempts)
                say(f"  film   {ep.slug}: READY FOR REVIEW  {checks['duration_s']} s vs take {checks['narration_s']} s, "
                    f"decode ok, narration corr {checks.get('narration_corr')}, sync {checks.get('sync_offset_ms')} ms")
                return "ready for review"
            say(f"  film   {ep.slug}: attempt {attempt} failed the check: {'; '.join(problems)}"
                + (" -> free automatic re-render" if attempt == 1 else ""))
        ledger.set_film(ep.slug, revision=ep.revision(), mp4=str(mp4), status="exception", reason="; ".join(problems),
                        checks_json=json.dumps(checks), attempts=attempts)
        return "exception"
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)  # reproducible intermediates only
        fcntl.flock(lock_f, fcntl.LOCK_UN)
        lock_f.close()

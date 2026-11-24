"""Weekly batch: produce seven episodes in one run, release one per day.

- One approval covers the week: every episode's script hash and creative-scope hash, the
  provider caps for the week, and the release start date. Episodes that cannot be approved
  (no script yet) are listed as not approved; the rest of the week still runs.
- One production run per local day for the batch (ledger day lock), one runner at a time.
- Each episode is run independently: a held episode (missing script, unresolved reference,
  budget) never stops the others.
- Narration first; clips wait for the take; the take retimes the episode within the approval.
"""
import csv
import html
import json
import math
import shutil
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .episodes import Episode, load_json, request_key
from .ledger import local_tz
from .money import fmt, to_milli
from .paths import EPISODES, REVIEW, ROOT, ensure_state
from .runner import DONE, NAMES, RunnerLock, run_episode



class Batch:
    def __init__(self, batch_id, root=None):
        self.root = root or EPISODES
        self.id = batch_id
        self.doc = load_json(self.root / "batches" / f"{batch_id}.json")
        if self.doc is None:
            raise SystemExit(f"no batch {batch_id}")
        self.episodes = self.doc["episodes"]
        self.approval = load_json(self.root / "batches" / f"{batch_id}.approval.json")

    def cap(self, provider):
        v = (self.approval or {}).get("caps", {}).get(provider)
        return None if v is None else to_milli(v)

    def release_dates(self):
        start = (self.approval or {}).get("release_start")
        if not start:
            return {}
        d0 = date.fromisoformat(start)
        approved = [s for s in self.episodes if s in (self.approval or {}).get("episodes", {})]
        return {s: (d0 + timedelta(days=i * self.doc["release"]["every_days"])).isoformat() for i, s in enumerate(approved)}

    def episode(self, slug):
        return Episode(slug, self.root, batch=self)


# ---------------------------------------------------------------------------- approval
def approve(batch, by, caps, release_start, reviewed):
    if not reviewed:
        raise SystemExit("needs --i-have-reviewed (scripts, visual approach and caps for the whole week)")
    for k, v in caps.items():
        to_milli(v)
    rec = {"batch": batch.id, "approved_by": by, "approved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "covers": "scripts + visual approach (reference boards and shot lists, timing excluded) + provider caps",
           "caps": caps, "release_start": release_start, "episodes": {}, "not_approved": {}}
    for slug in batch.episodes:
        ep = Episode(slug, batch.root)
        if not ep.has_script() or ep.shots_doc is None:
            rec["not_approved"][slug] = ep.meta.get("status") or "no script or shot list"
            continue
        rec["episodes"][slug] = {"script_sha256": ep.script_sha(), "look_sha256": ep.creative_sha()}
    (batch.root / "batches" / f"{batch.id}.approval.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return rec


# ---------------------------------------------------------------------------- retiming
def _probe_seconds(path):
    for exe in (shutil.which("ffprobe"), str(ROOT / "node_modules/ffprobe-static/bin/darwin/x64/ffprobe")):
        if exe and Path(exe).exists():
            r = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                               capture_output=True, text=True)
            try:
                return float(r.stdout.strip())
            except ValueError:
                return None
    return None


def retime(ep, ledger, audio_path):
    """Size each clip from the real take: the spoken span of its shot(s), from the take's character
    timestamps (else its pauses). A clip may get shorter, never longer than quoted, so spend stays
    within the approved quote; a shot longer than its clip holds the clip's last frame."""
    from .captions import load_alignment, pause_alignment

    audio_s = _probe_seconds(audio_path)
    voice = ep.voice_text()
    on = [s for s in ep.shots_doc["shots"] if s.get("text")]
    al = load_alignment(audio_path) if audio_s else None
    method = "character timestamps"
    if audio_s and al is None:
        al = pause_alignment(voice, audio_path)
        method = "pauses"
    span = {}
    if al:
        st = al["character_start_times_seconds"]
        pos, starts = 0, []
        for s in on:
            a = voice.index(s["text"], pos)
            starts.append(st[a])
            pos = a + len(s["text"])
        for i, s in enumerate(on):
            end = starts[i + 1] if i + 1 < len(on) else al["character_end_times_seconds"][-1] + 1.0
            span[s["id"]] = end - starts[i]
    est = ep.shots_doc.get("est_total_s")
    scale = audio_s / est if (audio_s and est) else 1.0
    by_id = {s["id"]: s for s in ep.shots_doc["shots"]}
    clips = {}
    for s in ep.shots_doc["shots"]:
        for c in s["paid"]:
            if c["asset_type"] != "clip":
                continue
            ids = s.get("clip_spans") or [s["id"]]
            if all(x in span for x in ids):
                need = sum(span[x] for x in ids)
            elif all(by_id[x].get("est_dur_s") for x in ids):
                need = sum(by_id[x]["est_dur_s"] for x in ids) * scale
            else:
                need = c["settings"]["duration"]
            quoted = c["settings"]["duration"]
            d = min(quoted, max(3, math.ceil(need - 0.25)))
            rate = to_milli(c["quote"]) / quoted
            clips[s["id"]] = {"duration": d, "quote": fmt(round(d * rate)), "spoken_s": round(need, 2)}
    doc = {"source": ("take (" + method + ")") if audio_s else "take (mock audio: estimate timing kept)", "audio_s": audio_s,
           "scale": round(scale, 3), "derived_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "clips": clips}
    (ep.dir / "timing.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return f"{doc['source']}; {len(clips)} clips sized, none longer than quoted"


def _fault_for(slug):
    """Rehearsal only: GUDI_RENDER_FAULT=<slug>:truncate damages that film's first export."""
    import os

    spec = os.environ.get("GUDI_RENDER_FAULT", "")
    if not spec.startswith(slug + ":"):
        return None

    def truncate(mp4):
        tmp = mp4.with_suffix(".cut.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp4), "-t", "20", "-c", "copy", str(tmp)], check=True)
        tmp.replace(mp4)
    return truncate


def run_batch(batch, ledger, cfg, providers, say=print):
    """Paid assets for every approved episode, then each finished episode is rendered and checked.
    An episode that is held, waiting or failed never stops the others."""
    from .render import render_and_verify
    from .review import export

    day = datetime.now(local_tz(cfg)).date().isoformat()
    results = {}
    with RunnerLock(ensure_state()) as lock:
        if lock is None:
            say("LOCKED: another gudi runner is active; this launch exits without doing anything")
            return {"_": "locked"}
        got = ledger.take_day(day, f"batch:{batch.id}", "batch")
        if got != "ok":
            say(f"LOCKED: {got}")
            return {"_": "locked"}
        releases = batch.release_dates()
        for slug in batch.episodes:
            ep = batch.episode(slug)
            say(f"\n[{slug}] release {releases.get(slug, 'not scheduled')}")
            try:
                code = run_episode(ep, ledger, cfg, providers, say=say, lock_held=True, retimer=retime)
                if code == DONE:
                    film = render_and_verify(ep, ledger, cfg, say=say, fault=_fault_for(slug))
                    results[slug] = film
                    if film == "ready for review":
                        export(ep, ledger, cfg, say=say, release=releases.get(slug))
                else:
                    results[slug] = NAMES.get(code, str(code))
            except Exception as e:  # one episode's failure never stops the week
                say(f"  ERROR {slug}: {e}; held, other episodes continue")
                results[slug] = "error"
    say("\nBATCH SUMMARY " + batch.id)
    for slug, r in results.items():
        say(f"  {slug:22s} {r}")
    return results


# ---------------------------------------------------------------------------- quote
def quote_rows(batch, ledger=None):
    rows = []
    for slug in batch.episodes:
        ep = Episode(slug, batch.root)
        if not ep.has_script() or ep.shots_doc is None:
            rows.append({"episode": slug, "beat": "-", "asset": "-", "provider": "-", "model": "-", "seconds": "",
                         "quote": "", "status": ep.meta.get("status", "no script"), "blocked_by": ""})
            continue
        for c in ep.paid_calls():
            b = ep.blockers(c)
            if any("needs photo" in x for x in b):
                status = "waits for exterior photo (X1)"
            elif b:
                status = "blocked: " + "; ".join(b)
            elif c["asset_type"] == "clip":
                status = "after narration (length from the take)"
            else:
                status = "ready"
            state = ""
            if ledger is not None:
                j = ledger.job(request_key(ep, c))
                state = j["state"] if j else ""
            rows.append({"episode": slug, "beat": c["beat"], "asset": c["asset_type"], "provider": c["provider"],
                         "model": c.get("model", ""), "seconds": c.get("settings", {}).get("duration", "") or "",
                         "quote": c["quote"], "status": state or status,
                         "blocked_by": "; ".join(x.split(" (")[0] for x in b)})
    return rows


def write_quote_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def totals(rows):
    t = {}
    for r in rows:
        if not r["quote"]:
            continue
        e = t.setdefault(r["episode"], {}).setdefault(r["provider"], 0)
        t[r["episode"]][r["provider"]] = e + to_milli(r["quote"])
    return t

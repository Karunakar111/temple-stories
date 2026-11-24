"""The one code path that may reach a provider's submit().

Order of checks, all deterministic:
  1. approval current (script hash, creative-scope hash; timing is NOT part of it)
  2. the episode's whole remaining plan fits under every limit (episode cap, week cap,
     daily cap, monthly cap, recorded balance) before anything is reserved; otherwise that
     episode is held whole and the rest of the batch carries on
  3. one runner at a time (file lock); one production run per local day (ledger lock)
  4. per call: resume by request key -> reconcile -> reserve -> mark submitting -> submit
  5. clips are timing-dependent: they wait until the narration take exists and has been
     retimed. No take, no clips.
No automatic paid retries: a failed or unknown request is held for a person.
"""
import fcntl
import hashlib
import json
import os
import uuid
from datetime import datetime

from .episodes import request_key
from .ledger import local_tz
from .money import fmt, to_milli
from .paths import ensure_state

DONE, HOLD, BUDGET, LOCKED, RECONCILE = 0, 2, 3, 4, 5
NAMES = {DONE: "done", HOLD: "held", BUDGET: "held (budget)", LOCKED: "locked", RECONCILE: "needs reconcile"}


class RunnerLock:
    def __init__(self, state):
        self.path = state / "runner.lock"
        self.fh = None

    def __enter__(self):
        self.fh = open(self.path, "w")
        try:
            fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.fh.close()
            self.fh = None
            return None
        self.fh.write(str(os.getpid()))
        self.fh.flush()
        return self

    def __exit__(self, *a):
        if self.fh:
            fcntl.flock(self.fh, fcntl.LOCK_UN)
            self.fh.close()


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cap(cfg, provider, key):
    v = cfg["providers"].get(provider, {}).get(key)
    return None if v is None else to_milli(v)


def plan(ep, ledger, providers):
    rows = []
    for call in ep.paid_calls():
        key = request_key(ep, call)
        job = ledger.job(key)
        rows.append({"call": call, "key": key, "state": job["state"] if job else "new",
                     "quoted_milli": providers.quote(call), "blockers": ep.blockers(call)})
    return rows


def limits(ep, ledger, cfg, provider, local_day):
    lim = ledger.headroom(provider, ep.slug, ep.cap(provider), _cap(cfg, provider, "daily_cap"),
                          _cap(cfg, provider, "monthly_cap"), local_day)
    if ep.batch is not None:
        wk = ep.batch.cap(provider)
        lim["week cap"] = None if wk is None else wk - ledger.committed_for(provider, ep.batch.episodes)
    return lim


def budget_check(ep, ledger, cfg, rows, local_day):
    problems = []
    for prov in sorted({r["call"]["provider"] for r in rows}):
        need = sum(r["quoted_milli"] for r in rows
                   if r["call"]["provider"] == prov and r["state"] == "new" and not r["blockers"])
        if need == 0:
            continue
        for name, left in limits(ep, ledger, cfg, prov, local_day).items():
            if left is None:
                problems.append(f"{prov}: {name} not set (needs {fmt(need)})")
            elif left < need:
                problems.append(f"{prov}: needs {fmt(need)}, {name} leaves {fmt(left)}")
    return problems


def run_episode(ep, ledger, cfg, providers, run_id=None, daily=False, say=print, lock_held=False, retimer=None):
    run_id = run_id or uuid.uuid4().hex[:10]
    local_day = datetime.now(local_tz(cfg)).date().isoformat()
    problems = ep.approval_problems()
    if problems:
        say(f"HOLD {ep.slug}: " + "; ".join(problems))
        return HOLD
    if lock_held:
        return _run(ep, ledger, cfg, providers, run_id, daily, say, local_day, retimer)
    with RunnerLock(ensure_state()) as lock:
        if lock is None:
            say("LOCKED: another gudi runner is active; this launch exits without doing anything")
            return LOCKED
        return _run(ep, ledger, cfg, providers, run_id, daily, say, local_day, retimer)


def _run(ep, ledger, cfg, providers, run_id, daily, say, local_day, retimer):
    rows = plan(ep, ledger, providers)
    short = budget_check(ep, ledger, cfg, rows, local_day)
    if short:
        say(f"HOLD {ep.slug} before any reservation (no partial spending): " + "; ".join(short))
        ledger.event("budget_hold", {"episode": ep.slug, "short": short}, run_id)
        return BUDGET
    if daily:
        got = ledger.take_day(local_day, ep.slug, run_id)
        if got != "ok":
            say(f"LOCKED: {got}; one production run per day")
            return LOCKED

    downloaded = {r["call"]["beat"] + ":" + r["call"]["asset_type"] for r in rows if r["state"] == "downloaded"}
    new_paid, outcome, i = 0, DONE, 0
    while i < len(rows):
        r = rows[i]
        i += 1
        call, key = r["call"], r["key"]
        tag = f"{call['beat']}:{call['asset_type']}"
        prov = providers.get(call["provider"])
        if r["blockers"]:
            say(f"  hold   {tag:22s} unresolved: {'; '.join(r['blockers'])}")
            outcome = outcome or HOLD
            continue
        if call["asset_type"] == "clip" and not ep.narration_resolved():
            say(f"  hold   {tag:22s} timing-dependent; narration take not resolved yet")
            outcome = outcome or HOLD
            continue
        deps = call.get("after") or []
        deps = [deps] if isinstance(deps, str) else deps
        waiting = [d for d in deps if d not in downloaded]
        if waiting:
            say(f"  wait   {tag:22s} needs {', '.join(waiting)} downloaded first")
            outcome = outcome or HOLD
            continue
        job = ledger.job(key)
        payload = None
        if job is None or job["state"] == "reserved":
            from .media import resolve

            payload, missing = resolve(ep, call, ledger)
            if missing:
                say(f"  hold   {tag:22s} reference media: {'; '.join(missing)}")
                outcome = outcome or HOLD
                continue
        if job is None:
            res = ledger.reserve(
                {"request_key": key, "episode": ep.slug, "revision": ep.revision(), "beat": call["beat"],
                 "asset_type": call["asset_type"], "provider": call["provider"],
                 "params_json": json.dumps(dict(call, payload=payload), ensure_ascii=False, sort_keys=True),
                 "quoted_milli": r["quoted_milli"], "local_day": local_day},
                limits(ep, ledger, cfg, call["provider"], local_day),
            )
            if res != "reserved":
                say(f"  hold   {tag:22s} {res}")
                return BUDGET
            say(f"  reserve {tag:21s} {fmt(r['quoted_milli'])} {call['provider']}")
            job = ledger.job(key)

        st = job["state"]
        if st == "downloaded":
            rows = _maybe_retime(ep, ledger, providers, call, key, rows, i, retimer, say)
            continue
        if st in ("failed", "released"):
            say(f"  stop   {tag:22s} {st}; a new attempt needs explicit approval")
            continue
        if st in ("submitting", "unknown") and not job["provider_job_id"]:
            jid = prov.find(call, key, job["created_at"])
            if jid:
                ledger.set_state(key, "submitted", provider_job_id=jid, note="reconciled from provider history")
                say(f"  found  {tag:22s} reconciled job {jid} from provider history; not resubmitted")
                st = "submitted"
            else:
                ledger.set_state(key, "unknown", note="no id and not found in history; reservation held")
                say(f"  ??     {tag:22s} may exist at provider; held for `gudi reconcile` (never resent)")
                outcome = RECONCILE
                continue
        if st == "reserved":
            ledger.set_state(key, "submitting")  # committed before the provider is called
            try:
                jid = prov.submit(call, key, payload)
            except TimeoutError as e:  # operator mode: not submitted yet; the reservation stays, nothing is resent
                ledger.set_state(key, "unknown", note=str(e))
                say(f"  later  {tag:22s} waiting for the operator; resumes from the inbox on the next run")
                outcome = outcome or HOLD
                continue
            ledger.set_state(key, "submitted", provider_job_id=jid)
            new_paid += 1
            say(f"  submit {tag:22s} job {jid}")
            st = "submitted"
        job = ledger.job(key)
        if st == "submitted":
            s = prov.status(job["provider_job_id"])
            if s["state"] == "failed":
                ledger.set_state(key, "failed", settled_milli=s.get("charged_milli"))
                say(f"  FAILED {tag:22s} job {job['provider_job_id']}; not retried")
                continue
            if s["state"] != "completed":
                say(f"  pending {tag:21s} job {job['provider_job_id']}; next run resumes by polling")
                outcome = outcome or HOLD
                continue
            ledger.set_state(key, "succeeded", result_url=s["url"], settled_milli=s.get("charged_milli") or job["quoted_milli"])
            st = "succeeded"
        if st == "succeeded":
            job = ledger.job(key)
            ext = {"still": "png", "clip": "mp4", "narration": "mp3"}.get(call["asset_type"], "bin")
            # episode-prefixed and one beat per character sheet: no two assets can share a file name
            dest = ep.dir / "assets" / f"{ep.slug.split('-')[0]}-{call['beat']}-{call['asset_type']}.{ext}"
            prov.download(job["provider_job_id"], job["result_url"], dest)
            ledger.set_state(key, "downloaded", local_path=str(dest), sha256=_sha(dest))
            downloaded.add(tag)
            say(f"  saved  {tag:22s} -> {dest.relative_to(ep.dir)}")
        rows = _maybe_retime(ep, ledger, providers, call, key, rows, i, retimer, say)
    ledger.event("run_end", {"episode": ep.slug, "new_paid": new_paid, "outcome": outcome}, run_id)
    say(f"  {ep.slug}: {new_paid} new paid submission(s); {NAMES[outcome]}")
    return outcome


def _maybe_retime(ep, ledger, providers, call, key, rows, i, retimer, say):
    """After the take exists: derive timing from it once, then re-price the clips still to come."""
    if call["asset_type"] != "narration" or retimer is None or ep.narration_resolved():
        return rows
    job = ledger.job(key)
    if not job or job["state"] != "downloaded":
        return rows
    say(f"  retime {ep.slug}: {retimer(ep, ledger, job['local_path'])}")
    ep.__init__(ep.slug, ep.root, ep.batch)  # reload timing.json
    return rows[:i] + plan(ep, ledger, providers)[i:]

"""The one code path that may reach a provider's submit().

Order of checks, all deterministic:
  1. approval current (script hash, look hash, per-provider episode cap)
  2. every planned call priced; the WHOLE remaining plan fits under every limit
     (episode cap, daily cap, monthly cap, recorded balance) before anything is reserved
  3. one runner at a time (file lock) and one episode per local day (ledger lock)
  4. per call: resume by request key -> reconcile -> reserve -> mark submitting -> submit
No automatic paid retries: a failed or unknown request is held for a person.
"""
import fcntl
import hashlib
import json
import os
import uuid
from datetime import datetime

from .episodes import request_key
from .ledger import local_tz, now_utc
from .money import fmt, to_milli
from .paths import ensure_state

HOLD, DONE, BUDGET, LOCKED, RECONCILE = 2, 0, 3, 4, 5


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


def plan(ep, ledger, providers):
    """Price every call and classify it. Pure reads; safe in a dry run."""
    rows = []
    for call in ep.paid_calls():
        key = request_key(ep, call)
        job = ledger.job(key)
        rows.append(
            {
                "call": call,
                "key": key,
                "state": job["state"] if job else "new",
                "quoted_milli": providers.quote(call),
                "blockers": ep.blockers(call),
            }
        )
    return rows


def budget_check(ep, ledger, cfg, rows, local_day):
    """True if all still-to-pay, unblocked calls fit under every limit, per provider."""
    problems = []
    for prov in sorted({r["call"]["provider"] for r in rows}):
        need = sum(r["quoted_milli"] for r in rows if r["call"]["provider"] == prov and r["state"] == "new" and not r["blockers"])
        if need == 0:
            continue
        lim = ledger.headroom(prov, ep.slug, ep.cap(prov), _cap(cfg, prov, "daily_cap"), _cap(cfg, prov, "monthly_cap"), local_day)
        for name, left in lim.items():
            if left is None:
                problems.append(f"{prov}: {name} not set (needs {fmt(need)})")
            elif left < need:
                problems.append(f"{prov}: needs {fmt(need)}, {name} leaves {fmt(left)}")
    return problems


def run_episode(ep, ledger, cfg, providers, run_id=None, daily=False, say=print):
    run_id = run_id or uuid.uuid4().hex[:10]
    tz = local_tz(cfg)
    local_day = datetime.now(tz).date().isoformat()
    state_dir = ensure_state()

    problems = ep.approval_problems()
    if problems:
        say(f"HOLD {ep.slug}: " + "; ".join(problems))
        return HOLD

    with RunnerLock(state_dir) as lock:
        if lock is None:
            say("LOCKED: another gudi runner is active; this launch exits without doing anything")
            return LOCKED
        rows = plan(ep, ledger, providers)
        short = budget_check(ep, ledger, cfg, rows, local_day)
        if short:
            say(f"HOLD {ep.slug} before any reservation (no partial spending): " + "; ".join(short))
            ledger.event("budget_hold", short, run_id)
            return BUDGET
        if daily:
            got = ledger.take_day(local_day, ep.slug, run_id)
            if got != "ok":
                say(f"LOCKED: {got}; one episode per day")
                return LOCKED

        downloaded = {r["call"]["beat"] + ":" + r["call"]["asset_type"] for r in rows if r["state"] == "downloaded"}
        new_paid = 0
        outcome = DONE
        for r in rows:
            call, key = r["call"], r["key"]
            tag = f"{call['beat']}:{call['asset_type']}"
            prov = providers.get(call["provider"])
            if r["blockers"]:
                say(f"  hold   {tag:22s} unresolved: {'; '.join(r['blockers'])}")
                outcome = outcome or HOLD
                continue
            deps = call.get("after") or []
            deps = [deps] if isinstance(deps, str) else deps
            waiting = [d for d in deps if d not in downloaded]
            if waiting:
                say(f"  wait   {tag:22s} needs {', '.join(waiting)} downloaded first")
                continue
            job = ledger.job(key)
            if job is None:
                res = ledger.reserve(
                    {
                        "request_key": key, "episode": ep.slug, "revision": ep.revision(), "beat": call["beat"],
                        "asset_type": call["asset_type"], "provider": call["provider"],
                        "params_json": json.dumps(call, ensure_ascii=False, sort_keys=True),
                        "quoted_milli": r["quoted_milli"], "local_day": local_day,
                    },
                    ledger.headroom(
                        call["provider"], ep.slug, ep.cap(call["provider"]),
                        _cap(cfg, call["provider"], "daily_cap"), _cap(cfg, call["provider"], "monthly_cap"), local_day,
                    ),
                )
                if res != "reserved":
                    say(f"  hold   {tag:22s} {res}")
                    return BUDGET
                say(f"  reserve {tag:21s} {fmt(r['quoted_milli'])} {call['provider']}")
                job = ledger.job(key)

            st = job["state"]
            if st == "downloaded":
                say(f"  have   {tag:22s} already downloaded; 0 new credits")
                continue
            if st in ("failed", "released"):
                say(f"  stop   {tag:22s} {st}; a new attempt needs `gudi retry {key[:12]} --approve`")
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
                jid = prov.submit(call, key)
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
                    continue
                ledger.set_state(key, "succeeded", result_url=s["url"],
                                 settled_milli=s.get("charged_milli") or job["quoted_milli"])
                st = "succeeded"
            if st == "succeeded":
                job = ledger.job(key)
                ext = {"still": "png", "clip": "mp4", "narration": "mp3"}.get(call["asset_type"], "bin")
                dest = ep.dir / "assets" / f"{call['beat']}-{call['asset_type']}.{ext}"
                prov.download(job["provider_job_id"], job["result_url"], dest)
                ledger.set_state(key, "downloaded", local_path=str(dest), sha256=_sha(dest))
                downloaded.add(tag)
                say(f"  saved  {tag:22s} -> {dest.relative_to(ep.dir)}")
        ledger.event("run_end", {"episode": ep.slug, "new_paid": new_paid, "outcome": outcome}, run_id)
        say(f"  run {run_id}: {new_paid} new paid submission(s)")
        return outcome


def _cap(cfg, provider, key):
    v = cfg["providers"].get(provider, {}).get(key)
    return None if v is None else to_milli(v)

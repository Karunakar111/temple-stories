"""gudi command line.

  python3 -m gudi import                       split the Production Book into episodes/
  python3 -m gudi queue                        DRY RUN: next eligible episode, planned calls, spend, gaps
  python3 -m gudi run --episode EP --dry-run   DRY RUN for one episode, call by call
  python3 -m gudi run --episode EP --live      supervised paid run (all checks enforced)
  python3 -m gudi daily                        unattended: one approved episode per day, live
  python3 -m gudi approve EP --by NAME --cap higgsfield=72 --cap elevenlabs=1430 --i-have-reviewed
  python3 -m gudi balance record PROVIDER AMOUNT [--as-of ISO] [--source TEXT]
  python3 -m gudi balance show
  python3 -m gudi ledger [--episode EP]
  python3 -m gudi reconcile KEY (--attach JOB_ID | --release)
  python3 -m gudi export EP                    local review folder
  python3 -m gudi schedule print|install [--yes]
  python3 -m gudi demo                         mock demonstrations (no network, no money)
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

from . import paths
from .money import fmt, to_milli


def _cfg():
    return json.loads(paths.CONFIG.read_text(encoding="utf-8"))


def _ledger():
    from .ledger import Ledger

    return Ledger(paths.ensure_state() / "ledger.sqlite3")


class Providers:
    """Provider set for one process. mode: dry | mock | live."""

    def __init__(self, mode, cfg):
        self.mode = mode
        self.cfg = cfg
        self._p = {}

    def quote(self, call):
        return to_milli(call["quote"])

    def get(self, name):
        if name in self._p:
            return self._p[name]
        if self.mode == "dry":
            raise RuntimeError("dry run has no provider access")
        if self.mode == "mock":
            from .providers.mock import MockProvider

            p = MockProvider(name, paths.STATE / f"mock-{name}.json")
        elif self.mode == "operator":
            from .providers.operator import OperatorProvider

            p = OperatorProvider(name)
        else:
            if name == "higgsfield":
                from .paid.higgsfield import HiggsfieldViaClaude as P
            elif name == "elevenlabs":
                from .paid.elevenlabs import ElevenLabsTTS as P
            else:
                raise RuntimeError(f"no live adapter for {name}")
            p = P(self.cfg)
        self._p[name] = p
        return p


def _mode_for_paid():
    m = os.environ.get("GUDI_PROVIDER", "live")
    if m == "mock" and os.environ.get("GUDI_ALLOW_MOCK") != "1":
        raise SystemExit("mock providers are only for `gudi demo` and tests")
    return m


# ------------------------------------------------------------------ dry-run report
def _report_episode(ep, ledger, cfg, verbose):
    from .runner import budget_check, plan
    from .ledger import local_tz

    print(f"\n{ep.slug}  (slot {ep.meta.get('slot')})  {ep.meta.get('title_te','')}")
    print(f"  script  {ep.meta['script']['words']} words, sha256 {ep.script_sha()[:12]}  status: {ep.meta.get('status')}")
    if not ep.shots_doc:
        print("  shot list: not prepared yet (prepared one episode at a time)")
        return False
    rows = plan(ep, ledger, Providers("dry", cfg))
    totals = {}
    for r in rows:
        t = totals.setdefault(r["call"]["provider"], {"n": 0, "q": 0, "blocked": 0})
        t["n"] += 1
        t["q"] += r["quoted_milli"]
        t["blocked"] += 1 if r["blockers"] else 0
    for prov, t in totals.items():
        unit = cfg["providers"].get(prov, {}).get("unit", "credits")
        print(f"  {prov:10s} {t['n']:2d} paid calls, quoted {fmt(t['q'])} {unit}; {t['blocked']} blocked by references")
    if verbose:
        for r in rows:
            c = r["call"]
            flag = "BLOCKED " + "; ".join(r["blockers"]) if r["blockers"] else r["state"]
            print(f"    {c['beat']:5s} {c['asset_type']:9s} {c['provider']:10s} {fmt(r['quoted_milli']):>6s}  {flag}")
    missing = ep.approval_problems()
    day = datetime.now(local_tz(cfg)).date().isoformat()
    missing += budget_check(ep, ledger, cfg, rows, day)
    if missing:
        print("  missing before any paid call:")
        for m in missing:
            print(f"    - {m}")
    return not missing


def cmd_queue(a):
    os.environ["GUDI_DRY_RUN"] = "1"
    from .episodes import Episode, queue_order

    cfg, ledger = _cfg(), _ledger()
    print("gudi queue: DRY RUN (this process cannot load paid adapters)")
    for prov, pc in cfg["providers"].items():
        b = ledger.last_balance(prov)
        bal = f"{fmt(b['amount_milli'])} {pc.get('unit','credits')} as of {b['as_of']} ({b['source']})" if b else "not recorded"
        print(f"  {prov:10s} balance {bal}; daily cap {pc.get('daily_cap') or 'not set'}, monthly cap {pc.get('monthly_cap') or 'not set'}")
    next_ep = None
    for slug in queue_order():
        ep = Episode(slug)
        ok = _report_episode(ep, ledger, cfg, verbose=(a.verbose or (next_ep is None and ep.shots_doc is not None)))
        if next_ep is None and ep.shots_doc is not None:
            next_ep = (slug, ok)
    print()
    if next_ep is None:
        print("NEXT: nothing has a shot list yet.")
    elif next_ep[1]:
        print(f"NEXT: {next_ep[0]} is eligible for a paid run.")
    else:
        print(f"NEXT: {next_ep[0]} (not eligible yet; see 'missing' above). Exiting cleanly, nothing spent.")
    assert "gudi.paid" not in sys.modules
    return 0


def cmd_run(a):
    from .episodes import Episode
    from .runner import run_episode

    if a.dry_run or not a.live:
        os.environ["GUDI_DRY_RUN"] = "1"
        cfg, ledger = _cfg(), _ledger()
        ok = _report_episode(Episode(a.episode), ledger, cfg, verbose=True)
        print("\nDRY RUN: no reservation, no submission." + ("" if ok else " Not eligible yet."))
        assert "gudi.paid" not in sys.modules
        return 0
    cfg, ledger = _cfg(), _ledger()
    from .batch import retime

    return run_episode(Episode(a.episode), ledger, cfg, Providers(_mode_for_paid(), cfg), retimer=retime)


def cmd_daily(a):
    """The unattended entry point. Same checks as a supervised run, plus one episode per day."""
    from .episodes import Episode, queue_order
    from .review import export
    from .runner import DONE, run_episode

    cfg, ledger = _cfg(), _ledger()
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"gudi daily {stamp}")
    for slug in queue_order():
        ep = Episode(slug)
        if ep.shots_doc is None:
            continue
        if _complete(ep, ledger):
            continue
        problems = ep.approval_problems()
        if problems:
            print(f"PENDING {slug}: " + "; ".join(problems) + ". Nothing spent.")
            return 0
        from .batch import retime

        code = run_episode(ep, ledger, cfg, Providers(_mode_for_paid(), cfg), daily=True, retimer=retime)
        if code == DONE:
            export(ep, ledger, cfg)
        return code
    print("PENDING: no episode has a shot list. Nothing spent.")
    return 0


def _complete(ep, ledger):
    from .episodes import request_key

    calls = ep.paid_calls()
    if not calls or ep.approval_problems():
        return False
    for c in calls:
        j = ledger.job(request_key(ep, c))
        if not j or j["state"] != "downloaded":
            return False
    return True


def cmd_approve(a):
    from .episodes import Episode

    if not a.i_have_reviewed:
        raise SystemExit("approval needs --i-have-reviewed (script text, reference board and shot list)")
    ep = Episode(a.episode)
    caps = {}
    for c in a.cap or []:
        k, v = c.split("=", 1)
        to_milli(v)
        caps[k] = v
    rec = {
        "episode": ep.slug,
        "script_sha256": ep.script_sha(),
        "look_sha256": ep.look_sha(),
        "voice": json.loads(paths.PRODUCTION_CONFIG.read_text())["voice"]["voiceId"] if paths.PRODUCTION_CONFIG.exists() else None,
        "caps": caps,
        "approved_by": a.by,
        "approved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (ep.dir / "approval.json").write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"approved {ep.slug}: script {rec['script_sha256'][:12]}, look {rec['look_sha256'][:12]}, caps {caps}")
    return 0


def cmd_balance(a):
    ledger = _ledger()
    cfg = _cfg()
    if a.action == "record":
        as_of = a.as_of or datetime.now(timezone.utc).isoformat(timespec="seconds")
        as_of_utc = datetime.fromisoformat(as_of).astimezone(timezone.utc).replace(microsecond=0).isoformat()
        ledger.record_balance(a.provider, to_milli(a.amount), as_of_utc, a.source)
        print(f"recorded {a.provider} balance {a.amount} as of {as_of_utc} ({a.source})")
        pc = cfg["providers"].get(a.provider, {})
        if pc.get("daily_cap") is None or pc.get("monthly_cap") is None:
            print(f"NOTE: no daily/monthly spend cap set for {a.provider} in config/pipeline.json; paid runs stay held until one is.")
        return 0
    for prov in cfg["providers"]:
        b = ledger.last_balance(prov)
        print(f"{prov:10s} " + (f"{fmt(b['amount_milli'])} as of {b['as_of']} ({b['source']})" if b else "not recorded"))
    return 0


def cmd_ledger(a):
    for j in _ledger().jobs(a.episode):
        print(f"{j['request_key'][:12]} {j['episode']:16s} {j['beat']:5s} {j['asset_type']:9s} {j['provider']:10s} "
              f"{j['state']:10s} q={fmt(j['quoted_milli'])} s={fmt(j['settled_milli'])} job={j['provider_job_id']}")
    return 0


def cmd_reconcile(a):
    ledger = _ledger()
    rows = [j for j in ledger.jobs() if j["request_key"].startswith(a.key)]
    if len(rows) != 1:
        raise SystemExit("key prefix must match exactly one ledger row")
    j = rows[0]
    if a.attach:
        ledger.set_state(j["request_key"], "submitted", provider_job_id=a.attach, note="attached by a person")
    elif a.release:
        ledger.set_state(j["request_key"], "released", note="released by a person after checking provider history")
    print("updated", j["request_key"][:12])
    return 0


def cmd_export(a):
    from .episodes import Episode
    from .review import export

    export(Episode(a.episode), _ledger(), _cfg())
    return 0


def cmd_schedule(a):
    from .schedule import install, plist

    cfg = _cfg()
    if a.action == "print":
        print("# Manual run first (exactly what the LaunchAgent would run):")
        print(f"cd {paths.ROOT} && {cfg['schedule'].get('python','/usr/bin/python3')} -m gudi daily\n")
        print(plist(cfg))
        return 0
    return install(cfg, a.yes)


def cmd_import(a):
    from .importer import write

    for d in write():
        print(d)
    return 0


def cmd_batch(a):
    from .batch import Batch, approve, quote_rows, run_batch, write_quote_csv

    b = Batch(a.batch_id)
    if a.action == "approve":
        caps = dict(c.split("=", 1) for c in (a.cap or []))
        rec = approve(b, a.by, caps, a.release_start, a.i_have_reviewed)
        print(f"approved {b.id}: {len(rec['episodes'])} episodes, caps {caps}, release from {a.release_start}")
        for s, why in rec["not_approved"].items():
            print(f"  not approved: {s} ({why})")
        return 0
    if a.action in ("plan", "review"):
        os.environ["GUDI_DRY_RUN"] = "1"
        from .weekly import build

        ledger = _ledger()
        bal = {}
        for prov in _cfg()["providers"]:
            r = ledger.last_balance(prov)
            bal[prov] = f"{fmt(r['amount_milli'])} as of {r['as_of'][:10]}" if r else "not recorded"
        out = paths.REVIEW / b.id
        preview = demo = films = None
        if (out / "ep02-preview.mp4").exists():
            preview = {"src": "ep02-preview.mp4", "notes": [
                "Shot-list revision 2 timing with temporary art; the emergence and inscription fixes.",
                "Revision 3 (this week) keeps those fixes and removes every depiction of the linga."]}
        demo_txt = paths.ROOT / "docs" / "BATCH-DEMO-OUTPUT.txt"
        if demo_txt.exists():
            lines = demo_txt.read_text(encoding="utf-8").splitlines()
            demo = [(str(i + 1), l.strip()[6:]) for i, l in enumerate(x for x in lines if x.strip().startswith("PASS:"))]
            rows7 = []
            for l in lines:
                m = re.match(r"\s+(ep\d\d-\S+)\s+(ready for review|waiting|exception|held)\s+(\S+) s \(take (\S+) s\)\s+decode (\S+)\s+corr (\S+)\s+sync (\S+) ms\s+attempts (\d+)", l)
                if m:
                    rows7.append((m.group(1), m.group(2), m.group(3) + " s", m.group(4) + " s", "clean" if m.group(5) == "True" else m.group(5),
                                  f"corr {m.group(6)}, sync {m.group(7)} ms", m.group(8)))
            if rows7:
                films = {"rows": rows7, "video": "rehearsal-ep07.mp4" if (out / "rehearsal-ep07.mp4").exists() else None,
                         "caption": "EP07 as the rehearsal rendered it: real timing, captions and cuts from the shot list; every picture is a "
                                    "MOCK stand-in and the sound is a synthetic take of the script's length. Quarter size. The rehearsal mix is narration only, "
                                    "so the narration match is exact. With a sound bed mixed in, the 0.85 threshold is untested."}
        payload = None
        pt = paths.ROOT / "docs" / "PAYLOAD-TEST.md"
        if pt.exists():
            payload = [l[2:].replace("`", "") for l in pt.read_text(encoding="utf-8").splitlines() if l.startswith("- ")]
            payload += [" | ".join(c.strip().replace("`", "") for c in l.strip("|").split("|")) for l in pt.read_text(encoding="utf-8").splitlines()
                        if l.startswith("| S")]
        page, rows, eps = build(b, out, bal, preview=preview, demo=demo, payload=payload, films=films)
        write_quote_csv(rows, out / f"quote-{b.id}.csv")
        print(f"gudi batch {a.action} {b.id}: DRY RUN")
        for e in eps:
            print(f"  {e['slot']}  {e['slug']:20s} hf {fmt(e['hf']) if e['hf'] else '-':>6s}  el {fmt(e['el']) if e['el'] else '-':>6s}  "
                  f"{e['calls']} calls, {e['waits']} waiting on an exterior photo")
        print(f"  page  {page}\n  quote {out / ('quote-' + b.id + '.csv')}")
        assert "gudi.paid" not in sys.modules
        return 0
    if a.action == "run":
        if not a.live:
            raise SystemExit("batch run needs --live (paid). Use `gudi batch plan` for a dry run.")
        res = run_batch(b, _ledger(), _cfg(), Providers(_mode_for_paid(), _cfg()))
        return 4 if res.get("_") == "locked" else 0
    raise SystemExit("unknown batch action")


def cmd_operator(a):
    import json as _j
    from .providers.operator import box

    if a.action == "list":
        for f in sorted(box("outbox").glob("*.json")):
            if not (box("inbox") / f.name).exists():
                e = _j.loads(f.read_text(encoding="utf-8"))
                print(_j.dumps({"request_key": e["request_key"], "provider": e["provider"], "beat": e["beat"],
                                "asset_type": e["asset_type"], "quote": e["quote"], "payload": e["payload"],
                                "text_path": e["text_path"]}, ensure_ascii=False))
        return 0
    if a.action == "submitted":
        f = box("inbox") / f"{a.key}.json"
        if f.exists():
            raise SystemExit(f"already recorded: {f.read_text()}")
        if not (box("outbox") / f"{a.key}.json").exists():
            raise SystemExit("no such request in the outbox")
        f.write_text(_j.dumps({"job_id": a.value}))
        print("recorded", a.key[:12], "->", a.value)
        return 0
    if a.action == "done":
        rec = {"state": "completed", "url": a.value}
        if a.charged is not None:
            rec["charged"] = a.charged
        (box("done") / f"{a.key}.json").write_text(_j.dumps(rec))
        print("completed", a.key, "->", a.value)
        return 0
    raise SystemExit("unknown operator action")


def cmd_film(a):
    from .episodes import Episode
    from .render import render_and_verify

    r = render_and_verify(Episode(a.episode), _ledger(), _cfg())
    return 0 if r == "ready for review" else 2


def cmd_demo(a):
    from .demo import main as demo

    return demo()


def main(argv=None):
    p = argparse.ArgumentParser(prog="gudi")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import").set_defaults(f=cmd_import)
    q = sub.add_parser("queue")
    q.add_argument("--verbose", action="store_true")
    q.set_defaults(f=cmd_queue)
    r = sub.add_parser("run")
    r.add_argument("--episode", required=True)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--live", action="store_true")
    r.set_defaults(f=cmd_run)
    sub.add_parser("daily").set_defaults(f=cmd_daily)
    ap = sub.add_parser("approve")
    ap.add_argument("episode")
    ap.add_argument("--by", required=True)
    ap.add_argument("--cap", action="append")
    ap.add_argument("--i-have-reviewed", action="store_true")
    ap.set_defaults(f=cmd_approve)
    b = sub.add_parser("balance")
    b.add_argument("action", choices=["record", "show"])
    b.add_argument("provider", nargs="?")
    b.add_argument("amount", nargs="?")
    b.add_argument("--as-of")
    b.add_argument("--source", default="supplied by Karunakar")
    b.set_defaults(f=cmd_balance)
    l = sub.add_parser("ledger")
    l.add_argument("--episode")
    l.set_defaults(f=cmd_ledger)
    rc = sub.add_parser("reconcile")
    rc.add_argument("key")
    rc.add_argument("--attach")
    rc.add_argument("--release", action="store_true")
    rc.set_defaults(f=cmd_reconcile)
    e = sub.add_parser("export")
    e.add_argument("episode")
    e.set_defaults(f=cmd_export)
    s = sub.add_parser("schedule")
    s.add_argument("action", choices=["print", "install"])
    s.add_argument("--yes", action="store_true")
    s.set_defaults(f=cmd_schedule)
    sub.add_parser("demo").set_defaults(f=cmd_demo)
    op = sub.add_parser("operator")
    op.add_argument("action", choices=["list", "submitted", "done"])
    op.add_argument("key", nargs="?", help="request key (submitted) or job id (done)")
    op.add_argument("value", nargs="?", help="job id (submitted) or result URL / file path (done)")
    op.add_argument("--charged")
    op.set_defaults(f=cmd_operator)
    fm = sub.add_parser("film")
    fm.add_argument("episode")
    fm.set_defaults(f=cmd_film)
    bt = sub.add_parser("batch")
    bt.add_argument("action", choices=["plan", "review", "approve", "run"])
    bt.add_argument("batch_id")
    bt.add_argument("--by")
    bt.add_argument("--cap", action="append")
    bt.add_argument("--release-start")
    bt.add_argument("--i-have-reviewed", action="store_true")
    bt.add_argument("--live", action="store_true")
    bt.set_defaults(f=cmd_batch)
    a = p.parse_args(argv)
    return a.f(a)

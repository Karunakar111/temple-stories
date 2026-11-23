"""Mock demonstrations. Each scenario runs the REAL `python3 -m gudi daily` in a child process
against a throwaway sandbox (temp episodes, config, ledger) with the disk-backed mock
provider. No network, no money. Every scenario ends with assertions on the provider's
receipts, the provider's own record of what it charged.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .paths import EPISODES, ROOT

LINE = "-" * 78


def _sandbox(caps=None, episodes=("demo-ep",)):
    t = Path(tempfile.mkdtemp(prefix="gudi-demo-"))
    (t / "config").mkdir()
    (t / "episodes").mkdir()
    cfg = json.loads((ROOT / "config" / "pipeline.json").read_text())
    for prov, (daily, monthly) in (caps or {}).items():
        cfg["providers"][prov]["daily_cap"] = daily
        cfg["providers"][prov]["monthly_cap"] = monthly
    (t / "config" / "pipeline.json").write_text(json.dumps(cfg, indent=1))
    src = EPISODES / "ep02-kolanupaka"
    for slug in episodes:
        d = t / "episodes" / slug
        d.mkdir()
        for f in ("voice.te.txt", "sources.json", "cover.te.txt"):
            shutil.copy2(src / f, d / f)
        meta = json.loads((src / "episode.json").read_text(encoding="utf-8"))
        meta["id"] = slug
        (d / "episode.json").write_text(json.dumps(meta, ensure_ascii=False))
        (d / "reference-board.json").write_text(json.dumps({"references": [
            {"id": "STYLE", "subject": "style", "status": "approved-style"},
            {"id": "REF", "subject": "verified demo reference", "status": "verified"}]}))
        still = lambda beat, q="2": {"provider": "higgsfield", "asset_type": "still", "model": "nano_banana_2",
                                     "quote": q, "settings": {"resolution": "2k"}, "references": ["STYLE"],
                                     "needs": ["REF"], "prompt": f"{slug} {beat} still"}
        shots = {"revision": 1, "narration": [{"beat": "VO", "provider": "elevenlabs", "asset_type": "narration",
                                               "model": "eleven_v4", "quote": "1430", "settings": {"takes": 1},
                                               "needs": [], "prompt": "voice sha"}],
                 "shots": [{"id": "S01", "paid": [still("S01")]},
                           {"id": "S02", "paid": [still("S02"),
                                                  {"provider": "higgsfield", "asset_type": "clip", "model": "kling3_0",
                                                   "quote": "7.5", "settings": {"mode": "pro", "duration": 5},
                                                   "references": ["S02:still"], "needs": ["REF"],
                                                   "after": ["S02:still"], "prompt": f"{slug} S02 clip"}]}]}
        (d / "shots.json").write_text(json.dumps(shots))
    (t / "episodes" / "queue.json").write_text(json.dumps({"order": list(episodes)}))
    return t


def _gudi(t, *args, env=None, background=False):
    e = dict(os.environ, GUDI_ROOT=str(t), GUDI_STATE=str(t / "state"), GUDI_REVIEW=str(t / "review"),
             GUDI_PROVIDER="mock", GUDI_ALLOW_MOCK="1", PYTHONPATH=str(ROOT))
    e.pop("GUDI_MOCK_CRASH", None)
    e.update(env or {})
    cmd = [sys.executable, "-m", "gudi", *args]
    if background:
        return subprocess.Popen(cmd, env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    p = subprocess.run(cmd, env=e, capture_output=True, text=True)
    out = (p.stdout + p.stderr).rstrip()
    print("   $ gudi " + " ".join(args) + "".join(f"   [{k}={v}]" for k, v in (env or {}).items()))
    print("\n".join("     " + l for l in out.splitlines()))
    print(f"     (exit {p.returncode})")
    return p.returncode


def _receipts(t):
    n, credits = 0, {}
    for prov in ("higgsfield", "elevenlabs"):
        f = t / "state" / f"mock-{prov}.json"
        if f.exists():
            r = json.loads(f.read_text())["receipts"]
            n += len(r)
            credits[prov] = sum(float(x["credits"]) for x in r)
    return n, credits


def _approve(t, slug, hf, el):
    _gudi(t, "approve", slug, "--by", "Karunakar (demo)", "--cap", f"higgsfield={hf}", "--cap", f"elevenlabs={el}",
          "--i-have-reviewed")


def _balance(t):
    _gudi(t, "balance", "record", "higgsfield", "356.05", "--source", "demo")
    _gudi(t, "balance", "record", "elevenlabs", "10000", "--source", "demo")


def _check(cond, msg):
    print(f"   {'PASS' if cond else 'FAIL'}: {msg}")
    if not cond:
        raise SystemExit(1)


def main():
    caps = {"higgsfield": ("50", "200"), "elevenlabs": ("3000", "20000")}
    print("gudi demo: mock provider, sandboxed ledger, real runner. Plan per episode: narration 1430 +")
    print("still 2 + still 2 + clip 7.5 (clip waits for its still).")

    print(LINE + "\n1. No approved episode\n")
    t = _sandbox(caps)
    _balance(t)
    code = _gudi(t, "daily")
    _check(code == 0 and _receipts(t)[0] == 0, "exits cleanly with the pending item; 0 paid calls")

    print(LINE + "\n2. Insufficient budget (episode cap 5 credits, plan needs 11.5)\n")
    _approve(t, "demo-ep", "5", "2000")
    code = _gudi(t, "daily")
    _check(code == 3 and _receipts(t)[0] == 0, "held before any reservation; 0 paid calls")
    print("   And with no daily cap configured at all:")
    t2 = _sandbox({})
    _balance(t2)
    _approve(t2, "demo-ep", "50", "2000")
    code = _gudi(t2, "daily")
    _check(code == 3 and _receipts(t2)[0] == 0, "unset caps mean no spending")

    print(LINE + "\n3. Duplicate launch (two runners at once), then a second episode the same day\n")
    t = _sandbox(caps, episodes=("demo-ep", "demo-ep2"))
    _balance(t)
    _approve(t, "demo-ep", "20", "2000")
    _approve(t, "demo-ep2", "20", "2000")
    first = _gudi(t, "daily", env={"GUDI_MOCK_SLOW": "1.5"}, background=True)
    import time

    time.sleep(0.8)
    code = _gudi(t, "daily")
    out = first.communicate()[0]
    print("   (first runner, which held the lock:)\n" + "\n".join("     " + l for l in out.rstrip().splitlines()))
    n, cr = _receipts(t)
    _check(code == 4 and n == 4, f"second launch refused; first runner paid exactly 4 requests {cr}")
    code = _gudi(t, "daily")
    _check(code == 4 and _receipts(t)[0] == 4, "demo-ep2 waits for tomorrow: one episode per day; 0 new paid calls")

    print(LINE + "\n4. Crash right after a submission (before the job id was saved)\n")
    t = _sandbox(caps)
    _balance(t)
    _approve(t, "demo-ep", "20", "2000")
    _gudi(t, "daily", env={"GUDI_MOCK_CRASH": "after-submit:1"})
    _gudi(t, "ledger")
    print("   Resume:")
    _gudi(t, "daily")
    n, cr = _receipts(t)
    _check(n == 4, f"the crashed request was found in provider history, not resubmitted: 4 receipts {cr}")

    print(LINE + "\n5. Crash after submission AND the provider history cannot show the job\n")
    t = _sandbox(caps)
    _balance(t)
    _approve(t, "demo-ep", "20", "2000")
    _gudi(t, "daily", env={"GUDI_MOCK_CRASH": "after-submit:1"})
    code = _gudi(t, "daily", env={"GUDI_MOCK_FORGET": "1"})
    el = json.loads((t / "state" / "mock-elevenlabs.json").read_text())["receipts"]
    _check(code == 5 and len(el) == 1, "narration held as 'unknown' with its reservation and never resent: the provider shows exactly 1 charge for it; the other calls went ahead")
    from .ledger import Ledger

    row = [j for j in Ledger(t / "state" / "ledger.sqlite3").jobs() if j["state"] == "unknown"][0]
    jid = el[0]["job_id"]
    print(f"   A person checks provider history, finds {jid}, and attaches it:")
    _gudi(t, "reconcile", row["request_key"][:12], "--attach", jid)
    _gudi(t, "daily")
    _check(_receipts(t)[0] == 4, "completed with exactly 4 receipts")

    print(LINE + "\n6. Crash after a download, then resume\n")
    t = _sandbox(caps)
    _balance(t)
    _approve(t, "demo-ep", "20", "2000")
    _gudi(t, "daily", env={"GUDI_MOCK_CRASH": "after-download:2"})
    before = _receipts(t)[0]
    _gudi(t, "daily")
    _check(_receipts(t)[0] == 4, f"resume re-fetched the file only; receipts {before} -> 4 (only the never-submitted ones were added)")

    print(LINE + "\n7. Second identical run\n")
    before = _receipts(t)
    _gudi(t, "run", "--episode", "demo-ep", "--live")
    _check(_receipts(t) == before, f"0 new charges; receipts unchanged {before}")

    print(LINE + "\n8. Dry run has no paid access\n")
    code = _gudi(t, "queue")
    probe = subprocess.run([sys.executable, "-c", "import os; os.environ['GUDI_DRY_RUN']='1'; import gudi.paid"],
                           env=dict(os.environ, PYTHONPATH=str(ROOT)), capture_output=True, text=True)
    _check(code == 0 and "ImportError" in probe.stderr and _receipts(t) == before,
           "queue ran without importing gudi.paid; importing it under a dry run raises ImportError")
    print(LINE + "\nAll scenarios passed.")
    return 0

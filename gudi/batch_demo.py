"""Seven-episode weekly batch, rehearsed with mock providers.

Runs the REAL `python3 -m gudi batch ...` commands in child processes against a sandbox copy of
the real EP02-08 folders (real scripts, real shot lists, real quotes). No network, no money.

Sandbox differences from the real repo, all deliberate and printed:
- every reference is marked verified (as if D1/D2 were decided and the exterior picks confirmed);
- EP07 gets a MOCK STAND-IN script and shot list (a copy of EP06) so the week has six runnable
  films; EP08 keeps the real state: no script, so it is the blocked episode.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .paths import EPISODES, ROOT

LINE = "-" * 78
WEEK = "week-1"


def _sandbox():
    t = Path(tempfile.mkdtemp(prefix="gudi-week-"))
    (t / "config").mkdir()
    cfg = json.loads((ROOT / "config" / "pipeline.json").read_text())
    # A batch spends the week's budget in one day, so the daily cap must cover the week.
    cfg["providers"]["higgsfield"].update(daily_cap="400", monthly_cap="1600")
    cfg["providers"]["elevenlabs"].update(daily_cap="8000", monthly_cap="32000")
    (t / "config" / "pipeline.json").write_text(json.dumps(cfg, indent=1))
    shutil.copytree(EPISODES, t / "episodes", ignore=shutil.ignore_patterns("assets", "timing.json", "approval.json", "*.approval.json"))
    for board in (t / "episodes").glob("*/reference-board.json"):
        doc = json.loads(board.read_text(encoding="utf-8"))
        for r in doc.get("references", []):
            if r.get("status") not in ("approved-style",):
                r["status"] = "verified"
        board.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    src, dst = t / "episodes" / "ep06-kanipakam", t / "episodes" / "ep07-puri"
    for f in ("voice.te.txt", "shots.json", "reference-board.json", "sources.json", "cover.te.txt", "directions.json"):
        if (src / f).exists():
            shutil.copy2(src / f, dst / f)
    meta = json.loads((dst / "episode.json").read_text(encoding="utf-8"))
    meta["status"] = "MOCK STAND-IN (copy of EP06) for the rehearsal only"
    (dst / "episode.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return t


def _env(t, extra=None):
    e = dict(os.environ, GUDI_ROOT=str(t), GUDI_STATE=str(t / "state"), GUDI_REVIEW=str(t / "review"),
             GUDI_PROVIDER="mock", GUDI_ALLOW_MOCK="1", PYTHONPATH=str(ROOT))
    for k in ("GUDI_MOCK_CRASH", "GUDI_MOCK_SLOW", "GUDI_MOCK_FORGET", "GUDI_DRY_RUN"):
        e.pop(k, None)
    e.update(extra or {})
    return e


def _show(args, out, code, extra=None, keep=None):
    print("   $ gudi " + " ".join(args) + "".join(f"   [{k}={v}]" for k, v in (extra or {}).items()))
    lines = out.rstrip().splitlines()
    if keep:
        lines = [l for l in lines if keep(l)]
    print("\n".join("     " + l for l in lines))
    print(f"     (exit {code})")


def _gudi(t, *args, env=None, keep=None):
    p = subprocess.run([sys.executable, "-m", "gudi", *args], env=_env(t, env), capture_output=True, text=True)
    _show(args, p.stdout + p.stderr, p.returncode, env, keep)
    return p.returncode


def _receipts(t):
    out = {}
    for prov in ("higgsfield", "elevenlabs"):
        f = t / "state" / f"mock-{prov}.json"
        out[prov] = json.loads(f.read_text())["receipts"] if f.exists() else []
    return out


def _jobs(t):
    s = {}
    for prov in ("higgsfield", "elevenlabs"):
        f = t / "state" / f"mock-{prov}.json"
        if f.exists():
            for jid, j in json.loads(f.read_text())["jobs"].items():
                s[jid] = j["request_key"]
    return s


def _summary(t):
    r = _receipts(t)
    n = sum(len(v) for v in r.values())
    cr = {k: round(sum(float(x["credits"]) for x in v), 2) for k, v in r.items()}
    return n, cr


def _dupes(t):
    keys = list(_jobs(t).values())
    return len(keys) - len(set(keys))


def _planned(t):
    sys.path.insert(0, str(ROOT))
    total = 0
    for slug in json.loads((t / "episodes" / "batches" / f"{WEEK}.json").read_text())["episodes"]:
        d = t / "episodes" / slug
        if not (d / "voice.te.txt").exists() or not (d / "shots.json").exists():
            continue
        shots = json.loads((d / "shots.json").read_text(encoding="utf-8"))
        total += len(shots.get("narration", [])) + sum(len(s["paid"]) for s in shots["shots"])
    return total


def _check(cond, msg):
    print(f"   {'PASS' if cond else 'FAIL'}: {msg}")
    if not cond:
        raise SystemExit(1)


def _brief(l):
    return not l.startswith(("  reserve", "  submit", "  saved", "  wait")) or "S01" in l


def main():
    t = _sandbox()
    planned = _planned(t)
    print(f"gudi batch rehearsal: sandbox {t}")
    print("Real EP02-06 scripts and shot lists; EP07 = MOCK STAND-IN (copy of EP06); EP08 = no script (blocked).")
    print(f"Planned paid calls for the six runnable films: {planned}.")

    print(LINE + "\n1. One approval for the week (scripts + visual approach + caps)\n")
    _gudi(t, "balance", "record", "higgsfield", "1000", "--source", "demo")
    _gudi(t, "balance", "record", "elevenlabs", "20000", "--source", "demo")
    _gudi(t, "batch", "approve", WEEK, "--by", "Karunakar (demo)", "--cap", "higgsfield=400", "--cap", "elevenlabs=8000",
          "--release-start", "2026-11-26", "--i-have-reviewed")
    appr = json.loads((t / "episodes" / "batches" / f"{WEEK}.approval.json").read_text())
    _check(len(appr["episodes"]) == 6 and list(appr["not_approved"]) == ["ep08-bhadrachalam"],
           "six films approved in one step; EP08 listed as not approved (no script)")

    print(LINE + "\n2. Duplicate launch, then the first run is killed mid-batch\n")
    slow = {"GUDI_MOCK_SLOW": "0.15"}
    first = subprocess.Popen([sys.executable, "-m", "gudi", "batch", "run", WEEK, "--live"], env=_env(t, slow),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(2.0)
    code = _gudi(t, "batch", "run", WEEK, "--live")
    _check(code == 4, "second launch refused while the first holds the runner lock")
    time.sleep(4.0)
    first.send_signal(signal.SIGKILL)
    out = first.communicate()[0]
    _show(["batch", "run", WEEK, "--live"], out + "\n   !! process killed (SIGKILL) mid-run", -9, slow, keep=_brief)
    n1, cr1 = _summary(t)
    _check(0 < n1 < planned and _dupes(t) == 0, f"interrupted after {n1} of {planned} paid calls {cr1}; no request submitted twice")

    print(LINE + "\n3. Restart the same day\n")
    _gudi(t, "batch", "run", WEEK, "--live", keep=_brief)
    n2, cr2 = _summary(t)
    _check(n2 == planned and _dupes(t) == 0,
           f"all {planned} planned calls charged exactly once {cr2}; EP08 held, the other six finished")

    print(LINE + "\n4. Run the whole week again\n")
    _gudi(t, "batch", "run", WEEK, "--live", keep=lambda l: "new paid" in l or l.startswith(("BATCH", "  ep", "[", "HOLD")))
    _check(_summary(t) == (n2, cr2), f"0 new charges; receipts unchanged at {n2}")

    print(LINE + "\n5. What the restart did with clips and release dates\n")
    for slug in appr["episodes"]:
        tm = json.loads((t / "episodes" / slug / "timing.json").read_text())
        rv = sorted((t / "review" / slug).glob("*/*.json"))
        rel = None
        for f in rv:
            try:
                rel = json.loads(f.read_text()).get("planned_release") or rel
            except Exception:
                pass
        print(f"   {slug:20s} timing from: {tm['source']}; clips {len(tm['clips'])}; release {rel}")
    print(LINE + "\nAll batch scenarios passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""The seven-film week, rehearsed end to end with mock providers and real renders.

Runs the REAL `python3 -m gudi batch ...` commands in child processes against a sandbox copy of
the real EP02-08 folders (real scripts, shot lists, references and quotes). The mock provider
returns playable media (GUDI_MOCK_MEDIA=1): marked MOCK stills, short clips, and a take-shaped
narration as long as each script. Every film is rendered by Remotion and checked by the same
gate as production. No network, no money.

Sandbox differences from the real repo, all deliberate and printed:
- identified exteriors get stand-in media ids (mock-media-...), except Yadagirigutta's hill,
  left unresolved so EP05 shows an episode waiting on a reference while the others finish;
- renders at quarter size (270x480) to keep the rehearsal short; production renders 1080x1920.
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
UNRESOLVED = ("ep05-yadagirigutta", "Y-HILL")
FAULT = "ep04-srikalahasti"


def _sandbox():
    t = Path(tempfile.mkdtemp(prefix="gudi-week-"))
    (t / "config").mkdir()
    cfg = json.loads((ROOT / "config" / "pipeline.json").read_text())
    # A batch spends the week's budget in one day, so the daily cap must cover the week.
    cfg["providers"]["higgsfield"].update(daily_cap="500", monthly_cap="2000")
    cfg["providers"]["elevenlabs"].update(daily_cap="9000", monthly_cap="36000")
    cfg["render"] = {"scale": 0.25, "label": "MOCK ASSETS · rehearsal"}
    (t / "config" / "pipeline.json").write_text(json.dumps(cfg, indent=1))
    shutil.copy2(ROOT / "config" / "production.json", t / "config" / "production.json")
    shutil.copytree(EPISODES, t / "episodes", ignore=shutil.ignore_patterns("assets", "timing.json", "approval.json", "*.approval.json"))
    for board in (t / "episodes").glob("*/reference-board.json"):
        doc = json.loads(board.read_text(encoding="utf-8"))
        for r in doc.get("references", []):
            if r.get("status") == "needs photo" and (board.parent.name, r["id"]) != UNRESOLVED:
                r["media_id"] = f"mock-media-{r['id'].lower()}"
        board.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return t


def _env(t, extra=None):
    e = dict(os.environ, GUDI_ROOT=str(t), GUDI_STATE=str(t / "state"), GUDI_REVIEW=str(t / "review"),
             GUDI_PROVIDER="mock", GUDI_ALLOW_MOCK="1", GUDI_MOCK_MEDIA="1", PYTHONPATH=str(ROOT))
    for k in ("GUDI_MOCK_CRASH", "GUDI_MOCK_SLOW", "GUDI_MOCK_FORGET", "GUDI_DRY_RUN", "GUDI_RENDER_FAULT"):
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


def _state(t, prov):
    f = t / "state" / f"mock-{prov}.json"
    return json.loads(f.read_text()) if f.exists() else {"receipts": [], "jobs": {}}


def _summary(t):
    r = {p: _state(t, p)["receipts"] for p in ("higgsfield", "elevenlabs")}
    n = sum(len(v) for v in r.values())
    cr = {k: round(sum(float(x["credits"]) for x in v), 2) for k, v in r.items()}
    return n, cr


def _dupes(t):
    keys = [j["request_key"] for p in ("higgsfield", "elevenlabs") for j in _state(t, p)["jobs"].values()]
    return len(keys) - len(set(keys))


def _films(t):
    import sqlite3

    db = sqlite3.connect(t / "state" / "ledger.sqlite3")
    db.row_factory = sqlite3.Row
    return {r["episode"]: dict(r) for r in db.execute("SELECT * FROM films")}


def _brief(l):
    if l.startswith(("  reserve", "  submit", "  saved", "  wait")):
        return " S01:" in l
    if l.startswith("  hold   "):
        return "reference media" in l
    return True


def main():
    started = time.monotonic()
    t = _sandbox()
    print(f"gudi week rehearsal: sandbox {t}")
    print("Real EP02-08 scripts, shot lists and quotes. Mock media; quarter-size renders.")
    print(f"Left unresolved on purpose: {UNRESOLVED[1]} in {UNRESOLVED[0]}. Damaged first export on purpose: {FAULT}.")

    print(LINE + "\n1. One approval for the week (scripts + visual approach + caps)\n")
    _gudi(t, "balance", "record", "higgsfield", "1000", "--source", "demo")
    _gudi(t, "balance", "record", "elevenlabs", "20000", "--source", "demo")
    _gudi(t, "batch", "approve", WEEK, "--by", "Karunakar (demo)", "--cap", "higgsfield=500", "--cap", "elevenlabs=9000",
          "--release-start", "2026-11-26", "--i-have-reviewed")
    appr = json.loads((t / "episodes" / "batches" / f"{WEEK}.approval.json").read_text())
    ok = len(appr["episodes"]) == 7 and not appr["not_approved"]
    print(f"   {'PASS' if ok else 'FAIL'}: all seven real scripts approved in one step")
    if not ok:
        return 1

    print(LINE + "\n2. Duplicate launch, then the first run is killed mid-batch\n")
    slow = {"GUDI_MOCK_SLOW": "0.1"}
    first = subprocess.Popen([sys.executable, "-m", "gudi", "batch", "run", WEEK, "--live"], env=_env(t, slow),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(3.0)
    code = _gudi(t, "batch", "run", WEEK, "--live")
    ok2 = code == 4
    print(f"   {'PASS' if ok2 else 'FAIL'}: second launch refused while the first holds the runner lock")
    time.sleep(4.0)
    first.send_signal(signal.SIGKILL)
    out = first.communicate()[0]
    _show(["batch", "run", WEEK, "--live"], out + "\n   !! process killed (SIGKILL) mid-run", -9, slow, keep=_brief)
    n1, cr1 = _summary(t)
    ok3 = n1 > 0 and _dupes(t) == 0
    print(f"   {'PASS' if ok3 else 'FAIL'}: interrupted after {n1} paid calls {cr1}; no request submitted twice")

    print(LINE + "\n3. Restart the same day: assets, renders and the export check\n")
    r0 = time.monotonic()
    _gudi(t, "batch", "run", WEEK, "--live", env={"GUDI_RENDER_FAULT": f"{FAULT}:truncate"}, keep=_brief)
    render_wall = time.monotonic() - r0
    n2, cr2 = _summary(t)
    films = _films(t)
    ready = sorted(e for e, f in films.items() if f["status"] == "ready for review")
    ok4 = _dupes(t) == 0 and len(ready) == 6 and films.get(UNRESOLVED[0], {}).get("status") != "ready for review"
    print(f"   {'PASS' if ok4 else 'FAIL'}: {n2} paid calls, each charged once {cr2}; six films ready, "
          f"{UNRESOLVED[0]} not ready (waiting on {UNRESOLVED[1]})")
    f4 = films.get(FAULT, {})
    ok5 = f4.get("status") == "ready for review" and (f4.get("attempts") or 0) == 2
    print(f"   {'PASS' if ok5 else 'FAIL'}: {FAULT}'s damaged first export failed the check and passed after one free re-render")

    print(LINE + "\n4. What was actually sent: every image and clip request carries real media ids\n")
    bad, n_still, n_clip = [], 0, 0
    for rc in _state(t, "higgsfield")["receipts"]:
        ms = (rc.get("payload") or {}).get("medias", [])
        if rc["asset_type"] == "clip":
            n_clip += 1
            if len(ms) != 1 or ms[0]["role"] != "start_image":
                bad.append(rc["beat"])
        else:
            n_still += 1
            if not ms or any(m["role"] != "image_references" for m in ms):
                bad.append(rc["beat"])
        if any(":" in m["value"] or m["value"].startswith(("<", "http")) for m in ms):
            bad.append(rc["beat"])
    sample = next(rc for rc in _state(t, "higgsfield")["receipts"] if rc["asset_type"] == "clip")
    print("   sample clip payload: " + json.dumps({k: v for k, v in sample["payload"].items() if k != "prompt"}))
    ok6 = not bad
    print(f"   {'PASS' if ok6 else 'FAIL'}: {n_still} still and {n_clip} clip requests; every reference sent as an id with its role {bad or ''}")

    print(LINE + "\n5. Run the whole week again\n")
    _gudi(t, "batch", "run", WEEK, "--live", keep=lambda l: "new paid" in l or "film" in l or l.startswith(("BATCH", "  ep")))
    ok7 = _summary(t) == (n2, cr2)
    print(f"   {'PASS' if ok7 else 'FAIL'}: 0 new charges; verified films not re-rendered")

    print(LINE + f"\n6. The missing reference arrives for {UNRESOLVED[0]} (no new approval needed)\n")
    bf = t / "episodes" / UNRESOLVED[0] / "reference-board.json"
    doc = json.loads(bf.read_text(encoding="utf-8"))
    for r in doc["references"]:
        if r["id"] == UNRESOLVED[1]:
            r["media_id"] = "mock-media-y-hill"
    bf.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    _gudi(t, "batch", "run", WEEK, "--live", keep=lambda l: "new paid" in l or "film" in l or l.startswith(("BATCH", "  ep", "HOLD")))
    n3, cr3 = _summary(t)
    films = _films(t)
    ok8 = films[UNRESOLVED[0]]["status"] == "ready for review" and _dupes(t) == 0 and n3 > n2
    print(f"   {'PASS' if ok8 else 'FAIL'}: {UNRESOLVED[0]} finished ({n3 - n2} new calls, all its own); seven films ready; no duplicates")

    print(LINE + "\n7. The seven films\n")
    for e, f in sorted(films.items()):
        c = json.loads(f["checks_json"] or "{}")
        print(f"   {e:20s} {f['status']:17s} {c.get('duration_s')} s (take {c.get('narration_s')} s)  decode {c.get('full_decode')}  "
              f"corr {c.get('narration_corr')}  sync {c.get('sync_offset_ms')} ms  attempts {f['attempts']}")
    out_dir = ROOT / "exports" / "rehearsal"
    out_dir.mkdir(parents=True, exist_ok=True)
    for e, f in films.items():
        shutil.copy2(f["mp4"], out_dir / f"{e}-mock.mp4")
    print(f"\n   Machine wall time: {time.monotonic() - started:.0f} s total; step 3 (assets + renders + checks) {render_wall:.0f} s.")
    allok = all([ok, ok2, ok3, ok4, ok5, ok6, ok7, ok8])
    print(LINE + ("\nAll week scenarios passed." if allok else "\nSOME SCENARIOS FAILED."))
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())

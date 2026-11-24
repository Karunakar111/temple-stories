"""EP02 dress rehearsal of the attended live path, zero spend.

The real runner runs EP02 with the operator provider (reserve -> outbox -> inbox -> done ->
download), against a sandbox copy. This script plays the operator: for each request it makes
stand-in media (marked MOCK) and records a job id and result, exactly as the live session will
with Higgsfield and ElevenLabs. Then the film is built and checked (captions, SRT, cover, mix).

python3 -m gudi.operator_rehearsal [--scale 1.0]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .paths import EPISODES, ROOT

EP = "ep02-kolanupaka"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    a = ap.parse_args()
    t = Path(tempfile.mkdtemp(prefix="gudi-op-"))
    (t / "config").mkdir()
    cfg = json.loads((ROOT / "config" / "pipeline.json").read_text())
    cfg["providers"]["higgsfield"].update(daily_cap="69", monthly_cap="69")
    cfg["providers"]["elevenlabs"].update(daily_cap="1430", monthly_cap="1430")
    cfg["render"] = {"scale": a.scale, "label": "REHEARSAL · mock pictures and voice"}
    (t / "config" / "pipeline.json").write_text(json.dumps(cfg, indent=1))
    shutil.copy2(ROOT / "config" / "production.json", t / "config" / "production.json")
    (t / "episodes").mkdir()
    shutil.copytree(EPISODES / EP, t / "episodes" / EP, ignore=shutil.ignore_patterns("assets", "timing.json", "approval.json"))
    bf = t / "episodes" / EP / "reference-board.json"
    b = json.loads(bf.read_text(encoding="utf-8"))
    for r in b["references"]:
        if r["id"] == "K-EXTERIOR":
            r["media_id"] = "mock-media-k-exterior"  # stands in for the approved exterior photo
    bf.write_text(json.dumps(b, ensure_ascii=False, indent=1), encoding="utf-8")
    env = dict(os.environ, GUDI_ROOT=str(t), GUDI_STATE=str(t / "state"), GUDI_REVIEW=str(t / "review"),
               GUDI_PROVIDER="operator", GUDI_OPERATOR_WAIT="120", PYTHONPATH=str(ROOT))
    for k in ("GUDI_MOCK_MEDIA", "GUDI_DRY_RUN", "GUDI_ALLOW_MOCK"):
        env.pop(k, None)

    def g(*args):
        p = subprocess.run([sys.executable, "-m", "gudi", *args], env=env, capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    print(g("balance", "record", "higgsfield", "356.05", "--source", "rehearsal")[1].strip())
    print(g("balance", "record", "elevenlabs", "20000", "--source", "rehearsal (stand-in balance)")[1].strip())
    print(g("approve", EP, "--by", "rehearsal", "--cap", "higgsfield=69", "--cap", "elevenlabs=1430", "--i-have-reviewed")[1].strip())

    runner = subprocess.Popen([sys.executable, "-m", "gudi", "run", "--episode", EP, "--live"], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    sys.path.insert(0, str(ROOT))
    os.environ.update({"GUDI_ROOT": str(t), "GUDI_STATE": str(t / "state")})
    from .providers.mock_media import make

    ob, ib, done = (t / "state" / "operator" / n for n in ("outbox", "inbox", "done"))
    media = t / "operator-media"
    media.mkdir()
    answered, n = set(), 0
    sent = []
    while runner.poll() is None:
        for f in sorted(ob.glob("*.json")) if ob.exists() else []:
            if f.name in answered:
                continue
            e = json.loads(f.read_text(encoding="utf-8"))
            n += 1
            jid = f"op-{e['provider'][:2]}-{n:03d}"
            ext = {"still": "png", "clip": "mp4", "narration": "mp3"}[e["asset_type"]]
            out = media / f"{jid}.{ext}"
            job = {"asset_type": e["asset_type"], "beat": e["beat"], "text_path": e["text_path"],
                   "duration": (e["payload"] or {}).get("duration")}
            make(job, jid, out)
            ib.mkdir(parents=True, exist_ok=True)
            done.mkdir(parents=True, exist_ok=True)
            (ib / f.name).write_text(json.dumps({"job_id": jid}))
            (done / f"{jid}.json").write_text(json.dumps({"state": "completed", "url": str(out)}))
            sent.append({"beat": e["beat"], "asset": e["asset_type"], "job": jid,
                         "medias": [m["value"] for m in (e["payload"] or {}).get("medias", [])]})
            answered.add(f.name)
        time.sleep(0.5)
    run_log = runner.communicate()[0]
    print(run_log.strip().splitlines()[-1] if run_log.strip() else "")
    code, film_log = g("film", EP)
    print(film_log.strip())
    outd = t / "exports" / "films" / EP
    dst = ROOT / "exports" / "rehearsal"
    dst.mkdir(parents=True, exist_ok=True)
    for f in outd.glob(f"{EP}*"):
        shutil.copy2(f, dst / f.name.replace(EP, "ep02-operator-rehearsal"))
    (dst / "ep02-operator-rehearsal.sent.json").write_text(json.dumps(sent, indent=1))
    print(json.dumps({"requests_answered": n, "film_exit": code, "sandbox": str(t)}))
    return code


if __name__ == "__main__":
    sys.exit(main())

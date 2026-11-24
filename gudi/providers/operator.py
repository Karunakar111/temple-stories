"""Operator provider: for attended live runs, a person or an assistant session submits each
request with its own connector, and the runner keeps every safeguard.

The runner still reserves first, commits `submitting` before the request leaves, refuses
unresolved media ids, and records job ids, results and downloads in the one ledger. Only the
submission itself happens outside this process:

  state/operator/outbox/<request_key>.json   written by the runner: the exact payload to send
  state/operator/inbox/<request_key>.json    written after submitting: {"job_id": ...}
  state/operator/done/<job_id>.json          written when finished: {"state": "completed", "url": ...}
                                             (url: https URL, or a local file path for a take)

`python3 -m gudi operator list|submitted|done` reads and writes these files.
A request is never sent twice: the outbox entry has one inbox answer; a resumed run finds it.
"""
import json
import os
import shutil
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ..money import to_milli
from ..paths import ensure_state
from . import Provider


def box(name):
    d = ensure_state() / "operator" / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def _wait(path, seconds):
    end = time.monotonic() + seconds
    while True:  # always look at least once, even with a zero wait
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        if time.monotonic() >= end:
            return None
        time.sleep(2)


class OperatorProvider(Provider):
    def __init__(self, name):
        self.name = name
        self.wait_s = float(os.environ.get("GUDI_OPERATOR_WAIT", "1800"))
        self.status_wait_s = float(os.environ.get("GUDI_OPERATOR_STATUS_WAIT", str(self.wait_s)))
        self.only = os.environ.get("GUDI_OPERATOR_ONLY")  # e.g. "higgsfield": other providers wait without blocking

    def quote_milli(self, call):
        return to_milli(call["quote"])

    def submit(self, call, request_key, payload=None):
        entry = {"request_key": request_key, "provider": self.name, "beat": call["beat"], "asset_type": call["asset_type"],
                 "quote": call["quote"], "payload": payload, "text_path": call.get("text_path"),
                 "written": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        (box("outbox") / f"{request_key}.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
        wait = 0 if (self.only and self.only != self.name) else self.wait_s
        got = _wait(box("inbox") / f"{request_key}.json", wait)
        if not got:
            raise TimeoutError(f"no submission recorded for {call['beat']} {call['asset_type']}; the request stays unsent or unknown, never resent")
        return got["job_id"]

    def status(self, job_id):
        got = _wait(box("done") / f"{job_id}.json", self.status_wait_s)
        if not got:
            return {"state": "pending", "url": None, "charged_milli": None}
        return {"state": got.get("state", "completed"), "url": got.get("url"),
                "charged_milli": to_milli(got["charged"]) if got.get("charged") is not None else None}

    def find(self, call, request_key, since_iso):
        f = box("inbox") / f"{request_key}.json"
        return json.loads(f.read_text(encoding="utf-8"))["job_id"] if f.exists() else None

    def download(self, job_id, url, dest):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if url and url.startswith("http"):
            with urllib.request.urlopen(url, timeout=600) as r:
                dest.write_bytes(r.read())
        else:
            shutil.copy2(url, dest)
            side = Path(str(url) + ".alignment.json")
            if side.exists():
                shutil.copy2(side, Path(str(dest) + ".alignment.json"))
        if dest.stat().st_size < 2000:
            raise RuntimeError(f"download for {job_id} is only {dest.stat().st_size} bytes")
        return dest

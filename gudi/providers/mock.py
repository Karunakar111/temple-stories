"""A disk-backed mock provider for demonstrations and tests.

It keeps its own "receipts" (every charge it would have made) in a JSON file, so a crash in
one process and a resume in another can be checked against the provider's side of the books.
Crash injection (environment):
  GUDI_MOCK_CRASH=after-submit:N    die right after the Nth submit returns, before the id is saved
  GUDI_MOCK_CRASH=after-download:N  die right after the Nth download, before the ledger update
"""
import json
import os
import time
from pathlib import Path

from ..money import to_milli
from . import Provider


class MockProvider(Provider):
    is_paid = True

    def __init__(self, name, state_path):
        self.name = name
        self.path = Path(state_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self.path.exists():
            return json.loads(self.path.read_text())
        return {"jobs": {}, "receipts": [], "counter": 0, "submits": 0, "downloads": 0}

    def _save(self, s):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(s, indent=1))
        os.replace(tmp, self.path)

    def receipts(self):
        return self._load()["receipts"]

    def quote_milli(self, call):
        return to_milli(call["quote"])

    def _maybe_crash(self, stage, n):
        spec = os.environ.get("GUDI_MOCK_CRASH", "")
        if spec == f"{stage}:{n}":
            print(f"   !! simulated crash {stage} #{n} (process killed)", flush=True)
            os._exit(137)

    def submit(self, call, request_key, payload=None):
        s = self._load()
        s["counter"] += 1
        s["submits"] += 1
        job_id = f"mock-{self.name}-{s['counter']:04d}"
        s["jobs"][job_id] = {
            "request_key": request_key,
            "prompt": call.get("prompt", ""),
            "created": time.time(),
            "state": "completed",
            "url": f"mock://{job_id}.bin",
            "asset_type": call["asset_type"], "beat": call["beat"],
            "duration": call.get("settings", {}).get("duration"), "text_path": call.get("text_path"),
        }
        s["receipts"].append({"job_id": job_id, "credits": call["quote"], "beat": call["beat"],
                              "asset_type": call["asset_type"], "payload": payload})
        self._save(s)
        if os.environ.get("GUDI_MOCK_SLOW"):
            time.sleep(float(os.environ["GUDI_MOCK_SLOW"]))
        self._maybe_crash("after-submit", s["submits"])
        return job_id

    def status(self, job_id):
        j = self._load()["jobs"].get(job_id)
        if not j:
            return {"state": "missing", "url": None, "charged_milli": None}
        s = self._load()
        charged = sum(to_milli(r["credits"]) for r in s["receipts"] if r["job_id"] == job_id)
        return {"state": j["state"], "url": j["url"], "charged_milli": charged}

    def find(self, call, request_key, since_iso):
        # the mock can match on the request key; the live adapters match prompt + model + time
        if os.environ.get("GUDI_MOCK_FORGET") == "1":
            return None  # simulate a provider history that does not show the job
        for jid, j in self._load()["jobs"].items():
            if j["request_key"] == request_key:
                return jid
        return None

    def download(self, job_id, url, dest):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        j = self._load()["jobs"].get(job_id, {})
        if os.environ.get("GUDI_MOCK_MEDIA") == "1" and j.get("asset_type"):
            from .mock_media import make
            make(j, job_id, dest)
        else:
            dest.write_bytes(f"{job_id}\n".encode())
        s = self._load()
        s["downloads"] += 1
        self._save(s)
        self._maybe_crash("after-download", s["downloads"])
        return dest

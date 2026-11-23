"""ElevenLabs narration: one take per request through the API, recovered through Speech History
with the existing scripts/fetch-narration.sh (the Flows endpoint is gated on this plan).

NOT YET EXERCISED LIVE. The key is read from .env.local (gitignored) and never printed.
"""
import json
import subprocess
import urllib.request
from pathlib import Path

from ..money import to_milli
from ..paths import ROOT
from ..providers import Provider


def _key():
    for line in (ROOT / ".env.local").read_text().splitlines():
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("ELEVENLABS_API_KEY not found in .env.local")


class ElevenLabsTTS(Provider):
    name = "elevenlabs"

    def __init__(self, cfg):
        self.voice = json.loads((ROOT / "config" / "production.json").read_text())["voice"]
        self._last = {}

    def quote_milli(self, call):
        return to_milli(call["quote"])

    def submit(self, call, request_key):
        text = (ROOT / call["text_path"]).read_text(encoding="utf-8")
        body = json.dumps({"text": text, "model_id": self.voice["model"]}).encode("utf-8")
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice['voiceId']}?output_format=mp3_44100_128",
            data=body, method="POST",
            headers={"xi-api-key": _key(), "Content-Type": "application/json", "Accept": "audio/mpeg"},
        )
        with urllib.request.urlopen(req, timeout=600) as r:
            hid = r.headers.get("history-item-id")
            audio = r.read()
        if not hid:
            raise RuntimeError("no history-item-id header; reconcile via Speech History before resubmitting")
        self._last[hid] = audio
        return hid

    def status(self, job_id):
        return {"state": "completed", "url": f"history:{job_id}", "charged_milli": None}

    def find(self, call, request_key, since_iso):
        return None  # resolved by a person with `sh scripts/fetch-narration.sh` (lists recent items)

    def download(self, job_id, url, dest):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if job_id in self._last:
            dest.write_bytes(self._last.pop(job_id))
            return dest
        subprocess.run(["sh", "scripts/fetch-narration.sh", job_id, str(dest)], cwd=str(ROOT), check=True)
        return dest

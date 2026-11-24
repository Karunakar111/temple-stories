"""ElevenLabs narration: exactly one take per request, identified through Speech History.

- One REST call to /v1/text-to-speech/{voice}/with-timestamps is one take; it also returns the
  start and end time of every character, saved next to the take as <take>.alignment.json for
  phrase-level captions. If the model returns no alignment, captions fall back to the take's
  pauses (gudi/captions.py), at no cost. (The chat connector's creative_generate_speech
  defaults to generations_count 2 and charges per take; this adapter never uses it.)
- The documented REST response carries no history-item id we rely on. After the call, and on any
  resume, the take is identified in Speech History by voice, model, exact text and time window.
- find() is the same lookup, so a crash between the call and the ledger update reconciles
  without a second take.

NOT YET EXERCISED LIVE. The key is read from .env.local (gitignored) and never printed.
"""
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

from ..money import to_milli
from ..paths import ROOT
from ..providers import Provider

API = "https://api.elevenlabs.io/v1"


def _key():
    for line in (ROOT / ".env.local").read_text().splitlines():
        if line.startswith("ELEVENLABS_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise RuntimeError("ELEVENLABS_API_KEY not found in .env.local")


def _get(path, params=None, raw=False):
    url = f"{API}{path}" + (("?" + urllib.parse.urlencode(params)) if params else "")
    req = urllib.request.Request(url, headers={"xi-api-key": _key()})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    return data if raw else json.loads(data)


class ElevenLabsTTS(Provider):
    name = "elevenlabs"

    def __init__(self, cfg):
        self.voice = json.loads((ROOT / "config" / "production.json").read_text())["voice"]
        self._audio = {}

    def quote_milli(self, call):
        return to_milli(call["quote"])

    def _text(self, call):
        return (ROOT / call["text_path"]).read_text(encoding="utf-8")

    def _lookup(self, text, since_unix):
        """Newest Speech History item with this voice, model and exact text, made after since_unix."""
        items = _get("/history", {"page_size": 50, "voice_id": self.voice["voiceId"]}).get("history", [])
        hits = [h for h in items
                if h.get("text", "").strip() == text.strip()
                and h.get("model_id") in (None, self.voice["model"])
                and int(h.get("date_unix", 0)) >= since_unix - 5]
        if len(hits) > 1:
            raise RuntimeError(f"{len(hits)} matching takes in Speech History; a person must pick one (gudi reconcile)")
        return hits[0]["history_item_id"] if hits else None

    def submit(self, call, request_key, payload=None):
        if call.get("settings", {}).get("takes", 1) != 1:
            raise RuntimeError("narration is pinned to one take")
        text = self._text(call)
        since = int(time.time())
        body = json.dumps({"text": text, "model_id": self.voice["model"]}).encode("utf-8")
        req = urllib.request.Request(
            f"{API}/text-to-speech/{self.voice['voiceId']}/with-timestamps?output_format=mp3_44100_128",
            data=body, method="POST",
            headers={"xi-api-key": _key(), "Content-Type": "application/json", "Accept": "application/json"},
        )
        import base64
        import urllib.error
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                resp = json.loads(r.read())
            audio = base64.b64decode(resp["audio_base64"])
            self._alignment = resp.get("alignment")
        except urllib.error.HTTPError as e:
            if not (400 <= e.code < 500) or e.code in (401, 402, 429):
                raise  # not a validation refusal: stop, never resend blindly
            # the model refused timestamps before generating anything: one plain take instead
            plain = urllib.request.Request(
                f"{API}/text-to-speech/{self.voice['voiceId']}?output_format=mp3_44100_128", data=body, method="POST",
                headers={"xi-api-key": _key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
            with urllib.request.urlopen(plain, timeout=600) as r:
                audio = r.read()
            self._alignment = None
        for _ in range(6):  # history can lag the response by a few seconds
            hid = self._lookup(text, since)
            if hid:
                self._audio[hid] = audio
                return hid
            time.sleep(5)
        raise RuntimeError("take made but not yet visible in Speech History; held for `gudi reconcile` (never resent)")

    def status(self, job_id):
        return {"state": "completed", "url": f"history:{job_id}", "charged_milli": None}

    def find(self, call, request_key, since_iso):
        since = int(datetime.fromisoformat(since_iso).timestamp())
        return self._lookup(self._text(call), since)

    def download(self, job_id, url, dest):
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        data = self._audio.pop(job_id, None) or _get(f"/history/{job_id}/audio", raw=True)
        if len(data) < 2000:
            raise RuntimeError(f"history audio for {job_id} is only {len(data)} bytes")
        dest.write_bytes(data)
        al = getattr(self, "_alignment", None)
        if al:
            Path(str(dest) + ".alignment.json").write_text(json.dumps(al, ensure_ascii=False), encoding="utf-8")
        return dest

"""One narration take, reused whenever it already exists. Run on the machine that holds the
ElevenLabs key (the Mac).

python3 -m gudi.paid.tts_once <text_path> <out.mp3>

Order, so a take is never paid for twice:
  1. <out.mp3> already on disk          -> reuse it, no request.
  2. Speech History has this exact text -> download that take, no request.
     (same voice and model; more than one match stops for a person to choose)
  3. otherwise one take via /with-timestamps (character timings saved next to it);
     the audio is written to disk before anything else.
  4. if that request errors, Speech History is checked again before stopping;
     nothing is ever resent automatically.
Prints one JSON line. The key is read from .env.local and never printed.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

from ..paths import ROOT
from .elevenlabs import ElevenLabsTTS, _get


def _save_history(hid, dest):
    data = _get(f"/history/{hid}/audio", raw=True)
    if len(data) < 2000:
        raise RuntimeError(f"history audio for {hid} is only {len(data)} bytes")
    dest.write_bytes(data)
    return len(data)


def _out(**kw):
    print(json.dumps(kw, ensure_ascii=False))


def main(text_path, out):
    dest = Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    side = Path(str(dest) + ".alignment.json")
    if dest.exists() and dest.stat().st_size > 2000:
        _out(result="reused local take", path=str(dest), bytes=dest.stat().st_size, alignment=side.exists(), credits_spent=0)
        return 0
    p = ElevenLabsTTS({})
    text = (ROOT / text_path).read_text(encoding="utf-8")
    try:
        hid = p._lookup(text, 0)
    except RuntimeError as e:  # several matching takes: a person picks one
        _out(result="stopped", reason=str(e), credits_spent=0)
        return 2
    if hid:
        n = _save_history(hid, dest)
        _out(result="reused Speech History take", job_id=hid, path=str(dest), bytes=n, alignment=False, credits_spent=0)
        return 0
    since = int(time.time())
    try:
        audio, alignment = p.generate(text)
    except Exception as e:
        time.sleep(10)
        try:
            hid = p._lookup(text, since)
        except Exception:
            hid = None
        if hid:
            n = _save_history(hid, dest)
            _out(result="request errored but the take exists; saved from Speech History", job_id=hid, path=str(dest),
                 bytes=n, alignment=False, error=str(e)[:200])
            return 0
        _out(result="error; no take found in Speech History; nothing resent", error=str(e)[:300])
        return 1
    dest.write_bytes(audio)
    if alignment:
        side.write_text(json.dumps(alignment, ensure_ascii=False), encoding="utf-8")
    hid = None
    for _ in range(6):
        try:
            hid = p._lookup(text, since)
        except Exception as e:
            print(f"note: Speech History lookup: {e}", file=sys.stderr)
            break
        if hid:
            break
        time.sleep(5)
    _out(result="new take", job_id=hid or "local-" + hashlib.sha256(audio).hexdigest()[:12], path=str(dest),
         bytes=len(audio), alignment=bool(alignment), characters=len(text))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))

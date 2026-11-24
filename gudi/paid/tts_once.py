"""One narration take on the machine that holds the ElevenLabs key (the Mac), for an operator run.

python3 -m gudi.paid.tts_once <text_path> <out.mp3>

Writes the take (and <out.mp3>.alignment.json when ElevenLabs returns character timestamps)
BEFORE anything else, so a paid take is never lost; then looks the take up in Speech History
for its id. One take; never retried. The key is read from .env.local and never printed.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

from ..paths import ROOT
from .elevenlabs import ElevenLabsTTS


def main(text_path, out):
    p = ElevenLabsTTS({})
    text = (ROOT / text_path).read_text(encoding="utf-8")
    since = int(time.time())
    audio, alignment = p.generate(text)
    dest = Path(out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(audio)
    if alignment:
        Path(str(dest) + ".alignment.json").write_text(json.dumps(alignment, ensure_ascii=False), encoding="utf-8")
    hid = None
    for _ in range(6):
        try:
            hid = p._lookup(text, since)
        except Exception as e:  # the take is already saved; the id is a convenience
            print(f"note: Speech History lookup failed: {e}", file=sys.stderr)
            break
        if hid:
            break
        time.sleep(5)
    print(json.dumps({"job_id": hid or "local-" + hashlib.sha256(audio).hexdigest()[:12], "path": str(dest),
                      "bytes": len(audio), "alignment": bool(alignment)}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

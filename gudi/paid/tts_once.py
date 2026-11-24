"""One narration take on the machine that holds the ElevenLabs key (the Mac), for an operator run.

python3 -m gudi.paid.tts_once <text_path> <out.mp3>
Prints {"job_id": <history_item_id>, "path": <out.mp3>, "alignment": bool}. One take; never retried.
The key is read from .env.local by the adapter and never printed.
"""
import json
import sys
from pathlib import Path

from .elevenlabs import ElevenLabsTTS


def main(text_path, out):
    p = ElevenLabsTTS({})
    call = {"text_path": text_path, "settings": {"takes": 1}, "quote": "0"}
    jid = p.submit(call, "operator")
    dest = p.download(jid, None, out)
    print(json.dumps({"job_id": jid, "path": str(dest), "alignment": Path(str(dest) + ".alignment.json").exists()}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

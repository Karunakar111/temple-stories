"""Pending Higgsfield outbox entries as a generate_*_batch requests array (index = position) plus a key map."""
import json, subprocess, sys
kind = sys.argv[1]  # still | clip
rows = [json.loads(l) for l in subprocess.run(["python3", "scripts/ops/pending.py", "higgsfield"], capture_output=True, text=True).stdout.splitlines()]
rows = [r for r in rows if r["type"] == kind][: int(sys.argv[2]) if len(sys.argv) > 2 else 12]
req = [{"index": i, "params": dict(r["payload"], count=1)} for i, r in enumerate(rows)]
json.dump({str(i): r["key"] for i, r in enumerate(rows)}, open("/home/claude/work/keymap.json", "w"))
print(json.dumps(req, ensure_ascii=False))

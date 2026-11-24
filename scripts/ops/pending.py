"""Operator outbox entries not yet submitted (no inbox file), newest last. Usage: python3 scripts/ops/pending.py [provider]"""
import glob, json, os, sys
prov = sys.argv[1] if len(sys.argv) > 1 else None
rows = []
for f in glob.glob("state/operator/outbox/*.json"):
    d = json.load(open(f))
    if os.path.exists(f"state/operator/inbox/{d['request_key']}.json") or (prov and d["provider"] != prov):
        continue
    rows.append(d)
for d in sorted(rows, key=lambda d: d["written"]):
    out = {"key": d["request_key"], "beat": d["beat"], "type": d["asset_type"], "quote": d["quote"]}
    if d["provider"] == "higgsfield":
        out["payload"] = d["payload"]
    else:
        out["text_path"] = d.get("text_path")
    print(json.dumps(out, ensure_ascii=False))

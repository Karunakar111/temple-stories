"""recidx.py I:JOB ... -> operator submitted for keymap.json indices"""
import json, subprocess, sys
km = json.load(open("/home/claude/work/keymap.json"))
for x in sys.argv[1:]:
    i, job = x.split(":", 1)
    print(subprocess.run(["python3", "-m", "gudi", "operator", "submitted", km[i], job], capture_output=True, text=True).stdout.strip().splitlines()[-1])

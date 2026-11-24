"""done.py TS_JOB ... where TS_JOB is the result filename stem 20261124_143609_<job>[.png|.mp4]"""
import subprocess, sys
U = "https://d8j0ntlcm91z4.cloudfront.net/user_2wzFrTnK6i3u8OQ7IntsJa55EIk/hf_"
for x in sys.argv[1:]:
    ext = ".mp4" if x.endswith(".mp4") else ".png"
    stem = x.rsplit(".", 1)[0] if x.endswith((".mp4", ".png")) else x
    job = stem.split("_", 2)[2]
    r = subprocess.run(["python3", "-m", "gudi", "operator", "done", job, U + stem + ext], capture_output=True, text=True)
    print((r.stdout or r.stderr).strip().splitlines()[-1][:70])

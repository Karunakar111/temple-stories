"""Opt-in daily scheduling with a user LaunchAgent. Nothing is installed unless asked."""
import sys
from pathlib import Path

from .paths import ROOT

LABEL = "com.gudikathalu.daily"


def plist(cfg):
    hh, mm = cfg["schedule"]["local_time"].split(":")
    py = cfg["schedule"].get("python", "/usr/bin/python3")
    log = ROOT / "state" / "daily.log"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>{LABEL}</string>
  <key>WorkingDirectory</key><string>{ROOT}</string>
  <key>ProgramArguments</key><array>
    <string>{py}</string><string>-m</string><string>gudi</string><string>daily</string>
  </array>
  <!-- launchd uses the Mac's own clock; set it to India time or adjust the hour. -->
  <key>StartCalendarInterval</key><dict>
    <key>Hour</key><integer>{int(hh)}</integer><key>Minute</key><integer>{int(mm)}</integer>
  </dict>
  <key>StandardOutPath</key><string>{log}</string>
  <key>StandardErrorPath</key><string>{log}</string>
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin</string>
  </dict>
</dict></plist>
"""


def install(cfg, confirm):
    path = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
    if not cfg["schedule"].get("enabled"):
        print("Scheduling is off (config/pipeline.json schedule.enabled = false). Nothing installed.")
        return 2
    if not confirm:
        print(f"Would write {path} and run: launchctl bootstrap gui/$(id -u) {path}\nRe-run with --yes to do it.")
        return 2
    if sys.platform != "darwin":
        print("LaunchAgents are macOS only.")
        return 2
    path.write_text(plist(cfg))
    print(f"Wrote {path}. Load it with:\n  launchctl bootstrap gui/$(id -u) {path}")
    return 0

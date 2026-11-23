"""Higgsfield via the existing integration: the Higgsfield MCP connector, driven by Claude Code
in print mode with exactly one generation tool allowed per call.

NOT YET EXERCISED LIVE. The first paid run must be supervised (see docs/PIPELINE.md).
Spend is decided by gudi's ledger before this is ever called; Claude only executes the one
request it is handed, with the parameter shapes from config/production.json.
"""
import json
import re
import subprocess
import urllib.request
from pathlib import Path

from ..money import to_milli
from ..providers import Provider

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


class HiggsfieldViaClaude(Provider):
    name = "higgsfield"

    def __init__(self, cfg):
        self.cfg = cfg["providers"]["higgsfield"]
        self.server = self.cfg.get("mcp_server", "higgsfield")

    def _claude(self, prompt, tools):
        cmd = [self.cfg.get("claude_bin", "claude"), "-p", prompt, "--output-format", "json",
               "--allowedTools", ",".join(f"mcp__{self.server}__{t}" for t in tools), "--max-turns", "3"]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
        if out.returncode != 0:
            raise RuntimeError(f"claude exited {out.returncode}: {out.stderr[-400:]}")
        return json.loads(out.stdout).get("result", "")

    def quote_milli(self, call):
        return to_milli(call["quote"])

    def submit(self, call, request_key):
        tool = "generate_video" if call["asset_type"] == "clip" else "generate_image"
        params = dict(call["settings"], model=call["model"], prompt=call["prompt"])
        prompt = (
            f"Call {tool} exactly once with params = {json.dumps(params, ensure_ascii=False)} "
            f"(all arguments nested inside params). Do not call anything else and do not retry. "
            f"Reply with only the job id. Request key: {request_key[:16]}."
        )
        m = UUID.search(self._claude(prompt, [tool]))
        if not m:
            raise RuntimeError("no job id returned; reconcile before any resubmission")
        return m.group(0)

    def _history(self):
        text = self._claude("Call show_generations with no arguments and print its raw result only.", ["show_generations"])
        return text

    def status(self, job_id):
        text = self._history()
        for line in text.splitlines():
            if job_id in line:
                url = re.search(r"https://\S+?\.(?:png|mp4|jpg)", line)
                state = "completed" if "completed" in line else ("failed" if "failed" in line else "pending")
                return {"state": state, "url": url.group(0) if url else None, "charged_milli": None}
        return {"state": "pending", "url": None, "charged_milli": None}

    def find(self, call, request_key, since_iso):
        # show_generations lists id, model, url and created time; prompt text is matched by the
        # person resolving an `unknown` row, so this only proposes candidates
        return None

    def download(self, job_id, url, dest):
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, str(dest))
        return Path(dest)

"""Zero-spend payload test: build the exact outgoing Higgsfield params for real EP02 calls.

Board references resolve to their real media ids. Upstream stills that do not exist yet are
stood in for by existing EP01 media in the account (named below), so the payload is complete and
can be priced with Higgsfield's free estimate tools. Nothing is reserved or submitted.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ["GUDI_DRY_RUN"] = "1"

from .episodes import Episode, request_key  # noqa: E402
from .ledger import Ledger  # noqa: E402
from .media import resolve  # noqa: E402

# Existing media in the Higgsfield account (show_medias, 24 Nov 2026), used only as stand-ins.
STAND_IN = {
    "CS-RENUKA:still": ("a729414b-aec4-4dbe-b8f7-c9dcd3e341ed", "EP01 n10-hand start frame"),
    "S02:still": ("b23194fa-59e6-4cb8-8a2d-e190d7774d5e", "EP01 n01-oggu start frame"),
}
PICK = [("S02", "still"), ("S02", "clip")]
HELD = ("ep03-vemulavada", "S03", "still")  # an identified exterior with no photo yet


def main():
    ep = Episode("ep02-kolanupaka")
    with tempfile.TemporaryDirectory() as tmp:
        ledger = Ledger(Path(tmp) / "ledger.sqlite3")
        # pretend the upstream stills were generated and downloaded as the stand-in jobs
        for ref, (mid, _) in STAND_IN.items():
            beat, at = ref.split(":")
            c = next(c for c in ep.paid_calls() if c["beat"] == beat and c["asset_type"] == at)
            ledger.reserve({"request_key": request_key(ep, c), "episode": ep.slug, "revision": ep.revision(), "beat": beat,
                            "asset_type": at, "provider": "higgsfield", "params_json": "{}", "quoted_milli": 0, "local_day": "test"},
                           {"stand-in": 1})
            ledger.set_state(request_key(ep, c), "downloaded", provider_job_id=mid, local_path="-", sha256="-")
        out = []
        for beat, at in PICK:
            c = next(c for c in ep.paid_calls() if c["beat"] == beat and c["asset_type"] == at)
            params, problems = resolve(ep, c, ledger)
            out.append({"call": f"{beat}:{at}", "references": c["references"], "params": params, "held": problems})
        e3 = Episode(HELD[0])
        c = next(c for c in e3.paid_calls() if c["beat"] == HELD[1] and c["asset_type"] == HELD[2])
        params, problems = resolve(e3, c, ledger)
        out.append({"call": f"{HELD[0]} {HELD[1]}:{HELD[2]}", "references": c["references"], "params": params, "held": problems})
    print(json.dumps({"stand_ins": STAND_IN, "payloads": out}, ensure_ascii=False, indent=1))
    assert "gudi.paid" not in sys.modules


if __name__ == "__main__":
    main()

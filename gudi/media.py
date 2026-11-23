"""Resolve every reference of a paid call to the exact Higgsfield media it will send.

- Board references (style art, identified exteriors) need a `media_id` on the reference board:
  an uploaded Higgsfield media. A reference without one holds the call; nothing is reserved.
- Generated references ("S02:still", "CS-RENUKA:still") resolve through the ledger to the
  completed Higgsfield job of exactly that request (same script, scope and prompt). Higgsfield
  accepts a completed job id in `medias[].value`.
- Parameter shapes are the ones that produced accepted EP01 output (design/ep01-full/stills.json):
  everything inside `params`; stills pass `medias` with role `image_references` (authority first,
  style carrier last); Kling clips pass the first frame with role `start_image`.
"""
from .episodes import request_key

STILL_ROLE, CLIP_ROLE = "image_references", "start_image"


def _producer(ep, ref):
    beat, asset_type = ref.split(":")
    for c in ep.paid_calls():
        if c["beat"] == beat and c["asset_type"] == asset_type:
            return c
    return None


def resolve(ep, call, ledger):
    """Returns (params, problems). problems is empty only when every media value is a real id."""
    if call["provider"] != "higgsfield":
        return {"text_path": call.get("text_path"), "model": call.get("model"),
                "voice": call.get("settings", {}).get("voice"), "takes": 1}, []
    board = {r["id"]: r for r in (ep.board or {}).get("references", [])}
    clip = call["asset_type"] == "clip"
    role = CLIP_ROLE if clip else STILL_ROLE
    medias, problems, labels = [], [], []
    for ref in call.get("references", []):
        if ":" in ref:
            prod = _producer(ep, ref)
            job = ledger.job(request_key(ep, prod)) if prod else None
            if not job or job["state"] != "downloaded" or not job["provider_job_id"]:
                problems.append(f"{ref} not generated yet")
                continue
            value = job["provider_job_id"]
        else:
            r = board.get(ref)
            value = (r or {}).get("media_id")
            if not value:
                problems.append(f"{ref}: no Higgsfield media id ({(r or {}).get('status', 'not on board')})")
                continue
        medias.append({"value": value, "role": role})
        labels.append(ref)
    s = call["settings"]
    if clip:
        params = {"model": call["model"], "prompt": call["prompt"], "mode": s.get("mode", "pro"),
                  "sound": s.get("sound", "off"), "aspect_ratio": s.get("aspect_ratio", "9:16"),
                  "duration": s["duration"], "medias": medias}
        if len(medias) != 1:
            problems.append(f"a clip needs exactly one start image, has {len(medias)}")
    else:
        style_note = " The last reference image sets the illustration style only." if labels and labels[-1].startswith("STYLE-") else ""
        params = {"model": call["model"], "prompt": call["prompt"] + style_note,
                  "resolution": s.get("resolution", "2k"), "aspect_ratio": s.get("aspect_ratio", "9:16"), "medias": medias}
    for m in medias:  # never send a name, a placeholder or a URL
        if not m["value"] or m["value"].startswith(("<", "http")) or ":" in m["value"]:
            problems.append(f"unresolved media value {m['value']!r}")
    return params, problems

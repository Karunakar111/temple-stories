"""Episodes, approvals and the planned paid calls derived from a shot list.

Approval pins three things, and nothing else:
  - the exact script text (sha256 of voice.te.txt),
  - the CREATIVE scope: reference board + shot list with every timing field removed
    (starts, durations, clip lengths and the quotes that follow from them),
  - provider caps.
So routine retiming after narration keeps the approval, while any change to a prompt,
reference, shot, asset class or the script text makes it stale. Caps are enforced on
every reservation, so a retime that would exceed them is held anyway.

Approval comes from a weekly batch record (one act covering scripts, visual approach and
caps for the week), or from an episode's own approval.json.
"""
import copy
import hashlib
import json

from .money import to_milli
from .paths import EPISODES

TIMING_KEYS = {"est_start_s", "est_dur_s", "est_total_s", "timing_basis", "duration", "quote", "start_image", "timing"}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def load_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _strip_timing(obj):
    if isinstance(obj, dict):
        return {k: _strip_timing(v) for k, v in obj.items() if k not in TIMING_KEYS}
    if isinstance(obj, list):
        return [_strip_timing(v) for v in obj]
    return obj


class Episode:
    def __init__(self, slug, root=None, batch=None):
        self.slug = slug
        self.root = root or EPISODES
        self.dir = self.root / slug
        self.meta = load_json(self.dir / "episode.json", {})
        self.shots_doc = load_json(self.dir / "shots.json")
        self.board = load_json(self.dir / "reference-board.json")
        self.timing = load_json(self.dir / "timing.json")
        self.batch = batch
        self.approval = load_json(self.dir / "approval.json")
        if batch is not None and batch.approval:
            self.approval = batch.approval.get("episodes", {}).get(slug)

    # ------------------------------------------------------------ fingerprints
    def voice_text(self):
        return (self.dir / "voice.te.txt").read_text(encoding="utf-8").strip()

    def has_script(self):
        return (self.dir / "voice.te.txt").exists()

    def script_sha(self):
        p = self.dir / "voice.te.txt"
        return sha256_bytes(p.read_bytes()) if p.exists() else None

    def creative_sha(self):
        """Scope: what is drawn and from which identified sources. Excluded: timing (retimed from the
        take) and which uploaded file carries an identified place (media id), so importing the
        approved exterior photo does not void the approval. Depiction decisions stay in scope."""
        board = copy.deepcopy(self.board) or {}
        for r in board.get("references", []):
            for k in ("media_id", "media_check", "photo", "note"):
                r.pop(k, None)
            if r.get("status") in ("needs photo", "verified"):
                r["status"] = "identified"
        doc = {"board": board, "shots": _strip_timing(copy.deepcopy(self.shots_doc))}
        return sha256_bytes(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode("utf-8"))

    look_sha = creative_sha  # name used by earlier approvals

    def revision(self):
        return f"s{(self.script_sha() or 'none')[:12]}-c{self.creative_sha()[:12]}"

    # ------------------------------------------------------------ approval
    def approval_problems(self):
        if not self.has_script():
            return [self.meta.get("status") or "script not received"]
        if self.approval is None:
            return ["script, visual approach and caps not approved"]
        p = []
        if self.approval.get("script_sha256") != self.script_sha():
            p.append("script text changed since approval")
        if self.approval.get("look_sha256") != self.creative_sha():
            p.append("creative scope (shots, prompts or references) changed since approval")
        return p

    def cap(self, provider):
        """Episode-level cap if one was set; a batch approval caps the week instead."""
        if self.approval is None:
            return None
        v = self.approval.get("caps", {}).get(provider)
        if v is not None:
            return to_milli(v)
        if self.batch is not None and self.batch.cap(provider) is not None:
            return self.batch.cap(provider)  # never tighter than the week; the week cap is checked separately
        return None

    # ------------------------------------------------------------ plan
    def providers(self):
        return sorted({c["provider"] for c in self.paid_calls()})

    def paid_calls(self):
        if not self.shots_doc:
            return []
        calls = []
        am = load_json(self.dir / "amendments.json", {}) or {}
        skip, attempts = set(am.get("skip", [])), am.get("attempts", {})
        for c in self.shots_doc.get("narration", []):
            calls.append(dict(c, beat=c.get("beat", "VO")))
        for shot in self.shots_doc["shots"]:
            for c in shot.get("paid", []):
                c = dict(c, beat=shot["id"])
                t = (self.timing or {}).get("clips", {}).get(shot["id"])
                if c["asset_type"] == "clip" and t:
                    c["settings"] = dict(c["settings"], duration=t["duration"])
                    c["quote"] = t["quote"]
                tag = f"{shot['id']}:{c['asset_type']}"
                if tag in skip:
                    continue  # replaced by an approved amendment; never generated
                if tag in attempts:  # an approved new attempt: a new request key for this call only
                    c["settings"] = dict(c["settings"], attempt=attempts[tag])
                calls.append(c)
        return calls

    def narration_resolved(self):
        return bool(self.timing and self.timing.get("source", "").startswith("take"))

    def blockers(self, call):
        if not self.board:
            return ["reference board missing"]
        items = {r["id"]: r for r in self.board["references"]}
        out = []
        for ref in call.get("needs", []):
            r = items.get(ref)
            if r is None:
                out.append(f"{ref}: not on the reference board")
            elif r["status"] == "needs photo" and r.get("media_id"):
                continue  # identified place, photo imported: usable
            elif r["status"] not in ("verified", "approved-style"):
                out.append(f"{ref}: {r['status']} ({r['subject']})")
        return out


def request_key(episode, call):
    canonical = {
        "episode": episode.slug,
        "script": episode.script_sha(),
        "creative": episode.creative_sha(),
        "beat": call["beat"],
        "asset_type": call["asset_type"],
        "prompt": call.get("prompt", ""),
        "references": call.get("references", []),
        "model": call.get("model", ""),
        "settings": call.get("settings", {}),
    }
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def queue_order(root=None):
    q = load_json((root or EPISODES) / "queue.json", {"order": []})
    return q["order"]

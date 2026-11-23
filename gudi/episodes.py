"""Episodes, approvals and the planned paid calls derived from a shot list.

Approval is a file written only by `gudi approve` (a human command). It pins:
  - the exact script text (sha256 of voice.te.txt),
  - the look: sha256 of reference-board.json + shots.json,
  - the voice settings,
  - a per-provider spend cap for this episode.
Change any of the pinned files and the approval is stale; the runner then holds.
"""
import hashlib
import json

from .money import to_milli
from .paths import EPISODES


def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


class Episode:
    def __init__(self, slug, root=None):
        self.slug = slug
        self.dir = (root or EPISODES) / slug
        self.meta = load_json(self.dir / "episode.json", {})
        self.shots_doc = load_json(self.dir / "shots.json")
        self.board = load_json(self.dir / "reference-board.json")
        self.approval = load_json(self.dir / "approval.json")

    # ------------------------------------------------------------ fingerprints
    def script_sha(self):
        return sha256_file(self.dir / "voice.te.txt")

    def look_sha(self):
        h = hashlib.sha256()
        for name in ("reference-board.json", "shots.json"):
            p = self.dir / name
            h.update(p.read_bytes() if p.exists() else b"<missing>")
        return h.hexdigest()

    def revision(self):
        """Revision string used in request keys: script + look."""
        return f"s{self.script_sha()[:12]}-l{self.look_sha()[:12]}"

    # ------------------------------------------------------------ approval
    def approval_problems(self):
        if self.approval is None:
            return ["script, look and budget not approved (run `gudi approve`)"]
        p = []
        if self.approval.get("script_sha256") != self.script_sha():
            p.append("script changed since approval")
        if self.approval.get("look_sha256") != self.look_sha():
            p.append("reference board or shot list changed since approval")
        caps = self.approval.get("caps", {})
        for prov in self.providers():
            if caps.get(prov) is None:
                p.append(f"no episode spend cap approved for {prov}")
        return p

    def cap(self, provider):
        v = (self.approval or {}).get("caps", {}).get(provider)
        return None if v is None else to_milli(v)

    # ------------------------------------------------------------ plan
    def providers(self):
        return sorted({c["provider"] for c in self.paid_calls()})

    def paid_calls(self):
        """Every paid request the shot list implies, in dependency order."""
        if not self.shots_doc:
            return []
        calls = []
        for c in self.shots_doc.get("narration", []):
            calls.append(dict(c, beat=c.get("beat", "narration")))
        for shot in self.shots_doc["shots"]:
            for c in shot.get("paid", []):
                calls.append(dict(c, beat=shot["id"]))
        return calls

    def blockers(self, call):
        """Unresolved references that must be fixed before this call may be paid for."""
        if not self.board:
            return ["reference board missing"]
        items = {r["id"]: r for r in self.board["references"]}
        out = []
        for ref in call.get("needs", []):
            r = items.get(ref)
            if r is None:
                out.append(f"{ref}: not on the reference board")
            elif r["status"] not in ("verified", "approved-style"):
                out.append(f"{ref}: {r['status']} ({r['subject']})")
        return out


def request_key(episode, call):
    canonical = {
        "episode": episode.slug,
        "revision": episode.revision(),
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

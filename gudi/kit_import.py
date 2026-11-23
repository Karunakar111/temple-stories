"""Import scripts from the weekly kit (weekly-kit/episodes/EPnn.md) into episode folders.

The Voice section is copied verbatim (the kit's own validator: Telugu only, no Latin letters).
If an episode already has a voice file with different text, nothing is overwritten: the diff is
written to proposed-edits.diff and the import stops for that episode (one source of truth).

Usage: python3 -m gudi.kit_import <weekly-kit dir> EP07 EP08
"""
import difflib
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

from .paths import EPISODES, ROOT

SLUGS = {"EP02": "ep02-kolanupaka", "EP03": "ep03-vemulavada", "EP04": "ep04-srikalahasti",
         "EP05": "ep05-yadagirigutta", "EP06": "ep06-kanipakam", "EP07": "ep07-puri", "EP08": "ep08-bhadrachalam"}


def parse(md):
    if md.count("### Voice\n") != 1 or md.count("### Direction and evidence\n") != 1:
        raise ValueError("needs exactly one Voice and one Direction section")
    head, rest = md.split("### Voice\n")
    voice, notes = rest.split("### Direction and evidence\n")
    voice = voice.strip()
    if not re.search("[ఁ-౿]", voice) or re.search("[A-Za-z]", voice):
        raise ValueError("Voice must be Telugu only")
    title = re.search(r"^# (EP\d\d) · (.+)$", head, re.M)
    cover = re.search(r"\*\*Cover\*\*\s*(.+)", head)
    links = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", notes)
    direction = notes.split("\n- [")[0].strip()
    return {"code": title.group(1), "title_te": title.group(2).strip(), "cover_te": cover.group(1).strip(),
            "voice": voice, "direction": direction, "sources": [{"id": f"N{i + 1}", "label": l, "url": u} for i, (l, u) in enumerate(links)]}


def import_one(kit_dir, code):
    src = Path(kit_dir) / "episodes" / f"{code}.md"
    md = src.read_text(encoding="utf-8")
    p = parse(md)
    d = EPISODES / SLUGS[code]
    d.mkdir(parents=True, exist_ok=True)
    vf = d / "voice.te.txt"
    if vf.exists() and vf.read_text(encoding="utf-8").strip() == p["voice"]:
        return f"{code}: identical to the repo script; left as is"
    if vf.exists():
        diff = difflib.unified_diff(vf.read_text(encoding="utf-8").splitlines(), p["voice"].splitlines(),
                                    "repo/voice.te.txt", f"kit/{code}.md", lineterm="")
        (d / "proposed-edits.diff").write_text("\n".join(diff) + "\n", encoding="utf-8")
        return f"{code}: CONFLICT with the repo script; diff in {d.name}/proposed-edits.diff; not imported"
    vf.write_text(p["voice"] + "\n", encoding="utf-8")
    (d / "cover.te.txt").write_text(p["cover_te"] + "\n", encoding="utf-8")
    (d / "sources.json").write_text(json.dumps({"note": "From the weekly kit's Direction and evidence section.",
                                                "sources": p["sources"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (d / "directions.json").write_text(json.dumps([{"cue": "whole film", "picture": p["direction"], "evidence": "N1-N%d" % len(p["sources"])}],
                                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not (d / "proposed-edits.diff").exists():
        (d / "proposed-edits.diff").write_text("", encoding="utf-8")
    meta_f = d / "episode.json"
    meta = json.loads(meta_f.read_text(encoding="utf-8")) if meta_f.exists() else {}
    known = meta.get("known", {})
    meta = {"id": SLUGS[code], "code": code, "slot": int(code[2:]), "title_te": p["title_te"],
            "cover_te": p["cover_te"],
            "script": {"path": "voice.te.txt", "sha256": hashlib.sha256(p["voice"].encode()).hexdigest(),
                       "characters": len(p["voice"]), "words": len(p["voice"].split()),
                       "imported_from": f"weekly-kit/episodes/{code}.md",
                       "kit_sha256": hashlib.sha256(md.encode()).hexdigest()},
            "status": "draft: awaiting editorial approval"}
    if known.get("verified_visual_facts"):
        meta["verified_visual_facts"] = known["verified_visual_facts"]
    meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    kept = ROOT / "source-docs" / "weekly-kit"
    kept.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, kept / src.name)
    return f"{code}: imported {len(p['voice'])} characters, {len(p['sources'])} sources -> episodes/{d.name}"


if __name__ == "__main__":
    for c in sys.argv[2:]:
        print(import_one(sys.argv[1], c))

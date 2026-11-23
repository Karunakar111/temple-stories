"""Split the EP02-06 Production Book into one folder per episode.

The Voice section is copied byte-for-byte (only the blank lines around the section are
trimmed) and re-verified as an exact substring of the book. Everything that must NOT go
to the narrator (cover, beat directions, evidence, sources) is stored separately.
"""
import hashlib
import json
import re
from pathlib import Path

from .paths import BOOK, EPISODES

SLUGS = {
    "EP02": "ep02-kolanupaka",
    "EP03": "ep03-vemulavada",
    "EP04": "ep04-srikalahasti",
    "EP05": "ep05-yadagirigutta",
    "EP06": "ep06-kanipakam",
}


def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _table(block):
    rows = []
    for line in block.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == "Spoken cue":
            continue
        if len(cells) >= 3:
            rows.append({"cue": cells[0], "picture": cells[1], "evidence": cells[2]})
    return rows


def parse(book_text):
    parts = re.split(r"^## (EP0[2-6]) · (.+)$", book_text, flags=re.M)
    episodes = []
    for i in range(1, len(parts), 3):
        code, title, body = parts[i], parts[i + 1].strip(), parts[i + 2]
        body = body.split("\n## ", 1)[0]  # stop at the next top-level section
        cover = re.search(r"^\*\*Cover\*\* (.+)$", body, flags=re.M).group(1).strip()
        voice_block = body.split("### Voice", 1)[1].split("### Direction and evidence", 1)[0]
        voice = voice_block.strip("\n")
        assert voice in book_text, f"{code}: voice text is not verbatim"
        directions_block = body.split("### Direction and evidence", 1)[1]
        table, _, rest = directions_block.partition("**Sources.**")
        note, _, src_list = rest.partition("\n- ")
        sources = []
        for line in ("- " + src_list).splitlines():
            m = re.match(r"^- (\w+) · \[(.+?)\]\((.+?)\)", line.strip())
            if m:
                sources.append({"id": m.group(1), "label": m.group(2), "url": m.group(3)})
        episodes.append(
            {
                "code": code,
                "title_te": title,
                "cover_te": cover,
                "voice": voice + "\n",
                "directions": _table(table),
                "sources_note": note.strip(),
                "sources": sources,
            }
        )
    return episodes


def write(book_path=BOOK, out=EPISODES, overwrite_voice=False):
    text = Path(book_path).read_text(encoding="utf-8")
    book_hash = sha256(text)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for slot, ep in enumerate(parse(text), start=2):
        d = out / SLUGS[ep["code"]]
        d.mkdir(exist_ok=True)
        vpath = d / "voice.te.txt"
        if vpath.exists() and not overwrite_voice and vpath.read_text(encoding="utf-8") != ep["voice"]:
            raise SystemExit(f"{vpath} differs from the book; refusing to overwrite an edited script")
        vpath.write_text(ep["voice"], encoding="utf-8")
        words = len(ep["voice"].split())
        meta_path = d / "episode.json"
        old = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        meta = {
            "id": SLUGS[ep["code"]],
            "code": ep["code"],
            "slot": slot,
            "title_te": ep["title_te"],
            "cover_te": ep["cover_te"],
            "script": {
                "path": "voice.te.txt",
                "sha256": sha256(ep["voice"]),
                "characters": len(ep["voice"].strip()),
                "words": words,
                "imported_from": "source-docs/Gudi_Kathalu_EP02-06_Production_Book.md",
                "book_sha256": book_hash,
            },
            # approvals are written only by `gudi approve`, never by the importer or runner
            "status": old.get("status", "draft: awaiting editorial approval"),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "directions.json").write_text(json.dumps(ep["directions"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (d / "sources.json").write_text(
            json.dumps({"note": ep["sources_note"], "sources": ep["sources"]}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (d / "cover.te.txt").write_text(ep["cover_te"] + "\n", encoding="utf-8")
        edits = d / "proposed-edits.diff"
        if not edits.exists():
            edits.write_text("", encoding="utf-8")  # empty = no Telugu edit proposed
        written.append(d)
    queue = out / "queue.json"
    q = {
        "_comment": "Slate order. EP01 is published and locked; the runner never touches it.",
        "locked": ["ep01-komuravelli (approved export: publishing/ep01/)"],
        "order": [SLUGS[c] for c in ("EP02", "EP03", "EP04", "EP05", "EP06")],
    }
    queue.write_text(json.dumps(q, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return written

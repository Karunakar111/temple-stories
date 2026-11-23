"""Local review export: everything a person needs to watch and decide, in one folder.
Publishing is never done here."""
import json
import shutil
from datetime import datetime

from .ledger import local_tz
from .money import fmt
from .paths import REVIEW, ROOT


def export(ep, ledger, cfg, say=print):
    day = datetime.now(local_tz(cfg)).date().isoformat()
    out = REVIEW / ep.slug / day
    out.mkdir(parents=True, exist_ok=True)
    jobs = ledger.jobs(ep.slug)
    by_prov = {}
    for j in jobs:
        p = by_prov.setdefault(j["provider"], {"quoted": 0, "settled": 0, "open": 0})
        p["quoted"] += j["quoted_milli"]
        if j["state"] == "downloaded":
            p["settled"] += j["settled_milli"] or j["quoted_milli"]
        elif j["state"] not in ("released",):
            p["open"] += j["quoted_milli"]
    cost = {
        prov: {"unit": cfg["providers"].get(prov, {}).get("unit", "credits"), "quoted": fmt(v["quoted"]),
               "settled": fmt(v["settled"]), "still_reserved": fmt(v["open"]), "delta_settled_minus_quoted":
               fmt(v["settled"] - (v["quoted"] - v["open"]))}
        for prov, v in by_prov.items()
    }
    film = ROOT / "exports" / f"{ep.slug}.mp4"
    captions = ep.dir / "captions.te.srt"
    pending = []
    if film.exists():
        shutil.copy2(film, out / film.name)
    else:
        pending.append(f"film: not rendered yet (expected {film.relative_to(ROOT)})")
    if captions.exists():
        shutil.copy2(captions, out / captions.name)
    else:
        pending.append("captions: produced after narration alignment")
    shutil.copy2(ep.dir / "cover.te.txt", out / "cover.te.txt")
    cover_img = ep.dir / "cover-1080x1920.jpg"
    if cover_img.exists():
        shutil.copy2(cover_img, out / cover_img.name)
    else:
        pending.append("cover image: not made yet")
    src = json.loads((ep.dir / "sources.json").read_text(encoding="utf-8"))
    (out / "platform-text-draft.md").write_text(
        f"# {ep.meta.get('title_te','')}\n\n{ep.meta.get('cover_te','')}\n\n## Sources\n"
        + "\n".join(f"- {s['id']}: {s['label']} {s['url']}" for s in src["sources"])
        + "\n\nDraft only. Karunakar decides whether and when to post.\n",
        encoding="utf-8",
    )
    manifest = {
        "episode": ep.slug, "revision": ep.revision(), "exported_local_day": day,
        "approval": ep.approval, "cost": cost, "pending": pending,
        "assets": [
            {"beat": j["beat"], "type": j["asset_type"], "provider": j["provider"], "state": j["state"],
             "request_key": j["request_key"], "provider_job_id": j["provider_job_id"], "path": j["local_path"],
             "sha256": j["sha256"], "quoted": fmt(j["quoted_milli"]), "settled": fmt(j["settled_milli"])}
            for j in jobs
        ],
        "publishing": "not done here; human approval of the rendered film comes first",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "cost.json").write_text(json.dumps(cost, indent=2) + "\n", encoding="utf-8")
    say(f"  review export -> {out}")
    return out

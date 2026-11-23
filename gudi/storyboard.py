"""Render storyboard.md and cost-sheet.md from shots.json + reference-board.json (no network)."""
from .episodes import Episode
from .money import fmt, to_milli


def _mmss(s):
    if s is None:
        return "  -  "
    return f"{int(s // 60)}:{s % 60:04.1f}"


def render(slug):
    ep = Episode(slug)
    d, board = ep.shots_doc, {r["id"]: r for r in ep.board["references"]}
    sb = [f"# {ep.meta['title_te']}: storyboard (revision {d['revision']})", "",
          f"Cover: {ep.meta['cover_te']}", "",
          f"Timing: {d['timing_basis']} Estimated length about {d['est_total_s']:.0f} s.", "",
          "| # | Time | Spoken words | Picture | What changes | Asset class | Paid | Blocked by |",
          "|---|---|---|---|---|---|---|---|"]
    for s in d["shots"]:
        paid = ", ".join(f"{c['asset_type']} {c['quote']}" for c in s["paid"]) or "none"
        blocks = sorted({b.split(':')[0] for c in s["paid"] for b in ep.blockers(dict(c, beat=s['id']))})
        sb.append(f"| {s['id']} | {_mmss(s['est_start_s'])} | {s['text'] or '(reference sheet, not on screen)'} | "
                  f"{s['picture']}{' *' + s['note'] + '*' if s.get('note') else ''} | {s['what_changes']} | {s['class']} | "
                  f"{paid} | {', '.join(blocks) or '-'} |")
    (ep.dir / "storyboard.md").write_text("\n".join(sb) + "\n", encoding="utf-8")

    rows = ["# " + ep.meta["title_te"] + ": cost sheet (provisional, quotes only, nothing bought)", "",
            "Higgsfield quotes come from the connector's free estimate tools (2 credits per 2k still; "
            "Kling 3.0 pro silent: 6 for 4 s, 7.5 for 5 s), fetched 23 Nov 2026. ElevenLabs: verified with the connector's free estimate (EP02, one take = 1,430 "
            "credits, 1 credit per character on eleven_v4). The connector defaults to two takes and charges per take; "
            "the pipeline pins one take. Clip lengths are provisional until the take exists and may shrink or grow "
            "within the approval.", "",
            "| Beat | Asset | Provider | Model / settings | Quote | Status |", "|---|---|---|---|---|---|"]
    tot, ready = {}, {}
    for c in ep.paid_calls():
        q = to_milli(c["quote"])
        b = ep.blockers(c)
        tot[c["provider"]] = tot.get(c["provider"], 0) + q
        if not b:
            ready[c["provider"]] = ready.get(c["provider"], 0) + q
        st = "BLOCKED: " + "; ".join(x.split(" (")[0] for x in b) if b else "quotable now"
        model = c.get("model", "") + " " + ", ".join(f"{k}={v}" for k, v in c.get("settings", {}).items() if k != "start_image")
        rows.append(f"| {c['beat']} | {c['asset_type']} | {c['provider']} | {model} | {c['quote']} | {st} |")
    rows += ["", "## Totals by provider", "", "| Provider | Unit | Full plan | Of which unblocked today |", "|---|---|---|---|"]
    units = {"higgsfield": "credits", "elevenlabs": "ElevenLabs credits (1 take)"}
    for p in sorted(tot):
        rows.append(f"| {p} | {units.get(p, 'credits')} | {fmt(tot[p])} | {fmt(ready.get(p, 0))} |")
    rows += ["", "Not included and not reserved: any repair of a still or clip (each needs your explicit retry "
             "approval), outsourced illustration (none planned), and the cover image (made locally from approved stills).",
             "", "Compare: EP01 spent 322.5 Higgsfield credits, 242.5 of them on assets in the film (docs/EP01-COST-AUDIT.md)."]
    (ep.dir / "cost-sheet.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    return tot, ready

"""One spend-free review page for the episodes still to be generated: for each, the opening hook, the
visual that identifies the temple and the hardest action, with the routine fixes already made and one
approval request for everything that still needs a decision or credits.

  python3 -m gudi.preflight week-1 ep03-vemulavada ... ep08-bhadrachalam
writes review/<batch>/preflight.html. Nothing is generated or spent.
"""
import json
import os
import sys

os.environ.setdefault("GUDI_DRY_RUN", "1")

from . import paths  # noqa: E402
from .batch import Batch, quote_rows, totals  # noqa: E402
from .episodes import Episode  # noqa: E402
from .money import fmt  # noqa: E402
from .visual_check import rows, summary  # noqa: E402
from .weekly import CSS, _e  # noqa: E402


def build(batch_id, slugs):
    b = Batch(batch_id)
    pf = json.loads((b.root / "batches" / f"{batch_id}.preflight.json").read_text(encoding="utf-8"))
    q = quote_rows(b)
    tot = totals(q)
    hf = {s: (tot.get(s, {}).get("higgsfield") or 0) / 1000 for s in slugs}
    el = {s: (tot.get(s, {}).get("elevenlabs") or 0) / 1000 for s in slugs}
    add = {}
    for n in pf["new_stills"]:
        add[n["episode"]] = add.get(n["episode"], 0) + n["quote"]
    hf_now, hf_add, el_now = sum(hf.values()), sum(add.values()), sum(el.values())

    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>Gudi Kathalu EP03 to EP08: before generation</title><style>{CSS}</style></head><body><main>"]
    h.append("<h1>గుడి కథలు · EP03 to EP08 before generation</h1>")
    h.append("<p class='sub'>Spend-free review: nothing here has been generated or charged. For each episode: the opening hook, the "
             "picture that identifies the temple, and the hardest action to show. Routine fixes are already made with existing "
             "assets. Everything left is in the one approval request below.</p>")

    # ------------------------------------------------------------- the one approval request
    h.append("<div class='card ask'><h2>Approval request</h2><ol>")
    h.append("<li><b>Temple reference photos (9).</b> Approve the candidate for each, or send your own. Each is a rights-cleared "
             "photo imported to Higgsfield as a reference only; the credit line goes in the description. "
             "<div class='scroll'><table><tr><th>Episode</th><th>Reference</th><th>Used in</th><th>Candidate</th><th>Licence</th></tr>")
    for r in pf["references"]:
        cand = f"<a href='{_e(r['url'])}'>{_e(r['candidate'])}</a>" if r.get("url") else f"<b class='hold'>{_e(r['candidate'])}</b>"
        if r.get("fallback"):
            cand += f"<br><span class='sub'>{_e(r['fallback'])}</span>"
        h.append(f"<tr><td>{_e(r['episode'][:4].upper())}</td><td><b>{_e(r['id'])}</b><br><span class='sub'>{_e(r['subject'])}</span></td>"
                 f"<td>{_e(r['used'])}</td><td>{cand}</td><td>{_e(r['licence'])}</td></tr>")
    h.append("</table></div></li>")
    h.append(f"<li><b>Four new stills for missing scenes: {fmt(round(hf_add * 1000))} Higgsfield credits, already inside the quote below.</b>"
             "<div class='scroll'><table><tr><th>Episode</th><th>Shot</th><th>Missing scene it fills</th><th class='n'>Credits</th></tr>")
    for n in pf["new_stills"]:
        h.append(f"<tr><td>{_e(n['episode'][:4].upper())}</td><td>{_e(n['shot'])}</td><td>{_e(n['what'])}</td><td class='n'>{n['quote']}</td></tr>")
    h.append("</table></div></li>")
    h.append("<li><b>Two judgement calls.</b><ul>" + "".join(
        f"<li>{_e(j['episode'][:4].upper())} {_e(j['shot'])}: {_e(j['question'])}</li>" for j in pf["judgement"]) + "</ul></li>")
    short = hf_now - float(pf["balances"]["higgsfield"].split()[0])
    h.append(f"<li><b>Revised cost for EP03 to EP08:</b> Higgsfield "
             f"<b>{fmt(round(hf_now * 1000))}</b>; ElevenLabs <b>{fmt(round(el_now * 1000))}</b>, one take each. "
             f"Higgsfield balance {_e(pf['balances']['higgsfield'])}"
             + (f": <b class='hold'>{fmt(round(short * 1000))} short</b>, so a top-up is needed before the last episode." if short > 0 else ".")
             + f" ElevenLabs: {_e(pf['balances']['elevenlabs'])}. Clip lengths are re-sized to each real take and never exceed the quote "
             "(EP02's clips came in at about two-thirds of their quote); failed or refused generations are refunded.</li>")
    h.append("</ol></div>")

    # ------------------------------------------------------------- per episode
    for s in slugs:
        ep = Episode(s, b.root)
        e = pf["episodes"][s]
        shots = {x["id"]: x for x in ep.shots_doc["shots"]}
        sm = summary(ep)
        r, rev = rows(ep)
        resolved = [n for n in rev.get("notes", []) if n["severity"] == "resolved"]
        h.append(f"<div class='card'><h2>{_e(ep.meta.get('code', s[:4].upper()))} · {_e(ep.meta.get('title_te', ''))}</h2>"
                 f"<p class='sub'>{_e(ep.meta.get('cover_te', ''))} · ~{ep.shots_doc.get('est_total_s', 0):.0f} s · "
                 f"Higgsfield {fmt(round(hf[s] * 1000))}{' + ' + str(add[s]) if s in add else ''} · ElevenLabs {fmt(round(el[s] * 1000))}</p>")
        h.append("<div class='scroll'><table>")
        h.append(f"<tr><th style='width:9em'>Opening hook</th><td><b>{_e(shots['S01']['text'])}</b><br>{_e(e['hook_seen'])}</td></tr>")
        h.append(f"<tr><th>Identifies the temple</th><td>{_e(e['identity'])}</td></tr>")
        h.append(f"<tr><th>Hardest action</th><td><b>{_e(e['hardest'])}</b><br>{_e(e['plan'])}</td></tr>")
        if resolved:
            h.append("<tr><th>Fixed today, no cost</th><td>" + "<br>".join(f"<b class='ok'>{_e(n['shot'])}</b> {_e(n['note'])}" for n in resolved) + "</td></tr>")
        miss = [n for n in rev.get("notes", []) if n["severity"] == "missing"]
        if miss:
            h.append("<tr><th>Missing, in the request</th><td>" + "<br>".join(
                f"<b class='hold'>{_e(n['shot'])}</b> {_e(n['note'])} ({n.get('quote', 0)} credits)" for n in miss) + "</td></tr>")
        h.append(f"<tr><th>Phrase check</th><td>{sm['phrases']} phrases; {len(sm['missing'])} missing; {sm['checks']} minor checks "
                 "(clip holds, reused pictures) listed in the weekly review.</td></tr>")
        h.append("</table></div></div>")
    h.append("<p class='sub'>Built from shots.json revision 3 with today's routine edits, the reviewed phrase checks and the live quote. "
             "No generation, publishing or spending happens from this page.</p></main></body></html>")
    out = paths.REVIEW / batch_id / "preflight.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(h), encoding="utf-8")
    return out, hf_now, hf_add, el_now


if __name__ == "__main__":
    out, a, b_, c = build(sys.argv[1], sys.argv[2:])
    print(out, f"hf {a} + {b_}", f"el {c}")

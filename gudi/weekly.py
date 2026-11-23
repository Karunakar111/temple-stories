"""One weekly review page: decisions, the single approval, seven films, quote, status."""
import html
import json
from datetime import datetime, timezone

from .batch import quote_rows, totals
from .episodes import Episode, load_json
from .money import fmt, to_milli

CSS = """
@font-face{font-family:'Noto Sans Telugu';src:url('NotoSansTelugu_700Bold.ttf') format('truetype');font-weight:400 900}
:root{--paper:#fbf4e6;--ink:#2a1b22;--muted:#6f5a52;--gold:#b7791f;--line:#e5d6bd;--hold:#9b2c2c;--ok:#2f6b3a;--wait:#8a5a00}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 -apple-system,Segoe UI,Roboto,'Noto Sans Telugu',sans-serif}
main{max-width:1040px;margin:0 auto;padding:32px 20px 60px}h1{font-size:26px;margin:0 0 4px}h2{font-size:18px;margin:34px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
.sub{color:var(--muted)}.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;font-weight:600;border:1px solid currentColor}
.paused{color:var(--hold)}.ok{color:var(--ok)}.wait{color:var(--wait)}.hold{color:var(--hold)}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}
.dec h3{margin:0 0 6px;font-size:16px}.dec ul{margin:6px 0 8px 18px;padding:0}.opt{margin:4px 0}.opt b{color:var(--gold)}
.rec{background:#fff7e6;border-left:3px solid var(--gold);padding:6px 10px;margin-top:8px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);border-radius:12px;overflow:hidden}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:14px}th{background:#f4e9d6;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
td.n{text-align:right;font-variant-numeric:tabular-nums}code{background:#f4e9d6;padding:1px 5px;border-radius:4px;font-size:13px}
pre{background:#2a1b22;color:#fbf4e6;padding:12px;border-radius:8px;overflow:auto;font-size:13px}
video{width:270px;border-radius:10px;border:1px solid var(--line);background:#000}.flex{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start}
"""


def _e(s):
    return html.escape(str(s))


def build(batch, out_dir, balances, preview=None, demo=None):
    rows = quote_rows(batch)
    tot = totals(rows)
    dec = load_json(batch.root / "batches" / f"{batch.id}.decisions.json", {"decisions": []})["decisions"]
    eps = []
    for slug in batch.episodes:
        ep = Episode(slug, batch.root)
        er = [r for r in rows if r["episode"] == slug]
        n_still = sum(1 for r in er if r["asset"] == "still")
        n_clip = sum(1 for r in er if r["asset"] == "clip")
        clip_s = sum(int(r["seconds"] or 0) for r in er if r["asset"] == "clip")
        waits = sorted({r["blocked_by"] for r in er if r["blocked_by"]})
        if not ep.has_script():
            status, cls = "Script not received", "hold"
        elif any("waits for your decision" == r["status"] for r in er):
            status, cls = "Ready except shots waiting on D1/D2", "wait"
        elif waits:
            status, cls = "Ready except routine reference picks", "wait"
        else:
            status, cls = "Ready to approve", "ok"
        eps.append({"slug": slug, "slot": ep.meta.get("slot"), "title": ep.meta.get("title_te", ""),
                    "cover": ep.meta.get("cover_te", ""), "len": (ep.shots_doc or {}).get("est_total_s"),
                    "stills": n_still, "clips": n_clip, "clip_s": clip_s,
                    "hf": tot.get(slug, {}).get("higgsfield"), "el": tot.get(slug, {}).get("elevenlabs"),
                    "status": status, "cls": cls, "script": (ep.script_sha() or "")[:12]})
    hf_total = sum(e["hf"] or 0 for e in eps)
    el_total = sum(e["el"] or 0 for e in eps)

    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>Gudi Kathalu: week review</title><style>{CSS}</style></head><body><main>"]
    h.append(f"<h1>గుడి కథలు · {_e(batch.doc['title'])}</h1>")
    h.append("<p class='sub'>Seven films produced in one run, released one a day. "
             "<span class='pill paused'>Paid generation and publishing paused</span></p>")

    h.append("<h2>1. Decisions only you can make</h2>")
    for d in dec:
        h.append(f"<div class='card dec'><h3>{_e(d['id'])} · {_e(d['title'])}</h3><div class='sub'>Affects: {_e(', '.join(d['affects']))}</div><ul>")
        h += [f"<li>{_e(f)}</li>" for f in d["facts"]]
        h.append("</ul>")
        h += [f"<div class='opt'><b>{_e(o['key'])}</b> {_e(o['label'])} <span class='sub'>({_e(o['cost'])})</span></div>" for o in d["options"]]
        h.append(f"<div class='rec'>{_e(d['recommendation'])}</div></div>")

    if preview:
        h.append("<h2>2. EP02 technical preview</h2><div class='flex'>")
        h.append(f"<video controls playsinline preload='metadata' src='{_e(preview['src'])}'></video>")
        h.append("<div style='flex:1;min-width:280px'><ul>" + "".join(f"<li>{_e(x)}</li>" for x in preview["notes"]) + "</ul></div></div>")

    h.append("<h2>3. The seven films</h2><table><tr><th>#</th><th>Episode</th><th>Length</th><th>Paid stills</th><th>Clips</th>"
             "<th class='n'>Higgsfield</th><th class='n'>ElevenLabs</th><th>Status</th></tr>")
    for e in eps:
        h.append(f"<tr><td>{e['slot']}</td><td><b>{_e(e['title'])}</b><br><span class='sub'>{_e(e['cover'])}</span></td>"
                 f"<td>{'~%.0f s' % e['len'] if e['len'] else '-'}</td><td>{e['stills'] or '-'}</td>"
                 f"<td>{('%d (%d s)' % (e['clips'], e['clip_s'])) if e['clips'] else '-'}</td>"
                 f"<td class='n'>{fmt(e['hf']) if e['hf'] else '-'}</td><td class='n'>{fmt(e['el']) if e['el'] else '-'}</td>"
                 f"<td class='{e['cls']}'>{_e(e['status'])}</td></tr>")
    h.append(f"<tr><td></td><td><b>Week total (quotable films)</b></td><td></td><td></td><td></td><td class='n'><b>{fmt(hf_total)}</b></td>"
             f"<td class='n'><b>{fmt(el_total)}</b></td><td></td></tr></table>")
    bal = " · ".join(f"{k}: {v}" for k, v in balances.items())
    h.append(f"<div class='card'><b>Money check.</b> The five quotable films need {fmt(hf_total)} Higgsfield credits. "
             "Two more films at this week's average would add about " + fmt(round(hf_total / max(1, sum(1 for e in eps if e['hf'])) * 2 / 1000) * 1000) +
             f". ElevenLabs needs {fmt(el_total)} credits for five takes; its balance is not recorded yet. "
             "Caps you set in the approval bound the whole week, and anything that does not fit is held, not part-bought.</div>")
    h.append(f"<p class='sub'>Recorded balances: {_e(bal)}. The itemised quote lists every paid call (file: <code>quote-{_e(batch.id)}.csv</code>). "
             "ElevenLabs: one take per episode at 1 credit per character, verified with a free estimate (EP02 = 1,430). "
             "The connector would default to two takes; the pipeline pins one. Clip lengths are provisional until each take exists.</p>")

    h.append("<h2>4. One approval for the week</h2><div class='card'>"
             "<p>Approving covers <b>the scripts</b> (each pinned by its hash), <b>the visual approach</b> (reference boards and shot lists, "
             "timing excluded) and <b>the provider caps</b>. Retiming after narration stays inside it while scope and caps hold. "
             "If a take is missing, that episode's clips wait. A blocked episode never stops the others.</p>"
             f"<pre>python3 -m gudi batch approve {_e(batch.id)} --by Karunakar \\\n  --cap higgsfield=300 --cap elevenlabs=6000 \\\n"
             "  --release-start YYYY-MM-DD --i-have-reviewed</pre>"
             f"<p class='sub'>Suggested caps: the five-film quote plus a small margin (288 and 5,961). Seven films need higher caps once EP07-08 are quoted. Then, with paid generation switched on by you: <code>python3 -m gudi batch run {_e(batch.id)} --live</code></p></div>")

    h.append("<h2>4b. Itemised quote</h2><p class='sub'>Every paid call, per film. Status says what it waits for; nothing is bought.</p>")
    for e in eps:
        er = [r for r in rows if r["episode"] == e["slug"]]
        if not e["hf"]:
            h.append(f"<details class='card'><summary><b>{_e(e['slug'])}</b>: not quotable ({_e(e['status'])})</summary></details>")
            continue
        h.append(f"<details class='card'><summary><b>{_e(e['slug'])}</b>: Higgsfield {fmt(e['hf'])} · ElevenLabs {fmt(e['el'])} · {len(er)} calls</summary>"
                 "<table><tr><th>Beat</th><th>Asset</th><th>Model</th><th>Sec</th><th class='n'>Quote</th><th>Status</th></tr>")
        h += [f"<tr><td>{_e(r['beat'])}</td><td>{_e(r['asset'])}</td><td>{_e(r['model'])}</td><td>{_e(r['seconds'])}</td>"
              f"<td class='n'>{_e(r['quote'])}</td><td>{_e(r['status'])}{(' · ' + _e(r['blocked_by'])) if r['blocked_by'] else ''}</td></tr>" for r in er]
        h.append("</table></details>")

    if demo:
        h.append("<h2>5. Batch rehearsal with mock providers</h2><table><tr><th>Scenario</th><th>Result</th></tr>")
        h += [f"<tr><td>{_e(a)}</td><td>{_e(b)}</td></tr>" for a, b in demo]
        h.append("</table>")
    h.append(f"<p class='sub' style='margin-top:30px'>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by <code>python3 -m gudi batch review {_e(batch.id)}</code>.</p>")
    h.append("</main></body></html>")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text("\n".join(h), encoding="utf-8")
    return out_dir / "index.html", rows, eps

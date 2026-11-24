"""One weekly review page: the approval request first, then the seven films, the itemised quote,
what changed, the payload test and the rehearsal."""
import html
from datetime import datetime, timezone

from .batch import quote_rows, totals
from .episodes import Episode, load_json
from .money import fmt

CSS = """
@font-face{font-family:'Noto Sans Telugu';src:url('NotoSansTelugu_700Bold.ttf') format('truetype');font-weight:400 900}
:root{color-scheme:light;--paper:#fbf4e6;--ink:#2a1b22;--muted:#6f5a52;--gold:#b7791f;--line:#e5d6bd;--hold:#9b2c2c;--ok:#2f6b3a;--wait:#8a5a00}
*{box-sizing:border-box;min-width:0}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 -apple-system,Segoe UI,Roboto,'Noto Sans Telugu',sans-serif;overflow-x:clip}
main{max-width:1040px;margin:0 auto;padding:32px 18px 60px}h1{font-size:30px;line-height:1.1;margin:0 0 6px}h2{font-size:19px;margin:34px 0 10px;border-bottom:2px solid var(--line);padding-bottom:6px}
.sub{color:var(--muted)}.pill{display:inline-block;padding:2px 9px;border-radius:99px;font-size:13px;font-weight:600;border:1px solid currentColor}
.paused{color:var(--hold)}.ok{color:var(--ok)}.wait{color:var(--wait)}.hold{color:var(--hold)}
.card{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin:12px 0}
.ask{border:2px solid var(--gold)}.ask h2{border:0;margin-top:0}
ul{margin:6px 0 8px 18px;padding:0}li{margin:3px 0}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line)}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:14px}th{background:#f4e9d6;font-size:13px;color:var(--muted)}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}.scroll{overflow-x:auto}
code{background:#f4e9d6;padding:1px 5px;border-radius:4px;font-size:13px;overflow-wrap:anywhere}
pre{background:#2a1b22;color:#fbf4e6;padding:12px;border-radius:8px;overflow:auto;font-size:13px;white-space:pre-wrap}
video{width:240px;max-width:100%;border-radius:10px;border:1px solid var(--line);background:#000}.flex{display:flex;gap:18px;flex-wrap:wrap;align-items:flex-start}
details summary{cursor:pointer;font-weight:600}
"""


def _e(s):
    return html.escape(str(s))


def build(batch, out_dir, balances, preview=None, demo=None, payload=None, films=None):
    rows = quote_rows(batch)
    tot = totals(rows)
    dec = load_json(batch.root / "batches" / f"{batch.id}.decisions.json", {"resolved": [], "open": []})
    eps = []
    for slug in batch.episodes:
        ep = Episode(slug, batch.root)
        er = [r for r in rows if r["episode"] == slug]
        eps.append({"slug": slug, "slot": ep.meta.get("slot"), "title": ep.meta.get("title_te", ""),
                    "cover": ep.meta.get("cover_te", ""), "len": (ep.shots_doc or {}).get("est_total_s"),
                    "stills": sum(1 for r in er if r["asset"] == "still"),
                    "clips": sum(1 for r in er if r["asset"] == "clip"),
                    "clip_s": sum(int(r["seconds"] or 0) for r in er if r["asset"] == "clip"),
                    "hf": tot.get(slug, {}).get("higgsfield"), "el": tot.get(slug, {}).get("elevenlabs"),
                    "waits": sum(1 for r in er if r["status"].startswith("waits")), "calls": len(er)})
    hf_total = sum(e["hf"] or 0 for e in eps)
    el_total = sum(e["el"] or 0 for e in eps)
    cap_hf, cap_el = (hf_total + 999) // 1000 + 2, (el_total + 999) // 1000 + 100

    h = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
         f"<title>Gudi Kathalu week 1</title><style>{CSS}</style></head><body><main>"]
    h.append(f"<h1>గుడి కథలు · {_e(batch.doc['title'])}</h1>")
    h.append(f"<p class='sub'>Seven real scripts, produced in one run, released one a day. Quote: <b>{fmt(hf_total)}</b> Higgsfield credits "
             f"and <b>{fmt(el_total)}</b> ElevenLabs credits. <span class='pill paused'>Generation and publishing paused until you approve</span></p>")

    # ---------------------------------------------------------------- the one approval request
    h.append("<div class='card ask'><h2>Approval request</h2>")
    h.append("<p>One approval covers <b>the seven scripts</b> (each pinned by its hash), <b>the visual approach</b> "
             "(reference boards and shot lists below; timing excluded) and <b>these caps</b>:</p><ul>"
             f"<li>Higgsfield {cap_hf} credits for the week (quote {fmt(hf_total)}). Balance 356.05 on 24 Nov: top up about 10, "
             "or the last film that cannot fit whole waits.</li>"
             f"<li>ElevenLabs {cap_el} credits (quote {fmt(el_total)}: one take per film at 1 credit per character). Balance not recorded yet.</li>"
             "<li>Importing nine openly licensed exterior photos to Higgsfield (no credits). Until each exists, only the stills that need it wait.</li></ul>")
    h.append(f"<pre>python3 -m gudi balance record elevenlabs &lt;credits left&gt; --source \"subscription page\"\n"
             f"python3 -m gudi batch approve {_e(batch.id)} --by Karunakar \\\n  --cap higgsfield={cap_hf} --cap elevenlabs={cap_el} \\\n"
             "  --release-start YYYY-MM-DD --i-have-reviewed\npython3 -m gudi batch run week-1 --live</pre>")
    h.append("<p class='sub'>Inside that approval: retiming after each take, shot allocation within the shot list, free re-renders. "
             "Outside it: any new paid attempt, any change of what is drawn, any cap. A film is marked ready for review only when its own MP4 "
             "exists, decodes end to end and matches its narration; nothing is published.</p></div>")

    if dec.get("open"):
        h.append("<h2>Open items inside the request</h2>")
        for d in dec["open"]:
            h.append(f"<div class='card'><b>{_e(d['id'])} · {_e(d['title'])}</b><div>{_e(d['detail'])}</div><div class='sub'>{_e(d['ask'])}</div></div>")

    # ---------------------------------------------------------------- seven films
    h.append("<h2>The seven films</h2><div class='scroll'><table><tr><th>#</th><th>Episode</th><th>Length</th><th>Stills</th><th>Clips</th>"
             "<th class='n'>Higgsfield</th><th class='n'>ElevenLabs</th><th>Waiting on</th></tr>")
    for e in eps:
        w = f"<span class='wait'>{e['waits']} still(s): exterior photo</span>" if e["waits"] else "<span class='ok'>nothing</span>"
        h.append(f"<tr><td>{e['slot']}</td><td><b>{_e(e['title'])}</b><br><span class='sub'>{_e(e['cover'])}</span></td>"
                 f"<td>{'~%.0f s' % e['len'] if e['len'] else '-'}</td><td>{e['stills']}</td><td>{e['clips']} ({e['clip_s']} s)</td>"
                 f"<td class='n'>{fmt(e['hf'])}</td><td class='n'>{fmt(e['el'])}</td><td>{w}</td></tr>")
    h.append(f"<tr><td></td><td><b>Week</b></td><td></td><td>{sum(e['stills'] for e in eps)}</td><td>{sum(e['clips'] for e in eps)}"
             f" ({sum(e['clip_s'] for e in eps)} s)</td><td class='n'><b>{fmt(hf_total)}</b></td><td class='n'><b>{fmt(el_total)}</b></td><td></td></tr></table></div>")
    h.append("<p class='sub'>Prices: Higgsfield free estimates (2 per 2k still; Kling 3.0 pro, sound off, 1.5 per second, 3 s minimum). "
             "ElevenLabs verified with a free estimate (EP02 = 1,430); the chat connector would default to two takes, the pipeline pins one. "
             "Clip lengths are provisional until each take exists. For scale: EP01's assets in the final film cost 242.5; this week averages "
             f"about {fmt(round(hf_total / 7 / 1000) * 1000)} per film because most shots are stills with local motion.</p>")

    # ---------------------------------------------------------------- phrase-to-visual check
    h.append(_visual_check_section(batch))

    # ---------------------------------------------------------------- itemised quote
    h.append(f"<h2>Itemised quote</h2><p class='sub'>Every paid call ({len(rows)}). Also in <code>quote-{_e(batch.id)}.csv</code>.</p>")
    for e in eps:
        er = [r for r in rows if r["episode"] == e["slug"]]
        h.append(f"<details class='card'><summary>{_e(e['slug'])}: Higgsfield {fmt(e['hf'])} · ElevenLabs {fmt(e['el'])} · {len(er)} calls</summary>"
                 "<div class='scroll'><table><tr><th>Beat</th><th>Asset</th><th>Model</th><th>Sec</th><th class='n'>Quote</th><th>Status</th></tr>")
        h += [f"<tr><td>{_e(r['beat'])}</td><td>{_e(r['asset'])}</td><td>{_e(r['model'])}</td><td>{_e(r['seconds'])}</td>"
              f"<td class='n'>{_e(r['quote'])}</td><td>{_e(r['status'])}</td></tr>" for r in er]
        h.append("</table></div></details>")

    # ---------------------------------------------------------------- changes
    h.append("<h2>What changed since the last review</h2>")
    for d in dec.get("resolved", []):
        h.append(f"<div class='card'><b>{_e(d['title'])}:</b> {_e(d['answer'])}<div class='sub'>{_e(d['applied'])}</div></div>")
    h.append("<div class='card'><b>Character sheets:</b> EP03 and EP05 each saved two sheets to one file name (<code>C1-still.png</code>) and every "
             "shot referred to an ambiguous <code>C1:still</code>. Each sheet now has its own beat (<code>CS-FAMILY</code>, <code>CS-NARENDRA</code>, "
             "<code>CS-YADA</code>, <code>CS-DEVOTEE</code>, and so on), files are episode-prefixed (<code>ep03-CS-NARENDRA-still.png</code>), "
             "and the shot-list build refuses any shared file name or dangling reference.</div>")
    h.append("<div class='card'><b>References resolve to media ids before any reservation:</b> board references use their Higgsfield "
             "media id; generated references use the completed job of exactly that request; a reference without an id holds that call only. "
             "Previously the adapter sent placeholders such as <code>&lt;S02:still&gt;</code>.</div>")

    if payload:
        h.append("<h2>Zero-spend payload test</h2><div class='card'><ul>" + "".join(f"<li>{_e(x)}</li>" for x in payload) + "</ul></div>")
    if films:
        h.append("<h2>Rehearsal: seven films rendered and checked (mock assets)</h2>")
        if films.get("video"):
            h.append(f"<div class='flex'><video controls playsinline preload='metadata' src='{_e(films['video'])}'></video>"
                     f"<div style='flex:1;min-width:260px'><p class='sub'>{_e(films['caption'])}</p></div></div>")
        h.append("<div class='scroll'><table><tr><th>Film</th><th>Result</th><th class='n'>Length</th><th class='n'>Take</th><th>Decode</th>"
                 "<th class='n'>Narration match</th><th class='n'>Attempts</th></tr>")
        for f in films["rows"]:
            h.append(f"<tr><td>{_e(f[0])}</td><td>{_e(f[1])}</td><td class='n'>{_e(f[2])}</td><td class='n'>{_e(f[3])}</td><td>{_e(f[4])}</td>"
                     f"<td class='n'>{_e(f[5])}</td><td class='n'>{_e(f[6])}</td></tr>")
        h.append("</table></div>")
    if demo:
        h.append("<div class='scroll'><table><tr><th>#</th><th>Rehearsal check</th></tr>")
        h += [f"<tr><td>{_e(a)}</td><td>{_e(b)}</td></tr>" for a, b in demo]
        h.append("</table></div>")
    if preview:
        h.append("<h2>EP02 technical preview (from the last review)</h2><div class='flex'>")
        h.append(f"<video controls playsinline preload='metadata' src='{_e(preview['src'])}'></video>")
        h.append("<div style='flex:1;min-width:260px'><ul>" + "".join(f"<li>{_e(x)}</li>" for x in preview["notes"]) + "</ul></div></div>")
    h.append(f"<p class='sub' style='margin-top:30px'>Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by "
             f"<code>python3 -m gudi batch review {_e(batch.id)}</code>.</p></main></body></html>")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text("\n".join(h), encoding="utf-8")
    return out_dir / "index.html", rows, eps


def _visual_check_section(batch):
    """Every narration phrase against the picture planned for it, before credits or renders."""
    from .visual_check import rows, summary

    out = ["<h2>Phrase-to-visual check</h2><p class='sub'>Every narration phrase against the picture planned for that moment. "
           "<b class='hold'>Missing</b> means the voice brings in a person, action or idea that nothing on screen shows; each has the "
           "fix and its quoted cost. <b>Check</b> items are judgement calls or zero-cost fixes. Run before generation; nothing here is spent.</p>"]
    out.append("<div class='scroll'><table><tr><th>Episode</th><th class='n'>Phrases</th><th class='n'>Missing</th><th class='n'>Checks</th>"
               "<th class='n'>Cost to fix missing</th></tr>")
    detail, tot = [], 0.0
    for slug in batch.episodes:
        ep = Episode(slug, batch.root)
        if not (ep.dir / "shots.json").exists():
            continue
        sm = summary(ep)
        tot += sm["quote_if_fixed"]
        out.append(f"<tr><td>{_e(slug)}</td><td class='n'>{sm['phrases']}</td>"
                   f"<td class='n'>{'<b class=hold>%d</b>' % len(sm['missing']) if sm['missing'] else '0'}</td>"
                   f"<td class='n'>{sm['checks']}</td><td class='n'>{fmt(round(sm['quote_if_fixed'] * 1000))}</td></tr>")
        r, _ = rows(ep)
        flagged = [x for x in r if x["flags"]]
        if not flagged:
            continue
        d = [f"<details{' open' if sm['missing'] else ''}><summary><b>{_e(slug)}</b>: {len(sm['missing'])} missing, {sm['checks']} to check</summary>"
             "<div class='scroll'><table><tr><th class='n'>Time</th><th>Shot</th><th>Narration</th><th>Planned picture</th><th>Flag</th></tr>"]
        for x in flagged:
            fl = "<br>".join(f"<b class='{'hold' if sev == 'missing' else 'wait'}'>{_e(sev)}</b> {_e(msg)}" for sev, msg in x["flags"])
            d.append(f"<tr><td class='n'>~{x['t']:.0f} s</td><td>{_e(x['asset'])}</td><td>{_e(x['words'])}</td>"
                     f"<td>{_e(x['picture'][:160])}</td><td>{fl}</td></tr>")
        d.append("</table></div></details>")
        detail.append("".join(d))
    out.append(f"<tr><td><b>Week</b></td><td></td><td></td><td></td><td class='n'><b>{fmt(round(tot * 1000))}</b></td></tr></table></div>")
    out.extend(detail)
    return "\n".join(out)

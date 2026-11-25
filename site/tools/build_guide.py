#!/usr/bin/env python3
"""Build a Gudi Kathalu temple guide page from a JSON content file.

Usage:  python3 site/tools/build_guide.py site/<slug>/guide.json
Writes: site/<slug>/index.html

Layout, CSS, the stop-by-stop JS and the map band come from site/tools/template.html
(a copy of a finished guide). Only the content changes per temple. Every text field
is a [telugu, english] pair. See docs/GUIDE-PLAYBOOK.md for the content rules.
"""
import json, re, sys, html
from pathlib import Path
from urllib.parse import quote_plus

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
LIC = {
    'CC0': ('CC0 1.0', 'https://creativecommons.org/publicdomain/zero/1.0/'),
    'CC BY 2.0': ('CC BY 2.0', 'https://creativecommons.org/licenses/by/2.0/'),
    'CC BY 3.0': ('CC BY 3.0', 'https://creativecommons.org/licenses/by/3.0/'),
    'CC BY 4.0': ('CC BY 4.0', 'https://creativecommons.org/licenses/by/4.0/'),
    'CC BY-SA 2.0': ('CC BY-SA 2.0', 'https://creativecommons.org/licenses/by-sa/2.0/'),
    'CC BY-SA 3.0': ('CC BY-SA 3.0', 'https://creativecommons.org/licenses/by-sa/3.0/'),
    'CC BY-SA 4.0': ('CC BY-SA 4.0', 'https://creativecommons.org/licenses/by-sa/4.0/'),
    'CC BY-NC-ND 2.0': ('CC BY-NC-ND 2.0', 'https://creativecommons.org/licenses/by-nc-nd/2.0/'),
    'Public domain': ('Public domain', 'https://creativecommons.org/publicdomain/mark/1.0/'),
}


def e(s):
    return html.escape(str(s), quote=False)


def t(pair):
    """[te, en] -> bilingual spans."""
    te, en = pair
    return f'<span class="te">{e(te)}</span><span class="en">{e(en)}</span>'


def li(pairs, indent=10):
    pad = ' ' * indent
    return '\n'.join(f'{pad}<li>{t(p)}</li>' for p in pairs)


def maps(coords):
    c = quote_plus(coords)
    return (f'https://maps.google.com/maps?q={c}&z=15&output=embed',
            f'https://www.google.com/maps/dir/?api=1&destination={c}',
            f'https://www.google.com/maps/search/?api=1&query={c}')


def body(g):
    emb, dirl, openl = maps(g['map']['coords'])
    h = g['hero']
    ph = h['photo']
    pos = f' style="object-position:{ph["position"]}"' if ph.get('position') else ''
    facts = '\n'.join(
        f'  <div class="fact"><b>{t(f["value"]) if isinstance(f["value"], list) else e(f["value"])}</b>{t(f["desc"])}</div>'
        for f in g['facts'])
    notice = ''
    if g.get('notice'):
        n = g['notice']
        notice = f'''<section class="band notice" id="notice">
  <div class="wrap"><div class="noticebox"><b>{t(n['title'])}</b><p>{t(n['text'])}</p></div></div>
</section>

'''
    story = '\n'.join(f'      <p>{t(p)}</p>' for p in g['story']['paras'])
    plan = g['plan']
    nearby = ''
    if g.get('nearby'):
        cards = []
        for n in g['nearby']:
            if n.get('href'):
                cards.append(f'      <a class="card" href="{e(n["href"])}" style="text-decoration:none;color:inherit"><h3>{t(n["title"])}</h3><p>{t(n["text"])}</p></a>')
            else:
                cards.append(f'      <div class="card"><h3>{t(n["title"])}</h3><p>{t(n["text"])}</p></div>')
        nearby = f'''<section class="band" id="nearby" style="padding-bottom:0">
  <div class="wrap">
    <h2>{t(["దగ్గర్లో", "Nearby"])}</h2>
    <div class="cols" style="margin-top:0">
{chr(10).join(cards)}
    </div>
  </div>
</section>

'''
    online = g['sevas']['online']
    status = ('<span class="status">' + t(online['status']) + '</span>\n        ') if online.get('status') else ''
    links = '\n        '.join(
        f'<a class="btn" style="border-color:var(--ink);color:var(--ink)" href="{e(u)}">{e(lbl)}</a>' for lbl, u in online['links'])
    day = '\n'.join(f'      <dt>{e(tm)}</dt><dd>{t([te, en])}</dd>' for tm, te, en in g['day'])
    credits = []
    for c in g['credits']:
        name, url = LIC[c['license']]
        modified = ' (not modified)' if 'ND' in c['license'] else ''
        credits.append(f'      <li>{t(c["what"])}: {e(c["author"])}, <a href="{url}">{name}</a>, <a href="{e(c["source"])}">{e(c.get("site", "Wikimedia Commons"))}</a>{modified}</li>')
    n_stops = len(g['stops'])
    temple_te, temple_en = g['short_name']
    return f'''<div lang="te" id="root">

<div class="top">
  <a class="brand" href="/"><span class="te">గుడి కథలు</span><span class="en">Gudi Kathalu</span></a>
  <div class="langs" role="group" aria-label="Language">
    <button id="b-te" type="button" aria-pressed="true">తెలుగు</button>
    <button id="b-en" type="button" aria-pressed="false">English</button>
  </div>
</div>

<header class="hero" id="top">
  <div class="htext">
    <h1>{t(h['h1'])}</h1>
    <div class="sub">{t(h['sub'])}</div>
    <p>{t(h['lead'])}</p>
    <div class="heroact"><a class="btn mapbtn solid" href="{dirl}"><span class="te">దారి చూపించు</span><span class="en">Get directions</span></a><a class="btn mapbtn" href="#map"><span class="te">మ్యాప్</span><span class="en">Map</span></a></div>
  </div>
  <figure class="scene">
    <img src="{e(ph['src'])}" alt="{e(ph['alt'])}"{pos}>
    <figcaption>{t(ph['caption'])}. Photo: {e(ph['credit'])}</figcaption>
  </figure>
</header>

<section class="facts" aria-label="Quick facts">
{facts}
</section>

{notice}<section class="band mapband" id="map">
  <div class="wrap mapgrid">
    <div class="mapbox"><iframe src="{emb}" title="Map" loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe></div>
    <div>
      <h2><span class="te">ఎక్కడ ఉంది, ఎలా వెళ్ళాలి</span><span class="en">Location and directions</span></h2>
      <p class="addr">{t(g['map']['addr'])}</p>
      <ul class="tick">
{li(g['map']['rows'])}
      </ul>
      <div class="heroact" style="margin-top:16px">
        <a class="btn mapbtn solid" href="{dirl}"><span class="te">Google Maps లో దారి</span><span class="en">Directions in Google Maps</span></a>
        <a class="btn mapbtn" href="{openl}"><span class="te">మ్యాప్‌లో చూడండి</span><span class="en">Open in Maps</span></a>
      </div>
    </div>
  </div>
</section>

<section class="band" id="story">
  <div class="wrap story">
    <div>
      <h2>{t(g['story']['h2'])}</h2>
{story}
    </div>
    <aside class="reel">
      <h3><span class="te">రీల్‌లో కథ చూడండి</span><span class="en">Watch the story</span></h3>
      <p>{t(g['story']['episode'])}</p>
      <a class="btn solid" href="https://www.instagram.com/gudikathalu/">Instagram</a>
      <a class="btn" href="https://www.youtube.com/@gudikathalutelugu">YouTube</a>
    </aside>
  </div>
</section>

<section class="band" id="plan" style="padding-top:0">
  <div class="wrap">
    <h2><span class="te">ప్రయాణం ప్లాన్ చేసుకోండి</span><span class="en">Plan the trip</span></h2>
    <div class="grid3">
      <div class="card"><h3><span class="te">కారులో</span><span class="en">By car</span></h3><p>{t(plan['car'])}</p></div>
      <div class="card"><h3><span class="te">బస్సులో</span><span class="en">By bus</span></h3><p>{t(plan['bus'])}</p></div>
      <div class="card"><h3><span class="te">రైలులో</span><span class="en">By train</span></h3><p>{t(plan['train'])}</p></div>
    </div>
    <div class="cols">
      <div class="card">
        <h3><span class="te">ఎప్పుడు వెళ్ళాలి</span><span class="en">When to go</span></h3>
        <ul class="tick">
{li(g['when'], 10)}
        </ul>
        <p class="note">{t(g['when_note'])}</p>
      </div>
      <div class="card">
        <h3><span class="te">వెంట తీసుకెళ్ళండి</span><span class="en">What to carry</span></h3>
        <ul class="tick">
{li(g['carry'], 10)}
        </ul>
      </div>
    </div>
  </div>
</section>

<section class="band routeband" id="visit">
  <div class="wrap">
    <div class="vhead">
      <div>
        <h2><span class="te">గుడిలో ఉన్నప్పుడు: అడుగడుగునా</span><span class="en">At the temple: stop by stop</span></h2>
        <p class="note" style="margin:-8px 0 0"><span class="te">ఒక్కో చోటు చూసాక "దర్శించాను" నొక్కండి. పక్కకు స్వైప్ చేసి తర్వాతి చోటుకు వెళ్ళండి.</span><span class="en">Tap "Seen" at each stop, then swipe to the next one.</span></p>
      </div>
      <div class="prog" aria-live="polite"><b id="cnt">0</b>/{n_stops} <span class="te">దర్శించారు</span><span class="en">seen</span><div class="bar"><i id="barfill"></i></div></div>
    </div>
    <div class="rail" id="rail" tabindex="0" aria-label="Temple stops"></div>
    <div class="railnav">
      <button type="button" class="nav" id="prev" aria-label="Previous stop">&#8592;</button>
      <button type="button" class="nav" id="next" aria-label="Next stop">&#8594;</button>
    </div>
    <div class="donecard" id="donecard" hidden>
      <svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="54" style="fill:#FBF2E6"/><circle cx="60" cy="60" r="44" style="fill:none;stroke:#2a1f18;stroke-width:3;stroke-dasharray:4 6"/><path d="M38 62 l14 14 l30 -32" style="fill:none;stroke:#2a1f18;stroke-width:9;stroke-linecap:round;stroke-linejoin:round"/></svg>
      <div>
        <h3><span class="te">{e(temple_te)} యాత్ర పూర్తి!</span><span class="en">{e(temple_en)} yatra complete!</span></h3>
        <p><span class="te">అన్ని చోట్లూ దర్శించారు. ఈ పేజీని మీ కుటుంబంతో పంచుకోండి, రీల్‌లో @gudikathalu ని ట్యాగ్ చేయండి.</span><span class="en">You saw every stop. Share this page with your family and tag @gudikathalu in your reel.</span></p>
        <a class="btn solid" id="wa" href="https://wa.me/">WhatsApp</a>
        <button type="button" class="btn" id="reset"><span class="te">మళ్ళీ మొదలు</span><span class="en">Start again</span></button>
      </div>
    </div>
    <aside class="miss">
      <h3><span class="te">చాలామంది మిస్ అయ్యేవి</span><span class="en">What most people miss</span></h3>
      <ul>
{li(g['miss'], 8)}
      </ul>
    </aside>
  </div>
</section>

{nearby}<section class="band" id="seva">
  <div class="wrap">
    <h2><span class="te">సేవలు, ఆన్‌లైన్ బుకింగ్</span><span class="en">Sevas and online booking</span></h2>
    <div class="cols" style="margin-top:0">
      <div class="card">
        <h3><span class="te">గుడిలో జరిగే సేవలు, మొక్కులు</span><span class="en">Sevas and offerings</span></h3>
        <p>{t(g['sevas']['at_temple'])}</p>
        <p class="note">{t(g['sevas']['note'])}</p>
      </div>
      <div class="card">
        {status}<h3><span class="te">ఆన్‌లైన్ సేవ, ప్రసాదం</span><span class="en">Online seva and prasadam</span></h3>
        <p>{t(online['text'])}</p>
        {links}
      </div>
    </div>
  </div>
</section>

<section class="band routeband" id="day">
  <div class="wrap">
    <h2><span class="te">ఒక రోజు ట్రిప్ ఇలా</span><span class="en">A one-day plan</span></h2>
    <dl class="plan">
{day}
    </dl>
    <p class="note" style="margin-top:12px">{t(g['day_note'])}</p>
  </div>
</section>

<footer class="band">
  <div class="wrap">
    <h3 style="font-size:24px"><span class="te">గుడి కథలు</span><span class="en">Gudi Kathalu</span></h3>
    <p><span class="te">ఈ వివరాలు {e(g['checked'][0])}లో పబ్లిక్ సమాచారం నుంచి సేకరించాం. సమయాలు, సేవలు మారవచ్చు. మీరు వెళ్ళి వచ్చాక ఏదైనా మారితే Instagram లో </span><span class="en">Details gathered from public sources in {e(g['checked'][1])}. Timings and sevas can change. Visited and found something different? Message </span><a href="https://www.instagram.com/gudikathalu/">@gudikathalu</a><span class="te"> కి మెసేజ్ చేయండి.</span><span class="en"> on Instagram.</span></p>
    <h3 style="font-size:18px;margin-top:18px"><span class="te">ఫోటోలు</span><span class="en">Photo credits</span></h3>
    <p style="font-size:14px;margin:0 0 6px"><span class="te">ఫోటోలు తీసి ఉచితంగా పంచుకున్న ఫోటోగ్రాఫర్లకు ధన్యవాదాలు. చిత్రాలను పేజీకి సరిపడేలా కత్తిరించాం; NoDerivatives (ND) చిత్రాలను మార్చలేదు.</span><span class="en">Thank you to the photographers who shared these freely. Images are cropped to fit the page; NoDerivatives (ND) images are shown unchanged.</span></p>
    <p style="font-size:14px;margin:0 0 10px">{t(g['photo_ask'])}</p>
    <ul class="credits">
{chr(10).join(credits)}
      <li><span class="te">మిగతావి గుడి కథలు చిత్రాలు</span><span class="en">Other pictures are Gudi Kathalu illustrations</span></li>
    </ul>
  </div>
</footer>

</div>
'''


NOTICE_CSS = '''.notice{padding-block:18px}
.noticebox{background:#5E1620;color:#FBF2E6;border-radius:16px;padding:16px 20px}
.noticebox b{font-family:"Tiro Telugu",serif;font-weight:400;font-size:20px;display:block;margin-bottom:4px}
.noticebox p{margin:0}
'''


def build(path):
    g = json.loads(Path(path).read_text())
    tpl = (HERE / 'template.html').read_text()
    head = tpl[:tpl.index('<body>') + len('<body>\n')]
    script = tpl[tpl.rindex('<script>\n{'):]
    slug = g['slug']
    head = re.sub(r'<title>[^<]*</title>', f'<title>{e(g["title"])}</title>', head)
    head = re.sub(r'<meta name="description"[^>]*>', f'<meta name="description" content="{e(g["description"])}">', head)
    head = re.sub(r'<meta property="og:title"[^>]*>', f'<meta property="og:title" content="{e(g["title"])} | Gudi Kathalu">', head)
    head = re.sub(r'<meta property="og:image"[^>]*>', f'<meta property="og:image" content="https://gudikathalu.vercel.app/{slug}/{g["hero"]["photo"]["src"]}">', head)
    if '.noticebox{' not in head:
        head = head.replace('footer{background', NOTICE_CSS + 'footer{background', 1)
    stops = [s['text'] for s in g['stops']]
    photos = {}
    arts = []
    for i, s in enumerate(g['stops']):
        arts.append(s.get('art', 3))
        p = s.get('photo')
        if p:
            v = [p['src'], p['caption'][0], p['caption'][1], p['credit']]
            if p.get('whole'):
                v.append(1)
            photos[i] = v
    js = lambda v: json.dumps(v, ensure_ascii=False)
    a = script.index('  const stops = ['); b = script.index('  const tt = (a, b) =>')
    block = ('  const stops = [\n' + ',\n'.join('    ' + js(x) for x in stops) + '\n  ];\n'
             + '  const photos = {\n' + ',\n'.join(f'    {k}: {js(v)}' for k, v in photos.items()) + '\n  };\n'
             + f'  const artFor = {js(arts)};\n')
    script = script[:a] + block + script[b:]
    script = script.replace('${art[i]}', '${art[artFor[i]]}')
    script = re.sub(r"const msg = '[^']*';", "const msg = " + js(g['share_msg'] + f' https://gudikathalu.vercel.app/{slug}/') + ";", script)
    script = re.sub(r"'gk-[a-z]+-seen'", f"'gk-{slug}-seen'", script)
    n = len(stops)
    script = script.replace('seen.length / 9 * 100', f'seen.length / {n} * 100').replace('seen.length < 9', f'seen.length < {n}').replace('if (i < 8)', f'if (i < {n - 1})')
    out = head + body(g) + '\n' + script
    dest = SITE / slug / 'index.html'
    dest.write_text(out)
    print('wrote', dest, len(out), 'bytes')


if __name__ == '__main__':
    build(sys.argv[1])

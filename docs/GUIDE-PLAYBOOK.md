# Gudi Kathalu temple guide playbook

How a new temple guide is researched, built and published on **gudikathalu.vercel.app**.
The daily scheduled task follows this file. Karunakar can edit it at any time.

Goal: the guide for the temple in today's 6 PM IST reel is live **before 17:45 IST**, so the
Instagram bio link already shows it when the reel goes out.

## 1. Pick today's temple

- Open `publishing/guide-schedule.json`. Today's date in IST picks the entry.
- `status: "done"`, or `site/<slug>/index.html` already exists: nothing to build. Report that and stop.
- No entry for today: report "no schedule entry for <date>; add the week's list to publishing/guide-schedule.json" and stop.
- `hook` is the reel's question. The story section should answer it.

## 2. Research (every fact needs a source)

Search the web for each of these. Prefer official temple / Endowments / state tourism sites, then reputable news.

1. **Current status first.** Search `<temple> darshan news` for the last few months: closures, renovation,
   darshan moved to another shrine, festival-only rules. Vemulawada (main temple closed, darshan at
   Bheemeshwara) is the example of why. If darshan has moved, the page gets a `notice`, the map points
   to where darshan actually happens, and the stops follow the current arrangement.
2. Legend / sthala puranam that answers the hook. Tell it as "devotees believe" / "the legend says".
3. Timings. If sources disagree, show the common range in the facts card and say "confirm before you go".
4. How to reach: distance from Hyderabad (or the nearest big city for temples outside Telangana), road,
   bus, nearest railway station, airport if useful.
5. Festivals and the busiest days; quiet times.
6. Dress code, what to carry, safety (crowds, steps, sun).
7. Sevas and online booking: official site, TTD / T App Folio / MeeSeva / state Endowments portal.
   Only mark online booking as available when an official page confirms it for this temple.
8. The visit, in order: 6 to 9 stops a visitor actually passes. Never invent layout details; when the
   order is not documented, use "what to see and do" stops and keep each one true on its own.
9. One or two nearby temples, plus a link card to another Gudi Kathalu guide when it is genuinely nearby
   or related.

Editorial rules (from the channel):
- No fabricated facts, prices, phone numbers or timings. Unsure means leave it out or say "confirm".
- Sacred images: use a real, credited photo of the deity only if a free-licensed one exists; never an
  AI image or a drawing of the deity. Drawings show light, doorways, devotees and exteriors.
- Plain Telugu that a devotee reads easily; English is a faithful version of the same text.
- No em dashes in the visible text.

## 3. Map coordinates

Use the temple's own Google Maps listing: open
`https://www.google.com/maps/search/?api=1&query=<temple name>` in Chrome, open the top listing, and take
`!3d<lat>!4d<lng>` from the URL. If darshan has moved, use the place where darshan happens now.
Without Chrome, use Wikipedia's coordinates and say so in the report. The page uses coordinates, not
names: the Google embed resolves names unreliably.

## 4. Photos (free licences only, every one credited)

Allowed: CC0, public domain, CC BY, CC BY-SA, CC BY-NC-ND (shown whole and unchanged: set `"whole": true`).
Never use photos from blogs, news sites or Google Images.

With Claude in Chrome (the workspace shell cannot reach Wikimedia):
1. Open `https://commons.wikimedia.org/wiki/Main_Page` and query the API from the page with
   `fetch('/w/api.php?action=query&generator=search&gsrsearch=<terms>&gsrnamespace=6&gsrlimit=50&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=1600&format=json&origin=*')`.
   Search several spellings. Keep only files that really show this temple (check the description,
   not just the title). Note Artist, LicenseShortName and the file page URL.
2. Also check Flickr: `https://www.flickr.com/search/?text=<temple>&license=1%2C2%2C3%2C4%2C5%2C6%2C9%2C10`.
   Capture Flickr images from a Commons tab, not the Flickr tab (an extension draws a badge over Flickr pages).
3. Capture: replace the page with a black page holding one `<img>` at `max-width:100vw;max-height:100vh`
   anchored top-left, hide the cursor (`*{cursor:none!important}`), hover the bottom-right corner, take
   a screenshot with `save_to_disk: true, scale: 1`, read the rendered size, then crop that rectangle
   from the saved file with Pillow into `site/<slug>/img/<name>.jpg` (quality about 80).
4. A sanctum or interior photo is fine only if it is free-licensed and clearly of this temple.

Without Chrome: publish with the built-in drawings, and list the photos still needed in the report.

## 5. Write the content and build

1. Copy `site/vemulawada/guide.json` as the pattern and write `site/<slug>/guide.json`.
   - Every visible text is a `["telugu", "english"]` pair.
   - `facts`: exactly 4 (distance, timings, time needed, dress).
   - `notice`: only when something important differs from normal (closure, moved darshan).
   - `stops`: 6 to 9. Each has `text` (6 strings: title te/en, description te/en, look-for te/en) and
     either a `photo` or an `art` drawing index:
     0 steps and water tap, 1 Nandi mandapam, 2 oath at a pedestal, 3 lamplit sanctum doorway,
     4 garlanded shrine door, 5 shrine with a pradakshina path, 6 museum, 7 small temple with a
     distance sign, 8 white marble temple, 9 hill with a ghat road, 10 temple tank.
     The hero needs an image: without a photo, use a drawing rendered to `img/hero.jpg` and set the
     hero `credit` to "" so the caption does not say "Photo".
   - `credits`: one entry per photo; `license` must be a key in `LIC` in `site/tools/build_guide.py`.
2. Build: `python3 site/tools/build_guide.py site/<slug>/guide.json`
3. Test in headless Chrome (Playwright, `executable_path="/usr/bin/google-chrome"`) at 1280 and 390 px:
   no page errors, `document.documentElement.scrollWidth` equals the viewport width, every "Seen"
   button works and the completion card appears, English toggle works.
4. Home page: in `site/index.html`, insert a new card right after the `<!-- cards:start ... -->` comment,
   newest first (copy the markup of the card below it), and add the photographer to the footer line.
5. In `publishing/guide-schedule.json` set today's entry to `"status": "done"`.

## 6. Publish

```
git checkout -b guide/<slug> origin/main
git add site publishing
git commit -m "Add <Temple> guide (EP<n>)"     # end with the session's attribution lines
git push -u origin guide/<slug>
git push origin guide/<slug>:main              # fast-forward main; Vercel deploys main automatically
```
If main has moved and the fast-forward is refused, rebase onto `origin/main` and push again.
Wait about a minute, then open `https://gudikathalu.vercel.app/<slug>/` and check it loads with its photos.

## 7. Report to Karunakar

Send a short message: the live link, the 2 to 4 facts he should double-check (conflicting timings,
anything marked "confirm", a closure), the photos still missing, and the one-line pinned-comment text
for the reel. Never post to Instagram/YouTube, never spend Higgsfield/ElevenLabs credits, never change
Vercel or GitHub settings, and do not touch files outside `site/`, `publishing/` and this playbook.

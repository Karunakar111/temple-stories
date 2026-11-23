# Episode 1 (full): timed visual plan, revision 2

**Timing candidate: `audio/01-mallanna-full-paced.mp3`, 107.84 s, 3235 frames @ 30 fps.**
No new take. Narration text: `script/01-komuravelli-mallanna-narration.txt`.

**No paid image or video job has been run.**

## 1. Verification of this audio

**It is the verified take plus pauses, nothing else.** Compared against the source take
`audio/01-mallanna-full.mp3` (104.24 s) at 11 points across the film: correlation 1.000 at
every point, with every offset matching the seven documented pause inserts (+3.60 s total).
So the speech-to-text check done on that take applies word for word to this file.

**Contents against the final script:** 198 written words, 197 spoken. No sentence missing,
nothing added, every beat present and in order. The single dropped word is a contraction
(ఎల్లమ్మకు ఇచ్చిండు, spoken ఎల్లమ్మకిచ్చిండు).

**Names:** మల్లన్న (9), మేడలమ్మ (2), బండారి (7), గంగమ్మ (1) all spoken correctly and evenly.
ఎల్లమ్మ at 31.41 s is quick (0.30 s), with a 0.35 s pause added before it. Accepted as is.

**Dialect, correcting the earlier note:** the -ిండు / -ిండ్రు forms stay Telangana
(చేరిండు, కనిపెట్టిండ్రు, పోయిండు, బయలుదేరిండు). The -న్నడు forms come out standard
(పెళ్లాడాలనుకున్నాడు, మార్చుకున్నాడు, గెలుచుకున్నాడు, తెలుసుకున్నాడు), as do the habitual
endings (-తారు, -న్నాయి) and -గా, -లి. Captions should follow the script; the audio is accepted.

**Timing method:** all 47 pauses in this file measured with FFmpeg silence detection. Every cut
below sits inside a measured pause. The 20 name timestamps from the forced alignment, shifted
by the pause inserts, each land inside the phrase assigned to them.

## 2. Beat plan

Times are cut points in the master. "Spoken" is what the voice actually says.

| # | Time | Spoken | Viewer sees | What changes | Asset |
|---|---|---|---|---|---|
| 1 | 0.00–3.04 | కొమురవెల్లి మల్లన్న జాతరలో మీరు చల్లే పసుపు | A hand flings turmeric into the dusk sky | Opens on the object of the story | Reuse `a2-throw` 0.0–3.04 |
| 2 | 3.04–5.16 | దాని వెనుక కథ తెలుసా? | Close on a hand letting turmeric pour onto a heap | From the crowd's gesture to one devotee's hand | Reuse `a4-hand` 0.0–2.12 |
| 3 | 5.16–7.98 | హైదరాబాద్ నుంచి ఎనభై ఐదు కిలోమీటర్లు | Map card: a line draws from Hyderabad toward Siddipet, "85 కి.మీ." counts up | Place begins: distance first | **New, free** (code-drawn map) |
| 4 | 7.98–10.21 | సిద్దిపేట జిల్లా, కొమురవెల్లి | The rocky hill with the temple at dusk; name title fades in | Map gives way to the real place | Reuse `a3-hill` 0.0–2.23 + title |
| 5 | 10.21–12.99 | మల్లన్న కథలు ఒగ్గు పాటల్లో వినిపిస్తాయి | Oggu artists singing with the drum, wide | Who keeps this story alive | **New: Oggu artists, 8 s** (window 0.0–2.78) |
| 6 | 12.99–16.20 | బండారి కోసం వెళ్ళిన కథకు వేరు వేరు రూపాలున్నాయి | Same performance, pushed in to the lead singer's face and drum | Wide to close: from the group to one teller (one telling among many) | Same Oggu clip 2.8–6.0, code punch-in |
| 7 | 16.20–18.13 | అందులో ఓ కథ ఇది | Hills at dusk, herders and sheep on the path | Present day ends; the story world opens | Reuse `a5-forest` 0.0–1.93 |
| 8 | 18.13–20.95 | మల్లన్న మేడలమ్మను పెళ్లాడాలనుకున్నాడు | Mallanna, half-turned, watches Medalamma pass at a distance | Hero introduced, and his wish | **New: Mallanna sees Medalamma, 3 s** |
| 9 | 20.95–22.66 | లింగ బలిజల బిడ్డ ఆమె | Medalamma walks out of her family's doorway | Cut to her, on screen while she is named | Reuse `a7-medalamma` 0.0–1.2, slowed 1.43× |
| 10 | 22.66–24.69 | ఆమె అన్నలు ఒక షరతు పెట్టిండ్రు | Her three brothers, arms folded, a wall | She leaves frame; the obstacle remains | Reuse `a7-medalamma` 1.9–3.93 |
| 11 | 24.69–27.23 | బండారి తీసుకురావాలి. పసుపు కొమ్ములు. | Glowing turmeric roots, close | The object named, shown exactly | **New: bandari pull-back, 5 s** (first half) |
| 12 | 27.23–29.10 | అవి ఎక్కడో దూరంగా ఉన్నాయి | Camera pulls back past the roots to a walled garden far across the hills | Close object becomes a distant place | Same clip, second half |
| 13 | 29.10–32.29 | బయలుదేరే ముందు మల్లన్న ఎల్లమ్మ దగ్గరికి పోయిండు | Mallanna arrives and bows before Yellamma | New character | **New: Yellamma gives the way, 5 s** (first half) |
| 14 | 32.29–33.90 | దారి ఆమె చెప్పింది | Yellamma raises her arm and points the way | Action: the guidance itself | Same clip, second half |
| 15 | 33.90–36.08 | దేవతలు ఎగిరే గుర్రం ఇచ్చిండ్రు | The winged white horse appears in a burst of light against the night sky | The gift arrives | Reuse `a9-horse` first frame held + code light reveal |
| 16 | 36.08–37.50 | మల్లన్న బయలుదేరిండు | The horse beats its wings and flies with Mallanna | Still becomes flight: departure | Reuse `a9-horse` 0.0–1.42, in motion |
| 17 | 37.50–40.51 | అక్కడ తోటమాలిగా చేరిండు. పేరు మార్చుకున్నాడు. | Mallanna in plain clothes watering the garden, guards on the wall behind | New place, hidden identity | Reuse `a10-garden` 0.0–3.01 |
| 18 | 40.51–43.70 | కొంతకాలం అక్కడే ఉండి వాళ్ళ నమ్మకం గెలుచుకున్నాడు | The garden's keeper nods and hands him a key; seasons in the light | Time passes; trust is won | **New: trust, 4 s** (optional, see cost) |
| 19 | 43.70–45.53 | బండారి ఉన్న చోటు తెలుసుకున్నాడు | Tight on the glowing bandari on its stone pedestal | He finds it | Reuse `a8-serpent`, code punch-in on the pedestal |
| 20 | 45.53–47.70 | ఐదు తలల పాము దానికి కాపలా | Pull out: the five-headed serpent coiled around it, hoods raised | The guard revealed | Reuse `a8-serpent`, pull out to full frame |
| 21 | 47.70–50.19 | ఒకరోజు బండారి తీసుకుని బయలుదేరిండు | His hand closes around the turmeric, he moves off | The theft | Reuse `a12-hishand` 4.5–6.99 (fist closes) |
| 22 | 50.19–52.08 | కానీ వాళ్ళు కనిపెట్టిండ్రు | Guards on the wall spot him and point, shouting | He is seen | **New: guards spot him, 3 s** |
| 23 | 52.08–54.46 | నల్ల కుక్కగా మారి పారిపోయిండు | Mallanna dissolves into a black dog that bolts | Transformation | **New: black dog, 3 s** |
| 24 | 54.46–56.89 | కొండలు దాటిండు. నదులు దాటిండు. | The dog races over a ridge, then leaps a river | Landscape and speed | **New: chase, 4 s** (first part) |
| 25 | 56.89–58.11 | వాళ్ళు వదల్లే | Pursuers crest the ridge behind | The threat stays on screen | Same chase clip, end |
| 26 | 58.11–60.27 | చివరికి గంగమ్మ అడ్డొచ్చింది | Gangamma rises from the river between the dog and the pursuers | Intervention | **New: Gangamma, 5 s** (first half) |
| 27 | 60.27–63.01 | ఆయన్ని కాపాడనీకి చెయ్యి అడ్డుపెట్టింది | She throws her right arm across to block the blow | Action: the shield | Same clip, second half |
| 28 | 63.01–65.98 | ఆ దెబ్బకు ఆమె కుడిచెయ్యి పోయింది | The blow lands in a flash of water and light; her right arm is gone at the sleeve. Shown without gore. Held. | The cost. The longest hold in the film | **New: her hand gone, 3 s** |
| 29 | 65.98–68.66 | ఎగిరే గుర్రం మీద ఆయన తిరిగి వచ్చిండు | The horse glides down at dawn, bandari in hand | The return; dawn against the night departure | **New: return flight, 3 s** |
| 30 | 68.66–69.72 | ఈ కొండకే | The Komuravelli hill from beat 4 | Callback: the same hill | Reuse `a3-hill` 2.0–3.06 |
| 31 | 69.72–72.14 | బండారిల కొంత ఎల్లమ్మకిచ్చిండు | Mallanna places a share of turmeric in Yellamma's hands | Resolution, part one | **New: share to Yellamma, 3 s** |
| 32 | 72.14–74.78 | మిగతాది తీసుకుని మేడలమ్మను పెళ్లాడిండు | Wedding: garlands, turmeric, Medalamma beside him | Resolution, part two | **New: wedding, 3 s** |
| 33 | 74.78–78.68 | ఇప్పటి మల్లన్న పూజల్లోనూ బండారికి ప్రత్యేక స్థానం ఉంది | Today: festival crowd throwing turmeric at the shrine | Cut from story to present | Reuse `B-kling-test` 0.0–3.9 |
| 34 | 78.68–81.91 | ఒగ్గు కళాకారులు మల్లన్న కథను పాడి వినిపిస్తారు | The Oggu artists again, wide | Back to the tellers | Oggu clip 4.8–8.0 |
| 35 | 81.91–85.24 | ఒగ్గు పూజారులు భక్తుల మొక్కుల కోసం పట్నం వేస్తారు | The priest at the corrected patnam, powder drifting | A separate act: the patnam | Reuse `pilot-shot3` 0.0–3.33 (frozen, approved) |
| 36 | 85.24–90.40 | పసుపు, కుంకుమ, బియ్యప్పిండి వంటి రంగు పొడులతో తీర్చిదిద్దే పూజా ముగ్గు అది | Overhead: the square fills in colour by colour, yellow on పసుపు, red on కుంకుమ, white on బియ్యప్పిండి | Each powder appears as it is named | **New, free** (code-drawn) |
| 37 | 90.40–93.12 | కొందరు భక్తులు పట్నం పొడిని సేకరించుకుంటారు | Devotees scoop patnam powder into a cloth | The act of collecting | **New: gathering powder, 3 s** |
| 38 | 93.12–96.69 | పొలాల్లో చల్లితే పంటలు బాగా పండుతాయని వాళ్ళ నమ్మకం | A farmer scatters it over a green field | Belief, shown as a person's practice | **New: field, 4 s** |
| 39 | 96.69–100.56 | సంక్రాంతి నుంచి ఉగాది దాకా, ప్రతి ఆదివారం జాతర | Mallanna's idol close, turmeric smoke; date card | When to go | Reuse `pilot-shot2` 0.0–3.87 + free card |
| 40 | 100.56–103.41 | మీ ఊళ్ళో మల్లన్న బండారి కథ ఎట్లా చెప్తారు? | The turmeric hand from beat 2, later in the pour | Bookend to the opening | Reuse `a4-hand` 2.1–4.95 |
| 41 | 103.41–105.22 | ఊరి పేరుతో కింద చెప్పుండ్రి | Comment-box graphic: "మీ ఊరు: ____" with an arrow down | Direct call to comment | **New, free** (code card) |
| 42 | 105.22–107.84 | కొమురవెల్లి మల్లన్నకు, కోటి దండాలు! | Black, the chant in turmeric-gold text | The chant alone | **New, free** |

**42 beats.** No composition stays on screen across a change of event. Where one clip covers
two beats (11–12, 13–14, 24–25, 26–27) the action itself changes on the cut point, and the
prompt is written so it does.

## 3. Changes from revision 1

- **`a7-medalamma` was marked as a new 7 s clip. It already exists** (used in Part 1). Reused, saving 10.5 credits.
- **"Patnam being laid" dropped as new.** The approved, frozen `pilot-shot3` covers it. Saves 9.5.
- **Split into separate visuals:** Mallanna's wish vs. the brothers' condition; the theft vs. being spotted; the share with Yellamma vs. the wedding; collecting powder vs. the field; the map vs. the hill.
- **Added:** Mallanna sees Medalamma, the trust beat, the guards spotting him.
- `a11-theft` **not used.** The serpents look sleepy in it, which reads as the "snake closed its eyes" claim we removed. `a12-hishand` covers the theft instead.
- `pilot-shot2` (deity close) now carries the festival dates, so `B-kling-test` is used once.

## 4. Revised generation cost (approval needed)

Rates from `config/production.json`: still 2 credits (`nano_banana_2`, 2k); clip 1.5 credits/s (`kling3_0` pro).

| New asset | Still | Clip | Credits |
|---|---|---|---|
| Oggu artists | 1 | 8 s | 14.0 |
| Mallanna sees Medalamma | 1 | 3 s | 6.5 |
| Bandari pull-back | 1 | 5 s | 9.5 |
| Yellamma gives the way | 1 | 5 s | 9.5 |
| Trust (optional) | 1 | 4 s | 8.0 |
| Guards spot him | 1 | 3 s | 6.5 |
| Black dog | 1 | 3 s | 6.5 |
| Chase | 1 | 4 s | 8.0 |
| Gangamma | 1 | 5 s | 9.5 |
| Her hand gone | 1 | 3 s | 6.5 |
| Return flight | 1 | 3 s | 6.5 |
| Share to Yellamma | 1 | 3 s | 6.5 |
| Wedding | 1 | 3 s | 6.5 |
| Gathering powder | 1 | 3 s | 6.5 |
| Field | 1 | 4 s | 8.0 |
| **Total** | **15 stills = 30.0** | **59 s = 88.5** | **118.5** |

Map, patnam fill, date card, comment card, end card: code-drawn, 0 credits. 12 reused clips: 0.

- Revision 1 was 115.0. This is **+3.5** for six more distinct visuals.
- Without the optional trust beat (beat 18 holds `a10-garden` 3.0–6.19 with a light change instead): **110.5**.
- Same plan in `std` mode: 30 + 73.75 = **103.75**.
- Last recorded balance 474.55, so about **356** after the full plan.

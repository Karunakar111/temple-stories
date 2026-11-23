#!/usr/bin/env python3
"""Planning-level shot lists and reference boards for EP02-EP06 (re-runnable).

Each shot is tied to an exact span of the approved Voice text. Timing is provisional
(EP01's measured 14.68 chars/s, +0.5 s per paragraph break, + any planned breath) and is
replaced by `gudi` from the real take. Clip lengths follow the screen time they must fill.
Prompts are drafts; they are part of the creative scope you approve.

Usage: python3 scripts/plan/shotlists.py
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EP = ROOT / "episodes"
CPS, PARA = 14.68, 0.5
STYLE = ["STYLE-DEITY", "STYLE-PATNAM"]
DRESS = "All figures fully clothed in simple period dress. No text, letters or script anywhere in the image."


def still(prompt, needs, after=None, refs=None):
    c = {"provider": "higgsfield", "asset_type": "still", "model": "nano_banana_2", "quote": "2",
         "settings": {"resolution": "2k", "aspect_ratio": "9:16"},
         "references": (refs or []) + STYLE, "needs": needs + STYLE, "prompt": prompt}
    if after:
        c["after"] = after
    return c


def clip(prompt, needs, start, max_s=5):
    return {"max_s": max_s, "provider": "higgsfield", "asset_type": "clip", "model": "kling3_0", "quote": None,
            "settings": {"mode": "pro", "sound": "off", "aspect_ratio": "9:16", "duration": None, "start_image": f"<{start}>"},
            "references": [start], "needs": needs, "after": [start], "timing_dependent": True, "prompt": prompt}


def S(i, text, picture, change, cls, paid=(), local=(), note=None, hold=0.0, clip_spans=None, media_from=None):
    return {"id": i, "media_from": media_from, "text": text, "picture": picture, "what_changes": change, "class": cls,
            "paid": list(paid), "local": list(local), "note": note, "hold_after_s": hold,
            "clip_spans": clip_spans, "on_screen": text is not None}


def build(slug, shots, board):
    d = EP / slug
    voice = (d / "voice.te.txt").read_text(encoding="utf-8")
    t, pos, by_id = 0.0, 0, {}
    for s in shots:
        by_id[s["id"]] = s
        if s["text"] is None:
            s["est_start_s"], s["est_dur_s"] = None, 0
            continue
        i = voice.index(s["text"], pos)
        t += PARA * voice[pos:i].count("\n\n")
        s["est_start_s"] = round(t, 2)
        s["est_dur_s"] = round(len(s["text"]) / CPS + s["hold_after_s"], 2)
        t += s["est_dur_s"]
        pos = i + len(s["text"])
    for s in shots:  # clip length = the screen time it has to fill (its own shot, or several)
        for c in s["paid"]:
            if c["asset_type"] == "clip":
                span = sum(by_id[x]["est_dur_s"] for x in (s.get("clip_spans") or [s["id"]]))
                # a clip covers the action, not the whole line: capped (default 5 s); the rest of a long
                # shot is held on the still with local camera / light movement
                dur = min(c.get("max_s", 5), max(3, math.ceil(span - 0.25)))
                c["settings"]["duration"] = dur
                c["quote"] = f"{dur * 1.5:g}"
    narr = [{"beat": "VO", "provider": "elevenlabs", "asset_type": "narration", "model": "eleven_v4",
             "quote": str(len(voice.strip())), "settings": {"voice": "JWn8KOVJuYWznmih5YXL", "takes": 1},
             "text_path": f"episodes/{slug}/voice.te.txt", "prompt": "voice.te.txt", "references": [], "needs": []}]
    doc = {"episode": slug, "revision": 2,
           "timing_basis": "PROVISIONAL until the take: EP01's 14.68 chars/s, +0.5 s per paragraph, + planned breaths.",
           "est_total_s": round(t, 1), "narration": narr, "shots": shots}
    (d / "shots.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "reference-board.json").write_text(json.dumps(board, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


STYLE_REFS = [
    {"id": "STYLE-DEITY", "subject": "EP01 deity close-up (accepted B-derived frame)", "status": "approved-style",
     "path": "assets/pilot/shot2-deity-close.png", "use": "style input only; never an identity reference", "rights": "own artwork"},
    {"id": "STYLE-PATNAM", "subject": "EP01 patnam close (accepted B-derived frame)", "status": "approved-style",
     "path": "assets/pilot/shot3-patnam-v3-final.png", "use": "style input only", "rights": "own artwork"},
]


def board(slug, refs):
    return {"episode": slug, "revision": 2, "prepared": "2026-11-23",
            "status_meanings": {"approved-style": "EP01 art, style only", "verified": "identity confirmed from a named source",
                                "lead": "identified source still to be chosen or confirmed", "unresolved": "no usable reference",
                                "decision": "waiting on Karunakar's call (see weekly review page)"},
            "references": STYLE_REFS + refs}


# ------------------------------------------------------------------------------------------ EP02
def ep02():
    refs = [
        {"id": "K-LINGA", "subject": "Swayambhu Someshwara linga, Kolanupaka", "status": "decision",
         "leads": ["Deccan Chronicle 15 Jul 2018 describes the linga as cracked",
                   "temple.yatradham.org: photography not allowed inside"],
         "use": "L1, E1, R1", "decision": "D1 deity depiction policy"},
        {"id": "K-RENUKA", "subject": "Renukacharya", "status": "verified",
         "basis": "Production book: 'The sage is a literary illustration.' Designed from the script/K1 4.3-4: ash, rudraksha, staff, water pot. Character sheet C1 is reviewed before any animation."},
        {"id": "K-AGASTYA", "subject": "Agastya and Lopamudra", "status": "verified",
         "basis": "Agastya: bearded, pot-bellied, matted hair, water pot in the left hand (Asian Civilisations Museum record; V&A: rosary and water vessel). Lopamudra: literary illustration in a simple sari."},
        {"id": "K-EXTERIOR", "subject": "Someshwara temple exterior, Kolanupaka", "status": "decision",
         "url": "https://www.kaladarshana.com/sites/kolanupaka/IMG00002.html",
         "use": "L2 and S16a", "decision": "D2 Kolanupaka exterior reference"},
        {"id": "K-INSCRIPTION-TEXT", "subject": "1067 endowment (Epigraphia Telanganica I, p.168, no.147)", "status": "verified",
         "use": "typeset caption only; the stone is generic and unreadable"},
        {"id": "MALAYA-ASHRAM", "subject": "Malaya mountain and ashram (painted, no mapped route)", "status": "verified"},
    ]
    R, A = ["K-RENUKA"], ["K-AGASTYA"]
    shots = [
        S("C1", None, "Character sheet: Renukacharya. Not on screen.", "n/a", "paid still (reference)",
          [still("Character sheet of a Shaiva sage in the attached illustrated folk style: lean ascetic, sacred ash over the body, rudraksha strands, wooden staff, brass water pot; front and three-quarter views, plain warm paper. " + DRESS, R)]),
        S("C2", None, "Character sheet: Agastya and Lopamudra. Not on screen.", "n/a", "paid still (reference)",
          [still("Character sheet: the sage Agastya (short, bearded, pot-bellied, matted hair, water pot in his left hand) and his wife Lopamudra in a simple sari; front and three-quarter views, attached style. " + DRESS, A)]),
        S("S01", "కొలనుపాక సోమేశ్వర", "Sanctum in lamp light; title 'కొలనుపాక సోమేశ్వరుడు' typeset on the FIRST frame.",
          "Lamps flicker; light starts gathering at the linga.", "paid still + local",
          [still("Interior of a stone Shiva sanctum at night, the linga as decided in D1, oil lamps, attached illustrated folk style. " + DRESS, ["K-LINGA"])],
          ["title card", "LampGlow", "Bloom"]),
        S("S02", "లింగం నుంచి ఓ గురువు వచ్చాడట. ఎవరాయన?", "The emergence: a sage resolves out of the light at the linga; hold on his face after the question.",
          "Light becomes a figure; settles; we hold his face.", "paid still + paid clip (priority: emergence)",
          [still("The same sanctum; a Shaiva sage (character sheet C1) standing in soft golden light rising from the linga, villagers' silhouettes in the foreground, attached style. " + DRESS, ["K-LINGA"] + R, ["C1:still"], ["C1:still"]),
           clip("The golden light around the sage softens as he becomes solid and still; the villagers lean back slightly. The linga and the sage's face, ash marks and rudraksha stay exactly the same. Camera almost still.", ["K-LINGA"] + R, "S02:still")],
          note="Was 0.5 s of narration for a 5 s clip. Now spans the whole hook plus a 1.2 s breath; the clip is cut to fit.", hold=1.2),
        S("S03", "ఊరి జనం కూడా ఆయన్ని చూసి అదే అడిగారు. వీరశైవుల గ్రంథం ‘సిద్ధాంత శిఖామణి’లో ఈ కథ ఇలా సాగుతుంది.",
          "Villagers looking up; source name typeset as an editorial card.", "Card rises on 'సిద్ధాంత శిఖామణి'.", "paid still + local",
          [still("Villagers of a Telangana village gathered at a temple doorway at night, looking in with wonder, lamp light on their faces, attached style. Respectful, no caricature. " + DRESS, [])], ["source card"]),
        S("S04", "ఒంటినిండా విభూతి. మెడలో రుద్రాక్షలు. చేతిలో దండం, కమండలం.", "Details from the S02 still at 2k: ash, rudraksha, staff, water pot.",
          "Camera moves detail to detail on each phrase.", "reuse + local", [], ["Stage camera"], media_from="S02"),
        S("S05", "తన పేరు రేణుకసిద్ధుడని, శివుడి ఆజ్ఞతో ఇక్కడికి వచ్చానని ఆ యోగి చెప్పాడట. ఆయన్నే రేణుకాచార్యుడని పిలుస్తారు.",
          "The sage speaking to seated villagers; name typeset 'రేణుకాచార్యుడు'.", "Name card on the name.", "paid still + local",
          [still("The Shaiva sage (C1) standing before the temple, speaking calmly to seated villagers, one hand raised in blessing, attached style. " + DRESS, R, ["C1:still"], ["C1:still"])], ["name card"]),
        S("S06", "ఊరి వాళ్లు ఇంకా చూస్తుండగానే ఆయన ఆకాశమార్గాన మలయ పర్వతానికి వెళ్లాడు.", "He rises out of frame; match cut to the mountain sky.",
          "Upward departure; heads tilt up.", "paid clip + local match cut",
          [clip("The sage rises gently straight upward and out of the top of the frame; the villagers tilt their heads to follow. Faces and dress stay the same. Camera still.", R, "S05:still")]),
        S("S07", "అక్కడ అగస్త్య మహర్షి ఆశ్రమం ఉంది.", "Wooded mountain and ashram.", "Mist, birds, hut lamp.", "paid still + local",
          [still("A wooded mountain ridge at dawn, a small thatched hermitage in a clearing with a sacred fire, attached illustrated folk style. No people. No text.", ["MALAYA-ASHRAM"])], ["Stage parallax", "Birds"]),
        S("S08", "రేణుకాచార్యుణ్ని చూడగానే అగస్త్యుడు కూర్చున్న చోటు నుంచి లేచాడు.", "Agastya sees the visitor and rises.", "Agastya stands to receive him.",
          "paid still + paid clip",
          [still("Agastya (C2) seated on a deer skin outside the hermitage, looking up as the Shaiva sage (C1) arrives, attached style. " + DRESS, A + R, ["C1:still", "C2:still"], ["C1:still", "C2:still"]),
           clip("Agastya rises from his seat and steps forward with joined hands to receive the visitor. Faces and dress stay the same; hands whole with five fingers. Camera still.", A + R, "S08:still")]),
        S("S09", "లోపాముద్ర నీళ్లు తీసుకొచ్చింది.", "Lopamudra brings the vessel; Agastya receives it.", "One readable hand-over.",
          "paid still + paid clip (priority: two-person welcome)",
          [still("Lopamudra (C2) walking from the hut with a brass water vessel towards Agastya (C2), the visiting sage (C1) standing nearby, attached style. " + DRESS, A + R, ["C1:still", "C2:still"], ["C1:still", "C2:still"]),
           clip("Lopamudra walks to Agastya and hands him the water vessel; he takes it in both hands. Faces and dress stay the same; hands whole. Camera still.", A, "S09:still")], hold=0.6),
        S("S10", "ఆ నీళ్లతో అగస్త్యుడు స్వయంగా అతిథి పాదాలు కడిగాడు.", "Closer: Agastya washes the visitor's feet.", "Water pours; hands wash.",
          "paid still + paid clip (priority)",
          [still("Close view: Agastya (C2) kneeling, pouring water from a brass vessel over the bare feet of the standing Shaiva sage (C1), attached style. " + DRESS, A + R, ["C1:still", "C2:still"], ["C1:still", "C2:still"]),
           clip("Agastya pours water slowly over the visitor's feet and gently washes them with his other hand. Feet, hands and faces stay whole and the same. Camera still.", A + R, "S10:still")]),
        S("S11", "ఆ తర్వాత ఇద్దరూ కూర్చున్నారు. ఎన్నో ఆగమాలు విన్న అగస్త్యుడికే ఇంకా సందేహాలున్నాయట. శివతత్త్వాన్ని మీ నోట వినాలని అడిగాడు.",
          "Both seated; Agastya asks.", "Cut on the question.", "paid still + local",
          [still("Agastya (C2) and the Shaiva sage (C1) seated facing each other in the hermitage, Agastya asking with an open hand, the sage listening with lowered eyes, attached style. " + DRESS, A + R, ["C1:still", "C2:still"], ["C1:still", "C2:still"])]),
        S("S12", "రేణుకాచార్యుడు ఒక్క క్షణం శివుణ్ని తలచుకుని చెప్పడం మొదలుపెట్టాడు.", "Teacher pauses, then begins; listening reaction.",
          "Key-pose cut T1 -> T2 (Experiment 01).", "paid still (second key pose) + local KeyPoseCut",
          [still("SAME composition and camera as the S11 still: now the Shaiva sage looks up and speaks with a raised teaching hand while Agastya listens with joined hands, attached style. " + DRESS, A + R, ["S11:still"], ["S11:still"])],
          ["KeyPoseCut"], note="If the two key poses do not register, a straight cut (no extra spend)."),
        S("S13", "భక్తుని ప్రయాణం ఎక్కడ మొదలవుతుంది? శివుడితో ఐక్యం కావడమంటే ఏంటి? ఆ గ్రంథం ముందుకు సాగేది ఇలాంటి ప్రశ్నలతోనే.",
          "The two questions typeset over the dimmed S12 frame.", "Each question on its phrase.", "reuse + local", [], ["typeset questions"], media_from="S12"),
        S("S14", "కథ చివర్లో రేణుకాచార్యుడు మళ్లీ కొలనుపాకకు వచ్చాడు. ఊరి జనం చూస్తుండగా సోమేశ్వరుడి ఎదుట నిలబడి ప్రార్థించాడు.",
          "Return to the opening composition: the sage in prayer before the linga.", "Lamps; slow push.", "paid still + local",
          [still("The same sanctum as S01: the Shaiva sage (C1) standing before the linga with palms joined in prayer, villagers watching from the doorway, attached style. " + DRESS, ["K-LINGA"] + R, ["S01:still", "C1:still"], ["S01:still", "C1:still"])]),
        S("S15", "లింగం నుంచి శివుడి పిలుపు వినిపించిందట. వచ్చిన దారినే, ఒక జ్యోతిలా, ఆయన అందులో ఐక్యమయ్యాడని ఈ సంప్రదాయం చెబుతుంది.",
          "He resolves into light at the same linga; a witness lowers his hands. Stone intact.", "Figure becomes light and merges.",
          "paid clip (priority: return into light) + local Bloom",
          [clip("The sage slowly turns into soft golden light that flows into the linga and disappears; a villager in the doorway lowers his joined hands. The linga stays intact. Camera still.", ["K-LINGA"] + R, "S14:still")],
          note="Artistic depiction of a tradition", hold=0.6),
        S("S16a", "ఇదే గుడి గురించి రాతి మీద మిగిలిన మాట కూడా ఒకటుంది.", "Museum courtyard of the temple: carved stones along the ambulatory.",
          "Slow lateral move past the stones.", "reuse (S17 exterior still) + local", [], ["Stage camera"],
          note="Inscription beat split: was one 13.3 s hold on a single stone", media_from="S17"),
        S("S16b", "వెయ్యి అరవై ఏడో సంవత్సరపు శాసనంలో ఇక్కడి స్వయంభూ సోమేశ్వరుడి పూజలకు ఇచ్చిన దానం నమోదైంది.",
          "Stone detail in raking light; typeset 'క్రీ.శ. 1067 · పూజలకు దానం' builds on the year.", "Light rakes; caption builds.", "paid still + local",
          [still("A weathered grey stone slab with eroded, unreadable carved lines in a museum courtyard, raking evening light, attached style. No legible letters of any script.", ["K-INSCRIPTION-TEXT"])], ["date card"]),
        S("S16c", "అంటే అప్పటికే ఇక్కడ పూజలు జరుగుతున్నాయని తెలుస్తోంది.", "Consequence: worship continuing at the sanctum (reuse S01 with lamps and a priest's arati glow).",
          "Lamps brighten; arati light circles.", "reuse + local", [], ["LampGlow", "Bloom"], media_from="S01"),
        S("S17", "కొలనుపాక వెళ్తే ఈ రెండు గుర్తుపెట్టుకోండి. లింగం దగ్గర రేణుకాచార్యుడి కథ. గుడి ఆవరణలోని శాసనంలో, ఆ పూజలు కొనసాగేందుకు ఎవరో ఇచ్చిన దానం.",
          "Someshwara exterior; map card; the two reminders typeset.", "Map pin; two lines appear.", "paid still + local",
          [still("Exterior of the Someshwara Shiva temple at Kolanupaka as in the reference chosen in D2 (NOT the Jain temple), late afternoon, attached style. " + DRESS, ["K-EXTERIOR"])], ["map card"]),
    ]
    return build("ep02-kolanupaka", shots, board("ep02-kolanupaka", refs))


# ------------------------------------------------------------------------------------------ EP03
def ep03():
    refs = [
        {"id": "V-KODE", "subject": "Kode mokku: pradakshina with a bull, then tying it as an offering", "status": "verified",
         "basis": "Telangana Tourism 'The Abode of Vemulawada Rajanna'; Telangana Today report photos (reference only, not reproduced)"},
        {"id": "V-EXTERIOR", "subject": "Sri Raja Rajeshwara temple, Vemulawada", "status": "lead",
         "note": "Photo not chosen yet: Wikimedia Commons was unreachable from this workspace; pick in a browser session (routine)"},
        {"id": "V-TANK", "subject": "Dharma Gundam tank beside the temple", "status": "lead", "note": "as V-EXTERIOR"},
        {"id": "V-1961", "subject": "1961 record: two uprights at the east entrance where calves and bulls were tied", "status": "verified",
         "basis": "Production book V1 (Census 1961, Karimnagar). Drawn as a simple ink view, no reconstructed gateway"},
        {"id": "NARENDRA", "subject": "King Narendra, the rishi (sthala purana)", "status": "verified", "basis": "literary illustration"},
    ]
    K = ["V-KODE"]
    shots = [
        S("C1", None, "Sheets: devotee family and bull; King Narendra. Not on screen.", "n/a", "paid still (reference)",
          [still("Character sheet: a Telangana farming family (father, mother, son) in everyday clothes and a young white bull with a rope halter; front and side views, attached style. " + DRESS, K),
           still("Character sheet: a king of legend in simple hunting dress with a bow, and an elderly rishi with a water pot; front and three-quarter views, attached style. " + DRESS, ["NARENDRA"])]),
        S("S01", "వేములవాడ రాజన్నకు కోడెను ఎందుకు కడతారు?", "Low beside walking feet and hooves; rise to reveal a devotee walking with the bull. Title on the first frame.",
          "Walking gait; slack lead; rise.", "paid still + paid clip (protect the bull's gait)",
          [still("Low angle on a temple courtyard: bare human feet walking beside the hooves of a young white bull on a slack rope, attached style. " + DRESS, K, ["C1:still"], ["C1:still"]),
           clip("The bull and the devotee walk forward together at a natural pace, the rope slack between them; the camera rises slowly to reveal the devotee. Natural gait, four legs moving correctly.", K, "S01:still", max_s=6)],
          ["title card"], hold=0.8, clip_spans=["S01", "S02"]),
        S("S02", "భక్తుల అడుగుల పక్కనే కోడె గిట్టలు. తాడు పట్టుకుని దానితోపాటు నడుస్తున్న ఆ కుటుంబాన్ని చూడండి.", "The family walking with the bull (clip continues).",
          "Continues the walk.", "covered by the S01 clip", media_from="S01"),
        S("S03", "ఇక్కడి శివుడి పేరు రాజరాజేశ్వరుడు. భక్తులు పిలిచేది మాత్రం రాజన్నా అని. ఇంటిల్లిపాదీ చల్లగా ఉండాలని కొందరు మొక్కుకుంటారు.",
          "Temple exterior; name cards 'రాజరాజేశ్వరుడు' and 'రాజన్న'.", "Cards on the names.", "paid still + local",
          [still("Exterior of the Sri Raja Rajeshwara temple at Vemulawada as in the chosen reference, morning, devotees in the courtyard, attached style. " + DRESS, ["V-EXTERIOR"])], ["name cards"]),
        S("S04", "కోడెతో కలిసి ప్రదక్షిణ చేసి,", "The same pair circles the shrine.",
          "Pradakshina; tether close-up.", "paid still + 2 paid clips (protect the tethering)",
          [still("The same family and bull walking clockwise around the shrine wall, attached style. " + DRESS, K + ["V-EXTERIOR"], ["C1:still"], ["C1:still"]),
           clip("The family and the bull walk clockwise along the shrine wall and out of frame. Natural gait. Camera still.", K, "S04:still")],
          ),
        S("S04b", "దాన్ని స్వామికి అర్పణగా కడతారు. అదే కోడె మొక్కు.", "Tether close-up.", "Hands knot the rope to a post.", "paid still + paid clip (protect the tethering)",
          [still("Close view: a devotee's hands tying the bull's rope to a stone post, attached style. " + DRESS, K, ["C1:still"], ["C1:still"]),
           clip("The hands loop and knot the rope around the post and let go; the bull stands calmly. Hands whole. Camera still.", K, "S04b:still")], hold=0.4),
        S("S05", "అరవై ఏళ్ల కిందటి వేములవాడ గురించి చదివితే ఒక చిన్న వివరముంటుంది. గుడి తూర్పు ద్వారం ముందు రెండు స్తంభాలు. భక్తులు తెచ్చిన దూడల్ని, కోడెల్ని అక్కడ కట్టేవారని అప్పటి నమోదులో ఉంది.",
          "A simple ink view: two uprights and a calf; 'ఆరవై ఏళ్ల క్రితం' card.", "Ink draws on.", "paid still + local",
          [still("A simple ink drawing on warm paper: two stone uprights at a temple entrance with a calf tied to one, sparse lines, attached style. No text.", ["V-1961"])], ["ink reveal"]),
        S("S06", "మరి ఆ రాజన్న ఈ ఊర్లో ఎలా వెలిశాడంటారు? దానికి ఇక్కడి స్థలపురాణం మనల్ని గుడి పక్కనున్న ధర్మగుండం దగ్గరికి తీసుకెళ్తుంది.",
          "Match cut to the tank; light shifts into legend.", "Water shimmer; light change.", "paid still + local",
          [still("The Dharma Gundam temple tank at Vemulawada as in the chosen reference, still water, evening, attached style. " + DRESS, ["V-TANK"])], ["water shimmer", "TimeOfDay"]),
        S("S07", "నరేంద్రుడనే రాజు వేటకు వెళ్లాడట. నీళ్లు తెచ్చుకోవడానికి వచ్చిన ఒక ఋషికి పొరపాటున అతని బాణం తగిలింది. ఋషి చనిపోయాడు.",
          "Forest stream: the rishi's vessel drops; the king reacts. No injury shown.", "Vessel falls; king lowers the bow.", "paid still + paid clip",
          [still("A forest stream: an elderly rishi kneeling to fill a water pot, the king (C1 sheet 2) half-hidden in the trees with a bow, attached style. " + DRESS, ["NARENDRA"], ["C1:still"], ["C1:still"]),
           clip("The water pot slips from the rishi's hands and rolls into the stream; the king lowers his bow in shock. No wound or blood shown. Camera still.", ["NARENDRA"], "S07:still")]),
        S("S08", "ఆ పాపం నుంచి బయటపడాలని రాజు ఎన్నో క్షేత్రాలు తిరిగాడు. చివరికి వేములవాడ చేరాడు.", "The king through changing landscapes.",
          "Days and seasons pass (local TimeOfDay).", "paid still + local",
          [still("The king (C1 sheet 2) walking alone along a long road through hills, attached style. " + DRESS, ["NARENDRA"], ["C1:still"], ["C1:still"])], ["TimeOfDay"]),
        S("S09", "ఇక్కడి ధర్మగుండంలోకి చెయ్యి చాపి మూడు దోసిళ్ల నీళ్లు తాగాడట. ఆ పాపం తొలగిందని కథ చెబుతుంది.",
          "His cupped hands and the water.", "Three handfuls.", "paid still + paid clip",
          [still("Close view: the king's cupped hands lifting water from a stone tank, attached style. " + DRESS, ["NARENDRA"], ["C1:still"], ["C1:still"]),
           clip("The cupped hands lift water three times; drops fall back into the tank. Hands whole. Camera still.", ["NARENDRA"], "S09:still")]),
        S("S10", "ఆ రాత్రి శివుడు కలలో కనిపించి, గుండం అడుగున లింగం ఉందనీ, దాన్ని తీసి ఒడ్డున ప్రతిష్ఠించాలనీ చెప్పాడు.",
          "The dream: the king asleep by the tank; a glow under the water.", "Water sound fades; glow rises.", "paid still + local",
          [still("Night: the king asleep on the bank of the tank, a soft light glowing beneath the water, attached style. " + DRESS, ["NARENDRA"], ["C1:still"], ["C1:still"])], ["Bloom"]),
        S("S11", "రాజు నీటిలో వెతికాడు. లింగం దొరికింది. దొరికిన గుండం ఒడ్డునే ప్రతిష్ఠించాడు. వేములవాడలో రాజేశ్వరుడి ఆవిర్భావాన్ని ఇలా చెప్పుకుంటారు.",
          "He finds the linga in the tank; consecration on the bank.", "Search, find, lift.", "paid still + paid clip",
          [still("The king waist-deep in the tank lifting a small stone linga from the water, attached style. " + DRESS, ["NARENDRA"], ["C1:still"], ["C1:still"]),
           clip("The king's hands find the linga under the water and lift it carefully above the surface. Hands whole. Camera still.", ["NARENDRA"], "S11:still")]),
        S("S12", "మీ ఇంట్లో ఎవరైనా రాజన్నకి కోడె మొక్కు తీర్చారా? ఆ రోజు మీకు గుర్తున్నది ఏంటో చెప్పండి.", "Back to the walking pair; comment card.",
          "Walk continues; card.", "reuse S01 clip + local", [], ["comment card"], media_from="S01"),
    ]
    return build("ep03-vemulavada", shots, board("ep03-vemulavada", refs))


# ------------------------------------------------------------------------------------------ EP04
def ep04():
    refs = [
        {"id": "S-ANIMALS", "subject": "Spider, snake, elephant (natural, no giant fantasy spider)", "status": "verified", "basis": "Production book S1"},
        {"id": "S-FOREST-LINGA", "subject": "Linga in the forest (before any temple)", "status": "verified", "basis": "literary illustration of the legend"},
        {"id": "S-TEMPLE-LINGA", "subject": "Present Srikalahasti linga with the three marks", "status": "decision",
         "basis": "Incredible India: a spider, two elephant tusks and a five-headed serpent at the base; sanctum photography prohibited",
         "decision": "D1 deity depiction policy"},
        {"id": "S-EXTERIOR", "subject": "Srikalahasti temple and the Swarnamukhi", "status": "lead", "note": "photo to choose in a browser session (routine)"},
    ]
    N = ["S-ANIMALS", "S-FOREST-LINGA"]
    shots = [
        S("C1", None, "Sheet: elephant, cobra, spider in house style. Not on screen.", "n/a", "paid still (reference)",
          [still("Design sheet in the attached illustrated folk style: an Indian elephant, a cobra, and a small natural garden spider with its web, each drawn naturally, plain warm paper. No text.", N)]),
        S("S01", "శ్రీకాళహస్తి కథలో ఏనుగు పూజ చేస్తే సాలెగూడు ఎందుకు తెగింది?", "Cold open in macro: silk releases, a gem rolls; tilt up the falling stream to the trunk. Title first frame.",
          "Web tears; gem rolls; stream revealed.", "paid still + paid clip (protect the pour)",
          [still("Macro: a stream of water falling onto a forest linga covered by a spider web with a red gem on top, the tip of an elephant trunk above, attached style. No text.", N, ["C1:still"], ["C1:still"]),
           clip("Water pours from the elephant's trunk onto the linga; the spider web tears and the red gem rolls aside; the camera tilts up the stream to reveal the trunk. Direction of flow stays downward.", N, "S01:still", max_s=6)],
          ["title card"], clip_spans=["S01", "S02"]),
        S("S02", "లింగం మీదికి నీళ్ల ధార పడింది. పాము తెచ్చి పెట్టిన మణులు కూడా పక్కకు దొర్లిపోయాయి. ఆ నీళ్లు పోసింది ఏనుగే.", "(clip continues)", "", "covered by the S01 clip", media_from="S01"),
        S("S03", "స్వర్ణముఖి ఒడ్డున ఉన్న శ్రీకాళహస్తి గురించి చెప్పుకునే కథల్లో ఇదొకటి.", "River and the identified temple; dissolve into forest.", "Water light; dissolve.",
          "paid still + local", [still("The Srikalahasti temple gopurams beside the Swarnamukhi river as in the chosen reference, morning, attached style. " + DRESS, ["S-EXTERIOR"])], ["map card"]),
        S("S04", "అడవిలో ఒక శివలింగం. ఎండ పడినా, వాన వచ్చినా లింగానికి అడ్డుగా ఉండాలని ఒక సాలెపురుగు దారం మీద దారం వేసి గూడు అల్లేది.",
          "Forest linga; the spider spins between two anchors; light makes the shelter legible.", "Web draws thread by thread.",
          "paid still + LOCAL web animation", [still("A stone linga in a quiet forest clearing between two branches, dappled light, no web yet, attached style. No text.", N)],
          ["procedural web drawn in code", "small spider sprite"], note="Web drawn in code instead of a paid clip"),
        S("S05", "పాము నేల లోపలి నుంచి మణులు తెచ్చి అదే లింగాన్ని అలంకరించేది.", "The same snake approaches; a jewel settles.", "Snake glides in; gem placed.",
          "paid still + paid clip", [still("The same forest linga under its web; a cobra emerging from a hole in the ground with a glowing red gem, attached style. No text.", N, ["S04:still"], ["S04:still"]),
                                     clip("The cobra glides to the linga and leaves the red gem at its base, then withdraws. Camera still.", N, "S05:still")]),
        S("S06", "ఏనుగు వంతు వచ్చేసరికి దాని తొండం నిండా నీళ్లు. అది లింగానికి అభిషేకం చేసేది. ఆ ధార తగిలితే గూడు నిలుస్తుందా? మణులు అక్కడే ఉంటాయా?",
          "Continuous trunk lift and pour; why one offering displaces the others.", "Trunk lifts, pours.", "paid still + paid clip (protect)",
          [still("The elephant (C1) at the forest linga with its trunk raised, water about to pour, web and gem visible, attached style. No text.", N, ["C1:still"], ["C1:still"]),
           clip("The elephant lifts its trunk in one continuous movement and pours water over the linga; the web sags and the gem washes aside. Trunk and stream stay continuous. Camera still.", N, "S06:still")]),
        S("S07", "తాను తెచ్చిన మణులు పక్కకు పోవడం చూసి పాముకి కోపం వచ్చింది. ఏనుగు తొండంలోకి దూరింది.", "The snake approaches the trunk.", "Snake rises.",
          "paid clip", [clip("The cobra rises and slides toward the elephant's trunk. No bite or injury shown. Camera still.", N, "S06:still")], media_from="S06"),
        S("S08", "ఊపిరాడక ఏనుగు చెట్టు బోదెకి గుద్దుకుంది. ఆ బోదె మీదే సాలెపురుగు కూడా ఉంది. ఈ కథనంలో మూడూ అక్కడే ప్రాణాలు విడిచాయి.",
          "The tree shudders; the web falls still. The voice carries the deaths.", "Shudder; stillness.", "paid still + local",
          [still("A large tree trunk in the forest with a spider web on its bark, leaves falling, no animals visible, attached style. No text.", N)], ["camera shake", "falling leaves"],
          note="No graphic injury"),
        S("S09", "ఒకటి నీడ ఇచ్చింది. ఒకటి తనకి దొరికిన మణులు ఇచ్చింది. ఇంకొకటి నీళ్లు తెచ్చింది. మూడింటి భక్తికీ మెచ్చి శివుడు వాటికి ముక్తినిచ్చాడని చెబుతారు.",
          "The three offerings together at the linga, lit.", "Light blooms on each offering in turn.", "paid still + local",
          [still("The forest linga with all three offerings at once: a spider web above it, a red gem at its base, water glistening on it, warm light, attached style. No text.", N)], ["Bloom"]),
        S("S10", "ఆ మూడు ప్రాణుల్ని ఈ క్షేత్రం పేరులోనే గుర్తు చేసుకుంటారు. శ్రీ అంటే ఇక్కడ సాలెపురుగు. కాళం అంటే పాము. హస్తి అంటే ఏనుగు. కలిపి పలకండి… శ్రీకాళహస్తి.",
          "One offering per spoken name; the Telugu name builds from typeset letters. Optional present linga per D1.", "Name builds.", "reuse + local",
          [], ["typeset name build"], note="If D1 = illustrate: one more still of the present linga with its marks (+2)", media_from="S09"),
    ]
    return build("ep04-srikalahasti", shots, board("ep04-srikalahasti", refs))


# ------------------------------------------------------------------------------------------ EP05
def ep05():
    refs = [
        {"id": "Y-HILL", "subject": "Yadagirigutta hill and the present temple (rebuilt in black stone, 2016-2022)", "status": "lead",
         "basis": "Wikipedia; Deccan Herald on the restored name", "note": "photo to choose (routine)"},
        {"id": "Y-FIGURES", "subject": "Yada rishi, Anjaneya, the woman devotee", "status": "verified", "basis": "literary illustration; Anjaneya in standard iconography"},
        {"id": "Y-DARSHAN", "subject": "Lakshmi Narasimha at the first darshan", "status": "decision", "decision": "D1 deity depiction policy"},
        {"id": "Y-FORMS", "subject": "The five forms, named on screen", "status": "verified", "basis": "Y1-Y2; names only, no five statues together"},
    ]
    F = ["Y-FIGURES"]
    shots = [
        S("C1", None, "Sheets: Yada rishi and Anjaneya; the woman devotee. Not on screen.", "n/a", "paid still (reference)",
          [still("Character sheet: an elderly rishi in penance (Yada) and Anjaneya in standard iconography; front and three-quarter views, attached style. " + DRESS, F),
           still("Character sheet: a village woman devotee in a simple sari, front and three-quarter views, attached style. " + DRESS, F)]),
        S("S01", "యాదగిరిగుట్టలో నరసింహుడు ఏ గుహలో ఉన్నాడో ఎలా తెలిసింది?", "The cave mouth from her point of view; cut before the reveal. Title first frame.",
          "Torch light flickers at the mouth.", "paid still + local",
          [still("Point of view looking into a rocky cave mouth on a hill at night, torch light, attached style. No people. No text.", ["Y-HILL"])], ["title card", "LampGlow"]),
        S("S02", "దేవస్థానం చెప్పే ఓ కథ ప్రకారం, ఆ దారి ఒక భక్తురాలికి కలలో తెలిసిందట. కానీ కథ మొదలయ్యేది గుట్ట కింద, ఒక ఋషి దగ్గర.",
          "Recurring hill silhouette; drop to its foot.", "Light moves down the hill.", "paid still + local",
          [still("The rocky hill of Yadagirigutta in silhouette at dawn with forest at its foot, attached style. No text.", ["Y-HILL"])], ["Stage camera"]),
        S("S03", "యాద ఋషి తపస్సు చేశాడట. ఆయన తపస్సుకు మెచ్చిన నారాయణుడు ఆంజనేయుణ్ని పంపాడు.", "Yada looks up from his penance.", "He opens his eyes and looks up.",
          "paid still + paid clip", [still("The rishi (C1) seated in penance at the foot of the hill, eyes closed, attached style. " + DRESS, F, ["C1:still"], ["C1:still"]),
                                     clip("The rishi opens his eyes and slowly looks up toward a soft light. Face stays the same. Camera still.", F, "S03:still")]),
        S("S04", "ఆంజనేయుడు ఋషికి దారి చూపాడు.", "Anjaneya turns and guides him onward; geography readable.", "Guiding gesture and walk.",
          "paid still + paid clip (protect the guidance)",
          [still("Anjaneya (C1) standing beside the rishi on a forest path at the foot of the hill, about to point the way, attached style. " + DRESS, F, ["C1:still"], ["C1:still"]),
           clip("Anjaneya turns, points along the path with his right hand and leads; the rishi follows. Hands whole; faces the same. Camera still.", F, "S04:still")], hold=0.8),
        S("S05", "అక్కడ యాద ఋషికి లక్ష్మీ నరసింహస్వామి దర్శనమిచ్చాడు. ఈ కథలో ఆ మొదటి దర్శనం జరిగేది గుట్ట కింద. ఋషి అక్కడే ఉండి స్వామిని ఎన్నో ఏళ్లు పూజించాడు.",
          "First darshan at the foot of the hill (per D1); years of worship pass.", "Light; seasons pass (local TimeOfDay).", "paid still + local",
          [still("At the foot of the hill, the rishi with joined hands before a radiant presence (as decided in D1), attached style. " + DRESS, F + ["Y-DARSHAN"], ["C1:still"], ["C1:still"])], ["Bloom", "TimeOfDay"]),
        S("S06", "యాద ఋషి కాలం తర్వాత, స్వామి అక్కడ ఉన్నాడని విని ఆ చుట్టుపక్కల గిరిజనులు పూజకు వచ్చేవారట. కొంతకాలానికి స్వామి గుట్ట మీదకు వెళ్లిపోయాడని కథ చెబుతుంది. మరి ఎక్కడికి వెళ్లాడు? వాళ్లు ఎంత వెతికినా జాడ దొరకలేదు.",
          "Local worshippers (change of light and cast); then the search in the hills.", "Torches move across the hill.", "paid still + paid clip",
          [still("Villagers from the surrounding forest bringing flowers to the foot of the hill, respectful everyday dress, attached style. No caricature. " + DRESS, F),
           clip("A small group with torches climbs among the rocks searching, moving left to right. Camera still.", F, "S06:still")]),
        S("S07", "ఒక రోజు వాళ్లలో ఒక భక్తురాలికి స్వామి కలలో కనిపించాడు. గుట్ట మీద ఓ పెద్ద గుహ ఉందని, తాను అక్కడ ఉన్నానని ఆమెకి తెలిపాడట. ఎన్నాళ్లుగానో వాళ్లు వెతుకుతున్న చోటు ఆ గుహ.",
          "Eye level with her: face to the cave opening; the rocky outline carries into the waking shot.", "Dream dissolve to cave.",
          "paid still + paid clip (protect the dream reveal)",
          [still("Night: the woman devotee (C1 sheet 2) asleep on a mat, her face in soft light, attached style. " + DRESS, F, ["C1:still"], ["C1:still"]),
           clip("Her face rests; the soft light behind her forms the outline of a rocky cave opening. Face stays the same. Camera slowly pushes in.", F, "S07:still")]),
        S("S08", "అక్కడ అందరికీ స్వామి ఐదు రూపాల్లో దర్శనమిచ్చాడని చెబుతారు. జ్వాల నరసింహుడు. యోగానంద నరసింహుడు. గండభేరుండ నరసింహుడు. ఉగ్ర నరసింహుడు. లక్ష్మీ నరసింహుడు. అందుకే యాదగిరిగుట్టను పంచ నరసింహ క్షేత్రం అని కూడా పిలుస్తారు.",
          "The gathered worshippers at the cave; each form named on its own beat (typeset), no five statues.", "Names appear one per beat.", "paid still + local",
          [still("The same woman (C1 sheet 2) and villagers gathered at the mouth of the cave with lamps, looking in, attached style. " + DRESS, F, ["C1:still"], ["C1:still"])], ["typeset five names"]),
        S("S09", "మొదట ఆంజనేయుడు ఒక ఋషికి దారి చూపాడు. తరవాత ఒక భక్తురాలికి వచ్చిన కలతో ఊరివాళ్లందరికీ దారి తెలిసింది. మీ ఇంట్లో యాదగిరిగుట్ట కథ ఎట్లా చెప్పేవాళ్లు?",
          "Echo the guidance gesture (reuse S04); finish on the present hill exterior.", "Cut to today's temple.", "reuse + paid still",
          [still("The present black-stone Yadagirigutta temple on its hill as in the chosen reference, evening, attached style. " + DRESS, ["Y-HILL"])], ["comment card"]),
    ]
    return build("ep05-yadagirigutta", shots, board("ep05-yadagirigutta", refs))


# ------------------------------------------------------------------------------------------ EP06
def ep06():
    refs = [
        {"id": "C-BROTHERS", "subject": "Three brothers (blind, deaf, unable to speak); no caricature", "status": "verified", "basis": "C1 telling; literary illustration"},
        {"id": "C-WATER", "subject": "Well, channel, field (no identity constraint)", "status": "verified"},
        {"id": "C-EXTERIOR", "subject": "Kanipakam temple exterior", "status": "lead", "note": "photo to choose (routine). Sanctum photography is prohibited; per the book no invented full-body murti"},
    ]
    B = ["C-BROTHERS"]
    W = ["C-WATER"]
    shots = [
        S("C1", None, "Sheet: three brothers. Not on screen.", "n/a", "paid still (reference)",
          [still("Character sheet: three farming brothers of different ages in simple dhotis, each with a distinct face; front and three-quarter views, attached style. Dignified, no caricature. " + DRESS, B)]),
        S("S01", "కాణిపాకం వినాయకుడు బావిలో ఎందుకున్నాడు?", "Water in a stone well; a ripple. Title first frame.", "Ripple spreads (local).", "paid still + local",
          [still("Looking down into a stone-lined well with still dark water, a single ripple, attached style. No text.", W)], ["title card", "ripple"]),
        S("S02", "ఆ బావి నీళ్లతో ఒకప్పుడు ముగ్గురు అన్నదమ్ములు పొలం సాగు చేసుకునేవారని కథ.", "Match cut: the ripple becomes an irrigation channel to a field.",
          "Water runs along the channel (local).", "paid still + local",
          [still("An irrigation channel running from a village well to green paddy fields, morning, attached style. No people. No text.", W)], ["flowing water"]),
        S("S03", "చిత్తూరు జిల్లాలోని ఈ క్షేత్రం గురించి దేవస్థానం చెప్పే కథ ఇది.", "Identified exterior.", "Map card.", "paid still + local",
          [still("Exterior of the Kanipakam Varasiddhi Vinayaka temple as in the chosen reference, morning, attached style. " + DRESS, ["C-EXTERIOR"])], ["map card"]),
        S("S04", "ఒకరికి కంటిచూపు లేదు. ఒకరికి వినికిడి లేదు. ఇంకొకరికి మాట రాదు. ముగ్గురూ కలిసి బావి నుంచి నీళ్లు తోడి కాలువ ద్వారా పొలానికి మళ్లించేవాళ్లు.",
          "The three brothers lifting water together; track the water to the field.", "Bucket rises; water pours into the channel.",
          "paid still + paid clip", [still("The three brothers (C1) working a rope-and-bucket lift at the well, water pouring into the channel, attached style. " + DRESS, B + W, ["C1:still"], ["C1:still"]),
                                     clip("The brothers pull the rope together; the bucket rises and tips water into the channel. Hands whole; faces the same. Camera still.", B + W, "S04:still")]),
        S("S05", "ఒక రోజు ఎంత తోడినా నీళ్లు రాలేదు. బావి ఇంకిపోయింది.", "Same action, empty vessel.", "Bucket comes up dry.", "paid still + paid clip",
          [still("The same brothers at the well; the bucket coming up empty, dry cracked mud below, attached style. " + DRESS, B + W, ["S04:still"], ["S04:still"]),
           clip("The bucket rises empty; the brothers look into it and then at each other. Camera still.", B + W, "S05:still")]),
        S("S06", "ఇంకా లోతు చేస్తే నీళ్లు పడతాయని ఒకరు బావిలోకి దిగారు. తవ్వుతుంటే పనిముట్టు గట్టి రాయికి తగిలింది.", "A brother lowers himself; the tool strikes stone.",
          "Climb down; strike (sound accent local).", "paid still + paid clip (protect the strike)",
          [still("Inside the dry well: one brother (C1) digging the mud floor with a short iron tool, light from above, attached style. " + DRESS, B, ["C1:still"], ["C1:still"]),
           clip("The brother swings the tool down and it strikes a hard stone with a jolt; he stops. Hands whole. Camera still.", B, "S06:still")]),
        S("S07", "నీళ్లు ఊరతాయనుకున్న చోట, ఆ రాయి నుంచి రక్తం వచ్చిందట. బావి నీరు ఎర్రబడింది. ఆ క్షణంలో ఒకరికి చూపు, ఒకరికి వినికిడి, ఇంకొకరికి మాట వచ్చాయని స్థలపురాణం చెబుతుంది.",
          "Restrained red tint spreading through rising water (code), then back to the brothers.", "Tint spreads; faces lift.", "reuse + paid still",
          [still("The three brothers at the well rim, one touching his eyes, one his ear, one his lips, in wonder, attached style. " + DRESS, B, ["C1:still"], ["C1:still"])], ["red tint in code"]),
        S("S08", "ఊరివాళ్లు అక్కడికి చేరారు. బావిలో కనిపించిన రూపం వినాయకుడిది. దాని అడుగు ఎక్కడుందో చూడాలని ఇంకాస్త తవ్వారు. ఎంత తవ్వినా అడుగు దొరకలేదట.",
          "Villagers work around the discovery, framed from above the rim; the waterline hides any base.", "Digging; water stays.", "paid still + paid clip",
          [still("From above the rim: villagers gathered around the well, water inside hiding everything below its surface, attached style. " + DRESS, B + W),
           clip("Villagers lean over the rim and dig at the edges; the water surface stays unbroken. Camera still.", W, "S08:still")]),
        S("S09", "వినాయకుడు అక్కడే స్వయంగా వెలిశాడని నమ్మి జనం కొబ్బరికాయలు సమర్పించారు. ఆ కొబ్బరినీళ్లు కాలువలో పారాయని కూడా కథలో చెబుతారు.",
          "Hands open a coconut; a narrow stream leads to the channel from the start.", "Coconut cracks; stream joins channel.", "paid still + paid clip",
          [still("Close view: hands breaking a coconut on a stone at the channel's edge, attached style. " + DRESS, W),
           clip("The coconut cracks open and its water runs in a thin stream into the irrigation channel. Hands whole. Camera still.", W, "S09:still")]),
        S("S10", "మొదట ఆ కాలువలో వాళ్లు ఎదురుచూసింది పొలానికి నీళ్లు. కథ చివరికి అదే కాలువలో పారింది స్వామికి సమర్పించిన కొబ్బరినీళ్లు. మరి ఆ బావి? కాణిపాకంలో ఈనాటికీ నీళ్ల మధ్యే వరసిద్ధి వినాయకుడిని దర్శించుకుంటారు.",
          "Return to the opening water, now understood; exterior plus water detail.", "Ripple; cut to exterior.", "reuse + local", [], ["ripple", "end card"], media_from="S01"),
    ]
    return build("ep06-kanipakam", shots, board("ep06-kanipakam", refs))


if __name__ == "__main__":
    for f in (ep02, ep03, ep04, ep05, ep06):
        d = f()
        clips = [(s["id"], c["settings"]["duration"]) for s in d["shots"] for c in s["paid"] if c["asset_type"] == "clip"]
        stills = sum(1 for s in d["shots"] for c in s["paid"] if c["asset_type"] == "still")
        print(f"{d['episode']:20s} ~{d['est_total_s']:5.1f}s  stills {stills:2d}  clips {clips}")

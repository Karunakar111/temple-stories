#!/usr/bin/env python3
"""Planning-level shot lists and reference boards for EP02-EP08 (re-runnable).

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
STYLE = ["STYLE-PATNAM"]
DRESS = "All figures fully clothed in simple period dress. No text, letters or script anywhere in the image."
# Unverified sacred imagery is never drawn: worshippers' reactions, light and identified exteriors carry it.
SACRED = "No deity figure, idol, murti or linga is visible; the sacred presence is carried only by light, lamps and the worshippers' reactions."
import re


def still(prompt, needs, after=None, refs=None):
    # references: image inputs, authority first and the style carrier last (config/production.json)
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


def S(i, text, picture, change, cls, paid=(), local=(), note=None, hold=0.0, clip_spans=None, media_from=None, cut_to=None):
    """text: the exact spoken span, or (first, last) sentence numbers of the voice; None = not on screen.
    cut_to: (shot id, seconds) for a second picture inside the same spoken span."""
    return {"id": i, "media_from": media_from, "text": text, "picture": picture, "what_changes": change, "class": cls,
            "paid": list(paid), "local": list(local), "note": note, "hold_after_s": hold,
            "clip_spans": clip_spans, "on_screen": text is not None, "cut_to": cut_to}


def sheet(i, desc, prompt, needs):
    """A character sheet: its own beat id, so its file and every reference to it are unambiguous."""
    return S(i, None, desc + " Not on screen.", "n/a", "paid still (character sheet)", [still(prompt + " " + DRESS, needs)])


def sentences(voice):
    return [m.group(0).strip() for m in re.finditer(r"[^.?!]+[.?!]", voice)]


def build(slug, shots, board):
    d = EP / slug
    voice = (d / "voice.te.txt").read_text(encoding="utf-8")
    sents = sentences(voice)
    t, pos, by_id = 0.0, 0, {}
    for s in shots:
        if isinstance(s["text"], tuple):
            a, b = s["text"]
            first = voice.index(sents[a], pos)
            s["text"] = voice[first:voice.index(sents[b], first) + len(sents[b])]
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
    _validate(slug, shots, board)
    narr = [{"beat": "VO", "provider": "elevenlabs", "asset_type": "narration", "model": "eleven_v4",
             "quote": str(len(voice.strip())), "settings": {"voice": "JWn8KOVJuYWznmih5YXL", "takes": 1},
             "text_path": f"episodes/{slug}/voice.te.txt", "prompt": "voice.te.txt", "references": [], "needs": []}]
    doc = {"episode": slug, "revision": 3,
           "timing_basis": "PROVISIONAL until the take: EP01's 14.68 chars/s, +0.5 s per paragraph, + planned breaths.",
           "est_total_s": round(t, 1), "narration": narr, "shots": shots}
    (d / "shots.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (d / "reference-board.json").write_text(json.dumps(board, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def _validate(slug, shots, board):
    """No two paid assets share a file name; every reference points at something that exists."""
    seen, stills = set(), {s["id"] for s in shots for c in s["paid"] if c["asset_type"] == "still"}
    board_ids = {r["id"] for r in board["references"]}
    for s in shots:
        for c in s["paid"]:
            key = (s["id"], c["asset_type"])
            if key in seen:
                raise SystemExit(f"{slug}: two {c['asset_type']}s on beat {s['id']} would share one file name")
            seen.add(key)
            for r in c.get("references", []) + c.get("after", []):
                if ":" in r:
                    if r.split(":")[0] not in stills:
                        raise SystemExit(f"{slug} {s['id']}: reference {r} has no producing still")
                elif r not in board_ids:
                    raise SystemExit(f"{slug} {s['id']}: reference {r} is not on the board")
        if s.get("media_from") and s["media_from"] not in stills:
            raise SystemExit(f"{slug} {s['id']}: reuses {s['media_from']}, which has no still")
        cuts = s.get("cut_to") or []
        for cid, _ in ([cuts] if cuts and not isinstance(cuts[0], (list, tuple)) else cuts):
            if cid not in stills:
                raise SystemExit(f"{slug} {s['id']}: cuts to {cid}, which has no still")


STYLE_REFS = [
    {"id": "STYLE-PATNAM", "subject": "EP01 patnam close (accepted B-derived frame)", "status": "approved-style",
     "path": "assets/pilot/shot3-patnam-v3-final.png", "use": "style input only", "rights": "own artwork",
     "media_id": "85b1b66a-3daa-4ab7-86e0-68bd5da05c9c",
     "media_check": "2026-11-24: Higgsfield media 85b1b66a matches the repo file pixel for pixel (mean abs diff 0.0)"},
]
EXT = {"status": "needs photo", "media_id": None,
       "note": "Identified exterior. Needs one rights-cleared photo (e.g. Wikimedia Commons, CC licence) imported to Higgsfield; until then the stills that use it are held."}


def board(slug, refs):
    return {"episode": slug, "revision": 3, "prepared": "2026-11-24",
            "status_meanings": {"approved-style": "EP01 art, style only", "verified": "identity confirmed from a named source",
                                "needs photo": "identified place; a rights-cleared photo must be imported to Higgsfield before use",
                                "not depicted": "sacred imagery not drawn: light, lamps and reactions instead"},
            "references": STYLE_REFS + refs}


# ------------------------------------------------------------------------------------------ EP02
def ep02():
    refs = [
        {"id": "K-LINGA", "subject": "Swayambhu Someshwara linga, Kolanupaka", "status": "not depicted",
         "basis": "Reported cracked (Deccan Chronicle, 2018); photography not allowed inside. Your rule: light, lamps and reactions."},
        {"id": "K-RENUKA", "subject": "Renukacharya", "status": "verified",
         "basis": "Production book: 'The sage is a literary illustration.' Ash, rudraksha, staff, water pot (K1 4.3-4)."},
        {"id": "K-AGASTYA", "subject": "Agastya and Lopamudra", "status": "verified",
         "basis": "Agastya: bearded, pot-bellied, matted hair, water pot in the left hand (Asian Civilisations Museum; V&A). Lopamudra: literary illustration."},
        {"id": "K-INSCRIPTION-TEXT", "subject": "1067 endowment (Epigraphia Telanganica I, p.168, no.147)", "status": "verified",
         "use": "typeset caption only; the stone is generic and unreadable"},
        {"id": "MALAYA-ASHRAM", "subject": "Malaya mountain and ashram (painted, no mapped route)", "status": "verified"},
    ]
    R, A = ["K-RENUKA"], ["K-AGASTYA"]
    RS, AS = "CS-RENUKA:still", "CS-AGASTYA:still"
    shots = [
        sheet("CS-RENUKA", "Character sheet: Renukacharya.",
              "Character sheet of a Shaiva sage in the attached illustrated folk style: lean ascetic, sacred ash over the body, rudraksha strands, wooden staff, brass water pot; front and three-quarter views, plain warm paper.", R),
        sheet("CS-AGASTYA", "Character sheet: Agastya and Lopamudra.",
              "Character sheet: the sage Agastya (short, bearded, pot-bellied, matted hair, water pot in his left hand) and his wife Lopamudra in a simple sari; front and three-quarter views, attached style.", A),
        S("S01", "కొలనుపాక సోమేశ్వర", "Temple interior at night: rows of oil lamps lead to a sanctum doorway of warm light; worshippers' silhouettes. Title on the first frame.",
          "Lamps flicker; light gathers in the doorway.", "paid still + local",
          [still("Interior of a stone Shiva temple at night seen from the hall: rows of oil lamps lead the eye to a sanctum doorway filled with warm golden light, its inside lost in the glow; two worshippers in silhouette with joined hands in the foreground, attached illustrated folk style. " + SACRED + " " + DRESS, [])],
          ["title card", "LampGlow", "Bloom"]),
        S("S02", "లింగం నుంచి ఓ గురువు వచ్చాడట. ఎవరాయన?", "The emergence: a sage resolves out of the light in the sanctum doorway; hold on his face after the question.",
          "Light becomes a figure; settles; we hold his face.", "paid still + paid clip (priority: emergence)",
          [still("The same temple doorway of golden light; a Shaiva sage (as in reference image 1) standing in the glow, the worshippers' silhouettes leaning back in wonder, attached style. " + SACRED + " " + DRESS, R, [RS], [RS]),
           clip("The golden light around the sage softens as he becomes solid and still; the worshippers lean back slightly. His face, ash marks and rudraksha stay exactly the same. Camera almost still.", R, "S02:still")],
          note="Spans the whole hook plus a 1.2 s breath; the clip is cut to fit.", hold=1.2),
        S("S03", "ఊరి జనం కూడా ఆయన్ని చూసి అదే అడిగారు. వీరశైవుల గ్రంథం ‘సిద్ధాంత శిఖామణి’లో ఈ కథ ఇలా సాగుతుంది.",
          "Villagers looking up; source name typeset as an editorial card.", "Card rises on 'సిద్ధాంత శిఖామణి'.", "paid still + local",
          [still("Villagers of a Telangana village gathered at a temple doorway at night, looking in with wonder, lamp light on their faces, attached style. Respectful, no caricature. " + SACRED + " " + DRESS, [])], ["source card"]),
        S("S04", "ఒంటినిండా విభూతి. మెడలో రుద్రాక్షలు. చేతిలో దండం, కమండలం.", "Details from the S02 still at 2k: ash, rudraksha, staff, water pot.",
          "Camera moves detail to detail on each phrase.", "reuse + local", [], ["Stage camera"], media_from="S02"),
        S("S05", "తన పేరు రేణుకసిద్ధుడని, శివుడి ఆజ్ఞతో ఇక్కడికి వచ్చానని ఆ యోగి చెప్పాడట. ఆయన్నే రేణుకాచార్యుడని పిలుస్తారు.",
          "The sage speaking to seated villagers outside the temple; name typeset 'రేణుకాచార్యుడు'.", "Name card on the name.", "paid still + local",
          [still("The Shaiva sage (reference image 1) standing in a temple courtyard, speaking calmly to seated villagers, one hand raised in blessing, attached style. " + DRESS, R, [RS], [RS])], ["name card"]),
        S("S06", "ఊరి వాళ్లు ఇంకా చూస్తుండగానే ఆయన ఆకాశమార్గాన మలయ పర్వతానికి వెళ్లాడు.", "He rises out of frame; match cut to the mountain sky.",
          "Upward departure; heads tilt up.", "paid clip + local match cut",
          [clip("The sage rises gently straight upward and out of the top of the frame; the villagers tilt their heads to follow. Faces and dress stay the same. Camera still.", R, "S05:still")]),
        S("S07", "అక్కడ అగస్త్య మహర్షి ఆశ్రమం ఉంది.", "Wooded mountain and ashram.", "Mist, birds, hut lamp.", "paid still + local",
          [still("A wooded mountain ridge at dawn, a small thatched hermitage in a clearing with a sacred fire, attached illustrated folk style. No people. No text.", ["MALAYA-ASHRAM"])], ["Stage parallax", "Birds"]),
        S("S08", "రేణుకాచార్యుణ్ని చూడగానే అగస్త్యుడు కూర్చున్న చోటు నుంచి లేచాడు.", "Agastya sees the visitor and rises.", "Agastya stands to receive him.",
          "paid still + paid clip",
          [still("Agastya (reference image 2) seated on a deer skin outside the hermitage, looking up as the Shaiva sage (reference image 1) arrives, attached style. " + DRESS, A + R, [RS, AS], [RS, AS]),
           clip("Agastya rises from his seat and steps forward with joined hands to receive the visitor. Faces and dress stay the same; hands whole with five fingers. Camera still.", A + R, "S08:still")]),
        S("S09", "లోపాముద్ర నీళ్లు తీసుకొచ్చింది.", "Lopamudra brings the vessel; Agastya receives it.", "One readable hand-over.",
          "paid still + paid clip (priority: two-person welcome)",
          [still("Outside the hermitage: Lopamudra (reference image 2) has just arrived beside Agastya (reference image 2), holding a brass water vessel out to him with both hands; Agastya reaches for it; the visiting Shaiva sage (reference image 1) stands a step away, attached style. " + DRESS, A + R, [RS, AS], [RS, AS]),
           clip("Lopamudra offers the brass vessel; Agastya takes it in both hands and she lets go and steps back. One continuous hand-over. Faces and dress stay the same; hands whole with five fingers. Camera still.", A, "S09:still")], hold=0.6),
        S("S10", "ఆ నీళ్లతో అగస్త్యుడు స్వయంగా అతిథి పాదాలు కడిగాడు.", "Closer: Agastya washes the visitor's feet.", "Water pours; hands wash.",
          "paid still + paid clip (priority)",
          [still("Close view: Agastya (reference image 2) kneeling, pouring water from a brass vessel over the bare feet of the standing Shaiva sage (reference image 1), attached style. " + DRESS, A + R, [RS, AS], [RS, AS]),
           clip("Agastya pours water slowly over the visitor's feet and gently washes them with his other hand. Feet, hands and faces stay whole and the same. Camera still.", A + R, "S10:still")]),
        S("S11", "ఆ తర్వాత ఇద్దరూ కూర్చున్నారు. ఎన్నో ఆగమాలు విన్న అగస్త్యుడికే ఇంకా సందేహాలున్నాయట. శివతత్త్వాన్ని మీ నోట వినాలని అడిగాడు.",
          "Both seated; Agastya asks.", "Cut on the question.", "paid still + local",
          [still("Agastya (reference image 2) and the Shaiva sage (reference image 1) seated facing each other on mats inside the hermitage, Lopamudra seated a little behind Agastya; Agastya asks with an open hand, the sage listens with lowered eyes, attached style. " + DRESS, A + R, [RS, AS], [RS, AS])]),
        S("S12", "రేణుకాచార్యుడు ఒక్క క్షణం శివుణ్ని తలచుకుని చెప్పడం మొదలుపెట్టాడు.", "Teacher pauses, then begins; listening reaction.",
          "Key-pose cut T1 -> T2 (Experiment 01).", "paid still (second key pose) + local KeyPoseCut",
          [still("SAME composition and camera as reference image 1: now the Shaiva sage looks up and speaks with a raised teaching hand while Agastya listens with joined hands, attached style. " + DRESS, A + R, ["S11:still"], ["S11:still"])],
          ["KeyPoseCut"], note="If the two key poses do not register, a straight cut (no extra spend)."),
        S("S13", "భక్తుని ప్రయాణం ఎక్కడ మొదలవుతుంది? శివుడితో ఐక్యం కావడమంటే ఏంటి? ఆ గ్రంథం ముందుకు సాగేది ఇలాంటి ప్రశ్నలతోనే.",
          "The two questions typeset over the dimmed S12 frame.", "Each question on its phrase.", "reuse + local", [], ["typeset questions"], media_from="S12"),
        S("S14", "కథ చివర్లో రేణుకాచార్యుడు మళ్లీ కొలనుపాకకు వచ్చాడు. ఊరి జనం చూస్తుండగా సోమేశ్వరుడి ఎదుట నిలబడి ప్రార్థించాడు.",
          "Return to the opening composition: the sage in prayer at the glowing doorway, villagers watching.", "Lamps; slow push.", "paid still + local",
          [still("The same temple interior as reference image 1: the Shaiva sage (reference image 2) standing before the glowing sanctum doorway with palms joined in prayer, villagers watching from behind, attached style. " + SACRED + " " + DRESS, R, ["S01:still", RS], ["S01:still", RS])]),
        S("S15", "లింగం నుంచి శివుడి పిలుపు వినిపించిందట. వచ్చిన దారినే, ఒక జ్యోతిలా, ఆయన అందులో ఐక్యమయ్యాడని ఈ సంప్రదాయం చెబుతుంది.",
          "He becomes light and flows into the doorway's glow; a witness lowers his hands.", "Figure becomes light and merges.",
          "paid clip (priority: return into light) + local Bloom",
          [clip("The sage slowly turns into soft golden light that flows into the glowing sanctum doorway and disappears; a villager lowers his joined hands. Nothing inside the doorway becomes visible. Camera still.", R, "S14:still")],
          note="Artistic depiction of a tradition", hold=0.6),
        S("S16a", "ఇదే గుడి గురించి రాతి మీద మిగిలిన మాట కూడా ఒకటుంది.", "The inscription card: the carved stone in raking light (the S16b still) before the date builds.",
          "Light rakes across the stone.", "reuse (S16b inscription still) + local", [], ["Stage camera"],
          note="No exterior photo needed (24 Nov)", media_from="S16b"),
        S("S16b", "వెయ్యి అరవై ఏడో సంవత్సరపు శాసనంలో ఇక్కడి స్వయంభూ సోమేశ్వరుడి పూజలకు ఇచ్చిన దానం నమోదైంది.",
          "Stone detail in raking light; typeset 'క్రీ.శ. 1067 · పూజలకు దానం' builds on the year.", "Light rakes; caption builds.", "paid still + local",
          [still("A weathered grey stone slab with eroded, unreadable carved lines in a museum courtyard, raking evening light, attached style. No legible letters of any script.", ["K-INSCRIPTION-TEXT"])], ["date card"]),
        S("S16c", "అంటే అప్పటికే ఇక్కడ పూజలు జరుగుతున్నాయని తెలుస్తోంది.", "Consequence: worship continuing (reuse S01 with lamps and arati glow).",
          "Lamps brighten; arati light circles.", "reuse + local", [], ["LampGlow", "Bloom"], media_from="S01"),
        S("S17", "కొలనుపాక వెళ్తే ఈ రెండు గుర్తుపెట్టుకోండి. లింగం దగ్గర రేణుకాచార్యుడి కథ. గుడి ఆవరణలోని శాసనంలో, ఆ పూజలు కొనసాగేందుకు ఎవరో ఇచ్చిన దానం.",
          "Close on the approved Renukacharya artwork (the S05 still: the sage addressing the villagers); the two reminders typeset.",
          "Slow push; two lines appear.", "reuse (S05 Renukacharya still) + local", [], ["reminders"],
          note="No exterior photo needed (24 Nov)", media_from="S05"),
    ]
    return build("ep02-kolanupaka", shots, board("ep02-kolanupaka", refs))


# ------------------------------------------------------------------------------------------ EP03
def ep03():
    """Focus: the kode mokku. The origin legend stays in the voice (approved text) but is carried
    mostly by stills and local motion; paid motion goes to the bull, the walk and the tethering."""
    refs = [
        {"id": "V-KODE", "subject": "Kode mokku: pradakshina with a bull, then tying it as an offering", "status": "verified",
         "basis": "Telangana Tourism 'The Abode of Vemulawada Rajanna'; reporting photos (reference only, not reproduced)"},
        dict(EXT, id="V-EXTERIOR", subject="Sri Raja Rajeshwara temple, Vemulawada"),
        {"id": "V-TANK", "subject": "Dharma Gundam tank beside the temple", "status": "not depicted",
         "note": "No rights-cleared photo found on Wikimedia Commons (24 Nov 2026). Agreed fallback: an illustrated tank marked ప్రతీకాత్మక చిత్రం."},
        {"id": "V-1961", "subject": "1961 record: two uprights at the east entrance where calves and bulls were tied", "status": "verified",
         "basis": "Production book V1 (Census 1961, Karimnagar). Simple ink view, no reconstructed gateway"},
        {"id": "NARENDRA", "subject": "King Narendra, the rishi (sthala purana)", "status": "verified", "basis": "literary illustration"},
    ]
    K = ["V-KODE"]
    FS, NS = "CS-FAMILY:still", "CS-NARENDRA:still"
    shots = [
        sheet("CS-FAMILY", "Character sheet: devotee family and bull.",
              "Character sheet: a Telangana farming family (father, mother, son) in everyday clothes and a young white bull with a rope halter; front and side views, attached style.", K),
        sheet("CS-NARENDRA", "Character sheet: King Narendra and the rishi.",
              "Character sheet: a king of legend in simple hunting dress with a bow, and an elderly rishi with a water pot; front and three-quarter views, attached style.", ["NARENDRA"]),
        S("S01", "వేములవాడ రాజన్నకు కోడెను ఎందుకు కడతారు?", "The tether on frame one: hands knotting the bull's rope to a stone post, the bull beside. Title on the first frame.",
          "Hands loop and knot the rope; the bull stands calmly.", "paid still + paid clip (protect the tethering; plays to the knot)",
          [still("Close view in a temple courtyard: a devotee's hands tying a young white bull's rope to a worn stone post, the rope already looped once, the bull from reference image 1 standing calmly beside the post, attached style. " + DRESS, K, [FS], [FS]),
           clip("The hands pull the loop tight, knot the rope around the post and let go; the bull stands calmly. Hands whole. Camera still.", K, "S01:still", max_s=4)],
          ["title card"]),
        S("S02", "భక్తుల అడుగుల పక్కనే కోడె గిట్టలు. తాడు పట్టుకుని దానితోపాటు నడుస్తున్న ఆ కుటుంబాన్ని చూడండి.", "Low beside walking feet and hooves; rise to reveal the family walking with the bull.",
          "Walking gait; slack lead; rise.", "paid still + paid clip (protect the bull's gait)",
          [still("Low angle on a temple courtyard: bare human feet walking beside the hooves of a young white bull on a slack rope, the family and bull as in reference image 1, attached style. " + DRESS, K, [FS], [FS]),
           clip("The bull and the devotee walk forward together at a natural pace, the rope slack between them; the camera rises slowly to reveal the family. Natural gait, four legs moving correctly.", K, "S02:still", max_s=6)]),
        S("S03", "ఇక్కడి శివుడి పేరు రాజరాజేశ్వరుడు. భక్తులు పిలిచేది మాత్రం రాజన్నా అని. ఇంటిల్లిపాదీ చల్లగా ఉండాలని కొందరు మొక్కుకుంటారు.",
          "Identified temple exterior with families and bulls in the courtyard; name cards 'రాజరాజేశ్వరుడు' and 'రాజన్న'.", "Cards on the names.", "paid still + local",
          [still("Exterior of the Sri Raja Rajeshwara temple at Vemulawada exactly as in reference image 1, morning, families leading young bulls in the courtyard, attached style. " + DRESS, ["V-EXTERIOR"], refs=["V-EXTERIOR"])], ["name cards"]),
        S("S04", "కోడెతో కలిసి ప్రదక్షిణ చేసి,", "The same pair circles the shrine.",
          "Pradakshina.", "paid still + paid clip (protect the walk)",
          [still("The same family and bull (reference image 1) walking clockwise around a temple shrine wall, attached style. " + DRESS, K, [FS], [FS]),
           clip("The family and the bull walk clockwise along the shrine wall and out of frame. Natural gait. Camera still.", K, "S04:still")]),
        S("S04b", "దాన్ని స్వామికి అర్పణగా కడతారు. అదే కోడె మొక్కు.", "The tether again: the knotted rope and the bull standing at the post (S01's picture, pulled back).",
          "Slow pull back from the knot to the bull.", "reuse S01 (no new asset)", [], ["pull back"], media_from="S01", hold=0.4),
        S("S05", "అరవై ఏళ్ల కిందటి వేములవాడ గురించి చదివితే ఒక చిన్న వివరముంటుంది. గుడి తూర్పు ద్వారం ముందు రెండు స్తంభాలు. భక్తులు తెచ్చిన దూడల్ని, కోడెల్ని అక్కడ కట్టేవారని అప్పటి నమోదులో ఉంది.",
          "A simple ink view: two uprights and a calf; 'ఆరవై ఏళ్ల క్రితం' card.", "Ink draws on.", "paid still + local",
          [still("A simple ink drawing on warm paper: two stone uprights at a temple entrance with a calf tied to one, sparse lines, attached style. No text.", ["V-1961"])], ["ink reveal"]),
        S("S06", "మరి ఆ రాజన్న ఈ ఊర్లో ఎలా వెలిశాడంటారు? దానికి ఇక్కడి స్థలపురాణం మనల్ని గుడి పక్కనున్న ధర్మగుండం దగ్గరికి తీసుకెళ్తుంది.",
          "An illustrated temple tank (marked ప్రతీకాత్మక చిత్రం); light shifts into legend.", "Water shimmer; light change.", "paid still + local",
          [still("A stepped stone temple tank beside an old temple, still water, evening light, attached style. " + DRESS, ["V-KODE"])], ["water shimmer", "TimeOfDay", "mark ప్రతీకాత్మక చిత్రం"],
          note="No rights-cleared photo of the Dharma Gundam was found; the agreed fallback is an illustrated tank marked ప్రతీకాత్మక చిత్రం."),
        S("S07", "నరేంద్రుడనే రాజు వేటకు వెళ్లాడట.", "The king drawing his bow among the trees, no target in frame.", "Local push.", "paid still + local (extra still, approved list)",
          [still("King Narendra (reference image 1) in simple hunting dress drawing his bow among forest trees, aiming off frame, no target visible, attached style. " + DRESS, ["NARENDRA"], [NS], [NS])], ["Stage camera"]),
        S("S07b", "నీళ్లు తెచ్చుకోవడానికి వచ్చిన ఒక ఋషికి పొరపాటున అతని బాణం తగిలింది. ఋషి చనిపోయాడు.",
          "Forest stream: the rishi's vessel lies in the stream; the king lowers his bow. No injury shown.", "Local push; no paid motion (legend kept short).", "paid still + local",
          [still("A forest stream: a fallen brass water pot in the shallows, the king (reference image 1) lowering his bow in shock among the trees, attached style. No wound or blood. " + DRESS, ["NARENDRA"], [NS], [NS])], ["Stage camera"]),
        S("S08", "ఆ పాపం నుంచి బయటపడాలని రాజు ఎన్నో క్షేత్రాలు తిరిగాడు. చివరికి వేములవాడ చేరాడు.", "The king through changing landscapes.",
          "Days and seasons pass (local TimeOfDay).", "paid still + local",
          [still("The king (reference image 1) walking alone along a long road through hills, attached style. " + DRESS, ["NARENDRA"], [NS], [NS])], ["TimeOfDay"]),
        S("S09", "ఇక్కడి ధర్మగుండంలోకి చెయ్యి చాపి మూడు దోసిళ్ల నీళ్లు తాగాడట. ఆ పాపం తొలగిందని కథ చెబుతుంది.",
          "His cupped hands and the water.", "Local ripples on three beats.", "paid still + local",
          [still("Close view: the king's cupped hands lifting water from a stone tank, attached style. " + DRESS, ["NARENDRA"], [NS], [NS])], ["ripples x3"]),
        S("S10", "ఆ రాత్రి శివుడు కలలో కనిపించి, గుండం అడుగున లింగం ఉందనీ, దాన్ని తీసి ఒడ్డున ప్రతిష్ఠించాలనీ చెప్పాడు.",
          "The dream: the king asleep by the tank; a glow under the water.", "Water sound fades; glow rises.", "paid still + local",
          [still("Night: the king (reference image 1) asleep on the bank of the tank, a soft light glowing beneath the water, attached style. " + SACRED + " " + DRESS, ["NARENDRA"], [NS], [NS])], ["Bloom"]),
        S("S11", "రాజు నీటిలో వెతికాడు. లింగం దొరికింది.",
          "The king waist-deep, his face lit from below by light in his hands.", "Glow rises with his hands.", "paid still + local Bloom",
          [still("The king (reference image 1) waist-deep in the tank at dawn, lifting his cupped hands from the water, his face lit from below by a warm glow between his hands, attached style. " + SACRED + " " + DRESS, ["NARENDRA"], [NS], [NS])], ["Bloom"]),
        S("S11b", "దొరికిన గుండం ఒడ్డునే ప్రతిష్ఠించాడు. వేములవాడలో రాజేశ్వరుడి ఆవిర్భావాన్ని ఇలా చెప్పుకుంటారు.",
          "The lamp-lit bank: the king kneeling before a small lamp-lit shrine, seen from behind.", "Lamps flicker (local).", "paid still + local (extra still, approved list)",
          [still("Dawn on the bank of the tank: the king (reference image 1) seen from behind, kneeling with joined hands before a small stone shrine ringed with oil lamps, attached style. " + SACRED + " " + DRESS, ["NARENDRA"], [NS], [NS])], ["lamp flicker"]),
        S("S12", "మీ ఇంట్లో ఎవరైనా రాజన్నకి కోడె మొక్కు తీర్చారా? ఆ రోజు మీకు గుర్తున్నది ఏంటో చెప్పండి.", "Back to the walking pair; comment card.",
          "Walk continues; card.", "reuse S02 clip + local", [], ["comment card"], media_from="S02"),
    ]
    return build("ep03-vemulavada", shots, board("ep03-vemulavada", refs))


# ------------------------------------------------------------------------------------------ EP04
STONE = "the stone in the clearing kept as a small dark shape in shadow, its form not detailed"


def ep04():
    refs = [
        {"id": "S-ANIMALS", "subject": "Spider, snake, elephant (natural, no giant fantasy spider)", "status": "verified", "basis": "Production book S1"},
        {"id": "S-FOREST-STONE", "subject": "The worshipped stone in the forest (legend)", "status": "not depicted",
         "basis": "Your rule: kept as a dark shape in shadow; the animals' actions and light carry it"},
        {"id": "S-TEMPLE-LINGA", "subject": "Present Srikalahasti linga", "status": "not depicted", "basis": "Sanctum photography prohibited; not drawn"},
        dict(EXT, id="S-EXTERIOR", subject="Srikalahasti temple gopurams and the Swarnamukhi"),
    ]
    N = ["S-ANIMALS"]
    AN = "CS-ANIMALS:still"
    shots = [
        sheet("CS-ANIMALS", "Design sheet: elephant, cobra, spider in house style.",
              "Design sheet in the attached illustrated folk style: an Indian elephant, a cobra, and a small natural garden spider with its web, each drawn naturally, plain warm paper.", N),
        S("S01", "శ్రీకాళహస్తి కథలో ఏనుగు పూజ చేస్తే సాలెగూడు ఎందుకు తెగింది?", "Cold open in macro: silk releases, a gem rolls; tilt up the falling stream to the trunk. Title first frame.",
          "Web tears; gem rolls; stream revealed.", "paid still + paid clip (protect the pour)",
          [still(f"Macro in a forest clearing: a stream of water falling from the tip of an elephant's trunk (reference image 1) through a spider web, a red gem on a flat rock below, {STONE}, attached style. No text.", N, [AN], [AN]),
           clip("Water pours from the elephant's trunk; the spider web tears and the red gem rolls aside; the camera tilts up the stream to reveal the trunk. Direction of flow stays downward.", N, "S01:still", max_s=6)],
          ["title card"], clip_spans=["S01", "S02"]),
        S("S02", "లింగం మీదికి నీళ్ల ధార పడింది. పాము తెచ్చి పెట్టిన మణులు కూడా పక్కకు దొర్లిపోయాయి. ఆ నీళ్లు పోసింది ఏనుగే.", "(clip continues)", "", "covered by the S01 clip", media_from="S01"),
        S("S03", "స్వర్ణముఖి ఒడ్డున ఉన్న శ్రీకాళహస్తి గురించి చెప్పుకునే కథల్లో ఇదొకటి.", "River and the identified temple; dissolve into forest.", "Water light; dissolve.",
          "paid still + local", [still("The Srikalahasti temple gopurams beside the Swarnamukhi river exactly as in reference image 1, morning, attached style. " + DRESS, ["S-EXTERIOR"], refs=["S-EXTERIOR"])], ["map card"]),
        S("S04", "అడవిలో ఒక శివలింగం. ఎండ పడినా, వాన వచ్చినా లింగానికి అడ్డుగా ఉండాలని ఒక సాలెపురుగు దారం మీద దారం వేసి గూడు అల్లేది.",
          "Forest clearing in dappled light; the spider spins a shelter between two branches; the stone stays in shadow.", "Web draws thread by thread.",
          "paid still + LOCAL web animation", [still(f"A quiet forest clearing between two low branches, dappled light falling around {STONE}, no web yet, attached style. No text.", N)],
          ["procedural web drawn in code", "small spider sprite"], note="Web drawn in code instead of a paid clip"),
        S("S05", "పాము నేల లోపలి నుంచి మణులు తెచ్చి అదే లింగాన్ని అలంకరించేది.", "The same snake approaches; a jewel settles in the light.", "Snake glides in; gem placed.",
          "paid still + paid clip", [still(f"The same clearing as reference image 1 under its web; a cobra (reference image 2) emerging from a hole in the ground with a glowing red gem, {STONE}, attached style. No text.", N, ["S04:still", AN], ["S04:still", AN]),
                                     clip("The cobra glides forward and leaves the red gem in a patch of light, then withdraws. Camera still.", N, "S05:still")]),
        S("S06", "ఏనుగు వంతు వచ్చేసరికి దాని తొండం నిండా నీళ్లు. అది లింగానికి అభిషేకం చేసేది. ఆ ధార తగిలితే గూడు నిలుస్తుందా? మణులు అక్కడే ఉంటాయా?",
          "Continuous trunk lift and pour; why one offering displaces the others.", "Trunk lifts, pours.", "paid still + paid clip (protect)",
          [still(f"The elephant (reference image 1) in the clearing with its trunk raised, water about to pour, web and gem visible, {STONE}, attached style. No text.", N, [AN], [AN]),
           clip("The elephant lifts its trunk in one continuous movement and pours water downward; the web sags and the gem washes aside. Trunk and stream stay continuous. Camera still.", N, "S06:still")]),
        S("S07", "తాను తెచ్చిన మణులు పక్కకు పోవడం చూసి పాముకి కోపం వచ్చింది. ఏనుగు తొండంలోకి దూరింది.", "The snake approaches the trunk.", "Snake rises.",
          "paid clip", [clip("The cobra rises and slides toward the elephant's trunk. No bite or injury shown. Camera still.", N, "S06:still")], media_from="S06"),
        S("S08", "ఊపిరాడక ఏనుగు చెట్టు బోదెకి గుద్దుకుంది. ఆ బోదె మీదే సాలెపురుగు కూడా ఉంది. ఈ కథనంలో మూడూ అక్కడే ప్రాణాలు విడిచాయి.",
          "The tree shudders; the web falls still. The voice carries the deaths.", "Shudder; stillness.", "paid still + local",
          [still("A large tree trunk in the forest with a spider web on its bark, leaves falling, no animals visible, attached style. No text.", N)], ["camera shake", "falling leaves"],
          note="No graphic injury"),
        S("S09", "ఒకటి నీడ ఇచ్చింది. ఒకటి తనకి దొరికిన మణులు ఇచ్చింది. ఇంకొకటి నీళ్లు తెచ్చింది. మూడింటి భక్తికీ మెచ్చి శివుడు వాటికి ముక్తినిచ్చాడని చెబుతారు.",
          "The three offerings together, lit.", "Light blooms on each offering in turn.", "paid still + local",
          [still(f"The forest clearing with all three offerings at once: a spider web catching the light, a red gem on a rock, water glistening, warm light falling through the leaves, {STONE}, attached style. No text.", N)], ["Bloom"]),
        S("S10", "ఆ మూడు ప్రాణుల్ని ఈ క్షేత్రం పేరులోనే గుర్తు చేసుకుంటారు. శ్రీ అంటే ఇక్కడ సాలెపురుగు. కాళం అంటే పాము. హస్తి అంటే ఏనుగు. కలిపి పలకండి… శ్రీకాళహస్తి.",
          "One offering per spoken name; the Telugu name builds from typeset letters, then the identified exterior.", "Name builds.", "reuse + local",
          [], ["typeset name build"], media_from="S09"),
    ]
    return build("ep04-srikalahasti", shots, board("ep04-srikalahasti", refs))


# ------------------------------------------------------------------------------------------ EP05
def ep05():
    refs = [
        dict(EXT, id="Y-HILL", subject="Yadagirigutta hill and the present black-stone temple (rebuilt 2016-2022)"),
        {"id": "Y-FIGURES", "subject": "Yada rishi and the woman devotee", "status": "verified", "basis": "literary illustration"},
        {"id": "Y-GUIDE", "subject": "Anjaneya as the guide", "status": "not depicted", "basis": "Your rule: light on the path and the rishi's reaction"},
        {"id": "Y-DARSHAN", "subject": "Lakshmi Narasimha at the first darshan", "status": "not depicted", "basis": "Light and the rishi's reaction"},
        {"id": "Y-FORMS", "subject": "The five forms, named on screen", "status": "verified", "basis": "Y1-Y2; names only, no statues"},
    ]
    F = ["Y-FIGURES"]
    YS, DS = "CS-YADA:still", "CS-DEVOTEE:still"
    shots = [
        sheet("CS-YADA", "Character sheet: Yada rishi.",
              "Character sheet: an elderly rishi in simple saffron cloth with matted hair and a water pot, seated in penance and standing; front and three-quarter views, attached style.", F),
        sheet("CS-DEVOTEE", "Character sheet: the woman devotee.",
              "Character sheet: a village woman devotee in a simple sari, front and three-quarter views, attached style.", F),
        S("S01", "యాదగిరిగుట్టలో నరసింహుడు ఏ గుహలో ఉన్నాడో ఎలా తెలిసింది?", "The cave mouth from her point of view; cut before the reveal. Title first frame.",
          "Torch light flickers at the mouth.", "paid still + local",
          [still("Point of view looking into a rocky cave mouth on a hill at night, torch light, the inside lost in darkness, attached style. No people. No text. " + SACRED, [])], ["title card", "LampGlow"]),
        S("S02", "దేవస్థానం చెప్పే ఓ కథ ప్రకారం, ఆ దారి ఒక భక్తురాలికి కలలో తెలిసిందట. కానీ కథ మొదలయ్యేది గుట్ట కింద, ఒక ఋషి దగ్గర.",
          "Recurring hill silhouette; drop to its foot.", "Light moves down the hill.", "paid still + local",
          [still("The rocky hill of Yadagirigutta as in reference image 1, seen in silhouette at dawn with forest at its foot, attached style. No text.", ["Y-HILL"], refs=["Y-HILL"])], ["Stage camera"]),
        S("S03", "యాద ఋషి తపస్సు చేశాడట. ఆయన తపస్సుకు మెచ్చిన నారాయణుడు ఆంజనేయుణ్ని పంపాడు.", "Yada looks up from his penance toward a light.", "He opens his eyes and looks up.",
          "paid still + paid clip", [still("The rishi (reference image 1) seated in penance at the foot of the hill, eyes closed, attached style. " + DRESS, F, [YS], [YS]),
                                     clip("The rishi opens his eyes and slowly looks up toward a soft warm light. Face stays the same. Camera still.", F, "S03:still")]),
        S("S04", "ఆంజనేయుడు ఋషికి దారి చూపాడు.", "A warm light moves ahead along the forest path; the rishi follows it. The guide himself is not drawn.", "Light leads; he follows.",
          "paid still + paid clip (protect the guidance)",
          [still("The rishi (reference image 1) standing on a forest path at the foot of the hill, turning toward a warm light further along the path, attached style. " + SACRED + " " + DRESS, F, [YS], [YS]),
           clip("The warm light moves along the path and the rishi follows it with joined hands. Face stays the same. Camera still.", F, "S04:still")], hold=0.8),
        S("S05", "అక్కడ యాద ఋషికి లక్ష్మీ నరసింహస్వామి దర్శనమిచ్చాడు. ఈ కథలో ఆ మొదటి దర్శనం జరిగేది గుట్ట కింద. ఋషి అక్కడే ఉండి స్వామిని ఎన్నో ఏళ్లు పూజించాడు.",
          "First darshan carried by the rishi's face lit by radiance from beyond frame; years of worship pass.", "Light; seasons pass (local TimeOfDay).", "paid still + local",
          [still("At the foot of the hill, the rishi (reference image 1) with joined hands and tears of joy, his face lit by a radiant golden light from beyond the frame, attached style. " + SACRED + " " + DRESS, F, [YS], [YS])], ["Bloom", "TimeOfDay"]),
        S("S06", "యాద ఋషి కాలం తర్వాత, స్వామి అక్కడ ఉన్నాడని విని ఆ చుట్టుపక్కల గిరిజనులు పూజకు వచ్చేవారట. కొంతకాలానికి స్వామి గుట్ట మీదకు వెళ్లిపోయాడని కథ చెబుతుంది.",
          "Local worshippers bring flowers to the foot of the hill.", "Local push up the hill.", "paid still + local",
          [still("Villagers from the surrounding forest bringing flowers to the foot of the hill, respectful everyday dress, attached style. No caricature. " + SACRED + " " + DRESS, F)], ["push up the hill"]),
        S("S06b", "మరి ఎక్కడికి వెళ్లాడు? వాళ్లు ఎంత వెతికినా జాడ దొరకలేదు.",
          "Night: a small torch party searching among the rocks of the hill.", "Torches move across the hill.", "paid still (extra still, approved list) + paid clip",
          [still("Night on a rocky hillside: a small group of villagers with burning torches searching among the boulders, respectful everyday dress, attached style. No caricature. " + SACRED + " " + DRESS, F),
           clip("The small group with torches climbs among the rocks searching, moving left to right; torch light flickers on the boulders. Camera still.", F, "S06b:still")]),
        S("S07", "ఒక రోజు వాళ్లలో ఒక భక్తురాలికి స్వామి కలలో కనిపించాడు. గుట్ట మీద ఓ పెద్ద గుహ ఉందని, తాను అక్కడ ఉన్నానని ఆమెకి తెలిపాడట. ఎన్నాళ్లుగానో వాళ్లు వెతుకుతున్న చోటు ఆ గుహ.",
          "Eye level with her: the soft light behind her forms a cave opening.", "Dream dissolve to cave.",
          "paid still + paid clip (protect the dream reveal)",
          [still("Night: the woman devotee (reference image 1) asleep on a mat, her face in soft light, attached style. " + DRESS, F, [DS], [DS]),
           clip("Her face rests; the soft light behind her forms the outline of a rocky cave opening. Face stays the same. Camera slowly pushes in.", F, "S07:still")]),
        S("S08", "అక్కడ అందరికీ స్వామి ఐదు రూపాల్లో దర్శనమిచ్చాడని చెబుతారు. జ్వాల నరసింహుడు. యోగానంద నరసింహుడు. గండభేరుండ నరసింహుడు. ఉగ్ర నరసింహుడు. లక్ష్మీ నరసింహుడు. అందుకే యాదగిరిగుట్టను పంచ నరసింహ క్షేత్రం అని కూడా పిలుస్తారు.",
          "The woman and villagers at the cave mouth, faces lit from inside; each form named on its own beat (typeset), no statues.", "Names appear one per beat.", "paid still + local",
          [still("The woman devotee (reference image 1) and villagers gathered at the mouth of a cave with lamps, faces lit by golden light from inside the cave, attached style. " + SACRED + " " + DRESS, F, [DS], [DS])], ["typeset five names"]),
        S("S09", "మొదట ఆంజనేయుడు ఒక ఋషికి దారి చూపాడు. తరవాత ఒక భక్తురాలికి వచ్చిన కలతో ఊరివాళ్లందరికీ దారి తెలిసింది. మీ ఇంట్లో యాదగిరిగుట్ట కథ ఎట్లా చెప్పేవాళ్లు?",
          "Echo the guiding light (reuse S04); the woman's dream (reuse S07) on her line; finish on the identified present temple.", "Cut to S07 on 'భక్తురాలికి', then to today's temple.", "reuse + paid still",
          [still("The present black-stone Yadagirigutta temple on its hill exactly as in reference image 1, evening, attached style. " + DRESS, ["Y-HILL"], refs=["Y-HILL"])], ["comment card"],
          cut_to=[("S04", 0.0), ("S07", 2.6), ("S09", 6.8)]),
    ]
    return build("ep05-yadagirigutta", shots, board("ep05-yadagirigutta", refs))


# ------------------------------------------------------------------------------------------ EP06
def ep06():
    refs = [
        {"id": "C-BROTHERS", "subject": "Three brothers (blind, deaf, unable to speak); no caricature", "status": "verified", "basis": "C1 telling; literary illustration"},
        {"id": "C-WATER", "subject": "Well, channel, field (no identity constraint)", "status": "verified"},
        dict(EXT, id="C-EXTERIOR", subject="Kanipakam Varasiddhi Vinayaka temple exterior (sanctum photography prohibited; no invented murti)"),
    ]
    B, W = ["C-BROTHERS"], ["C-WATER"]
    BS = "CS-BROTHERS:still"
    shots = [
        sheet("CS-BROTHERS", "Character sheet: three brothers.",
              "Character sheet: three farming brothers of different ages in simple dhotis, each with a distinct face; front and three-quarter views, attached style. Dignified, no caricature.", B),
        S("S01", "కాణిపాకం వినాయకుడు బావిలో ఎందుకున్నాడు?", "Water in a stone well; a ripple. Title first frame.", "Ripple spreads (local).", "paid still + local",
          [still("Looking down into a stone-lined well with still dark water, a single ripple, attached style. No text. " + SACRED, W)], ["title card", "ripple"]),
        S("S02", "ఆ బావి నీళ్లతో ఒకప్పుడు ముగ్గురు అన్నదమ్ములు పొలం సాగు చేసుకునేవారని కథ.", "Match cut: the ripple becomes an irrigation channel to a field.",
          "Water runs along the channel (local).", "paid still + local",
          [still("An irrigation channel running from a village well to green paddy fields, morning, attached style. No people. No text.", W)], ["flowing water"]),
        S("S03", "చిత్తూరు జిల్లాలోని ఈ క్షేత్రం గురించి దేవస్థానం చెప్పే కథ ఇది.", "Identified exterior.", "Map card.", "paid still + local",
          [still("Exterior of the Kanipakam Varasiddhi Vinayaka temple exactly as in reference image 1, morning, devotees at the entrance, attached style. " + DRESS, ["C-EXTERIOR"], refs=["C-EXTERIOR"])], ["map card"]),
        S("S04", "ఒకరికి కంటిచూపు లేదు. ఒకరికి వినికిడి లేదు. ఇంకొకరికి మాట రాదు. ముగ్గురూ కలిసి బావి నుంచి నీళ్లు తోడి కాలువ ద్వారా పొలానికి మళ్లించేవాళ్లు.",
          "The three brothers lifting water together; push to each brother on his own line, then track the water to the field.", "Push to each brother; bucket rises; water pours into the channel.",
          "paid still + paid clip", [still("The three brothers (reference image 1) working a rope-and-bucket lift at the well, water pouring into the channel, attached style. " + DRESS, B + W, [BS], [BS]),
                                     clip("The brothers pull the rope together; the bucket rises and tips water into the channel. Hands whole; faces the same. Camera still.", B + W, "S04:still")]),
        S("S05", "ఒక రోజు ఎంత తోడినా నీళ్లు రాలేదు. బావి ఇంకిపోయింది.", "Same action, empty vessel.", "Bucket comes up dry.", "paid still + paid clip",
          [still("The same brothers at the same well as reference image 1; the bucket coming up empty, dry cracked mud below, attached style. " + DRESS, B + W, ["S04:still"], ["S04:still"]),
           clip("The bucket rises empty; the brothers look into it and then at each other. Camera still.", B + W, "S05:still")]),
        S("S06", "ఇంకా లోతు చేస్తే నీళ్లు పడతాయని ఒకరు బావిలోకి దిగారు. తవ్వుతుంటే పనిముట్టు గట్టి రాయికి తగిలింది.", "A brother lowers himself; the tool strikes stone.",
          "Climb down; strike (sound accent local).", "paid still + paid clip (protect the strike)",
          [still("Inside the dry well: one brother (reference image 1) digging the mud floor with a short iron tool, light from above, attached style. " + DRESS, B, [BS], [BS]),
           clip("The brother swings the tool down and it strikes a hard stone with a jolt; he stops. Hands whole. Camera still.", B, "S06:still")]),
        S("S07", "నీళ్లు ఊరతాయనుకున్న చోట, ఆ రాయి నుంచి రక్తం వచ్చిందట. బావి నీరు ఎర్రబడింది. ఆ క్షణంలో ఒకరికి చూపు, ఒకరికి వినికిడి, ఇంకొకరికి మాట వచ్చాయని స్థలపురాణం చెబుతుంది.",
          "Restrained red tint spreading through rising water (code), then back to the brothers.", "Tint spreads; faces lift.", "reuse + paid still",
          [still("The three brothers (reference image 1) at the well rim, one touching his eyes, one his ear, one his lips, in wonder, attached style. " + DRESS, B, [BS], [BS])], ["red tint in code"]),
        S("S08", "ఊరివాళ్లు అక్కడికి చేరారు. బావిలో కనిపించిన రూపం వినాయకుడిది. దాని అడుగు ఎక్కడుందో చూడాలని ఇంకాస్త తవ్వారు. ఎంత తవ్వినా అడుగు దొరకలేదట.",
          "Villagers work around the discovery, framed from above the rim; the waterline hides everything below.", "Digging; water stays.", "paid still + paid clip",
          [still("From above the rim: villagers gathered around the well, their faces in wonder, the water inside hiding everything below its surface, attached style. " + SACRED + " " + DRESS, B + W),
           clip("Villagers lean over the rim and dig at the edges; the water surface stays unbroken. Camera still.", W, "S08:still")]),
        S("S09", "వినాయకుడు అక్కడే స్వయంగా వెలిశాడని నమ్మి జనం కొబ్బరికాయలు సమర్పించారు. ఆ కొబ్బరినీళ్లు కాలువలో పారాయని కూడా కథలో చెబుతారు.",
          "Hands open a coconut; a narrow stream leads to the channel.", "Coconut cracks; stream joins channel.", "paid still + paid clip",
          [still("Close view: hands breaking a coconut on a stone at the channel's edge, attached style. " + DRESS, W),
           clip("The coconut cracks open and its water runs in a thin stream into the irrigation channel. Hands whole. Camera still.", W, "S09:still")]),
        S("S10", "మొదట ఆ కాలువలో వాళ్లు ఎదురుచూసింది పొలానికి నీళ్లు. కథ చివరికి అదే కాలువలో పారింది స్వామికి సమర్పించిన కొబ్బరినీళ్లు. మరి ఆ బావి? కాణిపాకంలో ఈనాటికీ నీళ్ల మధ్యే వరసిద్ధి వినాయకుడిని దర్శించుకుంటారు.",
          "Return to the opening water, now understood; then the identified exterior.", "Ripple; cut to exterior.", "reuse + local", [], ["ripple", "end card"], media_from="S01",
          cut_to=("S03", 6.0)),
    ]
    return build("ep06-kanipakam", shots, board("ep06-kanipakam", refs))


# ------------------------------------------------------------------------------------------ EP07
CHARIOTS = ("three tall temple chariots in a row: the first with red and yellow canopy cloth on sixteen wheels, "
            "the second red and green on fourteen wheels, the third red and black on twelve wheels")


def ep07():
    refs = [
        {"id": "P-CHARIOTS", "subject": "Nandighosa (Jagannath) 16 wheels red/yellow; Taladhwaja (Balabhadra) 14 red/green; Darpadalana (Subhadra) 12 red/black",
         "status": "verified", "basis": "Odisha Reference Annual; Orissa Review; Odisha Tourism Ratha Jatra"},
        {"id": "P-DEITIES", "subject": "Jagannath, Balabhadra, Subhadra", "status": "not depicted",
         "basis": "Your rule: crowd reactions, cymbals, bells and light; the deities are named in type only"},
        {"id": "P-PAHANDI", "subject": "Pahandi: the swaying procession to the chariots with cymbals and bells", "status": "verified",
         "basis": "Odisha Tourism (N1); shown through the crowd, never the carried images"},
        {"id": "P-GAJAPATI", "subject": "Chhera pahanra: the Gajapati sweeps each chariot with a golden broom", "status": "verified",
         "basis": "Odisha Tourism (N1). A living person: seen from behind, face never shown"},
        dict(EXT, id="P-GUNDICHA", subject="Gundicha temple exterior, Puri"),
        dict(EXT, id="P-BADADANDA", subject="Bada Danda (Grand Road), Puri, with the chariots"),
    ]
    C = ["P-CHARIOTS"]
    shots = [
        S("S01", (0, 1), "A huge painted chariot wheel turning on the sand-coloured road. Title 'పూరీ జగన్నాథుడు · ఒడిశా' on the first frame.",
          "Wheel turns; question lands.", "paid still + paid clip (the opening motion)",
          [still("Close view of one huge wooden temple-chariot wheel with painted spokes on a sand-coloured street, red and yellow canopy cloth just visible above, devotees' feet beside it, morning light, attached style. " + DRESS, C),
           clip("The great wheel turns forward slowly as the chariot begins to move; dust lifts from the road. Spokes stay whole and evenly spaced. Camera still.", C, "S01:still", max_s=5)],
          ["title card"]),
        S("S02", (2, 4), "Reveal: the three chariots in a row, each distinct; typeset names over each (జగన్నాథుడు, బలభద్రుడు, సుభద్ర).", "Names on each spoken name.", "paid still + local",
          [still("Wide view down a broad street in Puri: " + CHARIOTS + ", huge crowds small in the distance, no figures visible on the chariot platforms, morning, attached style. " + SACRED + " " + DRESS, C + ["P-BADADANDA"], refs=["P-BADADANDA"])],
          ["three name cards"]),
        S("S03", (5, 5), "Craftsmen carving a new wheel from fresh timber.", "Adze strikes; shavings fly (local).", "paid still + local",
          [still("Temple carpenters in white dhotis carving a new chariot wheel from fresh logs in a yard, wood shavings, sunlight, attached style. " + DRESS, C)], ["Stage camera"]),
        S("S04", (6, 8), "Pahandi through the crowd: servitors from behind carry something on ropes just above frame; faces turned up; cymbals and bells raised; flower petals in the air. 'పహండీ' typeset.",
          "Cymbals clash; the crowd sways with the rhythm.", "paid still + paid clip (the procession's rhythm)",
          [still("A packed temple lane in Puri: temple servitors seen from behind, bare shoulders straining, carrying something heavy on thick ropes that rise past the top of the frame, devotees with joined hands looking up, men raising brass cymbals and bells, flower petals in the air, bright sun, attached style. " + SACRED + " " + DRESS, ["P-PAHANDI"]),
           clip("The cymbals clash and the crowd sways forward together to the rhythm, petals drifting down. Nothing enters the top of the frame. Camera still.", ["P-PAHANDI"], "S04:still")],
          ["typeset పహండీ"]),
        S("S05", (9, 12), "On a chariot's wooden deck: a man in white seen from behind sweeps with a golden broom.", "The broom sweeps in long strokes.",
          "paid still + paid clip (the sweeping gesture)",
          [still("On the wooden platform of a temple chariot, a man in a white dhoti and royal turban seen from behind, sweeping the deck with a golden broom, attendants around him, his face not visible, attached style. " + SACRED + " " + DRESS, ["P-GAJAPATI"]),
           clip("He sweeps the deck with the golden broom in slow long strokes, moving away from camera. His face is never seen. Camera still.", ["P-GAJAPATI"], "S05:still")]),
        S("S06", (13, 14), "Ropes pass into devotees' hands; they lean and pull; a wheel starts to turn.", "The pull and the first turn of the wheel.",
          "paid still + paid clip (protect the pull)",
          [still("A thick rope stretched along the street, dozens of devotees' hands gripping it, bodies leaning to pull, a chariot wheel behind them, attached style. " + DRESS, C),
           clip("The devotees lean back together and pull the rope; behind them the wheel begins to turn. Hands whole. Camera still.", C, "S06:still")]),
        S("S07", (15, 15), "The three chariots roll down the broad road toward a distant temple; route map card.", "Map line draws to Gundicha.", "reuse + local map",
          [], ["route map card"], media_from="S02"),
        S("S08", (16, 17), "The identified Gundicha temple exterior; card 'జన్మస్థలం అని భావించే సంప్రదాయం'.", "Card builds.", "paid still + local",
          [still("Exterior of the Gundicha temple in Puri exactly as in reference image 1, garden walls, afternoon, devotees at the gate, attached style. " + DRESS, ["P-GUNDICHA"], refs=["P-GUNDICHA"])], ["attribution card"]),
        S("S09", (18, 20), "Evening: the three chariots facing back along the same road. 'బహుడా యాత్ర' typeset.", "Light turns to evening; title builds.", "paid still + local",
          [still("Evening light on a broad street in Puri: " + CHARIOTS + ", now facing back the way they came, crowds with lamps, attached style. " + SACRED + " " + DRESS, C + ["P-BADADANDA"], refs=["P-BADADANDA"])],
          ["typeset బహుడా యాత్ర", "TimeOfDay"]),
        S("S10", (21, 23), "Back to the hands on the rope, then the three chariots together.", "Close on hands; release to the wide.", "reuse + local", [], ["end card"],
          media_from="S06", cut_to=("S02", 3.0)),
    ]
    return build("ep07-puri", shots, board("ep07-puri", refs))


# ------------------------------------------------------------------------------------------ EP08
def ep08():
    refs = [
        {"id": "B-GOPANNA", "subject": "Kancherla Gopanna (Ramadasu), 17th-century tahsildar", "status": "verified",
         "basis": "Sahitya Akademi biography (N1); literary illustration, no portrait claimed"},
        {"id": "B-DAMMAKKA", "subject": "Dammakka, devotee in the Bhadrachalam tradition", "status": "verified", "basis": "Sahitya Akademi (N1); TTD Bhaktha Ramdas (N2)"},
        {"id": "B-ICONS", "subject": "Sita, Rama and Lakshmana icons; Rama at the repayment", "status": "not depicted",
         "basis": "Your rule: light and the witnesses' reactions; the repayment is attributed aloud as the devotees' story"},
        dict(EXT, id="B-TEMPLE", subject="Bhadrachalam Sita Ramachandra temple and its steps"),
        dict(EXT, id="G-FORT", subject="Golconda fort, Hyderabad"),
    ]
    GS, DS = "CS-GOPANNA:still", "CS-DAMMAKKA:still"
    G, D = ["B-GOPANNA"], ["B-DAMMAKKA"]
    shots = [
        sheet("CS-GOPANNA", "Character sheet: Kancherla Gopanna.",
              "Character sheet: a 17th-century Telugu revenue official in a white angavastram, turban and simple jewellery, carrying a ledger; front and three-quarter views, attached style.", G),
        sheet("CS-DAMMAKKA", "Character sheet: Dammakka.",
              "Character sheet: an older village woman devotee in a simple cotton sari, front and three-quarter views, attached style.", D),
        S("S01", (0, 0), "Two pictures in quick succession: a stone temple step, then a prison gate closing. Title on the first frame.",
          "Cut on 'జైలుకెందుకు'; the gate shuts.", "paid still + paid still + paid clip",
          [still("Close view of worn stone temple steps at Bhadrachalam exactly as in reference image 1, a lamp on one step, morning, attached style. No people. No text.", ["B-TEMPLE"], refs=["B-TEMPLE"])],
          ["title card"], cut_to=("S01G", "జైలుకెందుకు")),
        S("S01G", None, "The prison gate (cut inside S01).", "Gate closes.", "paid still + paid clip",
          [still("A heavy iron-studded wooden prison gate in a stone fort wall, half closed, dim light, attached style. No people. No text.", G),
           clip("The heavy gate swings shut and its bar drops into place. Camera still.", G, "S01G:still", max_s=3)]),
        S("S02", (1, 2), "The Bhadrachalam temple on its hill above the Godavari; then a treasury chest of coins and a ledger.", "Cut on 'ఇంకో వైపు'.", "paid still (extra still, approved list) + paid still",
          [still("The Bhadrachalam Sita Ramachandra temple on its hill above the Godavari river exactly as in reference image 1, gopuram and steps, morning, attached style. No people in the foreground. No text.", ["B-TEMPLE"], refs=["B-TEMPLE"])],
          ["split cut"], cut_to=("S02M", "ఇంకో వైపు")),
        S("S02M", None, "Treasury chest (cut inside S02).", "Lamp flickers.", "paid still",
          [still("A wooden treasury chest of silver coins and a cloth-bound ledger on a low table, lamplight, attached style. No people. No legible writing.", G)]),
        S("S03", (3, 5), "Gopanna at work: villagers bringing taxes; he enters them in a ledger. Name typeset 'కంచర్ల గోపన్న'.", "Name card; coins counted.", "paid still + local",
          [still("The revenue official (reference image 1) seated at a low desk under a veranda, villagers bringing grain and coins, he writes in a ledger, attached style. No legible writing. " + DRESS, G, [GS], [GS])], ["name card", "tahsildar card"]),
        S("S04", (6, 7), "Dammakka asleep; a soft light in her dream. Name typeset 'ధమ్మక్క'.", "Light rises (local Bloom); name card.", "paid still + local",
          [still("Night: the woman devotee (reference image 1) asleep on a mat in a hut, her face in soft golden light, attached style. " + SACRED + " " + DRESS, D, [DS], [DS])], ["Bloom", "name card 'ధమ్మక్క'"]),
        S("S05", (8, 8), "Dammakka and villagers clearing earth with their hands; light rises from the ground; then a small lamp-lit mandapam. The icons are never drawn.",
          "Hands clear earth; light rises.", "paid still + paid clip (protect the uncovering)",
          [still("Dammakka (reference image 1) and village women kneeling, clearing earth with their hands, warm light rising from the ground in front of them and lighting their amazed faces, attached style. " + SACRED + " " + DRESS, D, [DS], [DS]),
           clip("Their hands brush away the earth and the light grows brighter on their faces; they sit back with joined hands. Hands whole. Nothing in the ground becomes visible. Camera still.", D, "S05:still")],
          cut_to=("S06", "ఒక చిన్న మండపంలో")),
        S("S06", (9, 9), "Gopanna before the small mandapam, imagining a great temple.", "Light sweeps (local).", "paid still + local",
          [still("The official (reference image 1) standing before a small lamp-lit thatched mandapam on a hill by a river, looking up thoughtfully, attached style. " + SACRED + " " + DRESS, G, [GS], [GS])]),
        S("S07", (10, 11), "Villagers give what they can; stone steps are laid up the hill.", "Stones set one by one.", "paid still + paid clip (protect the building)",
          [still("Villagers placing coins and grain into a basket, then carrying stone blocks up a hillside to lay steps, the official watching, attached style. " + DRESS, G, [GS], [GS]),
           clip("Two villagers lower a stone block into place as a new step; others carry more up the hill. Hands whole. Camera still.", G, "S07:still")]),
        S("S08", (12, 14), "Gopanna's decision: tax money passes from the chest into the temple works.", "Bags pass from chest to workers.",
          "paid still + paid clip (protect the hand-over)",
          [still("The official (reference image 1) beside the treasury chest, handing a cloth bag of coins to a master builder, temple scaffolding behind, attached style. " + DRESS, G, [GS, "S02M:still"], [GS, "S02M:still"]),
           clip("He lifts a cloth bag of coins from the chest and places it in the builder's hands; the builder bows and turns toward the works. Hands whole. Camera still.", G, "S08:still")]),
        S("S09", (15, 16), "The finished temple (reuse the S02 temple on its hill); the empty treasury chest (reuse S02M).", "Cut to the empty chest on 'ఖజానాకు'.", "reuse + local", [], ["split cut"],
          media_from="S02", cut_to=("S02M", "ఖజానాకు")),
        S("S10", (17, 17), "Identified Golconda fort exterior; the gate shuts (reuse S01G clip).", "Gate.", "paid still + reuse",
          [still("Golconda fort on its granite hill exactly as in reference image 1, late afternoon, attached style. No people. No text.", ["G-FORT"], refs=["G-FORT"])],
          cut_to=("S01G", 1.8)),
        S("S11", (18, 20), "Attributed aloud as the devotees' story: officials in a lamplit treasury, faces lit by a light from the doorway, coins on the table. The visitor is never shown.",
          "Light floods in; faces turn.", "paid still + local Bloom",
          [still("Night in a lamplit treasury room: two officials turning in astonishment toward a doorway full of bright golden light, a heap of coins on the table before them, attached style. " + SACRED + " " + DRESS, G)],
          ["Bloom", "attribution card 'భక్తుల కథ ప్రకారం'"]),
        S("S12", (21, 23), "Gopanna singing with eyes closed by a small lamp; end card 'భద్రాచల రామదాసు'.", "Lamp flicker; end card.", "paid still + local",
          [still("The official (reference image 1), older now, seated on the floor singing with eyes closed beside a small oil lamp, attached style. " + SACRED + " " + DRESS, G, [GS], [GS])],
          ["end card"], note="Original sound bed only; no film song"),
    ]
    return build("ep08-bhadrachalam", shots, board("ep08-bhadrachalam", refs))


ALL = (ep02, ep03, ep04, ep05, ep06, ep07, ep08)

if __name__ == "__main__":
    for f in ALL:
        d = f()
        clips = [(s["id"], c["settings"]["duration"]) for s in d["shots"] for c in s["paid"] if c["asset_type"] == "clip"]
        stills = sum(1 for s in d["shots"] for c in s["paid"] if c["asset_type"] == "still")
        print(f"{d['episode']:20s} ~{d['est_total_s']:5.1f}s  stills {stills:2d}  clips {clips}")

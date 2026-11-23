# Komuravelli pilot — 16 s, three shots

Delivered 2026-11-23. `exports/komuravelli-pilot.mp4`
1080×1920, 30 fps, 480 frames, **16.000 s**, h264 + AAC, 15.5 MB.
Video 16.000 s / audio 16.000 s — exact. Full decode pass clean.

## Structure — cut to the narration, not to a stopwatch

Shot boundaries come from the RMS gap map of the narration, so every cut lands in a
pause the voice already leaves.

| Shot | Frames | Time | Source | Narration |
|---|---|---|---|---|
| **1 Festival** | 0–123 | 0.00–4.10 | **the existing Kling clip, reused** | ఆ బండారే — ఈ రోజు మీరు జాతరల చల్లే పసుపు |
| **2 Deity close** | 123–193 | 4.10–6.42 | new clip | ఈ కథ ఏ పుస్తకంల లేదు |
| **3 Oggu priest + patnam** | 193–480 | 6.42–16.00 | new clip | ఒగ్గు పూజారి పాడతడు — పాడుకుంటనే నేల మీద గీస్తడు |

**Shot 1 uses the clip's best section**, not its opening: the clip begins clear,
clouds over heavily in the middle, then clears. Taking the last 4.1 s means the
turmeric *clears to reveal* the crowd and shrine, and the shot ends clean into the
cut. The walking was kept, as instructed — at this width it reads as a procession.

## Sourcing

Every line is from the locked script (Part 2 §6), and both new shots depict
documented things:

- **The patnam is drawn by the Oggu priest while he sings** — research §8, *Sakshi*:
  *"ఒగ్గు పూజారులు కథను చెబుతూ పట్నం వేస్తారు."*
- **The priest's costume** — research §3: knee-tied pant, coloured head cloth,
  cowrie-shell chain, dolu at the hip. All present.
- ~~**The horse worked into the patnam** — the drawing depicts the story being sung.~~
  **Withdrawn 2026-11-23.** No source says the patnam is drawn figuratively, and the
  overhead photograph of the pedda patam (research §8, `design/references/`) shows it is
  not: it is a square of many thin nested straight borders with a small four-panel centre.
  Shot 3 is being re-made to the photograph.
- **The deity is seated in his rock recess**, as the murti is. Nothing invented.

## Assets

| Reused | New |
|---|---|
| Festival clip (already paid) | Deity close-up still + clip |
| `audio/01-part2.mp3` narration | Patnam still + clip |
| Remotion render pipeline | — |
| B as the style reference for both new stills | — |

## Costs

| Item | Credits |
|---|---|
| Festival clip (earlier, reused) | 7.5 |
| Deity close-up still (`nano_banana_2`, 2k) | ~2 |
| Patnam still (`nano_banana_2`, 2k) | ~2 |
| Deity clip (`kling3_0`, pro, 5 s) | 7.5 |
| Patnam clip (`kling3_0`, pro, 5 s) | 7.5 |
| **This session's total** | **19 credits** (balance 634.55 → 615.55) |
| Narration | **0** — reused existing ElevenLabs audio |
| Sound effects | **0** — synthesised in FFmpeg |

**Two video clips generated, as instructed. No automatic retries.**

## Sound

Restrained and synthesised rather than generated: a low band-limited crowd murmur, a
single soft temple bell struck on the cut to the deity at 4.10 s, and a low drone
fading in under the patnam section. Bed sits at 34% under the narration, through a
limiter. Costs nothing and is fully controllable.

## Defects

| Defect | Severity | Repaired? |
|---|---|---|
| Shot 1 opened on a heavy turmeric cloud | **Real** — obscured the frame | **Yes** — re-cut to the clip's later window. Free, ~4 min. |
| Crowd walks rather than gesturing (shot 1) | Accepted per instruction | No — reads as a procession at this width |
| Shot 3 clip is 5 s against a 9.6 s shot | Structural | Held final frame with a slow push on the tail only; live footage is never re-scaled |
| Remotion cannot decode video here | Worked around | Clips pre-extracted to JPEG sequences by our FFmpeg — Remotion's decoder is the broken macOS-15 compositor |

**No repair needed for:** deity identity, faces, camera drift, style consistency.
The two new shots came back clean on the first generation.

## Hands-on work

| | |
|---|---|
| Narration cut + gap mapping | ~5 min |
| Writing the two still prompts | ~10 min |
| Composition (`src/pilot/Pilot.tsx`) | ~15 min |
| Frame extraction + sound bed + mux | ~10 min |
| Re-cut of shot 1 after reviewing | ~5 min |
| Renders (machine time, unattended) | ~6 min |
| **Hands-on total** | **≈45 min** |

## What this says about daily production

The expensive parts were **not** repeatable-per-episode. Prompting, the composition
and the sound bed are now templates. A second episode at this standard looks like:
pick the narration window, write two or three still prompts, generate, extract,
re-caption, render. Realistically **under 30 minutes of hands-on work and about 20
credits** — provided the first generation lands, which it did twice out of two here.

The one thing that would break it is needing retries. Of the three clips made so
far, one needed its framing re-cut (free) and none needed re-generating.

---

# Correction — shot 3 rebuilt to the photograph (2026-11-23)

Karunakar supplied an overhead photograph of the Komuravelli **pedda patam**
(Shivaratri 2023), now saved as `design/references/patnam-pedda-patam-photo.jpg` and
described in research §8. Shot 3's patnam was wrong and has been remade. **Shots 1 and
2 are untouched.**

## What was wrong

The original shot 3 drew the patnam as a **circular floral mandala with a horse and a
dog** worked into it. None of that is supported. The real pedda patam is a **square of
many thin nested straight borders**, predominantly yellow and white, with a small
four-panel centre. The horse justification in this report has been struck out above.

## What was made

| | |
|---|---|
| Still v2 | `nano_banana_2`, photograph + priest crop as references. Geometry corrected, but the field came back deep red and only 768×1376 — I had passed `quality`, and the model's parameter is `resolution`, so it silently defaulted to 1k. **Rejected.** |
| Still v3 | `nano_banana_2`, `resolution: "2k"` → **1536×2752**. Photograph as primary reference, v2 as the composition/character reference. |
| Clip | `kling3_0`, pro, 5 s, silent, v3 as start frame. |

## Check against the photograph, before animating

| Requirement | Result |
|---|---|
| Predominantly turmeric yellow and white | **Pass** |
| Many closely spaced thin straight borders | **Pass** — 13 resolvable stripes edge-to-centre against the photograph's 11, measured on a scanline through both |
| Minimal red accents, following the photograph | **Miss** — no red at all. Under-shoot, not an invention |
| No invented dots, horses or central X | **Fail in the raw generation** — the centre came back carrying a cross, because my prompt said "quartered by two faint lines". **Repaired locally, free** |
| Simplified centre where the photograph cannot resolve detail | **Pass** |
| ≥ 1080×1920 source | **Pass** — 1536×2752 |
| Priest, composition, illustration style preserved | **Pass** |

The X was removed with a masked median filter over the centre panel, then a small blur
over the residual crossing point (`assets/pilot/shot3-patnam-v3-final.png`). No credits.
The raw generation is kept alongside it as `shot3-patnam-v3.png`.

## Clip check

Measured, not eyeballed — the contact sheet reads as a pull-back, and it is not one:

- **Camera fixed.** Template-matched two lamps between the first and last frame:
  displacement **(0, 0) px** on both. (A third anchor mis-matched because turmeric haze
  crosses it — the same haze that produced the false impression of drift.)
- **The drawing never changes.** No line, symbol or pattern is added or erased.
- **The priest stays kneeling** and never walks. Face, cowrie chains and head cloth hold
  across all five seconds; the mouth moves with the song.
- **Hand and fingers intact** throughout, powder still falling onto the line.

## Cost of the correction

| Item | Credits |
|---|---|
| Still v2 (1k, rejected) | 1.5 |
| Still v3 (2k) | 2.0 |
| Clip (`kling3_0` pro 5 s silent) | 7.5 |
| Centre-X repair | **0** — local FFmpeg |
| Narration, captions, sound bed | **0** — all reused |
| **Total** | **11 credits** (615.55 → 604.55) |

One wasted generation: still v2, from my own `quality`/`resolution` parameter error.

## Open deviation

**The patnam has no red at all.** The photograph carries red and maroon rows as a
minority; ours is yellow and white only. It under-shoots the brief in the safe
direction rather than inventing anything, so it went into the cut — but it is the one
point of the five that did not land, and a re-roll would also mean re-making the clip.


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
- **The horse worked into the patnam** — the drawing depicts the story being sung.
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

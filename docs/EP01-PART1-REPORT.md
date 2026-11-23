# Episode 1, Part 1 — "పసుపు ఎక్కడిది?" · build report

**Delivered 2026-11-23.** `exports/komuravelli-ep01-part1.mp4`
1080×1920, 30 fps, **2030 frames / 67.667 s** video against **67.663 s** audio.
h264 + AAC, 43.1 MB. Full decode pass clean.

**Publication is pending Karunakar's review. Nothing is uploaded.**

## What this is

The first *full* episode, not a pilot: the whole of Part 1 of the locked script,
every second of it on live generated footage, in the approved B illustration
direction. Part 2 ("ఇంటికి") is still unbuilt.

## Structure — 13 picture segments over 9 narration beats

Narration timings come from `src/episodes/01-part1-timing.json`, derived from the RMS
envelope of the real voice, so every cut lands in a pause.

| # | Time | Clip | Len | Beat |
|---|------|------|-----|------|
| 1 | 0.00–3.40 | **black** | 3.40 | the chant, before any picture |
| 2 | 3.40–5.08 | a2-throw | 1.68 | turmeric flung into low sun |
| 3 | 5.08–9.80 | a3-hill | 4.72 | the hill at dawn · location pin |
| 4 | 9.80–14.48 | a4-hand | 4.68 | a hand in the turmeric heap |
| 5 | 14.48–20.60 | a5-forest | 6.12 | before the temple: forest, sheep, herders |
| 6 | 20.60–26.80 | a6-mound | 6.20 | the termite mound, the god forming |
| 7 | 26.80–28.00 | a7 (0.0–1.2) | 1.20 | Medalamma |
| 8 | 28.00–33.70 | a7 (1.9–7.0, ×1.11) | 5.70 | the brothers, a wall |
| 9 | 33.70–40.38 | a8-serpent | 6.68 | five heads awake · **card: పసుపు కొమ్ములు** |
| 10 | 40.38–44.22 | a9-horse | 3.84 | the flying horse — the widest shot |
| 11 | 44.22–51.38 | a10-garden | 7.16 | the gardener, the guards who don't look |
| 12 | 51.38–59.24 | a11-theft | 7.86 | five eyes shut, the hand closing |
| 13 | 59.24–67.68 | a12-hishand | 8.44 | his hand, the turmeric · next-part pin |

**No frozen tails anywhere.** Every segment is shorter than its clip, so no frame is
ever held. This was the explicit instruction and it is met for all thirteen.

## Captions

Telugu primary with an English subtitle beneath, in 29 chunks weighted by word count
inside each narration beat. Plus the opening chant card, the spoken location pin
(సిద్దిపేట జిల్లా · 85 కి.మీ.), the one hinge card, and the next-part pin.

All type is set in Remotion. **No AI-generated Telugu anywhere in any image.**

## Defects

| Defect | Severity | Repaired? |
|---|---|---|
| **Medalamma walks out of frame** by t≈1.5 s of the a7 clip, leaving the brothers alone | **Real** — the shot is about her | **Yes, free.** Cut into two segments: she is on screen while she is named, and the wall of brothers now lands exactly on *"కానీ ఆమె అన్నలు ఒక షరతు పెట్టిండ్రు."* The second half is slowed 1.11× to fill the beat. The defect became an edit. |
| **a12 still charged but produced no output** — never appeared in the listing | Infrastructure | Re-run once. Recorded as a silent failure, not a quality rejection. |
| `B-folk-narrative.png` **rejected by upload moderation as "nsfw"** (bare-chested devotees) and unusable as a style reference | Workflow | Used the accepted B-derived assets (patnam shot, deity close-up) as style anchors instead. Noted in the config. |
| a6 mound: the god's form shifts somewhat as the mound brightens | Minor | Accepted — identity (blue skin, crown, moustache) holds throughout |

**No repair needed for:** style consistency across 11 new stills, character identity,
hands and fingers, camera drift, or Telugu rendering.

## Costs — this episode

| Item | Credits |
|---|---|
| 11 stills (`nano_banana_2`, 2k) | 21.5 |
| 1 still re-run after silent failure | 2.0 |
| 11 clips (`kling3_0`, pro, silent) — 67 s of video at 1.5/s | 105.0 |
| Narration | **0** — `audio/01-part1.mp3` already existed |
| Sound bed | **0** — synthesised in Python/FFmpeg |
| Captions, cards, pins | **0** — Remotion |
| **Episode total** | **128.5 credits** |

Session total including the patnam correction: **139.5** (614.05 → **474.55**).

## Hands-on work

| | |
|---|---|
| Shot planning against the timing map | ~10 min |
| Writing 11 still prompts + 11 motion prompts | ~35 min |
| Upload / confirm cycle (3 calls per asset) | ~20 min |
| Reviewing stills and clips, finding the a7 defect | ~15 min |
| Caption composition + the two cards | ~25 min |
| Assembly, sound bed, chunked compositing, mux | ~30 min |
| **Hands-on total** | **≈2 h 15 min** |

Generation wait time was roughly 25 minutes on top, unattended.

## What this says about one video per day

The earlier estimate of "about 20 credits per episode" was taken from a **16-second
pilot** and does not survive contact with a full 68-second episode. The real number is
**~128 credits and a bit over two hours**, and the honest reason is simple: a full
episode is four times the length and needs eleven generated shots rather than three.

At 474 credits that is **three more episodes**, not thirty. The levers, in order of
effect:

1. **`std` instead of `pro`** saves 1.25 vs 1.5 per second — about 17 credits an
   episode, at some quality cost. Worth a side-by-side test on one shot.
2. **Fewer, longer shots.** Cost is per second of video, not per clip, so this saves
   nothing on credits — but it saves real hands-on time (each asset costs three
   upload calls and a prompt).
3. **Reuse.** Characters and locations recur across the series. The hill, the deity,
   the priest and the turmeric hand are all now generated and reusable in Part 2.

## Disk

This machine had **836 MB free** when the build started. That is the real constraint,
not credits. Two consequences, both now permanent parts of the pipeline:

- The picture track is assembled **entirely in FFmpeg** in one pass, never as a frame
  sequence. A 2030-frame JPEG sequence would have needed well over a gigabyte.
- Remotion renders **only a transparent caption layer**, composited over the picture in
  **chunks of 400 frames**, each chunk's PNGs deleted as soon as it is composited. The
  first attempt at rendering all 2030 caption frames at once hit `ENOSPC` at frame 1896.

`public/frames/` was cleared to make room; it is regenerable from `exports/pilot-shot*.mp4`.

## Still open

- Karunakar has not heard the narration against the picture. The dialect pass is mine
  and the script asks for his ear before anything is final.
- Part 2 is unbuilt.
- No title, description, thumbnail or pinned comment yet.
- Publishing window: next jatara ≈ mid-January 2027.

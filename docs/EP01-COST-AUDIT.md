# Episode 1 (Komuravelli Mallanna): cost audit from receipts

Audited 23 Nov 2026 from the Higgsfield transaction history, matched job by job to the
Higgsfield generation history, and from there to files in this repo by exact byte size.
Nothing here is taken from the earlier session reports.

## Higgsfield: the totals

| | Credits |
|---|---|
| Balance before the project (22 Nov, 15:56 UTC) | 681.55 |
| Balance now | 356.05 |
| **Spent in that window** | **325.5** |
| Not this project: 4 x GPT Image 2.6 at 0.75 (23 Nov, 06:39 and 07:18 UTC), absent from this project's generation history and session logs | 3.0 |
| **Spent on Episode 1** | **322.5** |
| On assets in the final film | **242.5** (75%) |
| On experimentation and discarded assets | **80.0** (25%) |

Episode 1 runs 1:47.8, so the project cost about **179 credits per finished minute**, or
**135 per minute** counting only what reached the screen.

Every charge in the window is accounted for: 85 paid jobs, plus one failed still that was
charged and refunded. The earlier session reports took their totals from balance changes, so the
Part 1 session figure (139.5) silently included the 3.0 credits above.

## In the final film: 242.5

| Group | What | Credits |
|---|---|---|
| Opening/date-card festival clip | Style direction B still (GPT Image 2.0, 3.5) + Kling clip 5 s (7.5) | 11.0 |
| Pilot shots | Deity close-up still 2 + clip 7.5 (also the cover); patnam v3 still 2 + clip 7.5 | 19.0 |
| Part 1 shots used | 8 stills (a3, a4, a5, a7, a8, a9, a10, a12) 16 + 8 clips 78 | 94.0 |
| Full-episode shots n01 to n15 | 15 stills 30 + 15 clips, 59 s, 88.5 | 118.5 |

Of the 126 s of clips generated for these shots, **88 s of distinct footage is on screen**
(70%). The rest was trimmed at the heads and tails of shots; at 1.5 credits a second that is
about 57 credits of generated-but-unseen footage inside the "final" column.

## Experimentation and discarded: 80.0

| Item | Credits |
|---|---|
| First look (22 Nov): flat-vector style, 1 style frame, 1 character sheet, 1 Ganga attempt, 17 storyboard scenes, all GPT Image 2.0. Abandoned for style B | 25.0 |
| Style directions A and C (not chosen) | 7.0 |
| Animation feasibility tests (image edit, inpaint) | 4.0 |
| Patnam v1 still + clip (wrong geometry), patnam v2 still (1k by parameter error) | 11.0 |
| Part 1 shots cut from the film: a2 throw (6.5), a6 sleeping-snake mound (12.5), a11 theft (14.0) | 33.0 |
| a12 still, first attempt failed (charged 2, refunded 2) | 0.0 |

The biggest discard is the three cut Part 1 shots (33). The look development (25 + 7 + 4)
is a one-time cost that Episode 2 should not repeat.

## ElevenLabs (narration): not fully auditable

The ElevenLabs connector refuses usage queries ("requires additional permissions"), so there
is no account receipt. What the session logs do show, from each call's own `credit_costs`:

| Call (22 to 23 Nov) | Takes | ElevenLabs credits |
|---|---|---|
| Sample line | 2 | 152 |
| Part 1 narration | 2 | 1,572 |
| Part 2 narration | 2 | 1,790 |
| Part 2 narration, revised | 2 | 1,832 |
| Corrected closing line | 2 | 266 |
| **Total logged** | 10 | **5,612** |

Each call produced **two takes by default**, so half of every narration charge bought a take
nobody used. None of these ten takes is in the final film. The final narration is ElevenLabs
history item `AejKh2mDKl4dRqThycOm` (eleven_v4, 23 Nov 09:19 UTC), generated outside these
logged calls; its cost is not in any receipt available here. The logged calls charged 1
credit per character per take.

## Not charged

Captions, title and map cards, music, sound effects and the full edit were made locally
(Python, FFmpeg). Zero credits.

## Proposed controlled comparison (not generated)

**Question:** can a cheaper setting animate an approved still without losing our illustration
quality or character movement?

**Held constant**
- Start frame: the approved n04 Yellamma still, Higgsfield media `9e1f74f9-e970-4953-9362-479527ace307`
- Action: the approved n04 prompt, word for word (Mallanna stays with palms joined and head
  bowed; Yellamma raises her right arm, points into the distance and holds; lamps flicker,
  leaves stir; faces, crowns and clothes unchanged; five-fingered hands; camera almost still)
- Duration 5 s, 9:16, silent where the model allows it, one generation each, no retries

**Control:** the approved n04 clip (Kling 3.0 pro, 1076x1928, 24 fps, 7.5 credits). Already
paid for, so not regenerated.

| Setting | Why test it | Quoted cost |
|---|---|---|
| A. Kling 3.0 **std**, silent | Same model family as everything approved; isolates the quality tier | 6.25 |
| B. Seedance 2.0 Mini, 720p, silent | Budget model tagged for identity consistency | 5.00 |
| C. Grok Imagine Video 1.5 Lite, 720p | Lowest quoted cost with a start frame | 5.00 |
| **Total test cost** | | **16.25** |

Quoted and rejected, because they cost the same as our current setting or more: Kling 3.0
Turbo (7.5 at 720p, 10 at 1080p), Kling 4.0 Flash (7.5), MiniMax H3 Max (12.5), Grok
Video 1.5 (22.5), Grok Lite at 1080p (20).

**How each result is judged against the control**
1. Style: line weight, flat colour and paper grain match the still; no drift towards
   photoreal or 3D.
2. Identity: both faces, Mallanna's crown and Yellamma's crown stay the same in every frame.
3. Action: Yellamma lifts her **right** arm and holds the point; Mallanna does not move his
   joined hands.
4. Hands: five fingers throughout, no merging.
5. Motion: no morphing, flicker or sudden jumps.
6. Sharpness at 1080x1920 after upscaling (B and C render at 720p).

Deliverables: a side-by-side of all four at 0, 1.25, 2.5, 3.75 and 5 s; a four-up playback
clip; and a frame-drift measurement against the start frame.

**Decision rule:** adopt the cheapest setting that passes all six checks against the
control. If none passes, stay on Kling 3.0 pro.

**What a pass would save**, at the 59 s of new clips Episode 1 needed: about 74 credits
instead of 88.5 with std (17% less), or 59 with B or C (33% less).

Daily paid production is not switched on. The test runs only on approval.

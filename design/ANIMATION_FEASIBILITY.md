# Can direction B be animated? — feasibility test, 2026-11-23

**Asked:** before implementing, check whether the separate artwork and the
reconstruction of revealed areas can be produced.

**Answer: no, not with the image tools available through this connector.**
Measured twice, both failed.

## Test 1 — image-to-image edit (`nano_banana_2`, no mask)

Asked for one change: lower one named pilgrim's raised arm, reconstruct the cliff
behind it, keep everything else identical — deity, faces, clothing, other pilgrims,
all other turmeric.

| | |
|---|---|
| Pixels changed by >10% | **8.7% of the frame** |
| Where | **everywhere**, not localised |

The deity — explicitly excluded — came back with a **different crown, different
garlands, different arch and a shifted position**. The sun moved. The rock changed
shape. The turmeric spray was entirely redrawn.

**It does not edit. It regenerates something that resembles the original.**

## Test 2 — masked inpaint (`nano_banana_2`, `is_inpaint: true` + uploaded mask)

Built a 752×1344 mask, white over the arm region (x 300–450, y 530–705), uploaded
and confirmed it, and re-ran with `is_inpaint: true`.

| | |
|---|---|
| Pixels changed by >10% | 10.9% of the frame |
| **Of that change, inside the mask** | **8.9%** |
| Outside the mask | **91%** |

The mask was accepted by the API and then effectively ignored. The whole frame
regenerated again.

## What is therefore missing

1. **A true regional image editor.** The model advertises `is_inpaint` and a `mask`
   role; through this connector neither constrains the output.
2. Consequently: **no clean background plate**, and **no isolated arm**. Without
   both, an arm cannot be moved — anything behind it would be a hole.

## What can still be done at full fidelity to the benchmark

Using the original B untouched, pixel for pixel:

- **A restrained camera move** — the frame sliced into depth bands and moved at
  different rates. No regeneration, nothing redrawn.
- **A fresh turmeric plume** — new particles composited in code over the original.
  Genuinely new motion, and it is additive, so nothing underneath is disturbed.

Both keep every face, hand and garment exactly as painted, and the deity perfectly
still.

**Not possible: the devotee's arm gesture.**

## Options to get the gesture

| | Cost | Note |
|---|---|---|
| **A. Hand-edit one plate** | ~20 min of a person's time | Cut the arm out in an image editor and patch the cliff behind it. Karunakar has Affinity installed. One plate plus one arm cut-out unlocks the full gesture, and the result is exact. **Recommended for this test.** |
| **B. Image-to-video model** | credits | Seedance/Kling/Wan accept a start frame. But they animate the *whole* frame, which risks the faces and the deity — the two things explicitly to preserve. **Not recommended.** |
| **C. Commission artwork in layers** | the real production answer | Per the layer list in VISUAL_BRIEF.md. For daily output this is needed regardless; today's blocker is just an early symptom of not having it. |

## Bearing on daily production

This is the finding that matters beyond today: **a finished flat illustration cannot
be taken apart afterwards with the tools here.** Layer separation has to happen at
creation, not after. Any daily pipeline built on "generate a beautiful still, then
animate it" will hit this wall every single day.

---

# Image-to-video test — Kling v3.0, 2026-11-23

The image-editing route failed, but the image-to-video route works. Run directly
through the configured Higgsfield integration.

## Integration and settings

| | |
|---|---|
| Model | **Kling v3.0** (`kling3_0`) — supported, with `start_image` and 9:16 |
| Mode | `pro` |
| Duration / ratio | 5 s, 9:16 |
| Sound | `off` (silent, lower cost) |
| Start frame | **the original `B-folk-narrative.png`**, by job id — not the edit experiment |
| Output | 1076×1924, h264, 24 fps, 121 frames, 5.04 s, 14.5 MB |
| **Cost** | **7.5 credits** (quoted and charged). Balance after: 634.55 |
| **Repair time** | **0 — no repair applied; none was needed (see below)** |

Other models offering `start_image` on this integration: Seedance 2.0 / Mini
(Bytedance), Wan 2.7, Cinema Studio Video 3.0 / v2. Kling was available, so Kling
was used as instructed.

## Measured results

| Check | Result |
|---|---|
| Real motion present | **Yes** — mean inter-frame change 2.61/255; all 120 transitions move |
| Start-frame fidelity | **Excellent** — only **1.7%** of pixels differ >10% from the original at frame 0 |
| **Camera drift** | **None.** Template-matched the shrine between frame 0 and 120: displacement **(0, 0) px**. The camera is genuinely fixed. |
| **Deity changed?** | **No.** Crown, moustache, blue face and garlands hold across the clip. He does not move or redraw. |
| Illustration style | Preserved — still reads as the same painting |
| Evening lighting | Preserved |
| Turmeric | **Works well** — large golden plumes disperse and fall convincingly |
| Clothing | Moves subtly, as asked |
| Character identity | Largely holds — the woman in the blue sari is recognisably the same person throughout |

### The one real failure

**The crowd walks instead of gesturing.** The prompt asked for devotees completing
an offering with *small wrist and arm movements*; Kling interpreted it as the
procession advancing up the path. Over five seconds the blue-sari woman travels
from left-of-centre to right-of-centre, and a few figures enter and leave frame.

Secondary: the turmeric becomes very heavy around the middle of the clip and
obscures more of the frame than "gently falls" implies.

### Step 5 — shrine overlay repair: not performed, and not needed

The repair was conditional on the deity changing. It did not. Measured displacement
is zero and the features are intact, so overlaying the original shrine region would
add seams and risk for no benefit. Skipped deliberately.

## Assessment

This route clears the bar that the image-editing route could not: **it preserves the
benchmark artwork and animates it, without regenerating faces or the deity.** The
1.7% start-frame deviation and the zero camera displacement are the two numbers that
matter, and both are good.

The remaining problem is **prompt control, not capability**. The motion is real and
clean; it is simply the wrong motion. Worth trying on a re-run:

- Say explicitly **"the devotees stay in place, their feet do not move, nobody walks
  forward"** — the walking is the model filling an under-specified brief.
- Ask for **less** turmeric: "a thin veil of turmeric, mostly transparent."
- Consider a shorter duration (3 s) — less time for the crowd to drift.

**No further paid generations made.** One clip, 7.5 credits, as instructed.

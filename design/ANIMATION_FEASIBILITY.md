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

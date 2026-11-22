# Visual style — Temple Stories

Decided 2026-11-22. **Flat 2D illustration with parallax depth.** Not 3D.

## The look in one line

Warm, flat, folk-art illustration with thick confident shapes — lit like late afternoon
on the Deccan, animated with real camera movement.

## Palette

Locked. Every asset is generated and then colour-corrected toward these.

| Role | Hex | Where |
|---|---|---|
| Turmeric | `#E8A33D` | the thread of the whole series — bandari, patnam, the jatara |
| Deep amber | `#C2702A` | warm ground, temple interiors, earth |
| Burnt sienna | `#8E4A2E` | the hill, termite mound, shadow on warm things |
| Night indigo | `#2B2546` | the chase, the night sky, anything far from the god |
| Dusk violet | `#5A4A72` | mid-tone for dusk and cloud |
| Bone | `#F2E4CE` | rice-flour white, highlights, the patnam's lightest line |
| Blood red | `#A32E2E` | vermillion in the patnam, used sparingly, never for blood |
| Ink | `#1C1A22` | outlines and the black dog |

**Rule:** warmth means Mallanna is present or near. The further he is from home, the colder
the frame. The chase (P2 §3) is the coldest thing in the episode; the return (P2 §5) snaps
back to turmeric within one cut.

## Drawing

- **Thick, even outlines** in ink. No sketchy or variable-width linework.
- **Flat fills with one shade step.** No gradients inside shapes; gradients only in sky,
  light shafts, and water.
- **Geometric, simplified bodies.** Characters read as silhouettes first — if the
  silhouette doesn't say who it is, redraw it.
- **Faces: minimal.** Eyes and brow only. No rendered mouths on deities.
- **No texture or grain inside shapes.** Atmosphere comes from layered light, not noise.

## Characters

Generate one **reference sheet per character, once**, and reuse it across the whole series.
Consistency across episodes matters more than any single image being beautiful.

| Character | Must read as |
|---|---|
| **Mallanna** | Horse, dog, sword, turmeric are his identification — not decoration. Warm ochre skin, turmeric-smeared. Never a generic Shiva. |
| **Mallanna as gardener** | Same face, same build, **plain cloth, head lowered**. The whole con is that he is unremarkable. |
| **The black dog** | Pure ink silhouette. Low, fast, no detail. |
| **Medalamma** | Linga Balija. Composed, still, frame right in both parts. |
| **Ganga** | River-blue, flowing form. **Her right hand is the episode.** Draw her whole first, so the loss reads. |
| **Yellamma** | Brief, warm, receiving. |
| **The brothers** | Three, interchangeable, a wall of shoulders. Not villains — a condition. |
| **The guards** | **Silhouette only, never faces.** They are pursuit, not people. |
| **The Oggu priest** | Research §3 exactly: knee-tied pant, coloured head cloth, cowrie chain (*gavvala darshanam*), dolu at the hip. Not a generic folk musician. |

## Depth

Three layers per parallax shot — foreground, midground, sky — moved at different rates in
Remotion. Plain CSS transforms; **no Three.js needed.**

Parallax only where it earns itself: **P1 §3** (pull back to the hill), **P1 §6** (horse on
night sky), **P2 §3** (the chase), **P2 §7** (pull back to the jatara). Everything else is
flat and still, which makes the moving shots hit harder.

## Type

All text is **real text in Remotion**. Never generated inside an image — AI-rendered Telugu
produces letterforms that are nonsense to anyone who reads the script, and this audience
reads the script.

- **Subtitles**: large, uppercase-weight Telugu, top third, phrase by phrase.
- **Location pin**: same position and design every episode.
- **Cards**: gold rule on dark, centred. Used twice per part, maximum.

## Hard rules

1. **No AI-generated Telugu or Devanagari lettering, ever.**
2. **No brand marks, no modern signage, no photoreal faces.**
3. **No depiction of the deity's face in a way that could read as disrespectful** — keep
   deity faces frontal, calm, symmetrical.
4. **Iconography before beauty.** A gorgeous Mallanna without his dog is wrong.
5. One shade step per fill. If a shot needs more, it needs better light, not more shades.

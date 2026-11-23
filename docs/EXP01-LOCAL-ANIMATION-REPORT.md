# Experiment 01: local illustrated animation in Remotion

23 Nov 2026. Preview: `exports/experiments/exp01-local-animation-preview.mp4`
(1080x1920, 30 fps, 22.8 s, H.264 + AAC, -15.2 LUFS, peak -1.4 dBFS).

**Cost: 0 credits.** No paid calls. No new narration, images or video were generated.
Episode 1 is untouched: the publishing files hash identically before and after, and the
experiment has its own Remotion entry point (`src/experiments/exp01/index.ts`), so
`src/Root.tsx` and every Episode 1 source file are unchanged.

## What the four requirements got

| # | Requirement | Result | How |
|---|---|---|---|
| 1 | Location introduction | **Done** | a3 hill split into sky, hill and front-rock layers moving at different depths; clouds drift, four ink birds flap across, the temple lamp lights on "కొమురవెల్లి"; Telugu title builds word by word with the narration |
| 2 | Character performing a meaningful gesture | **Not done as continuous motion.** Needs artwork (below) | No approved character exists as separate parts. I did not fake it with a warped or cut-up painting |
| 3 | Prop interaction or clear change of pose | **Done, as a pose-to-pose cut** | n04 (palms joined) and n12 (offering the bandari) are two drawn paintings of the same shot. Registered by homography, colour-matched, then cut on "ఎల్లమ్మకిచ్చిండు" with anticipation glow, a warm bloom on the cut, a small settle, and turmeric dust passing from his hands into Yellamma's. Two drawn keys, no in-betweens |
| 4 | Passing time through the environment | **Done** | a10 garden: on "కొంతకాలం" the sky, sun, moon, stars, light colour and a moving sun band run through about two and a half days and nights. The gardener does not move; only the world changes |

Closing: deity close-up with flickering lamps and rising turmeric haze under
"కొమురవెల్లి మల్లన్నకు కోటి దండాలు!".

## Approved material used

- **Narration:** four lines cut from `audio/01-mallanna-full-paced.mp3` inside its pauses
  (5.16-10.21, 37.49-43.66, 69.72-72.14, 105.21-107.84). Same take as the published episode.
- **Music and effects:** Episode 1's own stems (`build/ep01-full/music.wav`, `sfx.wav`)
  cut at the same moments, using Episode 1's mix chain (bed ducked under the voice). One soft bell at the cut,
  synthesised with Episode 1's `bell()` function.
- **Paintings:** a3 hill, a10 garden, n04 Yellamma, n12 share, pilot deity close-up.
- **Captions:** the words as corrected for Episode 1's final export.

## The three reference repos (all MIT)

| Repo | What it is | Adopted? |
|---|---|---|
| lubomier/explainer-video-skill | Remotion explainer kit. Characters are separately drawn pose bodies plus swappable head layers, crossfade-and-settle pose changes, layered idle motion, irregular blinks | **Yes, the pattern.** `sine`, `easeInOut`, the blink schedule idea and `coverCam` adapted in `lib/motion.ts` with attribution; the settle in `KeyPoseCut` follows its `Character` |
| mromidev/claude-animated-shorts | three.js-in-Remotion style guide for bean-head, stick-limb cartoon cards in a 3D town. The template source isn't in the repo, and its reference frames are another channel's study material | **No.** Its characters are the capsule/box people you ruled out. Its rules on camera holds and timing match what we already do |
| artemnovitckii/claude-animation-skills | HTML/HyperFrames/Playwright templates: stick figures, maps, graphs, low-poly | **No.** Not Remotion, and its people are stick figures |

## Hands-on work and render time

- **Hands-on work:** my work was about 20 minutes of wall-clock time on 23 Nov. That covered reading the
  repos and licences, preparing the layers, writing the components, two rounds of frame checks and fixes,
  and the full render. Your hands-on time was zero.
- **Layer preparation:** about 6 s (`scripts/experiments/exp01_layers.py`).
- **Audio:** about 3 s (`scripts/experiments/exp01_audio.py`).
- **Full render:** **115 s** for 684 frames on this 2-vCPU workspace (about 6 fps). The first
  render took 123 s.
- **Mac rendering:** the composition uses no video files, only images and audio, so the macOS 12
  video-decode problem that blocked Remotion for Episode 1 should not apply. Not tested on the Mac yet.

Fixes made during the checks:
1. The hill's sky plate still held a faint copy of the hill's edge, which showed as a ghost outline when
   the clouds drifted. The inpaint mask now reaches 30 px past the edge.
2. The Episode 1 caption position (y 1290) covered the hands during the handover and the water in the
   garden. Captions in this experiment sit at y 360. `Caption` now takes a per-line position.
3. Deep night in the garden was too dark to read the gardener, so it is lifted slightly.

## Reusable components (`src/experiments/exp01/`)

| Component | Use in future episodes |
|---|---|
| `Stage`, `Layer`, `Art` | Art-space camera (1536x2752 paintings), parallax by depth, drift |
| `TimeOfDay`: `Sky`, `LightOver`, `gradeFilter`, `lookAt` | Any "days passed" or "night fell" beat on any still with a sky mask |
| `LampGlow` | Flickering diyas and torches over painted lamps |
| `Dust`, `Bloom` | Turmeric, kumkum, sparks, haze; a soft flash on a cut |
| `Birds` | Ink birds matching the painted ones |
| `KeyPoseCut` | Pose-to-pose change between registered key drawings |
| `Caption`, `LocationTitle`, `ClosingTitle`, `useTeluguFont` | Episode 1 typography in Remotion (Noto Sans Telugu, OFL) |
| `scripts/experiments/exp01_layers.py` | Sky masks (GrabCut), inpainted plates, depth layers, registration and colour match of two paintings |
| `scripts/experiments/exp01_audio.py` | Re-cut approved narration and stems with Episode 1's mix chain |

## Known limits of this preview

- The gardener, the water stream and the wall guards stay frozen during the time-lapse. That reads as
  "he stayed", but the water would look better moving.
- The pose change is a cut. Beyond the pose, n12 also differs slightly in leaves and sky. Colour-matching
  hides most of that at phone size, but not all of it.
- The sky behind the hill is inpainted and soft. Only a thin strip of it is ever exposed.

## Artwork needed for real character animation

Separate parts, all in the approved Episode 1 style. Each part is drawn past its joints so rotation never
opens a gap, all parts share one canvas and one light direction, and backgrounds are transparent.

**A. To finish requirement 2 here: Yellamma points the way** (narration 29.12-34.11, "దారి ఆమె చెప్పింది")
1. Clean plate: the n04 shrine and tree **with neither character**.
2. Yellamma seated, **without her right arm**.
3. Yellamma's right upper arm, right forearm, and right hand in three states: resting on the knee,
   open palm rising, and pointing.
4. Yellamma's head in two states, eyes open and eyes closed (for blinks), crown included.
5. Mallanna standing with palms joined, as one separate layer, so he can breathe and blink while she moves.

**B. A reusable Mallanna rig** (every episode)
1. Body and dhoti without arms, three-quarter view facing right (mirroring gives the left).
2. Head: neutral, eyes closed, mouth open (speech), and a slight turn; the kireetam on its own layer.
3. Upper arm, forearm and hand, left and right.
4. Hands as separate drawings: open palm, palms joined (one combined layer), cupped holding bandari,
   pointing, gripping a pot.
5. Hair locks as a back layer.

**C. Props on their own layers:** bandari (turmeric heap or bundle), clay water pot, offering bowl.

**D. Clean plates without characters** for every scene where someone moves: the shrine, the garden,
and the hilltop.

**A cheaper option than full rigs:** three or four key poses of the same character on the same
registered canvas over a clean plate. n04 and n12 show that two registered paintings already give a
believable pose change; three or four keys would give a readable gesture.

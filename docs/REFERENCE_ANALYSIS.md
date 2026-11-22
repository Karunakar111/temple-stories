# How the reference videos are built

Three references, three different techniques. Written 2026-11-22.

---

## 1. `divinestoriesstudio` — Chhappan Bhog (Hindi)

**Flat 2D illustration, animated with simple transforms.** Jointed paper-puppet
characters with visible elbow and shoulder pivots, thick outlines, tight amber-and-purple
palette. Labelled "AI content" by Instagram, so the stills are very likely generated and
then animated with cut-out rigs. Big karaoke subtitles at the top.

**What we took:** the complete-story structure (problem → action → consequence → a living
ritual), and the discipline of one idea per episode.

---

## 2. `katha.chepthanu` — Sabarimala / Ayyappa Deeksha (Telugu)

This is the one Karunakar pointed at hardest, so it's worth being precise about it.

### What the footage shows

- **Repeated identical low-poly human models.** The crowd climbing the steps is one
  character duplicated many times — same silhouette, same clothing, same gait.
- **Uniform, slightly stiff walk cycles**, all in step. That is stock motion-capture
  retargeted onto a rig, not hand-keyed animation.
- **Simple modelled environments**: a tiled-roof building, a pavilion, a gate, steps,
  ground planes, scattered trees. Basic materials, one sun light, real shadows.
- **A continuously moving camera.** `ffmpeg` scene detection found **zero hard cuts in
  84 seconds** — scenes change by moving, not by cutting.
- **A 3D infographic** built in the same space as the scene: the seven *dhatus* as
  spheres on connectors, with a progress arc that builds up, over a banana leaf and food.
- **Telugu headings and labels composited on top**, animating in.

### Almost certainly

**Blender** (Eevee, for render speed) + **Mixamo** rigged characters and stock walk
animations + simple hand-modelled sets + Telugu type added in post. That is the standard,
affordable pipeline for this look, and every signature above matches it.

### Why I am not recommending we copy it

Not because it's bad — it's effective. Because of what it would actually cost us:

| | |
|---|---|
| **Different toolchain** | Blender, not Remotion. I can write Blender Python but cannot see the viewport — iteration would be slow and half-blind. |
| **This machine** | macOS 12, Intel, ~2.7 GB free. Blender renders are slow and disk-hungry here, and we have already had to work around three macOS-15-only binaries. |
| **Character animation is the hard part** | It is also the part that most often looks cheap. Stiff walk cycles are forgiving in a crowd and brutal in close-up — and this story needs close-ups. |
| **It is a crowded look** | Low-poly 3D explainer is increasingly common. It would make us look like everyone else. |

### The observation that decided it

**That video's single most striking section is the dhatu diagram — and that is motion
graphics, not character animation.** The arcs building, the labels landing, the counter
climbing. Even the channel we are admiring does its best work with the technique we can
do natively, for free, frame-exact.

---

## 3. `ultra.skills` — "30 Claude Animations"

A catalogue of **code-generated** effects: Map Route, Headline, Teardown, Split Flap,
Git City, Stat Chart, Globe Arcs, Agent Swarm, Before/After, Swiss Grid, Blueprint Draw,
Paper Desk, Laptop Reveal, Notifications, Iso Flow.

**This is Remotion's home ground**, and it is the direction Karunakar chose.

### Mapped onto this series

| Effect | Where it goes | Status |
|---|---|---|
| **Blueprint Draw** | The patnam drawing itself — the episode's climax | **built** |
| **Map Route** | The open: Hyderabad → Siddipet → Komuravelli, distance counting | **built** |
| **Globe Arcs** | Mallanna / Mailara / Khandoba across three states | future episode |
| **Iso Flow** | The powder's journey: patnam → swept up → the fields | to do |
| **Stat Chart** | The jatara in numbers — 50 yards, 41 rows, lakhs of Sundays | to do |
| **Split Flap** | The brothers' condition landing: **పసుపు కొమ్ములు** | to do |
| **Notifications** | Viewers' village tellings stacking up | future episode |

---

## The five lessons we are taking regardless of technique

1. **Stop cutting.** Zero hard cuts in 84 seconds is the single biggest difference between
   the reference and our first pass. Move the camera instead of changing the shot.
2. **Something moves in every frame.** Not the frame zooming — something *in the world*.
3. **Use depth and vary the angle.** Overhead, low, tracking. Not one flat plane.
4. **Type is an actor.** Headings arrive with weight and leave; they do not cross-fade.
5. **Build infographics progressively.** Never show a finished diagram — draw it.

Real 3D is still available to us where it genuinely helps: `src/three/HillFlyover.tsx`
proves a procedural low-poly hill with a flying camera and walking pilgrims renders fine
here, with no models and no credits.

---

## What code-drawing actually turned out to be good at (2026-11-22)

Built all nine shots of Part 1 in code and rendered them. The result splits cleanly,
and the split is worth recording because it should drive every future episode.

### Works, and works well

- **Maps and routes.** The Hyderabad → Siddipet → Komuravelli open is the strongest
  thing in the part. Precise, legible, and it does the series' job of saying *where*.
- **Counters and diagrams.** 85 కి.మీ. climbing, 400 రోజులు climbing. Cheap and effective.
- **Landscape and architecture.** The dusk hill, the termite mound, the garden rows, the
  stone chamber. Flat geometric scenery is easy to author and reads immediately.
- **Type as an actor.** The chant, the condition card, the closing question.
- **The patnam.** Still the best thing made so far.
- **Silhouettes and motion.** The journey arc with the horse riding its head.

### Does not work

- **Organic creatures.** Three attempts at the five-headed serpent produced, in order:
  a squiggle, green balloons on stalks, and detached alien heads. 
- **Hands.** The hand holding the bandari renders as a blue blob at every scale tried.
- **Anything needing anatomy.** Human figures only became acceptable once they were
  rebuilt as outlined folk figures with flat fills — and "acceptable" is the ceiling.

### Why

Authoring organic form as SVG bezier coordinates, without seeing the canvas while
drawing, is slow and unreliable. Geometry, type and diagrams have no such problem
because they are specified by numbers that mean what they say.

### The direction this points to

**Draw the whole episode in the patnam's language.** Not "illustrations rendered in
code" — *powder-line folk motifs*, which is the one creature register that has actually
worked, and which is authentic to this temple besides. The serpent appears the way the
patnam draws a serpent. The horse the way the patnam draws a horse. Everything on flat
dark ground in turmeric, vermillion, green and rice-flour line.

That turns the limitation into the identity: a series drawn the way its own temple
draws, in the powder its own story is about. Nothing else in Telugu devotional content
looks like that, and it is the only register where the creatures have come out right.

# Production checklist

One episode, start to finish. Repeat it per episode; it is meant to get faster each time.
Tick the boxes in a copy of this file under `docs/episodes/NN-slug.md`.

Times are estimates for episode 1 and should fall sharply by episode 3.

---

## Stage 0 — Decide the episode (30 min)

- [ ] Pick the temple and write one sentence: **what is the one thing a viewer will
      remember?** If that sentence is dull, the episode will be dull. Change the angle,
      not the production value.
- [ ] Check the **festival calendar**. Publishing two to four weeks before a temple's
      jatara is worth more than any amount of polish.
- [ ] Decide the runtime and ratio before writing. Changing it later invalidates the
      storyboard, the asset list and the render.

## Stage 1 — Research (2–4 h for episode 1)

- [ ] Write `research/NN-slug.md`.
- [ ] Tag every claim **[A] solid / [B] reasonable / [C] one telling / [?] unverified**.
      Oral traditions have real variants; saying "one telling goes…" is accurate, not weak.
- [ ] Prefer: state government, Endowments Department, mainstream press, academic work.
- [ ] Reject SEO travel sites. They copy each other and cite nothing.
- [ ] List **open questions for Karunakar** — things only a local or a temple visit settles.
- [ ] List what to **leave out** of this episode and why.

**Gate:** nothing marked [?] may appear in the script as a statement of fact.

## Stage 2 — Script (2–3 h)

- [ ] `script/NN-slug.md`, with a **shot-numbered table**: shot no. | duration | narration |
      what is on screen | asset needed.
- [ ] Write for the **ear**, not the page. Read it aloud, out loud, to a wall.
- [ ] First 3 seconds must earn the next 10. No "Namaskaram, welcome to the channel."
- [ ] **No target runtime and no target shot count.** Write the complete story first;
      the length is whatever it turns out to be. Then **runtime ≈ word count ÷ 2.0**
      for Telugu narration — a rate for predicting, not a budget to write into. **Measured**
      on episode 1: the cloned voice reads Telugu at **1.99–2.00 words/second** across both
      parts. (Earlier guesses of ÷2.5 and ×1.5 were both wrong — ÷2.5 would have produced a
      32-word script for 80 seconds, and ×1.5 over-ran by a third.) Silence over a good
      image is not dead air; it is the image doing its job.
- [ ] **Never trust the estimate.** Generate the narration, then run
      `python3 scripts/timing.py <part>` — it measures the real waveform, finds the pauses
      the voice actually leaves, and writes the shot boundaries to
      `src/episodes/*-timing.json`. The composition reads that file. Estimates are for
      writing; the waveform is for building.
- [ ] Name the communities and people correctly. Check every proper noun twice.
- [ ] Mark any line that depends on a **[?]** claim and resolve it or cut it.

**Gate:** Karunakar reads the script aloud and approves it. Do not generate a single asset
before this. Assets made against an unapproved script are the most expensive mistake here.

## Stage 3 — Voice (30–45 min)

- [ ] Generate narration with **ElevenLabs** (connected).
- [ ] Voice options already in the account:
      - **`JWn8KOVJuYWznmih5YXL` — "Karunakar Kadari"** — his own cloned voice. For a
        personal channel this is almost certainly the right answer: it is his, it is
        unrepeatable, and it cannot be mistaken for a generic AI channel.
      - `CZdRaSQ51p0onta4eec8` — Akshay, Indian narrator, calm
      - `LolxzR74HCt7Un4IvoxI` — Maneesh, South Indian narrator
      - `lyecpOZOEhQPx3iPunu7` — Meenakshi, Indian female storyteller
- [ ] **Telugu is the open risk.** Confirm the chosen voice + model actually produce clean
      Telugu before building a whole episode on it. Test a hard line first — one with
      temple vocabulary and a long compound word.
- [ ] Fix mispronounced proper nouns with a **pronunciation dictionary** rather than by
      respelling words phonetically in the script.
- [ ] Save to `audio/NN-narration.wav`. Keep the script text next to it.
- [ ] **The audio is now the clock.** Measure it and set the composition duration from it.
      Never animate to a guessed length and hope the voice fits.

**Gate:** Karunakar listens to the full narration and approves it.

## Stage 4 — Look (1–2 h, episode 1 only, then reuse)

- [ ] `design/style-guide.md`: palette, type, light, and the rule for how 3D and 2D sit
      together.
- [ ] Make **one** style frame and get it approved before making twenty.
- [ ] Decide the hard line: **what will this channel never show?** Faces of deities done
      badly, wrong iconography, and AI-mangled Telugu lettering are the three ways this
      kind of video loses an audience that cares.

## Stage 5 — Assets (1–3 h)

- [ ] List every asset the shot table needs. Generate nothing that is not on the list.
- [ ] **Higgsfield** (connected, **681.55 credits**, Plus) for images and video shots.
- [ ] Use `estimate_image_cost` / `estimate_video_cost` **before** generating, and record
      the spend in the episode log. Video costs far more than stills — prefer a still that
      a Remotion camera move brings to life.
- [ ] Keep a **reference element / character** for anything appearing in more than one
      shot, so it stays consistent between generations.
- [ ] **No AI-generated Telugu or Devanagari text inside images, ever.** It comes out as
      nonsense letterforms to anyone who reads the script. All text goes on in Remotion,
      as real text.
- [ ] Save approved assets to `assets/{characters,environments,props}/` and
      `git add -f` them, since the folder is gitignored by default.

**Gate:** Karunakar approves the asset set. Check the iconography: Mallanna's horse, dog,
sword and turmeric are not decoration, they are identification.

## Stage 6 — Build in Remotion (3–6 h for episode 1)

- [ ] One component per scene in `src/scenes/`, assembled in `src/episodes/NN-slug.tsx`.
- [ ] Register the composition in `src/Root.tsx`; set `durationInFrames` from the real
      narration length.
- [ ] **Every animated value is a function of `useCurrentFrame()`.** No `Date.now()`, no
      `Math.random()` without a seed, no `useFrame` deltas for anything that must land on a
      beat. Renders must be reproducible frame for frame.
- [ ] Drive 3D cameras from the frame inside the canvas (see `src/setup-check/SpinTest.tsx`);
      animating R3F's `camera` prop does not reliably update it.
- [ ] Keep text in HTML layers over the canvas, not as 3D text, unless it must live in the
      scene — it stays crisp and it stays editable.
- [ ] Check it in Studio at real speed: `npm run studio`.

**Gate:** `npx tsc --noEmit` is clean and the Studio preview plays through with no console
errors.

## Stage 7 — Render (15–40 min)

> On this machine `npx remotion render out.mp4` **cannot** produce a video — Remotion's
> bundled FFmpeg needs macOS 15. Use the project script, which renders frames and muxes
> them with the project's own FFmpeg. See `docs/SETUP_NOTES.md`.

- [ ] Preview pass first — half size, fast: `npm run preview -- EpisodeNN`
- [ ] Watch it **once, all the way through, with sound**, before the full render.
- [ ] Full render with narration:
      `npm run render -- EpisodeNN --audio audio/NN-narration.wav`
- [ ] Confirm the printed ffprobe summary: duration matches the narration, 1080×1920 (or
      the chosen frame), 30 fps, h264, yuv420p.
- [ ] Disk check before rendering — frames are large and this machine runs close to full.
      `df -h /` should show several GB free.

**Gate:** the exported file plays start to finish with audio in sync.

## Stage 8 — Review before publishing

- [ ] Watch on a **phone**, muted, with captions. That is how most people will see it.
- [ ] Every proper noun spelled right, on screen and in the description.
- [ ] Nothing marked **[?]** stated as fact.
- [ ] Communities named accurately and respectfully.
- [ ] Sources listed in the video description.
- [ ] Say that the visuals are illustrations, not documentary footage of the temple.

**Gate: Karunakar watches the whole thing and says yes. Nothing publishes without this.**

## Stage 9 — Publish (30 min)

- [ ] Title, description with sources, tags, thumbnail, chapters → `publishing/NN-slug.md`.
- [ ] Telugu **and** English in the title/description if the episode is Telugu — it doubles
      the surface YouTube can match against.
- [ ] Publish timed to the festival window identified in Stage 0.
- [ ] **Karunakar uploads.** I prepare the package; the account action is his.

## Stage 10 — Log it

- [ ] Fill in `docs/episodes/NN-slug.md`: hours per stage, Higgsfield credits spent,
      ElevenLabs characters used, what took longest, what to change next time.
- [ ] Commit everything.

---

## Running notes

**Where the time actually goes.** Expect episode 1 to be dominated by Stages 4–6, which are
one-time costs for the channel's look and the first scene components. Episode 2 should reuse
both.

**Credit discipline.** Higgsfield credits are finite and not being topped up. Every
generation should be traceable to a numbered shot. Regenerating because a shot was never
scripted properly is the main way this budget disappears.

**ElevenLabs usage reporting** is currently unavailable through the connector — it asked for
additional permissions on 2026-11-22. Reconnect it in connector settings to track character
spend from here; until then, read it in the ElevenLabs dashboard.

**The permanent rule.** Devotees will watch this. Getting a detail wrong about someone's
family god is not a rendering bug; it is a reason they never come back. Accuracy and respect
outrank polish at every single gate above.

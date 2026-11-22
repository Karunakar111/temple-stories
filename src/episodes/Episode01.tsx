import React from "react";
import {
  AbsoluteFill,
  Audio,
  Sequence,
  getRemotionEnvironment,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import part1 from "./01-part1-timing.json";
import part2 from "./01-part2-timing.json";
import { PALETTE } from "../design/palette";
import { LocationPin } from "../components/LocationPin";
import { Subtitle } from "../components/Subtitle";
import { ShotPlaceholder } from "../components/ShotPlaceholder";

export type Timing = typeof part1;

/**
 * Episode 1 — Komuravelli Mallanna, the Bandari story.
 *
 * Shot boundaries come from `scripts/timing.py`, which measures the real narration
 * waveform and snaps each cut into a pause the voice actually leaves. Nothing here
 * is timed by hand, and nothing is timed by guess — change the audio, re-run the
 * script, and the composition re-times itself.
 */

/** English subtitle per shot, in order. Telugu lives in the timing JSON. */
const SUBTITLES: Record<1 | 2, string[]> = {
  1: [
    "Komuravelli Mallanna — a crore of salutations!",
    "Eighty-five kilometres from Hyderabad. Siddipet district — the hill at Komuravelli. This turmeric you throw here — do you know where it came from?",
    "By the story the Oggu priests sing here — before the temple, this hill was forest. Sheep, and their herders. The god who came down for them was Mallanna. Not stone — termite-mound earth.",
    "Mallanna loved Medalamma — a daughter of the Linga Balijas. But her brothers set one condition.",
    "Bring the bandari. The turmeric horns. They were kept far away — with a five-headed serpent on guard.",
    "The gods gave him a flying horse. Mallanna set out.",
    "He didn't arrive as a god. He joined as a gardener. Changed his name. Days passed. Months passed. Until every one of them trusted him — he waited.",
    "One day — in the moment the serpent's eyes closed — the bandari was in his hand. For the first time. But someone saw.",
    "He had the turmeric. Now he had to get it home. That's the next story. Till then — in your village, what do they say the brothers asked for?",
  ],
  2: [
    "Komuravelli Mallanna — a crore of salutations! … The bandari was in Mallanna's hand. But someone had seen.",
    "He didn't flee as a god. He became a black dog. The guards came after him.",
    "Over hills. Across rivers. They didn't let go.",
    "At last Ganga stepped in. She put her arm across to shield him. The blow took her right hand. Even so — she didn't let go of Mallanna.",
    "On the flying horse he came back — to this very hill. He gave Yellamma a share of the bandari. With the rest — he married Medalamma.",
    "That bandari — is the turmeric you throw at the jatara. This story is in no book. The Oggu priest sings it. And as he sings — he draws it on the ground, in that same turmeric. That is the patnam. What you took for a rangoli — is this story.",
    "When the puja ends, people carry that powder home to their fields. For the harvest. Sankranti to Ugadi — every Sunday. Every fistful you throw — is Ganga's hand. And Mallanna's patience.",
    "How is this told in your village? Did Ganga lose her hand — or is there another telling? Tell us below, with your village's name.",
  ],
};

/** A hair of cross-fade so cuts land soft on a phone rather than snapping. */
const FADE = 6;

const Shot: React.FC<{
  index: number;
  durationInFrames: number;
  telugu: string;
  english: string;
  part: 1 | 2;
}> = ({ index, durationInFrames, telugu, english, part }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(
    frame,
    [0, FADE, durationInFrames - FADE, durationInFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={{ opacity }}>
      <ShotPlaceholder index={index} part={part} telugu={telugu} />
      <Subtitle text={english} />
    </AbsoluteFill>
  );
};

export const Episode01: React.FC<{ part: 1 | 2 }> = ({ part }) => {
  const timing = (part === 1 ? part1 : part2) as Timing;
  const { durationInFrames: total } = useVideoConfig();
  const frame = useCurrentFrame();

  // The pin rides the first 16 seconds, then leaves. Location is spoken as well,
  // so this is for the sound-off viewer.
  const pinOpacity = interpolate(
    frame,
    [12, 30, 16 * 30 - 30, 16 * 30],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.ink }}>
      {/* Studio-only. Remotion inspects <Audio> with its *bundled* ffprobe, which is
          the macOS-15-only binary that cannot run here (see docs/SETUP_NOTES.md) — so
          during a render it crashes the frame pass. The narration is muxed in afterwards
          by scripts/render.mjs using the project's own FFmpeg. Sync is safe either way:
          the shot boundaries and the mux are both derived from the same measured
          waveform. */}
      {getRemotionEnvironment().isRendering ? null : (
        <Audio src={staticFile(`audio/01-part${part}.mp3`)} />
      )}

      {timing.shots.map((shot, i) => (
        <Sequence
          key={shot.n}
          from={shot.startFrame}
          durationInFrames={Math.max(1, shot.durationInFrames)}
          name={`Shot ${shot.n}`}
        >
          <Shot
            index={shot.n}
            part={part}
            durationInFrames={Math.max(1, shot.durationInFrames)}
            telugu={shot.telugu}
            english={SUBTITLES[part][i] ?? ""}
          />
        </Sequence>
      ))}

      <AbsoluteFill style={{ opacity: pinOpacity }}>
        <LocationPin part={part} />
      </AbsoluteFill>

      {/* Guard: if the audio ever outruns the shot list, the screen stays black
          rather than showing a frozen last frame. */}
      {frame > total ? <AbsoluteFill style={{ backgroundColor: PALETTE.ink }} /> : null}
    </AbsoluteFill>
  );
};

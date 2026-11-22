import React from "react";
import {
  AbsoluteFill, Audio, Sequence, interpolate, staticFile,
  useCurrentFrame, getRemotionEnvironment,
} from "remotion";
import timing from "./01-part1-timing.json";
import { PALETTE } from "../design/palette";
import { Subtitle } from "../components/Subtitle";
import { LocationPin } from "../components/LocationPin";
import { ChantOpen } from "../components/ChantOpen";
import { MapRoute } from "../components/MapRoute";
import { S03Origin } from "../shots/S03Origin";
import { S04Condition } from "../shots/S04Condition";
import { S05Serpent } from "../shots/S05Serpent";
import { S06Journey } from "../shots/S06Journey";
import { S07TheWait } from "../shots/S07TheWait";
import { S08Theft } from "../shots/S08Theft";
import { S09Ask } from "../shots/S09Ask";

/**
 * Episode 1, Part 1 — fully code-drawn.
 *
 * Two rules from the reference analysis are enforced here rather than left to each
 * shot: nothing cuts hard (every shot dissolves through its neighbour), and every
 * shot carries its own camera move so no frame is ever static.
 */

const SUBTITLES = [
  "Komuravelli Mallanna — a crore of salutations!",
  "Eighty-five kilometres from Hyderabad. Siddipet district — the hill at Komuravelli. This turmeric you throw here — do you know where it came from?",
  "By the story the Oggu priests sing here — before the temple, this hill was forest. Sheep, and their herders. The god who came down for them was Mallanna. Not stone — termite-mound earth.",
  "Mallanna loved Medalamma — a daughter of the Linga Balijas. But her brothers set one condition.",
  "Bring the bandari. The turmeric horns. They were kept far away — with a five-headed serpent on guard.",
  "The gods gave him a flying horse. Mallanna set out.",
  "He didn't arrive as a god. He joined as a gardener. Changed his name. Days passed. Months passed. Until every one of them trusted him — he waited.",
  "One day — in the moment the serpent's eyes closed — the bandari was in his hand. For the first time. But someone saw.",
  "He had the turmeric. Now he had to get it home. That's the next story. Till then — in your village, what do they say the brothers asked for?",
];

/** Long dissolves, so the episode flows instead of cutting. */
const BLEND = 14;

const SHOT_COMPONENTS = [
  ChantOpen, MapRoute, S03Origin, S04Condition,
  S05Serpent, S06Journey, S07TheWait, S08Theft, S09Ask,
] as const;

const Shot: React.FC<{ i: number; dur: number }> = ({ i, dur }) => {
  const frame = useCurrentFrame();
  const Comp = SHOT_COMPONENTS[i];
  // First shot opens hard from black; the rest cross-dissolve.
  const opacity = interpolate(
    frame,
    [0, i === 0 ? 1 : BLEND, dur - BLEND, dur],
    [i === 0 ? 1 : 0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
  return (
    <AbsoluteFill style={{ opacity }}>
      <Comp durationInFrames={dur} />
      {i === 0 ? null : <Subtitle text={SUBTITLES[i]} />}
    </AbsoluteFill>
  );
};

export const Ep01Part1: React.FC = () => {
  const frame = useCurrentFrame();
  const pin = interpolate(frame, [170, 196, 420, 446], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.ink }}>
      {getRemotionEnvironment().isRendering ? null : (
        <Audio src={staticFile("audio/01-part1.mp3")} />
      )}

      {timing.shots.map((s, i) => (
        <Sequence
          key={s.n}
          // start each shot early by the blend so they overlap rather than butt
          from={Math.max(0, s.startFrame - (i === 0 ? 0 : BLEND))}
          durationInFrames={s.durationInFrames + (i === 0 ? 0 : BLEND)}
          name={`${s.n}. ${s.telugu.slice(0, 26)}`}
        >
          <Shot i={i} dur={s.durationInFrames + (i === 0 ? 0 : BLEND)} />
        </Sequence>
      ))}

      <AbsoluteFill style={{ opacity: pin }}>
        <LocationPin part={1} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

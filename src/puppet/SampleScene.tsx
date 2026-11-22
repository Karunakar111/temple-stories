import React from "react";
import {
  AbsoluteFill, Audio, Easing, getRemotionEnvironment, interpolate, spring,
  staticFile, useCurrentFrame, useVideoConfig,
} from "remotion";
import { SceneTemplate, TurmericBurst, TurmericHaze } from "./SceneTemplate";
import { Mallanna } from "./Mallanna";
import { Bandari } from "./props";
import { poseAt, breathe } from "./rig";
import { HOLDING, LIFT, SCATTER, BLESS } from "./poses";
import { PALETTE } from "../design/palette";

/**
 * Eight-second sample.
 *
 * Narration-driven: the action is the line. From the locked script, Part 2 §6 —
 *
 *   "ఆ బండారే — ఈ రోజు మీరు జాతరల చల్లే పసుపు."
 *   "That bandari — is the turmeric you throw at the jatara today."
 *
 * So he holds it, lifts it, and throws it, and the throw changes the world: the
 * air fills with turmeric and dusk turns to gold. Character action and
 * environmental change on the same beat, because the beat is about both.
 *
 * No claim here is new. The bandari, the hill and the jatara are all from the
 * sourced script; nothing is asserted that research does not carry.
 */

/**
 * Sync map.
 *
 * Measured off the real narration (audio/sample-line.mp3, cut from part 2 at
 * 33.80s). The RMS envelope puts the phrase boundaries here, and the gesture is
 * hung on them rather than on a guess:
 *
 *   0.10s  f3    "ఆ బండారే"            he presents what is in his hand
 *   0.82s  f25   em-dash pause          the arm begins to rise
 *   1.04s  f31   "ఈ రోజు మీరు జాతరల…"   rising
 *   2.20s  f66   "చల్లే"  (to throw)    THE RELEASE — fingers open on the word
 *   2.80s  f84   "…పసుపు." sentence end turmeric at full spread
 *   4.10s  f123  "ఈ కథ ఏ పుస్తకంల లేదు" he settles toward blessing
 *   5.84s  f175  "ఒగ్గు పూజారి పాడతడు"  held, warm
 */
const F_PRESENT = 3;
const F_RISE = 25;
const F_THROW = 66;
const F_SPREAD = 84;
const F_SETTLE = 123;

export const SampleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Pose timeline — this is the whole performance.
  const pose = poseAt(
    [
      { frame: 0, pose: HOLDING },
      { frame: F_PRESENT, pose: HOLDING },
      { frame: F_RISE, pose: HOLDING },
      { frame: F_THROW - 4, pose: LIFT, ease: Easing.out(Easing.cubic) },
      // the release lands on "చల్లే" — fast out of the lift, fingers opening
      { frame: F_THROW + 6, pose: SCATTER, ease: Easing.in(Easing.quad) },
      { frame: F_SPREAD, pose: SCATTER },
      { frame: F_SETTLE + 22, pose: BLESS, ease: Easing.inOut(Easing.cubic) },
      { frame: durationInFrames, pose: BLESS },
    ],
    frame,
  );
  const idle = breathe(frame, frame < F_THROW ? 1 : 0.4);
  const full = { ...pose, chest: (pose.chest ?? 0) + idle.chest, rise: (pose.rise ?? 0) + idle.rise };

  // Environmental change: dusk → gold, triggered by the throw.
  const warm = interpolate(frame, [F_THROW + 2, F_THROW + 86], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const haze = interpolate(frame, [F_THROW + 4, F_THROW + 56, durationInFrames], [0, 0.95, 0.7], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const lamp = 0.9 + Math.sin(frame / 7) * 0.12;

  // Camera: a slow push that tightens a touch on the throw.
  const zoom = interpolate(frame, [0, F_THROW, durationInFrames], [1.08, 1.14, 1.2], {
    extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad),
  });
  const shake = frame > F_THROW && frame < F_THROW + 14
    ? Math.sin((frame - F_THROW) * 2.2) * (14 - (frame - F_THROW)) * 0.6
    : 0;

  // Caption, straight from the locked script.
  const cap = spring({ frame: frame - F_PRESENT, fps, config: { damping: 16, mass: 0.6 } });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1C1A22" }}>
      {getRemotionEnvironment().isRendering ? null : (
        <Audio src={staticFile("audio/sample-line.mp3")} />
      )}
      <SceneTemplate
        warm={warm}
        lamp={lamp}
        zoom={zoom}
        panX={shake}
        panY={interpolate(frame, [0, durationInFrames], [-150, -192])}
        depth={interpolate(frame, [0, durationInFrames], [0, 1])}
        air={
          <>
            <TurmericBurst originX={706} originY={806} startAt={F_THROW + 2} count={190} />
            <TurmericHaze amount={haze} />
          </>
        }
      >
        <g transform="translate(430 1612)">
          <Mallanna pose={full} scale={2.18} rightHand={<Bandari scale={1.1} />} />
        </g>
      </SceneTemplate>

      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 120 }}>
        <div
          style={{
            opacity: cap,
            transform: `translateY(${interpolate(cap, [0, 1], [26, 0])}px)`,
            textAlign: "center",
            padding: "0 70px",
          }}
        >
          <div style={{ color: PALETTE.bone, fontSize: 56, fontWeight: 800, lineHeight: 1.26, textShadow: "0 5px 26px rgba(0,0,0,0.9)" }}>
            ఆ బండారే — ఈ రోజు మీరు
          </div>
          <div style={{ color: PALETTE.turmeric, fontSize: 76, fontWeight: 900, marginTop: 8, letterSpacing: -1, textShadow: "0 5px 26px rgba(0,0,0,0.9)" }}>
            జాతరల చల్లే పసుపు
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

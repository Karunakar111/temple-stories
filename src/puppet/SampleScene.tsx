import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
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

const SCATTER_AT = 112;

export const SampleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  // Pose timeline — this is the whole performance.
  const pose = poseAt(
    [
      { frame: 0, pose: HOLDING },
      { frame: 56, pose: HOLDING },
      { frame: 100, pose: LIFT, ease: Easing.out(Easing.cubic) },
      { frame: SCATTER_AT, pose: SCATTER, ease: Easing.in(Easing.quad) },
      { frame: 150, pose: SCATTER },
      { frame: 196, pose: BLESS, ease: Easing.inOut(Easing.cubic) },
      { frame: durationInFrames, pose: BLESS },
    ],
    frame,
  );
  const idle = breathe(frame, frame < 90 ? 1 : 0.35);
  const full = { ...pose, chest: (pose.chest ?? 0) + idle.chest, rise: (pose.rise ?? 0) + idle.rise };

  // Environmental change: dusk → gold, triggered by the throw.
  const warm = interpolate(frame, [SCATTER_AT, SCATTER_AT + 80], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const haze = interpolate(frame, [SCATTER_AT + 8, SCATTER_AT + 60, durationInFrames], [0, 0.95, 0.7], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  const lamp = 0.9 + Math.sin(frame / 7) * 0.12;

  // Camera: a slow push that tightens a touch on the throw.
  const zoom = interpolate(frame, [0, SCATTER_AT, durationInFrames], [1.0, 1.07, 1.13], {
    extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad),
  });
  const shake = frame > SCATTER_AT && frame < SCATTER_AT + 16
    ? Math.sin((frame - SCATTER_AT) * 2.1) * (16 - (frame - SCATTER_AT)) * 0.5
    : 0;

  // Caption, straight from the locked script.
  const cap = spring({ frame: frame - 18, fps, config: { damping: 16, mass: 0.6 } });

  return (
    <AbsoluteFill style={{ backgroundColor: "#1C1A22" }}>
      <SceneTemplate
        warm={warm}
        lamp={lamp}
        zoom={zoom}
        panX={shake}
        panY={interpolate(frame, [0, durationInFrames], [10, -26])}
        depth={interpolate(frame, [0, durationInFrames], [0, 1])}
        air={
          <>
            <TurmericBurst originX={700} originY={840} startAt={SCATTER_AT} count={170} />
            <TurmericHaze amount={haze} />
          </>
        }
      >
        <g transform="translate(430 1540)">
          <Mallanna pose={full} scale={2.0} rightHand={frame < SCATTER_AT ? <Bandari scale={1.15} /> : null} />
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

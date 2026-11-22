import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * The chant, over black. The first thing in every episode.
 *
 * Turmeric rises out of the dark, the cry lands in two beats the way it is
 * actually shouted — the name, then the salutation — and the dust keeps moving
 * after the words have gone.
 */

const Dust: React.FC<{ n?: number }> = ({ n = 90 }) => {
  const frame = useCurrentFrame();
  return (
    <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
      {Array.from({ length: n }).map((_, i) => {
        const seed = Math.sin(i * 73.1) * 0.5 + 0.5;
        const seed2 = Math.sin(i * 19.7) * 0.5 + 0.5;
        const speed = 0.55 + seed * 1.5;
        // rises, loops, drifts sideways on its own phase
        const y = 1960 - ((frame * speed + seed2 * 1900) % 2100);
        const x = 120 + seed * 840 + Math.sin(frame / 38 + i) * 26;
        const r = 1.6 + seed2 * 4.4;
        // interpolate needs an ascending input range, so this reads bottom-of-screen
        // last: invisible off the top, bright through the middle, invisible below.
        const fade = interpolate(y, [-40, 300, 1500, 1960], [0, 0.7, 0.85, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        const start = interpolate(frame, [0, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return <circle key={i} cx={x} cy={y} r={r} fill={PALETTE.turmeric} opacity={fade * 0.5 * start} />;
      })}
    </svg>
  );
};

export const ChantOpen: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const line1 = spring({ frame: frame - 14, fps, config: { damping: 14, mass: 0.6 } });
  const line2 = spring({ frame: frame - 44, fps, config: { damping: 11, mass: 0.5 } });

  // A single flare of light when the salutation lands.
  const flare = interpolate(frame, [44, 52, 86], [0, 0.5, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.quad),
  });
  const out = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", opacity: out }}>
      <Dust />
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 46%, rgba(232,163,61,${flare}) 0%, rgba(0,0,0,0) 62%)` }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ textAlign: "center" }}>
          <div
            style={{
              color: PALETTE.bone,
              fontSize: 76,
              fontWeight: 800,
              letterSpacing: -1,
              opacity: line1,
              transform: `translateY(${interpolate(line1, [0, 1], [26, 0])}px)`,
              textShadow: "0 6px 34px rgba(0,0,0,0.95)",
            }}
          >
            కొమురవెల్లి మల్లన్నకు
          </div>
          <div
            style={{
              color: PALETTE.turmeric,
              fontSize: 118,
              fontWeight: 900,
              marginTop: 18,
              letterSpacing: -2,
              opacity: line2,
              transform: `scale(${interpolate(line2, [0, 1], [0.82, 1])})`,
              textShadow: `0 0 54px rgba(232,163,61,0.55), 0 8px 40px rgba(0,0,0,0.95)`,
            }}
          >
            కోటి దండాలు
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

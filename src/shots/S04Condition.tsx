import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { PALETTE } from "../design/palette";
import { useCamera } from "../draw/primitives";
import { Figure, FigureSari } from "../draw/folk";

/**
 * Shot 4 — he loves Medalamma; her brothers set one condition.
 *
 * Three brothers slide in and physically close the frame, then the condition lands
 * as a split-flap card. The blocking is the point: the shape of the shot says "no"
 * before the words do.
 */

const Flap: React.FC<{ text: string; at: number }> = ({ text, at }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - at, fps, config: { damping: 15, mass: 0.6 } });
  // the card snaps down like a board flipping
  const rot = interpolate(s, [0, 1], [-78, 0]);
  if (frame < at) return null;
  return (
    <div
      style={{
        perspective: 900,
        opacity: Math.min(1, s * 1.8),
      }}
    >
      <div
        style={{
          transform: `rotateX(${rot}deg)`,
          transformOrigin: "top center",
          background: "#0d0a10",
          border: `4px solid ${PALETTE.murtiGold}`,
          borderRadius: 14,
          padding: "30px 54px",
          boxShadow: "0 24px 70px rgba(0,0,0,0.75)",
        }}
      >
        <div style={{ color: PALETTE.turmeric, fontSize: 90, fontWeight: 900, letterSpacing: -2 }}>
          {text}
        </div>
      </div>
    </div>
  );
};

export const S04Condition: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const cam = useCamera(durationInFrames, { zoom: [1.04, 1.14] });

  // Medalamma settles first, then the wall arrives.
  const her = interpolate(frame, [6, 40], [120, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.sienna, overflow: "hidden" }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ transform: cam.transform }}>
        <defs>
          <linearGradient id="g4" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={PALETTE.ink} />
            <stop offset="60%" stopColor={PALETTE.sienna} />
            <stop offset="100%" stopColor={PALETTE.amber} />
          </linearGradient>
        </defs>
        <rect width="1080" height="1920" fill="url(#g4)" />

        {/* her, on the right, composed and still */}
        <g transform={`translate(${her} 0)`}>
          <FigureSari x={830} y={1080} scale={1.25} cloth={PALETTE.murtiMagenta} />
        </g>

        {/* three brothers, arriving one after another, closing the frame */}
        {[0, 1, 2].map((i) => {
          const at = 34 + i * 16;
          const x = interpolate(frame, [at, at + 26], [-420, 180 + i * 200], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
          });
          return (
            <Figure
              key={i}
              x={x}
              y={1080}
              scale={1.28}
              body={PALETTE.sienna}
              cloth={[PALETTE.amber, PALETTE.murtiGreen, PALETTE.amber][i]}
              arms="folded"
              moustache
            />
          );
        })}
      </svg>

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", paddingBottom: 480 }}>
        <Flap text="పసుపు కొమ్ములు" at={112} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";
import { Dust } from "../draw/primitives";
import { HandWithBandari } from "../draw/folk";

/**
 * Shot 9 — he has it, he still has to get home, and we ask the audience the one
 * thing the sources genuinely disagree about.
 *
 * Ends on the question, alone, so it is the last thing read and the easiest thing
 * to answer.
 */
export const S09Ask: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const hand = spring({ frame: frame - 8, fps, config: { damping: 17, mass: 0.8 } });
  const q = spring({ frame: frame - 120, fps, config: { damping: 15, mass: 0.6 } });
  const next = interpolate(frame, [durationInFrames - 70, durationInFrames - 50], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.ink }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%">
        <defs>
          <radialGradient id="warm9">
            <stop offset="0%" stopColor={PALETTE.turmeric} stopOpacity={0.5} />
            <stop offset="100%" stopColor={PALETTE.turmeric} stopOpacity={0} />
          </radialGradient>
        </defs>
        <circle cx={540} cy={760} r={520} fill="url(#warm9)" opacity={hand * 0.8} />

        {/* his hand, holding it — framed like the viewer's hand in shot 1 */}
        <g transform={`scale(${interpolate(hand, [0, 1], [0.86, 1])})`}
           transform-origin="540 800" opacity={hand}>
          <HandWithBandari x={540} y={820} scale={1.5} />
        </g>
        <Dust n={40} color={PALETTE.turmeric} speed={0.6} opacity={0.3} />
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 300 }}>
        <div style={{ textAlign: "center", opacity: q, transform: `translateY(${interpolate(q, [0, 1], [28, 0])}px)` }}>
          <div style={{ color: PALETTE.bone, fontSize: 52, fontWeight: 700, opacity: 0.85 }}>
            మీ ఊళ్ల ఆ అన్నలు
          </div>
          <div style={{ color: PALETTE.turmeric, fontSize: 86, fontWeight: 900, marginTop: 10, letterSpacing: -2 }}>
            ఏం అడిగిండ్రు?
          </div>
          <div style={{
            marginTop: 34, opacity: next,
            color: PALETTE.bone, fontSize: 34, fontWeight: 600,
            border: `2px solid ${PALETTE.violet}`, borderRadius: 40, padding: "14px 34px", display: "inline-block",
          }}>
            రెండవ భాగం — రేపు
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

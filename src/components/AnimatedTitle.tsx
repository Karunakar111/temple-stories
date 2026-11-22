import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * Telugu heading that arrives with weight, the way the reference channel's titles do.
 * Springs in, holds, then leaves — never just a cross-fade.
 */
export const AnimatedTitle: React.FC<{
  text: string;
  sub?: string;
  startAt?: number;
  holdFor?: number;
}> = ({ text, sub, startAt = 0, holdFor = 70 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const local = frame - startAt;

  const enter = spring({ frame: local, fps, config: { damping: 16, mass: 0.7 } });
  const exit = interpolate(local, [holdFor, holdFor + 14], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(enter, exit);
  const y = interpolate(enter, [0, 1], [34, 0]);
  const scale = interpolate(enter, [0, 1], [0.9, 1]);

  if (local < 0) return null;

  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 130 }}>
      <div style={{ opacity, transform: `translateY(${y}px) scale(${scale})`, textAlign: "center" }}>
        <div
          style={{
            color: PALETTE.bone,
            fontSize: 86,
            fontWeight: 900,
            letterSpacing: -1,
            textShadow: "0 6px 30px rgba(0,0,0,0.95)",
          }}
        >
          {text}
        </div>
        {sub ? (
          <div
            style={{
              color: PALETTE.turmeric,
              fontSize: 38,
              fontWeight: 700,
              marginTop: 16,
              textShadow: "0 4px 18px rgba(0,0,0,0.95)",
            }}
          >
            {sub}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

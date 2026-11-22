import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, SHOT_REGISTER } from "../design/palette";

const BG = {
  dusk: [PALETTE.sienna, PALETTE.amber],
  cold: [PALETTE.indigo, PALETTE.violet],
  bright: [PALETTE.murtiBlue, PALETTE.murtiMagenta],
} as const;

/**
 * Stand-in until the illustrated asset for this shot exists. It carries a slow
 * Ken Burns drift so the *timing* can be judged at real speed — if the cut feels
 * wrong against the narration, that is visible now rather than after ten images
 * have been generated.
 */
export const ShotPlaceholder: React.FC<{
  index: number;
  part: 1 | 2;
  telugu: string;
}> = ({ index, part, telugu }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const register = SHOT_REGISTER[part][index - 1] ?? "dusk";
  const [a, b] = BG[register];
  const scale = interpolate(frame, [0, durationInFrames], [1, 1.07]);

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(160deg, ${a} 0%, ${b} 100%)`,
        transform: `scale(${scale})`,
        justifyContent: "center",
        alignItems: "center",
        padding: 90,
      }}
    >
      <div style={{ textAlign: "center" }}>
        <div style={{ color: PALETTE.bone, opacity: 0.45, fontSize: 30, letterSpacing: 6 }}>
          SHOT {index} · {register.toUpperCase()}
        </div>
        <div
          style={{
            color: PALETTE.bone,
            fontSize: 40,
            lineHeight: 1.45,
            marginTop: 34,
            opacity: 0.9,
          }}
        >
          {telugu}
        </div>
      </div>
    </AbsoluteFill>
  );
};

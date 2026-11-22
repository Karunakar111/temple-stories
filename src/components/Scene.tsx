import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";
import type { Move } from "../episodes/shots";

/** Slow, restrained camera moves on still illustrations. */
const transformFor = (move: Move, t: number, overscan: number): string => {
  const z = overscan;
  switch (move) {
    case "push":
      return `scale(${z * interpolate(t, [0, 1], [1.0, 1.1])})`;
    case "pull":
      return `scale(${z * interpolate(t, [0, 1], [1.12, 1.0])})`;
    case "driftLeft":
      return `scale(${z}) translateX(${interpolate(t, [0, 1], [4, -4])}%)`;
    case "driftRight":
      return `scale(${z}) translateX(${interpolate(t, [0, 1], [-4, 4])}%)`;
    case "riseUp":
      return `scale(${z}) translateY(${interpolate(t, [0, 1], [3, -3])}%)`;
    case "still":
    default:
      return `scale(${z * 1.02})`;
  }
};

export const Scene: React.FC<{
  image: string | null;
  move: Move;
  overscan?: number;
  /** Optional mid-shot cut to a second image. */
  second?: { at: number; image: string; blackout?: number };
  fallback?: React.ReactNode;
}> = ({ image, move, overscan = 1.06, second, fallback }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const t = durationInFrames <= 1 ? 0 : frame / durationInFrames;

  if (!image) return <>{fallback ?? null}</>;

  const cutAt = second ? Math.round(second.at * durationInFrames) : Infinity;
  const blackout = second?.blackout ?? 0;
  const past = frame >= cutAt;
  const src = past && second ? second.image : image;

  // One beat of black at the cut — the script asks for a full second of darkness
  // when the blow lands, and silence on screen is how that beat reads.
  const inBlackout = blackout > 0 && frame >= cutAt - blackout / 2 && frame < cutAt + blackout / 2;

  // Each image runs its move across its own half of the shot so neither feels frozen.
  const localT = second
    ? past
      ? (frame - cutAt) / Math.max(1, durationInFrames - cutAt)
      : frame / Math.max(1, cutAt)
    : t;

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.ink, overflow: "hidden" }}>
      <Img
        src={staticFile(`scenes/${src}`)}
        style={{
          width: "100%",
          height: "100%",
          objectFit: "cover",
          transform: transformFor(move, localT, overscan),
          transformOrigin: "center center",
        }}
      />
      {inBlackout ? <AbsoluteFill style={{ backgroundColor: PALETTE.ink }} /> : null}
    </AbsoluteFill>
  );
};

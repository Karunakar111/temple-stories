import React from "react";
import { interpolate } from "remotion";

/**
 * Cut-out puppet rig.
 *
 * The reference's characters are jointed puppets whose pivots are drawn as gold
 * discs — the construction is the ornament. That is the whole trick, and it is why
 * this style is both achievable and fast: a character is parts and angles, not
 * anatomy. Every part here is a function of numbers.
 *
 * Reusable across every episode. A new character is a new parts list; a new shot
 * is a new pose.
 */

export const INK = "#2A1B14";
export const GOLD = "#E8B33D";
export const GOLD_DK = "#B8832A";

/** The gold disc that marks a pivot. */
export const JointDisc: React.FC<{ r?: number; gold?: string }> = ({ r = 11, gold = GOLD }) => (
  <>
    <circle r={r} fill={gold} stroke={INK} strokeWidth={3} />
    <circle r={r * 0.34} fill={GOLD_DK} />
  </>
);

/**
 * One limb segment: a tapered capsule drawn from the pivot downward, with the
 * joint disc on top and children parented to its far end.
 */
export const Segment: React.FC<{
  length: number;
  top: number;
  bottom: number;
  fill: string;
  rotate?: number;
  joint?: boolean;
  jointR?: number;
  children?: React.ReactNode;
  /** Decorative band (armlet, anklet) at a fraction along the segment. */
  band?: { at: number; w?: number; color?: string };
}> = ({ length, top, bottom, fill, rotate = 0, joint = true, jointR, children, band }) => (
  <g transform={`rotate(${rotate})`}>
    <path
      d={`M ${-top} 0
          A ${top} ${top} 0 0 1 ${top} 0
          L ${bottom} ${length}
          A ${bottom} ${bottom} 0 0 1 ${-bottom} ${length} Z`}
      fill={fill}
      stroke={INK}
      strokeWidth={3.5}
      strokeLinejoin="round"
    />
    {band ? (
      <rect
        x={-(top + (bottom - top) * band.at) - 1.5}
        y={length * band.at - (band.w ?? 9) / 2}
        width={(top + (bottom - top) * band.at) * 2 + 3}
        height={band.w ?? 9}
        rx={3}
        fill={band.color ?? GOLD}
        stroke={INK}
        strokeWidth={2.5}
      />
    ) : null}
    {joint ? <JointDisc r={jointR ?? top * 0.9} /> : null}
    <g transform={`translate(0 ${length})`}>{children}</g>
  </g>
);

/** Blend between two pose objects. Keys missing from either side fall back to 0. */
export type Pose = Record<string, number>;

export const blendPose = (a: Pose, b: Pose, t: number): Pose => {
  const out: Pose = {};
  for (const k of new Set([...Object.keys(a), ...Object.keys(b)])) {
    out[k] = interpolate(t, [0, 1], [a[k] ?? 0, b[k] ?? 0]);
  }
  return out;
};

/** Walk through a timeline of keyed poses and return the pose for this frame. */
export const poseAt = (
  keys: { frame: number; pose: Pose; ease?: (t: number) => number }[],
  frame: number,
): Pose => {
  if (keys.length === 0) return {};
  if (frame <= keys[0].frame) return keys[0].pose;
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (frame >= a.frame && frame <= b.frame) {
      const raw = (frame - a.frame) / Math.max(1, b.frame - a.frame);
      const t = b.ease ? b.ease(raw) : raw;
      return blendPose(a.pose, b.pose, t);
    }
  }
  return keys[keys.length - 1].pose;
};

/** Gentle idle — never let a puppet sit perfectly still. */
export const breathe = (frame: number, amount = 1) => ({
  chest: Math.sin(frame / 26) * 0.9 * amount,
  rise: Math.sin(frame / 26) * 2.2 * amount,
  headTilt: Math.sin(frame / 34 + 1) * 0.7 * amount,
});

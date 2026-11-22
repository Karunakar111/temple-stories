import React from "react";
import { interpolate, useCurrentFrame, Easing } from "remotion";
import { PALETTE } from "../design/palette";

/** Shared drawing primitives. Every shot in the series is built from these. */

export const EASE = Easing.bezier(0.33, 0, 0.2, 1);

/** Deterministic pseudo-random — same output every render, no seeds to thread. */
export const rnd = (i: number, salt = 1) => {
  const x = Math.sin(i * 127.1 * salt + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** A path that draws itself between two frames. The series' core gesture. */
export const Stroke: React.FC<{
  d: string; color: string; width: number; from: number; to: number;
  len?: number; cap?: "round" | "butt" | "square"; opacity?: number; fill?: string;
}> = ({ d, color, width, from, to, len = 1600, cap = "round", opacity = 1, fill = "none" }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE,
  });
  if (p <= 0) return null;
  return (
    <path d={d} fill={fill} stroke={color} strokeWidth={width} strokeLinecap={cap}
      strokeLinejoin="round" strokeDasharray={len} strokeDashoffset={len * (1 - p)}
      opacity={opacity} />
  );
};

/** Shape that scales in from nothing, with a little overshoot. */
export const Pop: React.FC<{
  at: number; children: React.ReactNode; x?: number; y?: number; dur?: number;
}> = ({ at, children, x = 0, y = 0, dur = 12 }) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [at, at + dur], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.back(1.7)),
  });
  if (t <= 0) return null;
  return <g transform={`translate(${x} ${y}) scale(${t})`} opacity={Math.min(1, t * 1.6)}>{children}</g>;
};

/** Powder grains settling along a radius — the series' texture. */
export const Grains: React.FC<{
  cx: number; cy: number; r: number; from: number; n?: number; color: string; spread?: number;
}> = ({ cx, cy, r, from, n = 26, color, spread = 26 }) => {
  const frame = useCurrentFrame();
  return (
    <g>
      {Array.from({ length: n }).map((_, i) => {
        const a = (i / n) * Math.PI * 2 + i * 0.7;
        const rr = r + (rnd(i, 3) - 0.5) * spread;
        const appear = from + (i % 10) * 2;
        const o = interpolate(frame, [appear, appear + 10], [0, 0.72], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        return <circle key={i} cx={cx + Math.cos(a) * rr} cy={cy + Math.sin(a) * rr}
          r={1.6 + (i % 3) * 0.8} fill={color} opacity={o} />;
      })}
    </g>
  );
};

/** Drifting dust. Used in the open and wherever a frame would otherwise sit still. */
export const Dust: React.FC<{ n?: number; color?: string; speed?: number; opacity?: number }> = ({
  n = 70, color = PALETTE.turmeric, speed = 1, opacity = 0.45,
}) => {
  const frame = useCurrentFrame();
  return (
    <g>
      {Array.from({ length: n }).map((_, i) => {
        const s = rnd(i), s2 = rnd(i, 7);
        const y = 1980 - ((frame * (0.5 + s * 1.4) * speed + s2 * 1900) % 2120);
        const x = 90 + s * 900 + Math.sin(frame / 38 + i) * 24;
        const fade = interpolate(y, [-40, 300, 1500, 1980], [0, 0.7, 0.9, 0], {
          extrapolateLeft: "clamp", extrapolateRight: "clamp",
        });
        return <circle key={i} cx={x} cy={y} r={1.4 + s2 * 4} fill={color} opacity={fade * opacity} />;
      })}
    </g>
  );
};

/** A number that counts up — for distances, days, crowds. */
export const Counter: React.FC<{
  from: number; to: number; startAt: number; endAt: number;
  suffix?: string; size?: number; color?: string;
}> = ({ from, to, startAt, endAt, suffix, size = 100, color = PALETTE.turmeric }) => {
  const frame = useCurrentFrame();
  const v = Math.round(interpolate(frame, [startAt, endAt], [from, to], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE,
  }));
  return (
    <text fill={color} fontSize={size} fontWeight={900} textAnchor="middle">
      {v}
      {suffix ? <tspan fontSize={size * 0.5} fontWeight={700}> {suffix}</tspan> : null}
    </text>
  );
};

/** A full-frame camera move applied to any SVG scene — the "stop cutting" rule. */
export const useCamera = (
  durationInFrames: number,
  opts: { zoom?: [number, number]; panX?: [number, number]; panY?: [number, number] } = {},
) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: "clamp", easing: EASE });
  const [z0, z1] = opts.zoom ?? [1, 1.1];
  const [x0, x1] = opts.panX ?? [0, 0];
  const [y0, y1] = opts.panY ?? [0, 0];
  const zoom = interpolate(t, [0, 1], [z0, z1]);
  const px = interpolate(t, [0, 1], [x0, x1]);
  const py = interpolate(t, [0, 1], [y0, y1]);
  return { transform: `scale(${zoom}) translate(${px}px, ${py}px)`, t };
};

import React from "react";
import { ART_H, ART_W } from "./Stage";
import { clamp, flicker, rand, sine } from "../lib/motion";

/* ------------------------------------------------------------------ lamps */

export type Lamp = { x: number; y: number; r?: number };

/** Warm flame glow over painted lamps. Screen-blended, so it only ever adds light. */
export const LampGlow: React.FC<{ lamps: Lamp[]; frame: number; strength?: number; color?: string }> = ({
  lamps,
  frame,
  strength = 1,
  color = "255,176,72",
}) => (
  <>
    {lamps.map((l, i) => {
      const f = flicker(frame, i * 7 + 3);
      const r = (l.r ?? 90) * (0.92 + 0.12 * f);
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: l.x - r * 2,
            top: l.y - r * 2.2,
            width: r * 4,
            height: r * 4,
            borderRadius: "50%",
            mixBlendMode: "screen",
            opacity: clamp(strength * f, 0, 1),
            background: `radial-gradient(circle at 50% 55%, rgba(${color},0.85) 0%, rgba(${color},0.35) 18%, rgba(${color},0.10) 42%, rgba(${color},0) 70%)`,
          }}
        />
      );
    })}
  </>
);

/* ------------------------------------------------------------------ birds */

/** Small ink birds crossing the sky, wings flapping on their own rhythm (matches the painted ones). */
export const Birds: React.FC<{
  frame: number;
  flock: { x0: number; y0: number; vx: number; vy: number; size: number; phase: number }[];
  ink?: string;
}> = ({ frame, flock, ink = "#2a1e2c" }) => (
  <svg width={ART_W} height={ART_H} style={{ position: "absolute", left: 0, top: 0 }}>
    {flock.map((b, i) => {
      const t = frame / 30;
      const x = b.x0 + b.vx * t;
      const y = b.y0 + b.vy * t + 6 * Math.sin(t * 1.7 + b.phase);
      const flap = Math.sin(t * 9 + b.phase); // -1..1
      const s = b.size;
      const tipY = -s * (0.15 + 0.45 * flap);
      const d = `M ${-s} ${tipY} Q ${-s * 0.45} ${-s * 0.1 - flap * s * 0.15} 0 ${s * 0.12} Q ${s * 0.45} ${-s * 0.1 - flap * s * 0.15} ${s} ${tipY}`;
      return (
        <path
          key={i}
          d={d}
          transform={`translate(${x} ${y})`}
          fill="none"
          stroke={ink}
          strokeWidth={s * 0.16}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      );
    })}
  </svg>
);

/* ------------------------------------------------------------------ dust */

/**
 * Turmeric dust: deterministic particles. Each grain is born at `from` (with jitter),
 * travels along a curved path to `to`, then hangs and twinkles out.
 */
export const Dust: React.FC<{
  frame: number;
  start: number; // frame the stream begins
  count: number;
  from: { x: number; y: number; spread: number };
  to?: { x: number; y: number; spread: number };
  rise?: number; // px per second upward drift when there is no target
  travel?: number; // frames to reach the target
  life?: number; // frames each grain lives
  emitOver?: number; // frames over which grains are born
  size?: number;
  seed?: number;
  color?: string;
}> = ({
  frame,
  start,
  count,
  from,
  to,
  rise = 60,
  travel = 14,
  life = 60,
  emitOver = 20,
  size = 7,
  seed = 1,
  color = "255,196,64",
}) => {
  const grains = [];
  for (let i = 0; i < count; i++) {
    const born = start + rand(seed * 1000 + i) * emitOver;
    const age = frame - born;
    if (age < 0 || age > life) continue;
    const jx = (rand(seed * 2000 + i) - 0.5) * from.spread;
    const jy = (rand(seed * 3000 + i) - 0.5) * from.spread * 0.6;
    let x = from.x + jx;
    let y = from.y + jy;
    if (to) {
      const p = clamp(age / travel, 0, 1);
      const e = 1 - Math.pow(1 - p, 3);
      const tx = to.x + (rand(seed * 4000 + i) - 0.5) * to.spread;
      const ty = to.y + (rand(seed * 5000 + i) - 0.5) * to.spread * 0.5;
      const arc = -70 * Math.sin(Math.PI * e) * (0.6 + rand(seed * 6000 + i));
      x = x + (tx - x) * e;
      y = y + (ty - y) * e + arc;
      if (p >= 1) y -= ((age - travel) / 30) * 18; // after landing, a slow lift of fine dust
    } else {
      x += sine(age, 1.6 + rand(seed * 7000 + i), i) * 14;
      y -= (age / 30) * rise * (0.6 + rand(seed * 8000 + i));
    }
    const fadeIn = clamp(age / 4, 0, 1);
    const fadeOut = clamp((life - age) / (life * 0.45), 0, 1);
    const tw = 0.65 + 0.35 * Math.sin(age * 0.9 + i);
    const r = size * (0.5 + rand(seed * 9000 + i));
    grains.push(
      <div
        key={i}
        style={{
          position: "absolute",
          left: x - r,
          top: y - r,
          width: r * 2,
          height: r * 2,
          borderRadius: "50%",
          mixBlendMode: "screen",
          opacity: fadeIn * fadeOut * tw,
          background: `radial-gradient(circle, rgba(255,246,200,1) 0%, rgba(${color},0.9) 35%, rgba(${color},0) 70%)`,
        }}
      />,
    );
  }
  return <>{grains}</>;
};

/** A soft radial bloom (used for the cut-on-action flash and the hands' anticipation glow). */
export const Bloom: React.FC<{ x: number; y: number; r: number; opacity: number; color?: string }> = ({
  x,
  y,
  r,
  opacity,
  color = "255,190,70",
}) => (
  <div
    style={{
      position: "absolute",
      left: x - r,
      top: y - r,
      width: r * 2,
      height: r * 2,
      borderRadius: "50%",
      mixBlendMode: "screen",
      opacity: clamp(opacity, 0, 1),
      background: `radial-gradient(circle, rgba(255,240,190,0.95) 0%, rgba(${color},0.55) 30%, rgba(${color},0) 70%)`,
    }}
  />
);

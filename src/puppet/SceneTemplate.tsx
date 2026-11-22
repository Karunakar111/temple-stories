import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { SkyLayer, FarHills, MidHill, ShrineLayer, Foreground } from "./HillShrine";

/**
 * Scene template.
 *
 * Every episode's shots drop into this: five named background layers that each
 * take their own parallax offset, a `warm` value that moves the whole scene
 * through the day, and a slot for characters between the mid and foreground
 * planes. A new shot is new numbers and new children — not a new scene.
 */
export const SceneTemplate: React.FC<{
  warm: number;
  lamp?: number;
  /** Camera: a scale and an offset applied to everything. */
  zoom?: number;
  panX?: number;
  panY?: number;
  /** Multiplier on each layer's drift, for parallax. */
  depth?: number;
  children?: React.ReactNode;
  /** Drawn in front of characters but behind the foreground rocks. */
  midground?: React.ReactNode;
  /** Drawn over everything (haze, particles). */
  air?: React.ReactNode;
}> = ({ warm, lamp = 1, zoom = 1, panX = 0, panY = 0, depth = 0, children, midground, air }) => (
  <AbsoluteFill style={{ backgroundColor: "#1C1A22" }}>
    <svg viewBox="0 0 1080 1920" width="100%" height="100%"
      style={{ transform: `scale(${zoom}) translate(${panX}px, ${panY}px)` }}>
      <g transform={`translate(0 ${depth * -6})`}><SkyLayer warm={warm} /></g>
      <g transform={`translate(0 ${depth * -16})`}><FarHills warm={warm} /></g>
      <g transform={`translate(0 ${depth * -34})`}><MidHill warm={warm} /></g>
      <g transform={`translate(0 ${depth * -34})`}><ShrineLayer warm={warm} lamp={lamp} /></g>
      <g transform={`translate(0 ${depth * -52})`}>{children}</g>
      {midground}
      <g transform={`translate(0 ${depth * -78})`}><Foreground warm={warm} /></g>
      {air}
    </svg>
  </AbsoluteFill>
);

/** Turmeric thrown into the air, then settling. Reusable in any scatter shot. */
export const TurmericBurst: React.FC<{
  originX: number;
  originY: number;
  startAt: number;
  count?: number;
  power?: number;
}> = ({ originX, originY, startAt, count = 150, power = 1 }) => {
  const frame = useCurrentFrame();
  const t = (frame - startAt) / 30;
  if (t <= 0) return null;

  const rnd = (i: number, s = 1) => {
    const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453;
    return x - Math.floor(x);
  };

  return (
    <g>
      {Array.from({ length: count }).map((_, i) => {
        const delay = rnd(i, 2) * 0.22;
        const age = t - delay;
        if (age <= 0) return null;
        const ang = -2.5 + rnd(i, 3) * 2.0;          // thrown up and outward
        const sp = (240 + rnd(i, 5) * 420) * power;
        const x = originX + Math.cos(ang) * sp * age;
        const y = originY + Math.sin(ang) * sp * age + 0.5 * 560 * age * age;
        if (y > 1980) return null;
        const r = 3 + rnd(i, 7) * 8;
        const fade = Math.min(1, age * 6) * Math.max(0, 1 - age / 3.4);
        return (
          <circle key={i} cx={x} cy={y} r={r}
            fill={i % 5 === 0 ? "#FFD98A" : "#F0A32A"} opacity={fade * 0.92} />
        );
      })}
    </g>
  );
};

/** Hanging haze left behind after a burst — the environmental change. */
export const TurmericHaze: React.FC<{ amount: number }> = ({ amount }) => {
  const frame = useCurrentFrame();
  if (amount <= 0) return null;
  return (
    <g opacity={amount}>
      <defs>
        <radialGradient id="hazeG">
          <stop offset="0%" stopColor="#F0B32A" stopOpacity={0.5} />
          <stop offset="100%" stopColor="#F0B32A" stopOpacity={0} />
        </radialGradient>
      </defs>
      <ellipse cx={540} cy={1180} rx={900} ry={520} fill="url(#hazeG)" />
      {Array.from({ length: 70 }).map((_, i) => {
        const s = Math.sin(i * 91.7) * 0.5 + 0.5;
        const s2 = Math.sin(i * 33.1) * 0.5 + 0.5;
        const y = 1500 - ((frame * (0.3 + s * 0.8) + s2 * 1400) % 1500);
        const x = 60 + s * 960 + Math.sin(frame / 44 + i) * 28;
        return <circle key={i} cx={x} cy={y} r={2 + s2 * 6} fill="#F0B32A"
          opacity={interpolate(y, [200, 900, 1500], [0, 0.55, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />;
      })}
    </g>
  );
};

import React from "react";
import { interpolate } from "remotion";
import { INK, GOLD } from "./rig";

/**
 * The Komuravelli hill shrine, as a layered background.
 *
 * Layers are separate exported groups so a shot can move them independently —
 * that separation is what makes parallax and environmental change possible
 * without redrawing anything.
 *
 *   SkyLayer  ·  FarHills  ·  MidHill  ·  ShrineLayer  ·  Foreground
 *
 * `warm` runs 0 → 1 and takes the whole scene from dusk to gold. Every layer
 * reads it, so a single number changes the time of day.
 */

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const mix = (a: string, b: string, t: number) => {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const p = pa.map((v, i) => Math.round(v + (pb[i] - v) * t));
  return `#${p.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
};

export const SkyLayer: React.FC<{ warm: number }> = ({ warm }) => {
  const top = mix("#2B2546", "#8E4A2E", warm);
  const mid = mix("#5A4A72", "#D4761C", warm);
  const low = mix("#8E4A2E", "#F0B32A", warm);
  return (
    <g>
      <defs>
        <linearGradient id="skyG" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={top} />
          <stop offset="55%" stopColor={mid} />
          <stop offset="100%" stopColor={low} />
        </linearGradient>
        <radialGradient id="sunG">
          <stop offset="0%" stopColor="#FFD98A" stopOpacity={0.95} />
          <stop offset="100%" stopColor="#FFD98A" stopOpacity={0} />
        </radialGradient>
      </defs>
      <rect width={1080} height={1920} fill="url(#skyG)" />
      {/* the sun lifts and brightens as the scene warms */}
      <circle cx={760} cy={interpolate(warm, [0, 1], [1010, 780])} r={interpolate(warm, [0, 1], [300, 460])} fill="url(#sunG)" />
      <circle cx={760} cy={interpolate(warm, [0, 1], [1010, 780])} r={interpolate(warm, [0, 1], [62, 78])}
        fill={mix("#E8A33D", "#FFE08A", warm)} />
      {/* concentric decorative rings, as in the reference's arch */}
      {[0, 1, 2].map((i) => (
        <circle key={i} cx={760} cy={interpolate(warm, [0, 1], [1010, 780])} r={150 + i * 92}
          fill="none" stroke={GOLD} strokeWidth={2} opacity={0.12 + warm * 0.1}
          strokeDasharray="3 16" />
      ))}
    </g>
  );
};

export const FarHills: React.FC<{ warm: number }> = ({ warm }) => (
  <g opacity={0.9}>
    <path d="M -60 1180 L 150 1056 L 340 1142 L 540 1020 L 740 1128 L 940 1046 L 1140 1150 L 1140 1500 L -60 1500 Z"
      fill={mix("#5A4A72", "#A05A2E", warm)} />
  </g>
);

export const MidHill: React.FC<{ warm: number }> = ({ warm }) => (
  <g>
    <path d="M -60 1360 C 170 1230 350 1272 540 1186 C 730 1100 910 1180 1140 1300 L 1140 1700 L -60 1700 Z"
      fill={mix("#8E4A2E", "#C2702A", warm)} stroke={INK} strokeWidth={4} />
    {/* scrub, in a steady scatter */}
    {Array.from({ length: 14 }).map((_, i) => {
      const x = 40 + rnd(i, 5) * 1000;
      const y = 1270 + rnd(i, 9) * 120;
      const s = 14 + rnd(i, 13) * 18;
      return <ellipse key={i} cx={x} cy={y} rx={s} ry={s * 0.62} fill={INK} opacity={0.42} />;
    })}
  </g>
);

export const ShrineLayer: React.FC<{ warm: number; lamp: number }> = ({ warm, lamp }) => (
  <g transform="translate(726 1148) scale(0.92)">
    {/* rock recess it is cut into */}
    <path d="M -210 40 C -230 -120 -140 -250 0 -250 C 140 -250 230 -120 210 40 Z"
      fill={mix("#3E2F22", "#6B4A2E", warm)} stroke={INK} strokeWidth={4} />
    {/* shrine body */}
    <rect x={-96} y={-150} width={192} height={190} fill={mix("#74583F", "#A8763F", warm)}
      stroke={INK} strokeWidth={4} />
    {/* stepped vimana */}
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={-(156 - i * 30) / 2} y={-150 - (i + 1) * 30} width={156 - i * 30} height={30}
        fill={GOLD} stroke={INK} strokeWidth={3.5} />
    ))}
    <circle cy={-292} r={15} fill={GOLD} stroke={INK} strokeWidth={3.5} />
    {/* doorway and the lamp inside */}
    <rect x={-40} y={-104} width={80} height={144} fill="#160E14" stroke={INK} strokeWidth={4} />
    <circle cy={-30} r={26 * lamp} fill="#FFC658" opacity={0.5} />
    <circle cy={-30} r={11} fill="#FFD98A" />
    {/* dotted gold edging, the reference's signature detail */}
    <rect x={-104} y={-158} width={208} height={206} fill="none" stroke={GOLD}
      strokeWidth={3} strokeDasharray="2 12" opacity={0.75} />
  </g>
);

export const Foreground: React.FC<{ warm: number }> = ({ warm }) => (
  <g>
    <path d="M -60 1660 C 220 1580 420 1630 600 1596 C 790 1560 960 1610 1140 1660 L 1140 1960 L -60 1960 Z"
      fill={mix("#1C1A22", "#4A2E1C", warm)} stroke={INK} strokeWidth={4} />
    {[120, 380, 820, 1000].map((x, i) => (
      <ellipse key={i} cx={x} cy={1700 + (i % 2) * 40} rx={48 + i * 9} ry={26}
        fill={mix("#141218", "#3A2416", warm)} stroke={INK} strokeWidth={3} />
    ))}
  </g>
);

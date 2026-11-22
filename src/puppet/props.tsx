import React from "react";
import { INK, GOLD } from "./rig";
import { MARIGOLD, MARIGOLD_DK } from "./Mallanna";

/** Reusable props. Each is a plain SVG group so it can be parented to a hand. */

export const Bandari: React.FC<{ scale?: number }> = ({ scale = 1 }) => (
  <g transform={`scale(${scale})`}>
    {[0, 1, 2, 3].map((i) => (
      <ellipse key={i} cx={-18 + i * 12} cy={(i % 2) * 7} rx={13} ry={6.5}
        transform={`rotate(${-26 + i * 16} ${-18 + i * 12} ${(i % 2) * 7})`}
        fill={MARIGOLD} stroke={INK} strokeWidth={2.5} />
    ))}
  </g>
);

export const Pot: React.FC<{ scale?: number }> = ({ scale = 1 }) => (
  <g transform={`scale(${scale})`}>
    <path d="M -22 -6 C -28 14 -20 32 0 32 C 20 32 28 14 22 -6 Z"
      fill="#A65A32" stroke={INK} strokeWidth={3} />
    <ellipse cy={-6} rx={22} ry={7} fill="#C4733F" stroke={INK} strokeWidth={3} />
    <ellipse cy={-6} rx={14} ry={4} fill={MARIGOLD} />
  </g>
);

export const Sword: React.FC<{ scale?: number }> = ({ scale = 1 }) => (
  <g transform={`scale(${scale})`}>
    <path d="M 0 0 C 10 34 14 72 6 104 L -4 100 C 2 70 -2 34 -10 4 Z"
      fill="#D8D2C4" stroke={INK} strokeWidth={3} strokeLinejoin="round" />
    <rect x={-14} y={-14} width={28} height={12} rx={4} fill={GOLD} stroke={INK} strokeWidth={3} />
  </g>
);

/** A single marigold, for scattering. */
export const Marigold: React.FC<{ r?: number; dark?: boolean }> = ({ r = 9, dark = false }) => (
  <circle r={r} fill={dark ? MARIGOLD_DK : MARIGOLD} stroke={INK} strokeWidth={2} />
);

export const Dolu: React.FC<{ scale?: number }> = ({ scale = 1 }) => (
  <g transform={`scale(${scale})`}>
    <rect x={-34} y={-20} width={68} height={40} rx={8} fill="#8A5A2E" stroke={INK} strokeWidth={3} />
    <ellipse cx={-34} rx={7} ry={20} fill="#E8DCC2" stroke={INK} strokeWidth={3} />
    <ellipse cx={34} rx={7} ry={20} fill="#E8DCC2" stroke={INK} strokeWidth={3} />
    {[-18, 0, 18].map((x, i) => (
      <path key={i} d={`M ${x} -20 L ${x + 6} 20`} stroke={GOLD} strokeWidth={3} />
    ))}
  </g>
);

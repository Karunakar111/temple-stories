import React from "react";
import { INK } from "./rig";

/**
 * A hand with fingers that stays a hand all the way through a throw.
 *
 * `open` runs 0 (closed around something) → 1 (fingers spread, just released).
 * The fingers are drawn individually and rotate from their knuckles, so the hand
 * is never swapped out or hidden — it opens.
 */
export const Hand: React.FC<{
  skin: string;
  open?: number;
  scale?: number;
  /** Held object, drawn inside the fingers and faded as they open. */
  holding?: React.ReactNode;
}> = ({ skin, open = 0, scale = 1, holding }) => {
  // knuckle angles: closed fingers curl in, open ones splay
  const fingers = [
    { a0: 68, a1: -14, len: 20, r: 4.6 },
    { a0: 76, a1: 2, len: 23, r: 4.9 },
    { a0: 72, a1: 16, len: 21, r: 4.6 },
    { a0: 64, a1: 30, len: 18, r: 4.2 },
  ];
  return (
    <g transform={`scale(${scale})`}>
      {/* the held object sits behind the fingers and goes as they open */}
      {holding ? <g opacity={1 - open} transform="translate(2 6)">{holding}</g> : null}

      {/* palm — a rounded wedge, wider at the knuckles */}
      <path
        d="M -11 -4 C -14 6 -11 16 -2 19 C 8 22 16 17 17 7 C 18 -2 14 -8 6 -10 C -2 -12 -9 -11 -11 -4 Z"
        fill={skin} stroke={INK} strokeWidth={3} strokeLinejoin="round"
      />
      {/* fingers, rotating from the knuckle edge */}
      {fingers.map((f, i) => {
        const ang = f.a0 + (f.a1 - f.a0) * open;
        return (
          <g key={i} transform={`translate(${-6 + i * 7} 14) rotate(${ang})`}>
            <rect x={-f.r} y={0} width={f.r * 2} height={f.len} rx={f.r}
              fill={skin} stroke={INK} strokeWidth={2.6} />
            {/* second phalanx, trailing the first */}
            <g transform={`translate(0 ${f.len}) rotate(${(1 - open) * 44})`}>
              <rect x={-f.r * 0.88} y={0} width={f.r * 1.76} height={f.len * 0.66} rx={f.r * 0.88}
                fill={skin} stroke={INK} strokeWidth={2.4} />
            </g>
          </g>
        );
      })}
      {/* thumb, on the near side */}
      <g transform={`translate(-11 4) rotate(${-32 - open * 30})`}>
        <rect x={-5} y={0} width={10} height={19} rx={5} fill={skin} stroke={INK} strokeWidth={2.8} />
      </g>
    </g>
  );
};

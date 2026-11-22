import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";
import { PALETTE } from "../design/palette";
import { rnd, useCamera } from "../draw/primitives";

/**
 * Shot 6 — the gods give him a flying horse and he sets out. Only 3.8 seconds, so
 * it does exactly one thing: a route arcs away from the hill into the dark, with
 * the horse riding the head of the line. The map language from the open, reused —
 * which is what makes it read as the same series.
 */
const ARC = "M 120 1600 C 300 1380 420 1180 560 980 C 700 780 840 620 980 470";

export const S06Journey: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const cam = useCamera(durationInFrames, { zoom: [1.0, 1.12], panX: [20, -20] });
  const pathRef = React.useRef<SVGPathElement | null>(null);
  const [pt, setPt] = React.useState({ x: 120, y: 1600, a: 0 });

  const draw = interpolate(frame, [4, durationInFrames - 10], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.4, 0, 0.3, 1),
  });

  React.useEffect(() => {
    const el = pathRef.current;
    if (!el) return;
    const L = el.getTotalLength();
    const p = el.getPointAtLength(L * draw);
    const q = el.getPointAtLength(Math.min(L, L * draw + 6));
    setPt({ x: p.x, y: p.y, a: (Math.atan2(q.y - p.y, q.x - p.x) * 180) / Math.PI });
  }, [draw]);

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.indigo, overflow: "hidden" }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ transform: cam.transform }}>
        <rect width="1080" height="1920" fill={PALETTE.indigo} />
        {/* stars */}
        {Array.from({ length: 70 }).map((_, i) => {
          const tw = 0.4 + Math.abs(Math.sin(frame / 20 + i)) * 0.6;
          return <circle key={i} cx={rnd(i, 3) * 1080} cy={rnd(i, 11) * 1500}
            r={1 + rnd(i, 17) * 2} fill={PALETTE.bone} opacity={0.5 * tw} />;
        })}
        {/* hills he leaves behind */}
        <path d="M -60 1700 C 160 1596 340 1640 540 1572 C 740 1504 900 1570 1140 1640 L 1140 1960 L -60 1960 Z"
          fill={PALETTE.ink} />

        {/* ghost route, then the travelled part */}
        <path ref={pathRef} d={ARC} fill="none" stroke={PALETTE.violet} strokeWidth={5} opacity={0.4} strokeDasharray="14 18" />
        <path d={ARC} fill="none" stroke={PALETTE.turmeric} strokeWidth={8} strokeLinecap="round"
          strokeDasharray={2600} strokeDashoffset={2600 * (1 - draw)} />

        {/* the horse at the head of the line */}
        <g transform={`translate(${pt.x} ${pt.y}) rotate(${pt.a})`}
           opacity={interpolate(frame, [4, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
          <g transform="translate(-46 -34) scale(1.5)">
            <path d="M 0 40 L 0 24 C 0 16 6 10 16 10 L 46 10 C 54 10 58 6 60 -2 L 64 -14
                     C 66 -20 72 -22 76 -18 C 80 -14 80 -8 76 -4 L 72 2
                     C 78 6 80 12 80 20 L 80 32 C 80 40 74 46 66 46"
              fill="none" stroke={PALETTE.bone} strokeWidth={6} strokeLinecap="round" strokeLinejoin="round" />
            <path d="M 8 46 L 8 62 M 26 46 L 26 62 M 56 46 L 56 62 M 74 46 L 74 62"
              stroke={PALETTE.bone} strokeWidth={5} strokeLinecap="round" />
            {/* wings, beating */}
            <path d={`M 30 14 C 10 ${-12 + Math.sin(frame / 3) * 10} 54 ${-26 + Math.sin(frame / 3) * 12} 64 4`}
              fill="none" stroke={PALETTE.bone} strokeWidth={5} strokeLinecap="round" opacity={0.9} />
          </g>
        </g>
      </svg>
    </AbsoluteFill>
  );
};

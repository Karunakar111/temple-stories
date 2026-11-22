import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { PALETTE } from "../design/palette";
import { Stroke, Grains, useCamera } from "../draw/primitives";
import { SerpentHead } from "../draw/folk";

/**
 * Shot 5 — the bandari, kept far away, with a five-headed serpent on guard.
 *
 * The only warm thing in frame is the prize. Everything else is cold stone. The
 * heads rise one at a time so the threat accumulates rather than arriving at once.
 */
export const S05Serpent: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const cam = useCamera(durationInFrames, { zoom: [1.18, 1.0], panY: [-30, 20] });
  const lamp = 0.82 + Math.sin(frame / 8) * 0.18;

  return (
    <AbsoluteFill style={{ backgroundColor: "#0b0914", overflow: "hidden" }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ transform: cam.transform }}>
        <defs>
          <radialGradient id="pool">
            <stop offset="0%" stopColor={PALETTE.turmeric} stopOpacity={0.9} />
            <stop offset="100%" stopColor={PALETTE.turmeric} stopOpacity={0} />
          </radialGradient>
        </defs>
        <rect width="1080" height="1920" fill="#0b0914" />

        {/* stone courses, receding */}
        {Array.from({ length: 9 }).map((_, r) => (
          <g key={r} opacity={0.5 - r * 0.035}>
            {Array.from({ length: 6 }).map((_, c) => (
              <rect key={c} x={-40 + c * 200 + (r % 2 ? 100 : 0)} y={240 + r * 150}
                width={186} height={136} rx={5} fill="none"
                stroke={PALETTE.violet} strokeWidth={3} />
            ))}
          </g>
        ))}

        {/* plinth */}
        <Stroke from={0} to={34} color={PALETTE.violet} width={9} len={1400}
          d="M 330 1320 L 750 1320 L 790 1430 L 290 1430 Z" />
        <path d="M 330 1320 L 750 1320 L 790 1430 L 290 1430 Z" fill="#171226"
          opacity={interpolate(frame, [28, 50], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />

        {/* the prize */}
        <circle cx={540} cy={1286} r={210 * lamp} fill="url(#pool)" opacity={0.6} />
        {[0, 1, 2, 3, 4].map((i) => (
          <ellipse key={i}
            cx={470 + i * 36 + (i % 2) * 8} cy={1294 + (i % 2) * 12}
            rx={30} ry={15} transform={`rotate(${-24 + i * 12} ${470 + i * 36} ${1294})`}
            fill={PALETTE.turmeric}
            opacity={interpolate(frame, [36 + i * 5, 52 + i * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        ))}

        {/* the coil */}
        <Stroke from={54} to={104} color={PALETTE.murtiGreen} width={22} len={1500}
          d="M 790 1400 C 900 1330 900 1180 780 1130 C 680 1088 560 1110 520 1180" />

        {/* five heads, rising one at a time */}
        {[-2, -1, 0, 1, 2].map((k, i) => {
          const x = 540 + k * 168;
          const y = 880 - (2 - Math.abs(k)) * 84;
          const sway = Math.sin(frame / 22 + i * 1.1) * 9;
          const at = 96 + i * 13;
          const rise = interpolate(frame, [at, at + 30], [160, 0], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          const appear = interpolate(frame, [at, at + 14], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp",
          });
          return (
            <g key={i} opacity={appear}>
              {/* neck running down into the coil */}
              <Stroke from={at} to={at + 26} color={PALETTE.murtiGreen} width={26} len={520}
                d={`M 540 1180 C ${540 + k * 50} 1120 ${x + sway} ${y + rise + 230} ${x + sway} ${y + rise + 120}`} />
              <SerpentHead x={x + sway} y={y + rise} scale={0.92} />
            </g>
          );
        })}

        <Grains cx={540} cy={1300} r={240} from={150} n={20} color={PALETTE.turmeric} spread={50} />
      </svg>
    </AbsoluteFill>
  );
};

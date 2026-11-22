import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { PALETTE } from "../design/palette";
import { Counter, useCamera } from "../draw/primitives";

/**
 * Shot 7 — "he joined as a gardener, changed his name, days passed, months passed,
 * until every one of them trusted him — he waited."
 *
 * The whole beat is TIME, so time is what animates: the sun arcs over and over, the
 * day counter climbs, the figure keeps watering. On the final word everything stops
 * except the water — the pause the script asks for, made visual.
 */
export const S07TheWait: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const cam = useCamera(durationInFrames, { zoom: [1.0, 1.08] });

  // Everything freezes for the last beat — "ఆగిండు".
  const stopAt = durationInFrames - 46;
  const t = Math.min(frame, stopAt);

  const cycles = 7;
  const phase = (t / stopAt) * cycles;
  const dayT = phase % 1;
  const sunX = interpolate(dayT, [0, 1], [120, 960]);
  const sunY = 520 + Math.sin(dayT * Math.PI) * -300;
  const night = Math.max(0, Math.cos(dayT * Math.PI * 2)) * 0.55;

  const frozen = frame > stopAt;

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.amber, overflow: "hidden" }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ transform: cam.transform }}>
        <defs>
          <linearGradient id="g7" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={PALETTE.violet} />
            <stop offset="55%" stopColor={PALETTE.amber} />
            <stop offset="100%" stopColor={PALETTE.sienna} />
          </linearGradient>
        </defs>
        <rect width="1080" height="1920" fill="url(#g7)" />
        <rect width="1080" height="1920" fill={PALETTE.indigo} opacity={night} />

        {/* the sun, going round and round */}
        <circle cx={sunX} cy={sunY} r={56} fill={PALETTE.turmeric} opacity={0.9} />

        {/* garden wall, with guards passing along the top */}
        <rect x={-20} y={980} width={1120} height={150} fill={PALETTE.sienna} stroke={PALETTE.ink} strokeWidth={8} />
        {[0, 1].map((i) => {
          const gx = ((t * 1.6 + i * 540) % 1300) - 110;
          return (
            <g key={i} transform={`translate(${gx} 930)`} opacity={0.95}>
              <rect x={-12} y={-58} width={24} height={60} rx={10} fill={PALETTE.ink} />
              <circle cy={-70} r={15} fill={PALETTE.ink} />
              <rect x={20} y={-96} width={5} height={100} fill={PALETTE.ink} />
            </g>
          );
        })}

        {/* beds of plants */}
        {Array.from({ length: 4 }).map((_, row) =>
          Array.from({ length: 9 }).map((_, col) => {
            const x = 90 + col * 112;
            const y = 1260 + row * 150;
            const grow = interpolate(phase, [row * 1.2, row * 1.2 + 2], [0.5, 1], {
              extrapolateLeft: "clamp", extrapolateRight: "clamp",
            });
            return (
              <g key={`${row}-${col}`} transform={`translate(${x} ${y}) scale(${grow})`}>
                <path d="M 0 0 L 0 -42" stroke={PALETTE.murtiGreen} strokeWidth={7} strokeLinecap="round" />
                <ellipse cx={-17} cy={-38} rx={17} ry={10} fill={PALETTE.murtiGreen} />
                <ellipse cx={17} cy={-48} rx={17} ry={10} fill={PALETTE.murtiGreen} />
              </g>
            );
          }),
        )}

        {/* the gardener — head down, same action, over and over */}
        <g transform={`translate(${620 + Math.sin(phase * Math.PI * 2) * 150} 1560)`}>
          <path d="M 0 0 C -48 0 -70 56 -70 128 L 70 128 C 70 56 48 0 0 0 Z"
            fill={PALETTE.bone} stroke={PALETTE.ink} strokeWidth={7} />
          <circle cy={-44} r={36} fill={PALETTE.murtiBlue} stroke={PALETTE.ink} strokeWidth={7} />
          {/* the moustache, even in disguise */}
          <path d="M 0 -32 C -14 -34 -26 -28 -30 -20 C -32 -15 -28 -11 -22 -13
                   C -14 -16 -8 -24 0 -24 C 8 -24 14 -16 22 -13
                   C 28 -11 32 -15 30 -20 C 26 -28 14 -34 0 -32 Z" fill={PALETTE.ink} />
          {/* the pot and the water — the one thing still moving at the end */}
          <path d="M 62 30 L 104 30 L 96 78 L 70 78 Z" fill={PALETTE.sienna} stroke={PALETTE.ink} strokeWidth={6} />
          {Array.from({ length: 7 }).map((_, i) => {
            const d = ((frame * 5 + i * 17) % 110);
            return <circle key={i} cx={100 + d * 0.22} cy={84 + d} r={3.4}
              fill={PALETTE.bone} opacity={0.85 - d / 150} />;
          })}
        </g>
      </svg>

      {/* the counter — days, then months */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 220 }}>
        <svg viewBox="0 0 1080 360" width="86%">
          <g transform="translate(540 150)">
            <Counter from={1} to={frozen ? 400 : 400} startAt={0} endAt={stopAt} suffix="రోజులు" size={128} />
          </g>
          <g transform="translate(540 262)" opacity={frozen ? 1 : 0.0}>
            <text textAnchor="middle" fill={PALETTE.bone} fontSize={52} fontWeight={800}
              opacity={interpolate(frame, [stopAt, stopAt + 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
              ఆగిండు
            </text>
          </g>
        </svg>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

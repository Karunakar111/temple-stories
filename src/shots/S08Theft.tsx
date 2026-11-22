import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";
import { PALETTE } from "../design/palette";
import { useCamera } from "../draw/primitives";
import { SerpentHead, HandWithBandari } from "../draw/folk";

/**
 * Shot 8 — the serpent's eyes close one by one, the bandari leaves the plinth, and
 * somebody sees.
 *
 * Built as a count-down of ten eyes going dark. That is the tension: you watch the
 * guard fall asleep in real time, and the shot ends the instant it goes wrong.
 */
export const S08Theft: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const cam = useCamera(durationInFrames, { zoom: [1.0, 1.3], panY: [10, -40] });

  const lift = interpolate(frame, [138, 186], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  // the watcher resolves out of the dark right at the end
  const seen = interpolate(frame, [durationInFrames - 58, durationInFrames - 16], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0812", overflow: "hidden" }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ transform: cam.transform }}>
        <defs>
          <radialGradient id="prize">
            <stop offset="0%" stopColor={PALETTE.turmeric} stopOpacity={0.95} />
            <stop offset="100%" stopColor={PALETTE.turmeric} stopOpacity={0} />
          </radialGradient>
        </defs>
        <rect width="1080" height="1920" fill="#0a0812" />

        {/* heads overhead, hoods lowering as they sleep — ten eyes going dark */}
        {[-2, -1, 0, 1, 2].map((k, i) => {
          const x = 540 + k * 176;
          const closeAt = 20 + i * 22;
          const sleep = interpolate(frame, [closeAt, closeAt + 20], [0, 1], {
            extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad),
          });
          return <SerpentHead key={i} x={x} y={520 - (2 - Math.abs(k)) * 60} scale={0.88} sleep={sleep} />;
        })}
        <path d="M 540 760 C 430 880 470 1020 540 1100" stroke={PALETTE.murtiGreen}
          strokeWidth={28} fill="none" strokeLinecap="round" opacity={0.92} />

        {/* plinth and the prize, rising out of it */}
        <path d="M 330 1360 L 750 1360 L 792 1470 L 288 1470 Z" fill="#17122a"
          stroke={PALETTE.violet} strokeWidth={7} />
        <circle cx={540} cy={1320 - lift * 190} r={200} fill="url(#prize)" opacity={0.55} />
        <g transform={`translate(0 ${-lift * 190})`}>
          {[0, 1, 2, 3, 4].map((i) => (
            <ellipse key={i} cx={472 + i * 34} cy={1322 + (i % 2) * 11} rx={29} ry={14}
              transform={`rotate(${-22 + i * 11} ${472 + i * 34} 1322)`} fill={PALETTE.turmeric} />
          ))}
        </g>

        {/* the hand that takes it */}
        <g opacity={interpolate(frame, [120, 146], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
          <HandWithBandari x={700 - lift * 150} y={1420 - lift * 230} scale={0.92} rotate={-16 - lift * 12} />
        </g>

        {/* someone saw */}
        <g opacity={seen}>
          <ellipse cx={170} cy={1560} rx={54} ry={132} fill="#05040a" />
          <circle cx={170} cy={1400} r={44} fill="#05040a" />
          {[-15, 15].map((dx, i) => (
            <circle key={i} cx={170 + dx} cy={1394} r={5.5} fill={PALETTE.vermillion} opacity={seen} />
          ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};

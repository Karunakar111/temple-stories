import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";
import { PALETTE } from "../design/palette";
import { Stroke, Dust, rnd, useCamera } from "../draw/primitives";

/**
 * Shot 3 — before the temple there was forest, sheep, frightened herders, and a god
 * who came out of the earth itself.
 *
 * The longest shot in the part and its emotional foundation. Built in layers that
 * move at different rates, so the camera genuinely travels rather than zooming.
 */
export const S03Origin: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const cam = useCamera(durationInFrames, { zoom: [1.0, 1.22], panY: [30, -60] });

  // Layers drift at different rates — real parallax, not a single scale.
  const far = interpolate(frame, [0, durationInFrames], [0, -26], { extrapolateRight: "clamp" });
  const mid = interpolate(frame, [0, durationInFrames], [0, -64], { extrapolateRight: "clamp" });
  const near = interpolate(frame, [0, durationInFrames], [0, -130], { extrapolateRight: "clamp" });

  // The sun sinks across the shot; the glow in the mound answers it.
  const sunY = interpolate(frame, [0, durationInFrames], [640, 790], { extrapolateRight: "clamp" });
  const glow = interpolate(frame, [190, 300], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.indigo, overflow: "hidden" }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%" style={{ transform: cam.transform }}>
        <defs>
          <linearGradient id="sky3" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={PALETTE.indigo} />
            <stop offset="52%" stopColor={PALETTE.violet} />
            <stop offset="78%" stopColor={PALETTE.amber} />
            <stop offset="100%" stopColor={PALETTE.turmeric} />
          </linearGradient>
          <radialGradient id="mglow">
            <stop offset="0%" stopColor={PALETTE.turmeric} stopOpacity={0.95} />
            <stop offset="100%" stopColor={PALETTE.turmeric} stopOpacity={0} />
          </radialGradient>
        </defs>

        <rect width="1080" height="1920" fill="url(#sky3)" />
        <circle cx={760} cy={sunY} r={78} fill={PALETTE.turmeric} opacity={0.55} />

        {/* far hills */}
        <g transform={`translate(0 ${far})`}>
          <path d="M -60 980 L 150 862 L 330 944 L 520 836 L 720 930 L 900 860 L 1140 952 L 1140 1200 L -60 1200 Z"
            fill={PALETTE.violet} opacity={0.85} />
        </g>

        {/* mid hill — where the temple will one day be */}
        <g transform={`translate(0 ${mid})`}>
          <path d="M -60 1140 C 180 1020 340 1058 520 980 C 700 902 880 976 1140 1086 L 1140 1400 L -60 1400 Z"
            fill={PALETTE.sienna} />
          {/* scrub */}
          {Array.from({ length: 16 }).map((_, i) => {
            const x = 40 + rnd(i, 5) * 1000;
            const y = 1040 + rnd(i, 9) * 110;
            const s = 12 + rnd(i, 13) * 20;
            return <ellipse key={i} cx={x} cy={y} rx={s} ry={s * 0.68} fill={PALETTE.ink} opacity={0.62} />;
          })}
        </g>

        {/* the flock — small, moving, the reason he comes */}
        <g transform={`translate(0 ${mid})`}>
          {Array.from({ length: 11 }).map((_, i) => {
            const base = 150 + i * 56 + rnd(i, 21) * 30;
            const x = base + Math.sin(frame / 52 + i) * 16;
            const y = 1180 + rnd(i, 23) * 42;
            const bob = Math.abs(Math.sin(frame / 11 + i * 1.4)) * 3;
            return (
              <g key={i} transform={`translate(${x} ${y - bob})`} opacity={0.95}>
                <ellipse rx={17} ry={11} fill={PALETTE.bone} opacity={0.9} />
                <circle cx={15} cy={-5} r={6} fill={PALETTE.ink} />
                <rect x={-9} y={9} width={3} height={11} fill={PALETTE.ink} />
                <rect x={6} y={9} width={3} height={11} fill={PALETTE.ink} />
              </g>
            );
          })}
          {/* two herders with staffs */}
          {[260, 820].map((x, i) => (
            <g key={i} transform={`translate(${x} ${1150 + i * 38})`}>
              <rect x={-5} y={-42} width={10} height={44} rx={5} fill={PALETTE.ink} />
              <circle cy={-50} r={10} fill={PALETTE.ink} />
              <rect x={14} y={-62} width={3} height={66} fill={PALETTE.ink} />
            </g>
          ))}
        </g>

        {/* the termite mound, drawing itself out of the foreground */}
        <g transform={`translate(0 ${near})`}>
          <Stroke from={60} to={150} color={PALETTE.ink} width={14} len={2200}
            d="M 300 1760 C 330 1560 372 1400 430 1286 C 470 1206 520 1160 560 1160
               C 600 1160 650 1206 690 1286 C 748 1400 790 1560 820 1760 Z" />
          <path
            d="M 300 1760 C 330 1560 372 1400 430 1286 C 470 1206 520 1160 560 1160
               C 600 1160 650 1206 690 1286 C 748 1400 790 1560 820 1760 Z"
            fill={PALETTE.ink}
            opacity={interpolate(frame, [140, 180], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}
          />
          {/* ridges in the mound */}
          <Stroke from={150} to={210} color={PALETTE.sienna} width={5} len={900} opacity={0.75}
            d="M 356 1640 C 430 1600 640 1598 740 1646 M 382 1510 C 450 1476 650 1474 724 1518
               M 420 1380 C 480 1352 620 1350 674 1388" />

          {/* the glow inside, then the form */}
          <circle cx={560} cy={1420} r={240 * glow} fill="url(#mglow)" opacity={glow * 0.85} />
          <g opacity={glow}>
            {/* crown */}
            <Stroke from={230} to={286} color={PALETTE.murtiGold} width={11} len={700}
              d="M 492 1292 L 506 1222 L 532 1266 L 560 1200 L 588 1266 L 614 1222 L 628 1292 Z" />
            {/* head */}
            <Stroke from={248} to={300} color={PALETTE.murtiBlue} width={12} len={420}
              d="M 560 1300 m -46 0 a 46 52 0 1 0 92 0 a 46 52 0 1 0 -92 0" />
            {/* the moustache — the thing that makes him recognisable */}
            <Stroke from={282} to={320} color={PALETTE.ink} width={14} len={520}
              d="M 560 1322 C 532 1318 506 1326 494 1344 C 486 1356 492 1368 506 1366
                 C 522 1364 536 1348 560 1346 C 584 1348 598 1364 614 1366
                 C 628 1368 634 1356 626 1344 C 614 1326 588 1318 560 1322 Z" />
            {/* eyes */}
            {[-18, 18].map((dx, i) => (
              <circle key={i} cx={560 + dx} cy={1292} r={6}
                fill={PALETTE.bone}
                opacity={interpolate(frame, [300, 314], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
            ))}
            {/* shoulders rising out of the earth */}
            <Stroke from={300} to={344} color={PALETTE.murtiBlue} width={13} len={700}
              d="M 470 1430 C 480 1384 512 1358 560 1358 C 608 1358 640 1384 650 1430" />
          </g>
        </g>

        <Dust n={46} color={PALETTE.turmeric} speed={0.5} opacity={0.3} />
      </svg>
    </AbsoluteFill>
  );
};

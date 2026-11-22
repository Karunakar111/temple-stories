import React from "react";
import { PALETTE } from "../design/palette";

/**
 * Figures drawn the way the patnam draws them.
 *
 * The first pass built people and creatures as filled rounded capsules and they
 * read as bowling pins. Folk drawing works the opposite way: a bold outline, flat
 * fill inside it, and a few decisive interior marks. These components enforce that
 * so every shot in the series speaks one language.
 */

export const Figure: React.FC<{
  x: number; y: number; scale?: number;
  body: string; cloth: string;
  moustache?: boolean;
  arms?: "folded" | "down" | "open";
  skin?: string;
}> = ({ x, y, scale = 1, body, cloth, moustache = false, arms = "down", skin = PALETTE.sienna }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    {/* torso — tapered, with shoulders, not a capsule */}
    <path
      d="M -62 0 L -74 44 C -86 110 -80 200 -62 260 L 62 260 C 80 200 86 110 74 44 L 62 0 Z"
      fill={cloth} stroke={PALETTE.ink} strokeWidth={9} strokeLinejoin="round"
    />
    {/* a border band, the way cloth is drawn in folk work */}
    <path d="M -70 232 L 70 232" stroke={PALETTE.murtiGold} strokeWidth={10} strokeLinecap="round" />

    {/* arms */}
    {arms === "folded" ? (
      <path d="M -70 96 C -30 130 30 130 70 96" fill="none" stroke={PALETTE.ink} strokeWidth={13} strokeLinecap="round" />
    ) : arms === "open" ? (
      <path d="M -62 40 C -110 70 -124 120 -116 164 M 62 40 C 110 70 124 120 116 164"
        fill="none" stroke={body} strokeWidth={17} strokeLinecap="round" />
    ) : (
      <path d="M -66 38 C -96 90 -98 150 -88 196 M 66 38 C 96 90 98 150 88 196"
        fill="none" stroke={body} strokeWidth={17} strokeLinecap="round" />
    )}

    {/* neck + head, outlined */}
    <rect x={-13} y={-26} width={26} height={34} fill={skin} stroke={PALETTE.ink} strokeWidth={7} />
    <circle cy={-66} r={48} fill={skin} stroke={PALETTE.ink} strokeWidth={9} />
    {/* eyes — two marks, which is all folk faces need */}
    <circle cx={-17} cy={-74} r={6.5} fill={PALETTE.ink} />
    <circle cx={17} cy={-74} r={6.5} fill={PALETTE.ink} />
    {moustache ? (
      <path
        d="M 0 -50 C -17 -53 -32 -45 -37 -34 C -40 -27 -35 -21 -27 -24
           C -17 -28 -10 -38 0 -38 C 10 -38 17 -28 27 -24
           C 35 -21 40 -27 37 -34 C 32 -45 17 -53 0 -50 Z"
        fill={PALETTE.ink}
      />
    ) : (
      <path d="M -12 -50 Q 0 -44 12 -50" stroke={PALETTE.ink} strokeWidth={5} fill="none" strokeLinecap="round" />
    )}
  </g>
);

/** A woman's figure — same language, different silhouette. */
export const FigureSari: React.FC<{
  x: number; y: number; scale?: number; cloth: string; border?: string;
}> = ({ x, y, scale = 1, cloth, border = PALETTE.murtiGold }) => (
  <g transform={`translate(${x} ${y}) scale(${scale})`}>
    <path d="M -52 0 L -64 40 C -86 120 -94 210 -96 272 L 96 272
             C 94 210 86 120 64 40 L 52 0 Z"
      fill={cloth} stroke={PALETTE.ink} strokeWidth={9} strokeLinejoin="round" />
    {/* pallu across the shoulder */}
    <path d="M -44 16 C 0 56 40 110 56 190" fill="none" stroke={border} strokeWidth={12} strokeLinecap="round" />
    <path d="M -92 250 L 92 250" stroke={border} strokeWidth={12} strokeLinecap="round" />
    <path d="M -58 34 C -92 86 -96 148 -86 192" fill="none" stroke={PALETTE.sienna} strokeWidth={15} strokeLinecap="round" />
    <rect x={-12} y={-24} width={24} height={32} fill={PALETTE.sienna} stroke={PALETTE.ink} strokeWidth={7} />
    <circle cy={-62} r={44} fill={PALETTE.sienna} stroke={PALETTE.ink} strokeWidth={9} />
    {/* hair, drawn as one bold shape */}
    <path d="M -44 -70 C -44 -104 44 -104 44 -70 C 44 -86 30 -98 0 -98 C -30 -98 -44 -86 -44 -70 Z"
      fill={PALETTE.ink} />
    <path d="M 40 -58 C 68 -36 72 10 56 44" fill="none" stroke={PALETTE.ink} strokeWidth={13} strokeLinecap="round" />
    <circle cx={-15} cy={-68} r={6} fill={PALETTE.ink} />
    <circle cx={15} cy={-68} r={6} fill={PALETTE.ink} />
    <circle cy={-92} r={5} fill={PALETTE.vermillion} />
  </g>
);

/**
 * One serpent head — outlined hood, flat fill, two marks for eyes.
 * `sleep` 0..1 lowers the hood and closes the eyes.
 */
export const SerpentHead: React.FC<{
  x: number; y: number; scale?: number; sleep?: number;
}> = ({ x, y, scale = 1, sleep = 0 }) => (
  <g transform={`translate(${x} ${y + sleep * 44}) scale(${scale})`}>
    {/* hood — broad, flared, unmistakably a cobra */}
    <path
      d={`M 0 128 C -96 86 -112 -16 -58 -62 C -30 -86 30 -86 58 -62
          C 112 -16 96 86 0 128 Z`}
      fill={PALETTE.murtiGreen} stroke={PALETTE.ink} strokeWidth={10} strokeLinejoin="round"
    />
    {/* hood markings */}
    <circle cy={-6} r={26} fill="none" stroke={PALETTE.ink} strokeWidth={7} />
    <circle cy={-6} r={10} fill={PALETTE.ink} />
    {/* snout */}
    <path d="M -26 92 C -10 112 10 112 26 92" fill="none" stroke={PALETTE.ink} strokeWidth={8} strokeLinecap="round" />
    {/* eyes */}
    {sleep > 0.55 ? (
      <>
        <path d="M -40 56 Q -26 68 -12 56" stroke={PALETTE.ink} strokeWidth={6} fill="none" strokeLinecap="round" />
        <path d="M 12 56 Q 26 68 40 56" stroke={PALETTE.ink} strokeWidth={6} fill="none" strokeLinecap="round" />
      </>
    ) : (
      <>
        <circle cx={-26} cy={58} r={11} fill={PALETTE.turmeric} stroke={PALETTE.ink} strokeWidth={5} />
        <circle cx={26} cy={58} r={11} fill={PALETTE.turmeric} stroke={PALETTE.ink} strokeWidth={5} />
      </>
    )}
  </g>
);

/** An open hand holding the turmeric horns — outlined, not a blob. */
export const HandWithBandari: React.FC<{ x: number; y: number; scale?: number; rotate?: number }> = ({
  x, y, scale = 1, rotate = 0,
}) => (
  <g transform={`translate(${x} ${y}) rotate(${rotate}) scale(${scale})`}>
    {/* palm */}
    <path d="M -96 40 C -120 -10 -96 -70 -34 -86 C 20 -100 90 -92 124 -62
             C 152 -36 150 16 120 48 C 88 82 10 96 -44 88 C -76 82 -88 64 -96 40 Z"
      fill={PALETTE.murtiBlue} stroke={PALETTE.ink} strokeWidth={10} strokeLinejoin="round" />
    {/* fingers curling over the top */}
    {[-60, -16, 28, 70].map((fx, i) => (
      <path key={i} d={`M ${fx} -82 C ${fx - 6} -124 ${fx + 34} -128 ${fx + 32} -86`}
        fill={PALETTE.murtiBlue} stroke={PALETTE.ink} strokeWidth={9} strokeLinejoin="round" />
    ))}
    {/* the horns themselves, sitting in the palm */}
    {[0, 1, 2, 3].map((i) => (
      <ellipse key={i} cx={-54 + i * 44} cy={-30 + (i % 2) * 16} rx={31} ry={15}
        transform={`rotate(${-28 + i * 15} ${-54 + i * 44} ${-30})`}
        fill={PALETTE.turmeric} stroke={PALETTE.ink} strokeWidth={6} />
    ))}
  </g>
);

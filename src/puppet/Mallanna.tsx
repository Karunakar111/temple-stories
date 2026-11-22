import React from "react";
import { INK, GOLD, GOLD_DK, Segment, type Pose } from "./rig";
import { Hand } from "./Hand";

/**
 * Mallanna, as a cut-out puppet.
 *
 * Iconography is locked to the real Komuravelli murti (see design/style-guide.md):
 * deep blue skin, a very large upturned handlebar moustache, a tall layered gold
 * kireetam, heavy marigold, green chest ornament over a magenta dhoti.
 * The moustache is non-negotiable — it is how devotees recognise him.
 *
 * Reusable: every episode uses this component. A shot is a pose, not a redraw.
 */

export const SKIN = "#2E63B8";
export const SKIN_DK = "#24509A";
export const CLOTH = "#C2246B";
export const CHEST = "#1F8A4C";
export const MARIGOLD = "#F0A32A";
export const MARIGOLD_DK = "#D4761C";

/** Named parts, so other scenes can reuse pieces without the whole figure. */

export const Kireetam: React.FC = () => (
  <g>
    {/* tall layered crown */}
    {[0, 1, 2, 3].map((i) => {
      const w = 52 - i * 10;
      const y = -78 - i * 20;
      return (
        <path key={i} d={`M ${-w} ${y + 20} L ${-w * 0.74} ${y} L ${w * 0.74} ${y} L ${w} ${y + 20} Z`}
          fill={GOLD} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
      );
    })}
    <circle cy={-160} r={9} fill={GOLD} stroke={INK} strokeWidth={3} />
    {/* gem row */}
    {[-26, 0, 26].map((x, i) => (
      <circle key={i} cx={x} cy={-68} r={6} fill={["#C8342F", "#1F8A4C", "#C8342F"][i]} stroke={INK} strokeWidth={2} />
    ))}
    {/* ear flares */}
    {[-1, 1].map((d) => (
      <path key={d} d={`M ${d * 48} -52 C ${d * 86} -60 ${d * 92} -26 ${d * 62} -14 Z`}
        fill={GOLD} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
    ))}
  </g>
);

export const Moustache: React.FC = () => (
  <path
    d="M 0 16 C -16 12 -34 16 -44 30 C -50 39 -44 48 -34 44
       C -21 39 -12 26 0 26 C 12 26 21 39 34 44
       C 44 48 50 39 44 30 C 34 16 16 12 0 16 Z"
    fill={INK}
  />
);

export const MarigoldGarland: React.FC<{ r?: number }> = ({ r = 1 }) => (
  <g transform={`scale(${r})`}>
    {/* two strands from the shoulders meeting low, the way a garland actually hangs */}
    {[-1, 1].map((side) =>
      Array.from({ length: 11 }).map((_, i) => {
        const t = i / 10;
        const x = side * (46 - t * 34);
        const y = t * t * 112 + t * 26;
        return (
          <circle key={`${side}-${i}`} cx={x} cy={y} r={11 - t * 2}
            fill={i % 2 ? MARIGOLD : MARIGOLD_DK} stroke={INK} strokeWidth={2.5} />
        );
      }),
    )}
    {/* the knot where they meet */}
    <circle cy={142} r={14} fill={MARIGOLD_DK} stroke={INK} strokeWidth={3} />
  </g>
);

const Head: React.FC<{ tilt: number; turn: number }> = ({ tilt, turn }) => (
  <g transform={`rotate(${tilt}) translate(${turn * 2.2} 0)`}>
    {/* face */}
    <ellipse rx={46} ry={50} fill={SKIN} stroke={INK} strokeWidth={3.5} />
    <Kireetam />
    {/* eyes — large and round, the folk-idol look */}
    {[-18, 18].map((x, i) => (
      <g key={i} transform={`translate(${x + turn * 1.6} -8)`}>
        <ellipse rx={12} ry={11} fill="#F4EBDA" stroke={INK} strokeWidth={2.5} />
        <circle r={5.4} fill={INK} />
      </g>
    ))}
    {/* brow */}
    <path d="M -30 -26 C -22 -33 -10 -33 -4 -27 M 30 -26 C 22 -33 10 -33 4 -27"
      stroke={INK} strokeWidth={3.5} fill="none" strokeLinecap="round" />
    {/* third-eye mark */}
    <path d="M 0 -34 L 0 -22" stroke="#C8342F" strokeWidth={5} strokeLinecap="round" />
    <Moustache />
    {/* earrings */}
    {[-1, 1].map((d) => (
      <circle key={d} cx={d * 46} cy={4} r={8} fill={GOLD} stroke={INK} strokeWidth={2.5} />
    ))}
  </g>
);

export const Mallanna: React.FC<{
  pose: Pose;
  x?: number;
  y?: number;
  scale?: number;
  /** What the right hand is holding, parented to the hand. */
  rightHand?: React.ReactNode;
}> = ({ pose, x = 0, y = 0, scale = 1, rightHand }) => {
  const p = (k: string, d = 0) => pose[k] ?? d;

  return (
    <g transform={`translate(${x} ${y + p("rise")}) scale(${scale})`}>
      {/* ── BACK ARM (behind the torso) ───────────────────────────────── */}
      <g transform={`translate(-54 -196)`}>
        <Segment length={78} top={15} bottom={12} fill={SKIN_DK} rotate={p("armLU", 8)}
          jointR={8} band={{ at: 0.86, color: GOLD_DK }}>
          <Segment length={72} top={12} bottom={9.5} fill={SKIN_DK} rotate={p("armLL", 10)} jointR={6.5}>
            <g transform="translate(0 6)"><Hand skin={SKIN_DK} open={0.25} scale={0.92} /></g>
          </Segment>
        </Segment>
      </g>

      {/* ── LEGS ───────────────────────────────────────────────────────── */}
      {([["legR", 22], ["legL", -22]] as const).map(([key, dx]) => (
        <g key={key} transform={`translate(${dx} -74)`}>
          <Segment length={74} top={17} bottom={13} fill={CLOTH} rotate={p(`${key}U`)} jointR={9}>
            <Segment length={70} top={13} bottom={10} fill={SKIN} rotate={p(`${key}L`)} jointR={7}
              band={{ at: 0.92, color: GOLD }}>
              {/* foot */}
              <path d="M -11 0 L 13 0 L 26 18 L -13 18 Z" fill={SKIN_DK} stroke={INK} strokeWidth={3} strokeLinejoin="round" />
            </Segment>
          </Segment>
        </g>
      ))}

      {/* ── DHOTI ──────────────────────────────────────────────────────── */}
      <path d="M -44 -88 L 44 -88 C 52 -56 60 -24 66 4
               C 44 12 22 8 0 8 C -22 8 -44 12 -66 4
               C -60 -24 -52 -56 -44 -88 Z"
        fill={CLOTH} stroke={INK} strokeWidth={3.5} strokeLinejoin="round" />
      {/* hem band, following the drape */}
      <path d="M -64 0 C -42 8 -20 4 0 4 C 20 4 42 8 64 0" fill="none"
        stroke={GOLD} strokeWidth={9} strokeLinecap="round" />
      {/* two pleats, for weight */}
      <path d="M 10 -86 C 8 -50 10 -20 14 2" stroke={INK} strokeWidth={2.5} fill="none" opacity={0.4} />
      <path d="M -14 -86 C -14 -50 -16 -20 -20 2" stroke={INK} strokeWidth={2.5} fill="none" opacity={0.4} />

      {/* ── TORSO ──────────────────────────────────────────────────────── */}
      <g transform={`rotate(${p("chest")})`}>
        {/* chest: broad at the shoulders, drawn in at the waist */}
        <path d="M -56 -202 C -64 -176 -60 -140 -46 -104 C -40 -94 -36 -88 -34 -84
                 L 34 -84 C 36 -88 40 -94 46 -104 C 60 -140 64 -176 56 -202
                 C 40 -216 -40 -216 -56 -202 Z"
          fill={SKIN} stroke={INK} strokeWidth={3.5} strokeLinejoin="round" />
        {/* green chest ornament, as on the murti */}
        <path d="M -36 -190 C -42 -156 -38 -126 -30 -100 L 30 -100 C 38 -126 42 -156 36 -190
                 C 24 -200 -24 -200 -36 -190 Z"
          fill={CHEST} stroke={INK} strokeWidth={3} />
        {/* waist belt */}
        <rect x={-42} y={-96} width={84} height={15} rx={6} fill={GOLD} stroke={INK} strokeWidth={3} />
        {/* necklace */}
        <path d="M -30 -192 C -14 -172 14 -172 30 -192" fill="none" stroke={GOLD} strokeWidth={7} strokeLinecap="round" />

        <g transform="translate(0 -150)">
          <MarigoldGarland r={0.92} />
        </g>

        {/* ── HEAD ─────────────────────────────────────────────────────── */}
        <g transform={`translate(0 -246)`}>
          <Head tilt={p("headTilt")} turn={p("headTurn")} />
        </g>

        {/* ── FRONT ARM (over the torso) ─────────────────────────────── */}
        <g transform={`translate(54 -196)`}>
          <Segment length={78} top={15} bottom={12} fill={SKIN} rotate={p("armRU", -8)}
            jointR={8} band={{ at: 0.86, color: GOLD }}>
            <Segment length={72} top={12} bottom={9.5} fill={SKIN} rotate={p("armRL", -10)} jointR={6.5}>
              {/* hand */}
              <g transform={`translate(0 6) rotate(${p("handR")})`}>
                <Hand skin={SKIN} open={p("handOpen")} holding={rightHand} />
              </g>
            </Segment>
          </Segment>
        </g>
      </g>

    </g>
  );
};

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * The patnam, drawing itself.
 *
 * The Oggu priest lays the patnam *while he sings the story* — so the drawing is
 * the story. This animates that literally: the border bands, then the horse, the
 * dog and the five-headed serpent emerge in powder, in the order the narration
 * names them.
 *
 * Every stroke is a frame-driven dash offset, so it renders deterministically and
 * costs nothing. This is the one shot that could not be bought.
 */

const C = {
  stone: "#141018",
  turmeric: PALETTE.turmeric,
  vermillion: "#C8342F",
  rose: "#D4668A",
  green: "#3E8F4F",
  rice: PALETTE.bone,
};

/** A stroke that draws itself between two frames. */
const Stroke: React.FC<{
  d: string;
  color: string;
  width: number;
  from: number;
  to: number;
  len?: number;
  cap?: "round" | "butt";
}> = ({ d, color, width, from, to, len = 1200, cap = "round" }) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.4, 0, 0.2, 1),
  });
  if (p <= 0) return null;
  return (
    <path
      d={d}
      fill="none"
      stroke={color}
      strokeWidth={width}
      strokeLinecap={cap}
      strokeLinejoin="round"
      strokeDasharray={len}
      strokeDashoffset={len * (1 - p)}
      opacity={0.96}
    />
  );
};

/** Powder grains that settle along a line once it has been laid. */
const Grains: React.FC<{ cx: number; cy: number; r: number; from: number; n?: number; color: string }> = ({
  cx, cy, r, from, n = 26, color,
}) => {
  const frame = useCurrentFrame();
  return (
    <g>
      {Array.from({ length: n }).map((_, i) => {
        const a = (i / n) * Math.PI * 2 + i * 0.7;
        const rr = r + ((Math.sin(i * 91.3) * 0.5 + 0.5) - 0.5) * 26;
        const appear = from + (i % 10) * 2;
        const o = interpolate(frame, [appear, appear + 10], [0, 0.75], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });
        return (
          <circle key={i} cx={cx + Math.cos(a) * rr} cy={cy + Math.sin(a) * rr}
            r={1.6 + (i % 3) * 0.8} fill={color} opacity={o} />
        );
      })}
    </g>
  );
};

export const PatnamDraw: React.FC<{ startAt?: number }> = ({ startAt = 0 }) => {
  const frame = useCurrentFrame() - startAt;

  // The whole drawing breathes very slightly, as if seen from above by someone kneeling.
  const breathe = 1 + Math.sin(frame / 42) * 0.006;
  const reveal = interpolate(frame, [0, 18], [0.86, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <AbsoluteFill style={{ backgroundColor: C.stone, justifyContent: "center", alignItems: "center" }}>
      <svg viewBox="0 0 1080 1080" width="100%" style={{ transform: `scale(${reveal * breathe})` }}>
        {/* 1. the ground is marked out — outer bands */}
        <Stroke d="M 540 90 A 450 450 0 1 1 539 90" color={C.rice} width={7} from={0} to={34} len={2900} />
        <Stroke d="M 540 150 A 390 390 0 1 1 539 150" color={C.turmeric} width={11} from={10} to={46} len={2500} />
        <Stroke d="M 540 215 A 325 325 0 1 1 539 215" color={C.vermillion} width={6} from={22} to={56} len={2100} />

        {/* petal ring */}
        {Array.from({ length: 16 }).map((_, i) => {
          const a = (i / 16) * Math.PI * 2;
          const x = 540 + Math.cos(a) * 358;
          const y = 540 + Math.sin(a) * 358;
          const d = `M ${x} ${y} m -26 0 a 26 26 0 1 0 52 0 a 26 26 0 1 0 -52 0`;
          return <Stroke key={i} d={d} color={C.rose} width={5} from={30 + i * 1.6} to={46 + i * 1.6} len={170} />;
        })}

        {/* 2. the serpent, fanned above — what guarded the turmeric.
               Real patnam work is geometric and symmetrical, not naturalistic, so
               these are built from arcs and straight runs on a centre axis. */}
        <g>
          <Stroke from={60} to={92} color={C.green} width={13} len={700}
            d="M 540 455 C 470 455 436 414 446 364 C 454 322 492 300 540 300" />
          <Stroke from={60} to={92} color={C.green} width={13} len={700}
            d="M 540 455 C 610 455 644 414 634 364 C 626 322 588 300 540 300" />
          {[-2, -1, 0, 1, 2].map((k, i) => {
            const x = 540 + k * 88;
            const y = 300 - (2 - Math.abs(k)) * 34;
            return (
              <g key={i}>
                <Stroke from={86 + i * 5} to={112 + i * 5} color={C.green} width={12} len={260}
                  d={`M 540 320 C ${540 + k * 30} 300 ${x} ${y + 60} ${x} ${y + 26}`} />
                {/* hood */}
                <Stroke from={104 + i * 5} to={128 + i * 5} color={C.green} width={11} len={260}
                  d={`M ${x} ${y + 26} C ${x - 34} ${y + 10} ${x - 30} ${y - 34} ${x} ${y - 34}
                      C ${x + 30} ${y - 34} ${x + 34} ${y + 10} ${x} ${y + 26} Z`} />
                <circle cx={x} cy={y - 6} r={6} fill={C.turmeric}
                  opacity={interpolate(frame, [124 + i * 5, 134 + i * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
              </g>
            );
          })}
        </g>

        {/* 3. the horse, centred and large — the gods' gift */}
        <g>
          {/* body as one bold geometric run */}
          <Stroke from={132} to={178} color={C.turmeric} width={16} len={1700}
            d="M 408 648 L 408 596 C 408 572 424 556 450 556 L 596 556
               C 622 556 640 540 648 516 L 664 468 C 670 448 688 440 702 450
               C 714 458 714 474 704 486 L 686 512
               C 700 520 708 536 708 558 L 708 600 C 708 628 690 648 662 648" />
          {/* four legs, straight and even */}
          <Stroke from={168} to={192} color={C.turmeric} width={14} len={560}
            d="M 432 648 L 432 742 M 506 648 L 506 742 M 614 648 L 614 742 M 686 648 L 686 742" />
          {/* mane and tail as repeated marks, the way powder work repeats a motif */}
          <Stroke from={186} to={206} color={C.vermillion} width={9} len={420}
            d="M 652 506 L 676 488 M 638 528 L 664 514 M 626 548 L 652 538" />
          <Stroke from={192} to={212} color={C.vermillion} width={9} len={300}
            d="M 408 600 C 376 596 358 572 360 540" />
          <circle cx={694} cy={468} r={7} fill={C.rice}
            opacity={interpolate(frame, [178, 188], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        </g>

        {/* 4. the dog, below and smaller — the form he escaped in */}
        <g>
          <Stroke from={214} to={252} color={C.rice} width={13} len={1100}
            d="M 430 858 L 430 826 C 430 810 442 798 460 798 L 566 798
               C 584 798 596 788 602 772 L 612 742 C 616 730 628 726 638 732
               C 646 738 646 748 640 756 L 630 772
               C 640 778 646 788 646 802 L 646 830 C 646 848 634 858 616 858" />
          <Stroke from={244} to={266} color={C.rice} width={11} len={430}
            d="M 448 858 L 448 918 M 500 858 L 500 918 M 578 858 L 578 918 M 630 858 L 630 918" />
          <Stroke from={258} to={276} color={C.rice} width={10} len={240}
            d="M 430 826 C 408 822 396 806 398 786" />
          <circle cx={632} cy={744} r={6} fill={C.turmeric}
            opacity={interpolate(frame, [252, 262], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })} />
        </g>

        {/* powder settling, last */}
        <Grains cx={540} cy={540} r={390} from={276} n={34} color={C.turmeric} />
        <Grains cx={540} cy={540} r={325} from={288} n={26} color={C.vermillion} />
      </svg>
    </AbsoluteFill>
  );
};

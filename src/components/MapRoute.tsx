import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, Easing, spring, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * The route from Hyderabad to the temple, drawn.
 *
 * Deliberately NOT a survey map. Drawing a real state outline by hand would be
 * inaccurate and a wrong map in a temple video is worse than no map. What is
 * accurate here is the *relationship*: Hyderabad at the bottom, the road running
 * north-east through Siddipet, Komuravelli 85 km out. Direction, order and
 * distance are true; the rest is design.
 *
 * Reusable for every episode — change the waypoints and the distance.
 */

export type Waypoint = { t: number; label: string; kind: "origin" | "via" | "destination" };

const ROUTE =
  "M 190 1560 C 300 1430 330 1330 300 1210 C 272 1098 330 1010 450 950 C 560 896 610 810 586 700 C 566 610 620 530 740 470";

/** Point along the route path, for placing markers without hardcoding coordinates. */
const usePointAt = (d: string, t: number) => {
  const ref = React.useRef<SVGPathElement | null>(null);
  const [pt, setPt] = React.useState({ x: 0, y: 0 });
  React.useEffect(() => {
    if (!ref.current) return;
    const len = ref.current.getTotalLength();
    const p = ref.current.getPointAtLength(len * Math.min(Math.max(t, 0), 1));
    setPt({ x: p.x, y: p.y });
  }, [d, t]);
  return { ref, pt };
};

const Marker: React.FC<{
  x: number; y: number; label: string; kind: Waypoint["kind"]; at: number;
}> = ({ x, y, label, kind, at }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - at, fps, config: { damping: 13, mass: 0.5 } });
  if (frame < at) return null;

  const big = kind === "destination";
  const r = big ? 20 : kind === "origin" ? 14 : 9;
  const colour = big ? PALETTE.turmeric : kind === "origin" ? PALETTE.bone : PALETTE.violet;
  const drop = interpolate(s, [0, 1], [-46, 0]);

  return (
    <g transform={`translate(${x} ${y + drop})`} opacity={s}>
      {big ? (
        <circle r={r + 20 + Math.sin(frame / 7) * 4} fill="none"
          stroke={PALETTE.turmeric} strokeWidth={3} opacity={0.4} />
      ) : null}
      <circle r={r * s} fill={colour} />
      {big ? <circle r={r * 0.42} fill={PALETTE.ink} /> : null}
      <text
        x={kind === "origin" ? -28 : 36}
        y={8}
        textAnchor={kind === "origin" ? "end" : "start"}
        fill={big ? PALETTE.turmeric : PALETTE.bone}
        fontSize={big ? 50 : 34}
        fontWeight={big ? 900 : 700}
        opacity={interpolate(s, [0.3, 1], [0, 1])}
      >
        {label}
      </text>
    </g>
  );
};

export const MapRoute: React.FC<{ startAt?: number; durationInFrames: number }> = ({
  startAt = 0,
  durationInFrames,
}) => {
  const frame = useCurrentFrame() - startAt;

  const draw = interpolate(frame, [20, 150], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.bezier(0.3, 0, 0.2, 1),
  });
  const km = Math.round(interpolate(frame, [20, 150], [0, 85], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
    easing: Easing.bezier(0.3, 0, 0.2, 1),
  }));

  // Everything drifts and scales a little as the route draws — the map is being
  // travelled, not displayed.
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.14], { extrapolateRight: "clamp" });
  const ty = interpolate(frame, [0, durationInFrames], [40, -40], { extrapolateRight: "clamp" });
  const gridOpacity = interpolate(frame, [0, 24], [0, 0.17], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const hyd = usePointAt(ROUTE, 0);
  const sid = usePointAt(ROUTE, 0.62);
  const kom = usePointAt(ROUTE, 1);

  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.ink }}>
      <svg viewBox="0 0 1080 1920" width="100%" height="100%"
        style={{ transform: `scale(${scale}) translateY(${ty}px)` }}>
        {/* ground grid */}
        <g opacity={gridOpacity} stroke={PALETTE.violet} strokeWidth={1.5}>
          {Array.from({ length: 13 }).map((_, i) => (
            <line key={`v${i}`} x1={i * 90} y1={0} x2={i * 90} y2={1920} />
          ))}
          {Array.from({ length: 22 }).map((_, i) => (
            <line key={`h${i}`} x1={0} y1={i * 90} x2={1080} y2={i * 90} />
          ))}
        </g>

        {/* the road: a faint full-length ghost, then the travelled part over it */}
        <path d={ROUTE} ref={hyd.ref} fill="none" stroke={PALETTE.violet}
          strokeWidth={6} opacity={0.35} strokeLinecap="round" />
        <path d={ROUTE} ref={sid.ref} fill="none" stroke="transparent" />
        <path d={ROUTE} ref={kom.ref} fill="none" stroke="transparent" />
        <path
          d={ROUTE}
          fill="none"
          stroke={PALETTE.turmeric}
          strokeWidth={9}
          strokeLinecap="round"
          strokeDasharray={2400}
          strokeDashoffset={2400 * (1 - draw)}
        />

        <Marker x={hyd.pt.x} y={hyd.pt.y} label="హైదరాబాద్" kind="origin" at={24} />
        <Marker x={sid.pt.x} y={sid.pt.y} label="సిద్దిపేట" kind="via" at={104} />
        <Marker x={kom.pt.x} y={kom.pt.y} label="కొమురవెల్లి" kind="destination" at={146} />

        {/* distance, counting as the road is travelled */}
        <g transform="translate(540 1770)" textAnchor="middle">
          <text fill={PALETTE.turmeric} fontSize={104} fontWeight={900}
            opacity={interpolate(frame, [24, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
            {km} <tspan fontSize={54} fontWeight={700}>కి.మీ.</tspan>
          </text>
          <text y={56} fill={PALETTE.bone} fontSize={34} fontWeight={600} opacity={0.72}>
            హైదరాబాద్ నుంచి
          </text>
        </g>
      </svg>
    </AbsoluteFill>
  );
};

import React from "react";
import { ART_H, ART_W } from "./Stage";
import { clamp, lerp, mixHex, rand } from "../lib/motion";

/**
 * Passing time through the environment, painted over an existing still.
 * phase: 0 dawn, 0.25 afternoon (the painting exactly as drawn), 0.52 dusk, 0.75 midnight, 1 = next dawn.
 * Nothing about the characters changes: only sky, light colour, sun/moon/stars and lamps.
 */
type Look = {
  top: string;
  hor: string;
  skyOp: number; // how much of the painted sky is replaced
  mul: string; // multiply tint over the whole scene
  mulOp: number;
  bright: number;
  sat: number;
  stars: number;
  lamps: number; // lamp/torch glow strength
};

const LOOKS: [number, Look][] = [
  [0.0, { top: "#6d78b8", hor: "#f4b49a", skyOp: 0.92, mul: "#e6a2a6", mulOp: 0.3, bright: 0.87, sat: 0.92, stars: 0.08, lamps: 0.2 }],
  [0.12, { top: "#9cc0e6", hor: "#f9dcae", skyOp: 0.55, mul: "#f3c39a", mulOp: 0.12, bright: 0.96, sat: 0.98, stars: 0, lamps: 0 }],
  [0.25, { top: "#bcd6ec", hor: "#f6ecc8", skyOp: 0, mul: "#ffffff", mulOp: 0, bright: 1, sat: 1, stars: 0, lamps: 0 }],
  [0.42, { top: "#93acd6", hor: "#ffcf8a", skyOp: 0.65, mul: "#ffb070", mulOp: 0.22, bright: 0.97, sat: 1.05, stars: 0, lamps: 0 }],
  [0.53, { top: "#424a8c", hor: "#ef8656", skyOp: 0.96, mul: "#dd7d5f", mulOp: 0.42, bright: 0.8, sat: 0.92, stars: 0.15, lamps: 0.55 }],
  [0.75, { top: "#0c1330", hor: "#283463", skyOp: 1, mul: "#2c3c8c", mulOp: 0.68, bright: 0.62, sat: 0.6, stars: 1, lamps: 1 }],
  [0.92, { top: "#262c60", hor: "#946689", skyOp: 1, mul: "#4c4d8e", mulOp: 0.56, bright: 0.68, sat: 0.7, stars: 0.5, lamps: 0.7 }],
  [1.0, { top: "#6d78b8", hor: "#f4b49a", skyOp: 0.92, mul: "#e6a2a6", mulOp: 0.3, bright: 0.87, sat: 0.92, stars: 0.08, lamps: 0.2 }],
];

export function lookAt(phase: number): Look {
  const p = ((phase % 1) + 1) % 1;
  let i = 1;
  while (i < LOOKS.length - 1 && LOOKS[i][0] < p) i++;
  const [p0, a] = LOOKS[i - 1];
  const [p1, b] = LOOKS[i];
  const t = clamp((p - p0) / (p1 - p0), 0, 1);
  const s = t * t * (3 - 2 * t);
  return {
    top: mixHex(a.top, b.top, s),
    hor: mixHex(a.hor, b.hor, s),
    skyOp: lerp(a.skyOp, b.skyOp, s),
    mul: mixHex(a.mul, b.mul, s),
    mulOp: lerp(a.mulOp, b.mulOp, s),
    bright: lerp(a.bright, b.bright, s),
    sat: lerp(a.sat, b.sat, s),
    stars: lerp(a.stars, b.stars, s),
    lamps: lerp(a.lamps, b.lamps, s),
  };
}

/** CSS filter for the painting itself at this phase. */
export const gradeFilter = (phase: number) => {
  const l = lookAt(phase);
  return `brightness(${l.bright.toFixed(3)}) saturate(${l.sat.toFixed(3)})`;
};

/** Sky replacement, sun, moon and stars, clipped by an alpha sky mask. */
export const Sky: React.FC<{
  phase: number;
  maskSrc: string;
  box: { x0: number; y0: number; x1: number; y1: number }; // where sun/moon travel
  frame: number;
}> = ({ phase, maskSrc, box, frame }) => {
  const l = lookAt(phase);
  const p = ((phase % 1) + 1) % 1;
  // sun is up for p in (-0.03, 0.55), moon for p in (0.5, 1.02)
  const sunT = (p + 0.03) / 0.58;
  const moonT = (p - 0.5) / 0.52;
  const arc = (t: number) => ({
    x: lerp(box.x0, box.x1, t),
    y: box.y1 - Math.sin(Math.PI * clamp(t, 0, 1)) * (box.y1 - box.y0),
  });
  const sun = arc(sunT);
  const moon = arc(moonT);
  const sunOn = sunT > 0 && sunT < 1;
  const moonOn = moonT > 0 && moonT < 1;
  const sunWarm = 1 - Math.sin(Math.PI * clamp(sunT, 0, 1)); // redder near the horizon
  const mask: React.CSSProperties = {
    WebkitMaskImage: `url(${maskSrc})`,
    maskImage: `url(${maskSrc})`,
    WebkitMaskSize: `${ART_W}px ${ART_H}px`,
    maskSize: `${ART_W}px ${ART_H}px`,
    WebkitMaskRepeat: "no-repeat",
    maskRepeat: "no-repeat",
  };
  const stars = [];
  if (l.stars > 0.01) {
    for (let i = 0; i < 70; i++) {
      const x = rand(i * 13 + 1) * ART_W;
      const y = box.y0 * 0.2 + rand(i * 17 + 5) * (box.y1 - box.y0 * 0.2);
      const tw = 0.55 + 0.45 * Math.sin(frame * (0.15 + rand(i) * 0.25) + i);
      const r = 1.6 + rand(i * 7) * 2.6;
      stars.push(
        <div
          key={i}
          style={{
            position: "absolute",
            left: x - r,
            top: y - r,
            width: r * 2,
            height: r * 2,
            borderRadius: "50%",
            background: "#fff6dc",
            opacity: l.stars * tw,
            boxShadow: `0 0 ${r * 3}px rgba(255,246,220,0.8)`,
          }}
        />,
      );
    }
  }
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: ART_W, height: ART_H, ...mask }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: l.skyOp,
          background: `linear-gradient(180deg, ${l.top} 0%, ${l.hor} ${Math.round((box.y1 / ART_H) * 100) + 4}%)`,
        }}
      />
      {stars}
      {sunOn && (
        <div
          style={{
            position: "absolute",
            left: sun.x - 70,
            top: sun.y - 70,
            width: 140,
            height: 140,
            borderRadius: "50%",
            background: mixHex("#fff4d6", "#ff9a52", sunWarm),
            boxShadow: `0 0 90px 40px ${mixHex("#ffe9b0", "#ff8a40", sunWarm)}88`,
            opacity: clamp(l.skyOp * 1.4, 0, 1),
          }}
        />
      )}
      {moonOn && (
        <div
          style={{
            position: "absolute",
            left: moon.x - 55,
            top: moon.y - 55,
            width: 110,
            height: 110,
            borderRadius: "50%",
            background: "radial-gradient(circle at 40% 40%, #fffbea 0%, #ece6cf 60%, #d9d2b8 100%)",
            boxShadow: "0 0 70px 24px rgba(220,230,255,0.45)",
            opacity: clamp(l.stars * 1.2, 0, 1),
          }}
        />
      )}
    </div>
  );
};

/** Whole-scene light colour: multiply tint (night blue, dusk amber) plus a soft moving sun band. */
export const LightOver: React.FC<{ phase: number }> = ({ phase }) => {
  const l = lookAt(phase);
  const p = ((phase % 1) + 1) % 1;
  const day = clamp(1 - Math.abs(p - 0.25) / 0.25, 0, 1);
  const bandX = lerp(-0.3, 1.3, clamp((p + 0.03) / 0.56, 0, 1)) * ART_W;
  return (
    <>
      <div style={{ position: "absolute", inset: 0, background: l.mul, opacity: l.mulOp, mixBlendMode: "multiply" }} />
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: 0.35 * day,
          mixBlendMode: "soft-light",
          background: `radial-gradient(ellipse 900px 1700px at ${bandX}px ${ART_H * 0.62}px, rgba(255,236,190,1) 0%, rgba(255,236,190,0) 70%)`,
        }}
      />
    </>
  );
};

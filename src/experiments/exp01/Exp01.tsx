import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Art, Layer, Stage } from "./components/Stage";
import { Birds, Bloom, Dust, LampGlow } from "./components/effects";
import { gradeFilter, LightOver, Sky } from "./components/TimeOfDay";
import { KeyPoseCut } from "./components/KeyPoseCut";
import { Caption, ClosingTitle, LocationTitle, useTeluguFont } from "./components/Type";
import { BEATS, CAPTIONS, DURATION, FPS, WORDS } from "./timeline";
import { clamp, easeInOut, flicker, lerp, ramp } from "./lib/motion";

const f = (s: string) => staticFile(`exp01/${s}`);
const XF = 8; // crossfade frames between beats

/** Opacity for a beat that overlaps its neighbours by XF frames. */
const beatOpacity = (frame: number, a: number, b: number, first = false, last = false) => {
  const fa = Math.round(a * FPS);
  const fb = Math.round(b * FPS);
  const inK = first ? 1 : clamp((frame - fa) / XF, 0, 1);
  const outK = last ? 1 : clamp((fb + XF - frame) / XF, 0, 1);
  return Math.min(inK, outK);
};

/* ---------------------------------------------------------- 1. location */
const Location: React.FC<{ frame: number }> = ({ frame }) => {
  const t = frame / FPS;
  const zoom = lerp(1.0, 1.075, easeInOut(clamp(t / 6.6, 0, 1)));
  const temple = { x: 1000, y: 1078 };
  const lampOn = ramp(t, WORDS.place - 0.1, WORDS.place + 0.6);
  return (
    <Stage camera={{ zoom, fx: temple.x, fy: temple.y + 120 }}>
      <Layer depth={0.35} drift={-t * 9}>
        <div style={{ position: "absolute", inset: 0, transform: "scale(1.08)", transformOrigin: "50% 30%" }}>
          <Art src={f("hill-sky.jpg")} />
        </div>
      </Layer>
      <Layer depth={0.5}>
        <Birds
          frame={frame}
          flock={[
            { x0: -80, y0: 720, vx: 120, vy: -6, size: 22, phase: 0 },
            { x0: -170, y0: 770, vx: 116, vy: -4, size: 17, phase: 1.3 },
            { x0: 1650, y0: 600, vx: -95, vy: 3, size: 19, phase: 2.2 },
            { x0: 1760, y0: 655, vx: -101, vy: 2, size: 15, phase: 0.6 },
          ]}
        />
      </Layer>
      <Layer depth={1}>
        <Art src={f("hill-mid.png")} />
        <Bloom x={temple.x} y={temple.y} r={70 + 30 * lampOn} opacity={lampOn * 0.8 * flicker(frame, 5)} />
        <LampGlow lamps={[{ x: temple.x, y: temple.y + 10, r: 34 }]} frame={frame} strength={lampOn} />
      </Layer>
      <Layer depth={1.6}>
        <Art src={f("hill-front.png")} />
      </Layer>
    </Stage>
  );
};

/* ---------------------------------------------------------- 2. passing time */
const PassingTime: React.FC<{ frame: number; t0: number }> = ({ frame, t0 }) => {
  const t = frame / FPS - t0; // local seconds
  const s = WORDS.someTime - t0 - 0.15; // time starts moving on "కొంతకాలం"
  const phase = lerp(0.27, 2.55, easeInOut(clamp((t - s) / 3.9, 0, 1)));
  const zoom = lerp(1.0, 1.05, clamp(t / 7.5, 0, 1));
  return (
    <Stage camera={{ zoom, fx: 870, fy: 1550 }}>
      <Layer depth={1}>
        <div style={{ position: "absolute", inset: 0, filter: gradeFilter(phase) }}>
          <Art src={f("garden.jpg")} />
        </div>
        <Sky phase={phase} frame={frame} maskSrc={f("garden-skymask-alpha.png")} box={{ x0: 60, y0: 70, x1: 1480, y1: 470 }} />
        <LightOver phase={phase} />
      </Layer>
    </Stage>
  );
};

/* ---------------------------------------------------------- 3. key-pose change with a prop */
const LAMPS_SHRINE = [
  { x: 650, y: 1478, r: 70 },
  { x: 1228, y: 1480, r: 70 },
  { x: 603, y: 1925, r: 70 },
  { x: 1278, y: 1923, r: 70 },
  { x: 598, y: 2208, r: 75 },
  { x: 1149, y: 2215, r: 75 },
];

const Offering: React.FC<{ frame: number; t0: number }> = ({ frame, t0 }) => {
  const { fps } = useVideoConfig();
  const t = frame / FPS - t0;
  const cut = Math.round(WORDS.giveCut * FPS);
  const zoom = lerp(1.0, 1.045, easeInOut(clamp(t / 5.6, 0, 1)));
  return (
    <Stage camera={{ zoom, fx: 680, fy: 1560 }}>
      <Layer depth={1}>
        <KeyPoseCut
          frame={frame}
          fps={fps}
          srcA={f("pose-a.jpg")}
          srcB={f("pose-b.jpg")}
          cutAt={cut}
          anticipation={{ x: 452, y: 1410, frames: 18 }}
          impact={{ x: 760, y: 1610 }}
        />
        <LampGlow lamps={LAMPS_SHRINE} frame={frame} strength={0.75} />
        {/* before the cut: a few grains escape his joined palms */}
        <Dust frame={frame} start={cut - 16} count={14} from={{ x: 455, y: 1395, spread: 40 }} rise={45} life={30} emitOver={16} size={6} seed={3} />
        {/* after the cut: the bandari passes from his hands into hers, then hangs and settles */}
        <Dust frame={frame} start={cut} count={70} from={{ x: 700, y: 1600, spread: 90 }} to={{ x: 820, y: 1700, spread: 120 }} travel={14} life={80} emitOver={34} size={7} seed={7} />
        <Dust frame={frame} start={cut + 10} count={26} from={{ x: 800, y: 1660, spread: 180 }} rise={30} life={70} emitOver={60} size={5} seed={11} />
      </Layer>
    </Stage>
  );
};

/* ---------------------------------------------------------- 4. closing */
const Closing: React.FC<{ frame: number; t0: number }> = ({ frame, t0 }) => {
  const t = frame / FPS - t0;
  const zoom = lerp(1.0, 1.06, easeInOut(clamp(t / 3.6, 0, 1)));
  const startF = Math.round(t0 * FPS) - XF;
  return (
    <Stage camera={{ zoom, fx: 768, fy: 1150 }}>
      <Layer depth={1}>
        <Art src={f("deity.jpg")} />
        <LampGlow lamps={[{ x: 273, y: 1372, r: 95 }, { x: 1289, y: 1378, r: 95 }]} frame={frame} strength={0.9} />
        <Dust frame={frame} start={startF} count={110} from={{ x: 768, y: 2150, spread: 1300 }} rise={80} life={100} emitOver={110} size={7} seed={21} />
      </Layer>
    </Stage>
  );
};

/* ---------------------------------------------------------- composition */
export const Exp01: React.FC = () => {
  useTeluguFont();
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const L = BEATS.location;
  const T = BEATS.time;
  const O = BEATS.offering;
  const C = BEATS.closing;
  const span = (a: number, b: number) => ({ from: Math.max(0, Math.round(a * FPS) - XF), durationInFrames: Math.round((b - a) * FPS) + 2 * XF });
  const endFade = 1 - ramp(t, C.b - 0.4, C.b);
  return (
    <AbsoluteFill style={{ backgroundColor: "#0e0810" }}>
      <AbsoluteFill style={{ opacity: endFade }}>
        <Sequence {...span(L.a, L.b)} layout="none">
          <AbsoluteFill style={{ opacity: beatOpacity(frame, L.a, L.b, true) }}>
            <Location frame={frame} />
          </AbsoluteFill>
        </Sequence>
        <Sequence {...span(T.a, T.b)} layout="none">
          <AbsoluteFill style={{ opacity: beatOpacity(frame, T.a, T.b) }}>
            <PassingTime frame={frame} t0={T.a} />
          </AbsoluteFill>
        </Sequence>
        <Sequence {...span(O.a, O.b)} layout="none">
          <AbsoluteFill style={{ opacity: beatOpacity(frame, O.a, O.b) }}>
            <Offering frame={frame} t0={O.a} />
          </AbsoluteFill>
        </Sequence>
        <Sequence {...span(C.a, C.b)} layout="none">
          <AbsoluteFill style={{ opacity: beatOpacity(frame, C.a, C.b, false, true) }}>
            <Closing frame={frame} t0={C.a} />
          </AbsoluteFill>
        </Sequence>
        <LocationTitle t={t} distAt={WORDS.distance + 0.05} districtAt={WORDS.district} nameAt={WORDS.place} outAt={L.b - 0.45} />
        <Caption t={t} lines={CAPTIONS} />
        <ClosingTitle t={t} a1={WORDS.closing1} a2={WORDS.closing2} />
      </AbsoluteFill>
      <Audio src={staticFile("exp01/exp01-mix.wav")} />
    </AbsoluteFill>
  );
};

export const EXP01_FRAMES = DURATION;

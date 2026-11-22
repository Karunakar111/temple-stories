import React from "react";
import { AbsoluteFill, Sequence, Audio, staticFile, getRemotionEnvironment } from "remotion";
import { ChantOpen } from "../components/ChantOpen";
import { MapRoute } from "../components/MapRoute";
import { PALETTE } from "../design/palette";
import timing from "./01-part1-timing.json";

/**
 * The open: chant, then the route in.
 *
 * Both beats are cut to the measured narration — the chant runs exactly as long
 * as the chant is spoken, and the route draws across the location line.
 */
const CHANT = timing.shots[0].durationInFrames;       // 0 – 5.08s
const ROUTE = timing.shots[1].durationInFrames;       // 5.08 – 14.48s

export const Ep01Open: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: PALETTE.ink }}>
    {getRemotionEnvironment().isRendering ? null : (
      <Audio src={staticFile("audio/01-part1.mp3")} />
    )}
    <Sequence durationInFrames={CHANT} name="Chant">
      <ChantOpen durationInFrames={CHANT} />
    </Sequence>
    <Sequence from={CHANT} durationInFrames={ROUTE} name="Map route">
      <MapRoute durationInFrames={ROUTE} />
    </Sequence>
  </AbsoluteFill>
);

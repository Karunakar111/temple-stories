import React from "react";
import { Composition } from "remotion";
import { Episode01 } from "./episodes/Episode01";
import part1 from "./episodes/01-part1-timing.json";
import part2 from "./episodes/01-part2-timing.json";
import { ProofShot } from "./three/ProofShot";
import { PatnamDraw } from "./components/PatnamDraw";
import { Sample } from "./three/Sample";
import { CharacterStill, WalkTest } from "./three/CharacterTest";
import { Ep01Open } from "./episodes/Ep01Open";
import { Ep01Part1 as Ep01Part1Drawn } from "./episodes/Ep01Part1";
import p1t from "./episodes/01-part1-timing.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="Ep01Part1"
        component={Episode01}
        defaultProps={{ part: 1 as const }}
        durationInFrames={part1.durationInFrames}
        fps={part1.fps}
        width={1080}
        height={1920}
      />
      <Composition
        id="Ep01Part2"
        component={Episode01}
        defaultProps={{ part: 2 as const }}
        durationInFrames={part2.durationInFrames}
        fps={part2.fps}
        width={1080}
        height={1920}
      />
      <Composition
        id="ProofShot3D"
        component={ProofShot}
        durationInFrames={150}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="PatnamDraw"
        component={PatnamDraw}
        durationInFrames={330}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Ep01Open"
        component={Ep01Open}
        durationInFrames={p1t.shots[0].durationInFrames + p1t.shots[1].durationInFrames}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Ep01Part1Drawn"
        component={Ep01Part1Drawn}
        durationInFrames={p1t.durationInFrames}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Sample3D"
        component={Sample}
        durationInFrames={270}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition id="CharacterStill" component={CharacterStill}
        durationInFrames={1} fps={30} width={1080} height={1920} />
      <Composition id="WalkTest" component={WalkTest}
        durationInFrames={60} fps={30} width={1080} height={1920} />
    </>
  );
};

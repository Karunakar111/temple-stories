import React from "react";
import { Composition } from "remotion";
import { Episode01 } from "./episodes/Episode01";
import part1 from "./episodes/01-part1-timing.json";
import part2 from "./episodes/01-part2-timing.json";
import { ProofShot } from "./three/ProofShot";

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
    </>
  );
};

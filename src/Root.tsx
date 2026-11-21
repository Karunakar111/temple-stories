import React from "react";
import { Composition } from "remotion";
import { SpinTest } from "./setup-check/SpinTest";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SetupCheck"
        component={SpinTest}
        durationInFrames={90}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};

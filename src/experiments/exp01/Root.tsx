import React from "react";
import { Composition } from "remotion";
import { Exp01, EXP01_FRAMES } from "./Exp01";

export const Exp01Root: React.FC = () => (
  <Composition id="Exp01Animation" component={Exp01} durationInFrames={EXP01_FRAMES} fps={30} width={1080} height={1920} />
);

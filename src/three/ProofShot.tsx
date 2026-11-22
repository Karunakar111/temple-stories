import React from "react";
import { AbsoluteFill } from "remotion";
import { HillFlyover } from "./HillFlyover";
import { AnimatedTitle } from "../components/AnimatedTitle";
import { LocationPin } from "../components/LocationPin";

/** Side-by-side-able proof: real 3D camera + moving crowd + animated Telugu type. */
export const ProofShot: React.FC = () => (
  <AbsoluteFill>
    <HillFlyover />
    <AnimatedTitle text="కొమురవెల్లి" sub="మల్లన్న కొండ" startAt={14} holdFor={78} />
    <AbsoluteFill style={{ opacity: 0.95 }}>
      <LocationPin part={1} />
    </AbsoluteFill>
  </AbsoluteFill>
);

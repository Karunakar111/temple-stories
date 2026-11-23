import React from "react";
import { spring } from "remotion";
import { Art } from "./Stage";
import { Bloom } from "./effects";
import { clamp, ramp } from "../lib/motion";

/**
 * Pose-to-pose change between two DRAWN key poses of the same, registered painting.
 * It is a cut on the action, not in-between animation: no frame is invented.
 * What sells it is borrowed from limited animation:
 *  - anticipation: light gathers where the action will happen before the cut;
 *  - the cut itself lands under a short warm bloom;
 *  - a small settle (overshoot -> rest) on the new pose, as in explainer-video-skill's Character.
 */
export const KeyPoseCut: React.FC<{
  frame: number;
  fps: number;
  srcA: string;
  srcB: string;
  cutAt: number; // frame
  anticipation: { x: number; y: number; frames: number };
  impact: { x: number; y: number };
}> = ({ frame, fps, srcA, srcB, cutAt, anticipation, impact }) => {
  const after = frame >= cutAt;
  const local = frame - cutAt;
  const settle = after ? spring({ frame: local, fps, config: { damping: 9, stiffness: 170 } }) : 0;
  const s = after ? 1 + (1 - settle) * 0.012 : 1;
  const gather = ramp(frame, cutAt - anticipation.frames, cutAt);
  const flash = after ? clamp(1 - local / 9, 0, 1) : clamp((frame - (cutAt - 2)) / 2, 0, 1) * 0.6;
  return (
    <>
      <div style={{ position: "absolute", inset: 0, transformOrigin: `${impact.x}px ${impact.y}px`, transform: `scale(${s})` }}>
        <Art src={after ? srcB : srcA} />
      </div>
      {!after && <Bloom x={anticipation.x} y={anticipation.y} r={60 + 90 * gather} opacity={0.85 * gather} />}
      <Bloom x={impact.x} y={impact.y} r={230 + 120 * flash} opacity={flash * 0.95} />
    </>
  );
};

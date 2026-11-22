import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE } from "../design/palette";
import { Courtyard } from "./lib/Courtyard";
import { Devotee } from "./lib/Devotee";

const hex = (c: string) => new THREE.Color(c);

/**
 * Two tests, deliberately plain.
 *
 * The camera is locked off in both so the only things moving are the character and
 * the light. If the model or the walk is wrong, there is nothing here to hide it.
 */

const FixedCam: React.FC<{ pos: [number, number, number]; look: [number, number, number]; fov?: number }> = ({
  pos, look,
}) => {
  const camera = useThree((s) => s.camera);
  camera.position.set(...pos);
  camera.lookAt(...look);
  camera.updateProjectionMatrix();
  return null;
};

/** Key / fill / rim, plus the courtyard's own lamps. */
const Lighting: React.FC<{ flicker: number }> = ({ flicker }) => (
  <>
    <directionalLight
      position={[9, 8, 7]}
      intensity={3.2}
      color={hex("#ffc275")}
      castShadow
      shadow-mapSize={[2048, 2048]}
      shadow-camera-left={-14}
      shadow-camera-right={14}
      shadow-camera-top={14}
      shadow-camera-bottom={-14}
      shadow-camera-far={60}
      shadow-bias={-0.0006}
    />
    {/* cool bounce from the open sky */}
    <directionalLight position={[-7, 4, -5]} intensity={0.85} color={hex("#7e86c4")} />
    {/* warm rim from behind, separates him from the dark colonnade */}
    <directionalLight position={[-2, 3.5, -9]} intensity={1.5} color={hex("#ffaa55")} />
    <ambientLight intensity={0.34} color={hex("#6a5a86")} />
    <hemisphereLight args={[hex("#ffd9a0"), hex("#241a2c"), 0.45]} />
    <pointLight position={[1.4, 1.6, 1.8]} intensity={1.1 * flicker} distance={6} color={hex("#ffb859")} />
  </>
);

/* ── 1. a well-lit still ─────────────────────────────────────────────────── */

export const CharacterStill: React.FC = () => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "#140e0a" }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ fov: 32, near: 0.1, far: 200 }}>
        <FixedCam pos={[2.05, 1.12, 3.5]} look={[0.05, 0.88, 0.6]} />
        <color attach="background" args={["#140e0a"]} />
        <fog attach="fog" args={["#2a1b14", 22, 70]} />
        <Lighting flicker={1} />
        <Courtyard flicker={1} />
        {/* held at a passing pose — mid-stride, which shows the rig better than a T-pose */}
        <Devotee
          phase={0.18}
          position={[0, 0, 0.6]}
          rotation={[0, 2.5, 0]}
          cloth={PALETTE.bone}
          shawl={PALETTE.turmeric}
          carryPot
        />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

/* ── 2. two seconds of walking, locked off ──────────────────────────────── */

const WALK_SPEED = 1.3;
const STRIDE = 1.5;

export const WalkTest: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const sec = frame / fps;
  const flicker = 0.9 + Math.sin(sec * 11) * 0.06 + Math.sin(sec * 23) * 0.04;

  // He walks across frame, left to right, in front of a static camera.
  const x = -1.35 + sec * WALK_SPEED;
  const phase = (sec * WALK_SPEED) / STRIDE;

  return (
    <AbsoluteFill style={{ backgroundColor: "#140e0a" }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ fov: 34, near: 0.1, far: 200 }}>
        <FixedCam pos={[0, 1.25, 6.4]} look={[0, 0.92, 0.6]} />
        <color attach="background" args={["#140e0a"]} />
        <fog attach="fog" args={["#2a1b14", 22, 70]} />
        <Lighting flicker={flicker} />
        <Courtyard flicker={flicker} />
        <Devotee
          phase={phase}
          position={[x, 0, 1.4]}
          rotation={[0, Math.PI / 2, 0]}
          cloth={PALETTE.bone}
          shawl={PALETTE.turmeric}
          carryPot
        />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

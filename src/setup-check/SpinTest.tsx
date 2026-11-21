import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import {
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  AbsoluteFill,
} from "remotion";

/**
 * Setup verification composition.
 * Purpose: prove that Remotion + React Three Fiber + Three.js render
 * deterministic animated 3D frames on this machine. Not production art.
 */

/** Drives the real camera from the current frame, so renders are deterministic. */
const CameraRig: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const camera = useThree((s) => s.camera);

  const z = interpolate(frame, [0, durationInFrames], [5.6, 4.1]);
  const y = interpolate(frame, [0, durationInFrames], [1.6, 0.8]);
  const x = interpolate(frame, [0, durationInFrames], [2.4, 1.2]);

  camera.position.set(x, y, z);
  camera.lookAt(0, 0.1, 0);
  camera.updateProjectionMatrix();

  return null;
};

const Scene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const spin = t * 1.2;
  const bob = Math.sin(t * 2) * 0.12;

  return (
    <>
      <CameraRig />
      <ambientLight intensity={0.55} color="#ffd9a0" />
      <directionalLight
        position={[4, 6, 3]}
        intensity={2.2}
        color="#ffcf8a"
        castShadow
        shadow-mapSize={[1024, 1024]}
      />
      <directionalLight position={[-4, 2, -3]} intensity={0.45} color="#7aa6ff" />

      {/* Stacked blocks: a stand-in for a stone pillar */}
      <group position={[0, bob, 0]} rotation={[0, spin, 0]}>
        <mesh position={[0, 0.92, 0]} castShadow>
          <boxGeometry args={[1.1, 0.35, 1.1]} />
          <meshStandardMaterial color="#c98b4b" roughness={0.75} />
        </mesh>
        <mesh position={[0, 0, 0]} castShadow>
          <boxGeometry args={[0.9, 1.5, 0.9]} />
          <meshStandardMaterial color="#d9a469" roughness={0.8} />
        </mesh>
        <mesh position={[0, -0.95, 0]} castShadow>
          <boxGeometry args={[1.3, 0.4, 1.3]} />
          <meshStandardMaterial color="#b9793c" roughness={0.85} />
        </mesh>
      </group>

      <mesh position={[0, -1.18, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color="#8a5f3a" roughness={1} />
      </mesh>
    </>
  );
};

export const SpinTest: React.FC = () => {
  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#2a1a12" }}>
      <ThreeCanvas width={width} height={height} shadows>
        <Scene />
      </ThreeCanvas>
      <AbsoluteFill
        style={{
          justifyContent: "flex-end",
          alignItems: "center",
          paddingBottom: 90,
        }}
      >
        <div
          style={{
            color: "#fff4e4",
            fontFamily: "sans-serif",
            fontSize: 40,
            letterSpacing: 1,
          }}
        >
          setup check: Remotion + Three.js
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

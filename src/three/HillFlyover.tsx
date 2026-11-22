import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * Proof shot: a real 3D camera flying up to the shrine.
 *
 * Everything is a pure function of the frame, so it renders deterministically.
 * Geometry is procedural and cheap — no models to download, no credits, and it
 * can be re-staged for any temple in the series by changing numbers.
 */

const hex = (c: string) => new THREE.Color(c);

/** Deterministic pseudo-random so scatter is identical on every render. */
const rand = (i: number, salt = 1) => {
  const x = Math.sin(i * 127.1 * salt + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const CameraRig: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const camera = useThree((s) => s.camera);
  const t = interpolate(frame, [0, durationInFrames], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.33, 0, 0.2, 1), // ease out — settles on the shrine
  });

  // Start low and wide at the foot of the hill, finish high and close on the shrine.
  const radius = interpolate(t, [0, 1], [46, 17]);
  const angle = interpolate(t, [0, 1], [-0.75, -0.16]);
  const height = interpolate(t, [0, 1], [4.5, 15]);

  camera.position.set(Math.sin(angle) * radius, height, Math.cos(angle) * radius);
  camera.lookAt(0, interpolate(t, [0, 1], [5, 11]), 0);
  camera.updateProjectionMatrix();
  return null;
};

/** Stepped hill built from stacked cylinders — reads as rock, costs nothing. */
const Hill: React.FC = () => (
  <group>
    {Array.from({ length: 7 }).map((_, i) => {
      const y = i * 1.5;
      const r = 17 - i * 2.1;
      return (
        <mesh key={i} position={[0, y, 0]} receiveShadow castShadow>
          <cylinderGeometry args={[r, r + 1.5, 1.6, 9]} />
          <meshStandardMaterial
            color={hex(i % 2 ? PALETTE.sienna : PALETTE.amber)}
            roughness={1}
            flatShading
          />
        </mesh>
      );
    })}
  </group>
);

/** The shrine in its rock recess, as the real murti sits. */
const Shrine: React.FC = () => {
  const frame = useCurrentFrame();
  const glow = 1.6 + Math.sin(frame / 9) * 0.35; // a lamp, not a strobe
  return (
    <group position={[0, 10.6, 0]}>
      <mesh castShadow>
        <boxGeometry args={[5.2, 4.2, 4.2]} />
        <meshStandardMaterial color={hex(PALETTE.sienna)} roughness={1} flatShading />
      </mesh>
      {/* stepped vimana */}
      {[0, 1, 2, 3].map((i) => (
        <mesh key={i} position={[0, 2.3 + i * 0.85, 0]} castShadow>
          <boxGeometry args={[4.2 - i * 0.85, 0.85, 4.2 - i * 0.85]} />
          <meshStandardMaterial color={hex(PALETTE.murtiGold)} roughness={0.75} flatShading />
        </mesh>
      ))}
      {/* the dark recess, and the lamp inside it */}
      <mesh position={[0, -0.35, 2.12]}>
        <planeGeometry args={[2.1, 2.9]} />
        <meshBasicMaterial color={hex("#120d18")} />
      </mesh>
      <pointLight position={[0, -0.2, 2.6]} intensity={glow * 11} distance={13} color={hex(PALETTE.turmeric)} />
      <mesh position={[0, -0.7, 2.2]}>
        <sphereGeometry args={[0.3, 10, 10]} />
        <meshBasicMaterial color={hex(PALETTE.turmeric)} />
      </mesh>
    </group>
  );
};

/** Pilgrims climbing — simple forms, but they move, which is the whole point. */
const Pilgrims: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <group>
      {Array.from({ length: 26 }).map((_, i) => {
        // Each walks its own loop up the spiral path.
        const prog = ((frame / fps) * 0.045 + rand(i) ) % 1;
        const y = prog * 10.2;
        const r = 16.2 - prog * 14.4;
        const a = prog * 3.1 + rand(i, 3) * 6.28;
        const bob = Math.abs(Math.sin((frame / fps) * 6 + i)) * 0.18;
        return (
          <group key={i} position={[Math.sin(a) * r, y + 1.1 + bob, Math.cos(a) * r]}>
            <mesh castShadow>
              <capsuleGeometry args={[0.22, 0.6, 3, 6]} />
              <meshStandardMaterial
                color={hex([PALETTE.murtiMagenta, PALETTE.turmeric, PALETTE.murtiGreen, PALETTE.vermillion][i % 4])}
                roughness={1}
                flatShading
              />
            </mesh>
          </group>
        );
      })}
    </group>
  );
};

const Scenery: React.FC = () => (
  <group>
    {Array.from({ length: 40 }).map((_, i) => {
      const a = rand(i, 7) * 6.28;
      const r = 19 + rand(i, 11) * 22;
      const s = 0.7 + rand(i, 13) * 1.5;
      return (
        <mesh key={i} position={[Math.sin(a) * r, s * 0.5, Math.cos(a) * r]} castShadow>
          <dodecahedronGeometry args={[s, 0]} />
          <meshStandardMaterial color={hex(PALETTE.ink)} roughness={1} flatShading />
        </mesh>
      );
    })}
  </group>
);

export const HillFlyover: React.FC = () => {
  const { width, height } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: PALETTE.indigo }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ fov: 42 }}>
        <CameraRig />
        <color attach="background" args={[PALETTE.indigo]} />
        <fog attach="fog" args={[PALETTE.indigo, 40, 95]} />
        <ambientLight intensity={0.5} color={hex(PALETTE.violet)} />
        <directionalLight
          position={[26, 34, 14]}
          intensity={2.6}
          color={hex(PALETTE.turmeric)}
          castShadow
          shadow-mapSize={[1024, 1024]}
        />
        <directionalLight position={[-20, 10, -16]} intensity={0.5} color={hex(PALETTE.murtiBlue)} />
        <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[300, 300]} />
          <meshStandardMaterial color={hex("#3a2418")} roughness={1} />
        </mesh>
        <Hill />
        <Shrine />
        <Pilgrims />
        <Scenery />
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

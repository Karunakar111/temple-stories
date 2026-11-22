import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import * as THREE from "three";
import {
  AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig, Easing, Sequence, spring,
} from "remotion";
import { PALETTE } from "../design/palette";
import { Courtyard } from "./lib/Courtyard";
import { Devotee } from "./lib/Devotee";

const hex = (c: string) => new THREE.Color(c);
const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/* ───────────────────────── Shot A — the courtyard ───────────────────────── */

const WALK_SPEED = 1.35;      // metres per second
const STRIDE_LENGTH = 1.5;    // metres per full cycle

const CourtyardCamera: React.FC<{ walkZ: number }> = ({ walkZ }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const camera = useThree((s) => s.camera);
  const t = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: "clamp" });

  // Tracks alongside and slightly behind, easing in toward him and rising a little.
  const side = interpolate(t, [0, 1], [4.6, 2.3], { easing: Easing.inOut(Easing.quad) });
  const back = interpolate(t, [0, 1], [5.2, 3.4]);
  const high = interpolate(t, [0, 1], [1.95, 1.55]);

  // A touch of handheld so the move doesn't feel mechanical.
  const sec = frame / fps;
  const shakeX = Math.sin(sec * 2.3) * 0.035 + Math.sin(sec * 5.1) * 0.012;
  const shakeY = Math.cos(sec * 1.9) * 0.028;

  camera.position.set(side + shakeX, high + shakeY, walkZ + back);
  camera.lookAt(0.1, 1.08, walkZ - 1.6);
  camera.updateProjectionMatrix();
  return null;
};

const ShotCourtyard: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();
  const sec = frame / fps;

  const walkZ = 6 - sec * WALK_SPEED;
  const phase = (sec * WALK_SPEED) / STRIDE_LENGTH;
  const fade = interpolate(frame, [0, 12, durationInFrames - 10, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity: fade, backgroundColor: "#140e0a" }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ fov: 38, near: 0.1, far: 220 }}>
        <CourtyardCamera walkZ={walkZ} />
        <color attach="background" args={["#140e0a"]} />
        <fog attach="fog" args={["#2a1b14", 18, 62]} />

        {/* low sun raking down the colonnade, which is what makes the bars of light */}
        <directionalLight
          position={[14, 11, 16]}
          intensity={3.1}
          color={hex("#ffbe66")}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-24}
          shadow-camera-right={24}
          shadow-camera-top={24}
          shadow-camera-bottom={-24}
          shadow-camera-far={90}
          shadow-bias={-0.0008}
        />
        <ambientLight intensity={0.42} color={hex("#6a5a86")} />
        <hemisphereLight args={[hex("#ffd9a0"), hex("#2a1b2e"), 0.5]} />

        <Courtyard />

        {/* our devotee */}
        <Devotee
          phase={phase}
          position={[0.1, 0, walkZ]}
          rotation={[0, Math.PI, 0]}
          cloth={PALETTE.bone}
          shawl={PALETTE.turmeric}
          carryPot
        />

        {/* a few others further up the courtyard, at their own speeds */}
        {[
          { x: -2.4, z0: -4, sp: 1.0, cloth: "#c9a978", shawl: PALETTE.vermillion },
          { x: 2.7, z0: -9, sp: 1.18, cloth: "#b9b0a0", shawl: PALETTE.murtiGreen },
          { x: -1.2, z0: -14, sp: 0.92, cloth: "#d8c6a4", shawl: PALETTE.murtiMagenta },
        ].map((p, i) => (
          <Devotee
            key={i}
            phase={(sec * p.sp) / STRIDE_LENGTH + rnd(i, 5)}
            position={[p.x, 0, p.z0 - sec * p.sp]}
            rotation={[0, Math.PI, 0]}
            cloth={p.cloth}
            shawl={p.shawl}
            stride={0.92}
          />
        ))}

        {/* dust in the sun shafts */}
        {Array.from({ length: 60 }).map((_, i) => {
          const y = 0.4 + ((sec * 0.12 + rnd(i, 3)) % 1) * 3.2;
          return (
            <mesh key={i} position={[-7 + rnd(i, 7) * 14, y, walkZ - 2 - rnd(i, 11) * 16]}>
              <sphereGeometry args={[0.012 + rnd(i, 13) * 0.016, 5, 5]} />
              <meshBasicMaterial color={hex(PALETTE.turmeric)} transparent opacity={0.4} />
            </mesh>
          );
        })}
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

/* ───────────────────── Shot B — turmeric from the hand ───────────────────── */

const HandCamera: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const camera = useThree((s) => s.camera);
  const t = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: "clamp" });
  // Start on the hand, then settle down the falling stream — the powder is the
  // subject, the hand is just where it comes from.
  camera.position.set(
    interpolate(t, [0, 1], [0.26, 0.14]),
    interpolate(t, [0, 1], [0.16, -0.34]),
    interpolate(t, [0, 1], [1.15, 0.92]),
  );
  camera.lookAt(0.02, interpolate(t, [0, 1], [0.2, -0.42]), 0);
  camera.updateProjectionMatrix();
  return null;
};

/** A hand, tipped, releasing turmeric. Kept high in frame so the fall is the subject. */
const Hand: React.FC<{ open: number }> = ({ open }) => (
  <group position={[0, 0.46, 0]} rotation={[0.55, -0.4, -0.52 - open * 0.5]}>
    {/* forearm running out of frame */}
    <mesh position={[-0.33, 0.04, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
      <capsuleGeometry args={[0.075, 0.42, 6, 12]} />
      <meshStandardMaterial color={hex("#8a5a3c")} roughness={0.75} />
    </mesh>
    {/* palm */}
    <mesh castShadow>
      <boxGeometry args={[0.22, 0.072, 0.2]} />
      <meshStandardMaterial color={hex("#8a5a3c")} roughness={0.75} />
    </mesh>
    {/* fingers, curling open as the turmeric goes */}
    {[-0.072, -0.024, 0.024, 0.072].map((z, i) => (
      <group key={i} position={[0.1, -0.008, z]} rotation={[0, 0, -0.5 + open * 0.75]}>
        <mesh position={[0.05, 0, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <capsuleGeometry args={[0.019, 0.08, 4, 8]} />
          <meshStandardMaterial color={hex("#8a5a3c")} roughness={0.75} />
        </mesh>
        <group position={[0.108, 0, 0]} rotation={[0, 0, -0.55 + open * 0.5]}>
          <mesh position={[0.038, 0, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
            <capsuleGeometry args={[0.017, 0.06, 4, 8]} />
            <meshStandardMaterial color={hex("#8a5a3c")} roughness={0.75} />
          </mesh>
        </group>
      </group>
    ))}
    {/* thumb */}
    <group position={[0.03, 0.01, -0.1]} rotation={[0, -0.7, -0.3]}>
      <mesh position={[0.05, 0, 0]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <capsuleGeometry args={[0.021, 0.07, 4, 8]} />
        <meshStandardMaterial color={hex("#8a5a3c")} roughness={0.75} />
      </mesh>
    </group>
    {/* the turmeric still sitting in the palm */}
    <mesh position={[0.02, 0.05, 0]} scale={[1, 1 - open * 0.8, 1]}>
      <sphereGeometry args={[0.062, 14, 10, 0, Math.PI * 2, 0, Math.PI / 2.6]} />
      <meshStandardMaterial color={hex("#E8A33D")} roughness={1} />
    </mesh>
  </group>
);

const Turmeric: React.FC<{ release: number }> = ({ release }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sec = frame / fps;
  const N = 420;
  return (
    <group>
      {Array.from({ length: N }).map((_, i) => {
        const born = rnd(i) * 0.9;
        const age = Math.max(0, (sec - 0.45) - born * 0.9);
        if (release <= 0 || age <= 0) return null;
        // a little sideways scatter, gravity below
        const vx = (rnd(i, 3) - 0.5) * 0.28;
        const vz = (rnd(i, 7) - 0.5) * 0.24;
        const x = 0.06 + vx * age;
        const z = vz * age;
        const y = 0.46 - 0.5 * 9.81 * age * age * 0.11 - 0.06;
        if (y < -1.5) return null;
        const r = 0.0045 + rnd(i, 11) * 0.011;
        const fade = Math.min(1, age * 7) * Math.max(0, 1 - Math.max(0, -y - 0.9) * 1.6);
        return (
          <mesh key={i} position={[x, y, z]}>
            <sphereGeometry args={[r, 5, 4]} />
            <meshStandardMaterial
              color={hex(i % 7 === 0 ? "#F5C76B" : "#E8A33D")}
              emissive={hex("#E8A33D")}
              emissiveIntensity={0.28}
              roughness={1}
              transparent
              opacity={fade}
            />
          </mesh>
        );
      })}
    </group>
  );
};

const ShotHand: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();
  const open = interpolate(frame, [8, 34], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const fade = interpolate(frame, [0, 10, durationInFrames - 8, durationInFrames], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ opacity: fade, backgroundColor: "#140d0a" }}>
      <ThreeCanvas width={width} height={height} shadows camera={{ fov: 34, near: 0.01, far: 40 }}>
        <HandCamera />
        <color attach="background" args={["#140d0a"]} />
        <fog attach="fog" args={["#140d0a", 1.6, 4.5]} />
        <directionalLight position={[1.6, 1.8, 1.4]} intensity={4.2} color={hex("#ffcb7a")} castShadow shadow-mapSize={[1024, 1024]} />
        <directionalLight position={[-1.4, 0.4, -0.8]} intensity={0.8} color={hex("#7a6cab")} />
        <ambientLight intensity={0.3} color={hex("#5d4a6b")} />
        <Hand open={open} />
        <Turmeric release={open} />
        {/* the ground it falls toward, barely lit */}
        <mesh position={[0, -1.15, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[14, 14]} />
          <meshStandardMaterial color={hex("#3a2a1e")} roughness={1} />
        </mesh>
      </ThreeCanvas>
    </AbsoluteFill>
  );
};

/* ───────────────────────────── Telugu overlay ───────────────────────────── */

const Caption: React.FC<{ text: string; at: number }> = ({ text, at }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - at, fps, config: { damping: 16, mass: 0.6 } });
  if (frame < at) return null;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 260 }}>
      <div
        style={{
          color: PALETTE.bone,
          fontSize: 58,
          fontWeight: 800,
          textAlign: "center",
          padding: "0 70px",
          opacity: s,
          transform: `translateY(${interpolate(s, [0, 1], [26, 0])}px)`,
          textShadow: "0 6px 30px rgba(0,0,0,0.95)",
        }}
      >
        {text}
      </div>
    </AbsoluteFill>
  );
};

/* ──────────────────────────────── Sample ────────────────────────────────── */

const A = 165; // 5.5s courtyard
const B = 105; // 3.5s hand

export const Sample: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "#0d0908" }}>
    <Sequence durationInFrames={A} name="Courtyard">
      <ShotCourtyard />
      <Caption text="సిద్దిపేట జిల్లా — కొమురవెల్లి కొండ" at={26} />
    </Sequence>
    <Sequence from={A} durationInFrames={B} name="Turmeric">
      <ShotHand />
      <Caption text="ఇక్కడ మీరు చల్లే ఈ పసుపు" at={22} />
    </Sequence>
  </AbsoluteFill>
);

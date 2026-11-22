import React from "react";
import * as THREE from "three";
import { PALETTE } from "../../design/palette";

const hex = (c: string) => new THREE.Color(c);
const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** A South Indian temple courtyard: flagstones, a colonnade, a shrine, steps. */

const Pillar: React.FC<{ position: [number, number, number] }> = ({ position }) => (
  <group position={position}>
    <mesh position={[0, 0.12, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.72, 0.24, 0.72]} />
      <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
    </mesh>
    <mesh position={[0, 1.7, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.46, 2.9, 0.46]} />
      <meshStandardMaterial color={hex("#7d6048")} roughness={1} />
    </mesh>
    {/* carved bands — cheap, but they catch the light and read as stone */}
    {[0.8, 1.6, 2.4].map((y, i) => (
      <mesh key={i} position={[0, y, 0]} castShadow>
        <boxGeometry args={[0.54, 0.1, 0.54]} />
        <meshStandardMaterial color={hex("#8d6c4f")} roughness={1} />
      </mesh>
    ))}
    <mesh position={[0, 3.26, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.78, 0.32, 0.78]} />
      <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
    </mesh>
    <mesh position={[0, 3.6, 0]} castShadow>
      <boxGeometry args={[0.95, 0.36, 0.95]} />
      <meshStandardMaterial color={hex("#7d6048")} roughness={1} />
    </mesh>
  </group>
);

export const Courtyard: React.FC = () => (
  <group>
    {/* flagstone floor */}
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[80, 120]} />
      <meshStandardMaterial color={hex("#56402f")} roughness={1} />
    </mesh>
    {Array.from({ length: 22 }).map((_, r) =>
      Array.from({ length: 9 }).map((_, c) => {
        const x = -8 + c * 2;
        const z = 10 - r * 2;
        const shade = 0.86 + rnd(r * 9 + c) * 0.22;
        return (
          <mesh key={`${r}-${c}`} position={[x, 0.012, z]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[1.88, 1.88]} />
            <meshStandardMaterial color={hex("#6a5038").clone().multiplyScalar(shade)} roughness={1} />
          </mesh>
        );
      }),
    )}

    {/* colonnade both sides */}
    {Array.from({ length: 9 }).map((_, i) => (
      <React.Fragment key={i}>
        <Pillar position={[-5.6, 0, 8 - i * 4]} />
        <Pillar position={[5.6, 0, 8 - i * 4]} />
      </React.Fragment>
    ))}

    {/* roof slabs over the colonnade, so the light breaks into bars across the floor */}
    {[-5.6, 5.6].map((x, i) => (
      <mesh key={i} position={[x, 3.95, -8]} castShadow receiveShadow>
        <boxGeometry args={[2.6, 0.3, 40]} />
        <meshStandardMaterial color={hex("#5d4433")} roughness={1} />
      </mesh>
    ))}

    {/* steps up to the shrine */}
    {Array.from({ length: 5 }).map((_, i) => (
      <mesh key={i} position={[0, 0.14 + i * 0.26, -22 - i * 0.9]} receiveShadow castShadow>
        <boxGeometry args={[9 - i * 0.5, 0.28, 1.6]} />
        <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
      </mesh>
    ))}

    {/* the shrine, set into its rock face */}
    <group position={[0, 0, -27.5]}>
      <mesh position={[0, 2.1, 0]} castShadow receiveShadow>
        <boxGeometry args={[7.2, 4.2, 4]} />
        <meshStandardMaterial color={hex("#74583f")} roughness={1} />
      </mesh>
      {[0, 1, 2, 3, 4].map((i) => (
        <mesh key={i} position={[0, 4.4 + i * 0.72, 0]} castShadow>
          <boxGeometry args={[5.8 - i * 1.0, 0.72, 3.2 - i * 0.5]} />
          <meshStandardMaterial color={hex(PALETTE.murtiGold)} roughness={0.7} metalness={0.15} />
        </mesh>
      ))}
      {/* the dark doorway, and the lamp inside it */}
      <mesh position={[0, 1.6, 2.02]}>
        <planeGeometry args={[1.8, 2.8]} />
        <meshBasicMaterial color={hex("#0d0810")} />
      </mesh>
      <pointLight position={[0, 1.5, 2.4]} intensity={9} distance={9} color={hex(PALETTE.turmeric)} />
      {/* rock face behind */}
      <mesh position={[0, 5, -4]} castShadow receiveShadow>
        <dodecahedronGeometry args={[9, 0]} />
        <meshStandardMaterial color={hex("#4a382a")} roughness={1} flatShading />
      </mesh>
    </group>
  </group>
);

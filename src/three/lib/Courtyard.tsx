import React from "react";
import * as THREE from "three";
import { PALETTE } from "../../design/palette";

const hex = (c: string) => new THREE.Color(c);
const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 127.1 * s + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** A South Indian temple courtyard: flagstones, a colonnade, a shrine, steps. */

const Pillar: React.FC<{ position: [number, number, number]; flip?: boolean }> = ({
  position, flip = false,
}) => (
  <group position={position} rotation={[0, flip ? Math.PI : 0, 0]}>
    {/* stepped base — three mouldings, which is what reads as masonry */}
    <mesh position={[0, 0.07, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.86, 0.14, 0.86]} />
      <meshStandardMaterial color={hex("#5d4433")} roughness={1} />
    </mesh>
    <mesh position={[0, 0.2, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.74, 0.12, 0.74]} />
      <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
    </mesh>
    <mesh position={[0, 0.31, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.62, 0.1, 0.62]} />
      <meshStandardMaterial color={hex("#74583f")} roughness={1} />
    </mesh>

    {/* shaft — square at the base, octagonal above, the usual Deccan treatment */}
    <mesh position={[0, 0.75, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.48, 0.78, 0.48]} />
      <meshStandardMaterial color={hex("#7d6048")} roughness={1} />
    </mesh>
    <mesh position={[0, 2.0, 0]} rotation={[0, Math.PI / 8, 0]} castShadow receiveShadow>
      <cylinderGeometry args={[0.23, 0.25, 1.74, 8]} />
      <meshStandardMaterial color={hex("#846a4f")} roughness={1} />
    </mesh>
    {/* carved bands up the shaft */}
    {[1.2, 1.72, 2.26, 2.74].map((y, i) => (
      <mesh key={i} position={[0, y, 0]} rotation={[0, Math.PI / 8, 0]} castShadow>
        <cylinderGeometry args={[0.275, 0.275, 0.07, 8]} />
        <meshStandardMaterial color={hex("#96785a")} roughness={1} />
      </mesh>
    ))}

    {/* capital */}
    <mesh position={[0, 2.98, 0]} castShadow receiveShadow>
      <cylinderGeometry args={[0.34, 0.26, 0.2, 8]} />
      <meshStandardMaterial color={hex("#74583f")} roughness={1} />
    </mesh>
    <mesh position={[0, 3.16, 0]} castShadow receiveShadow>
      <boxGeometry args={[0.82, 0.18, 0.82]} />
      <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
    </mesh>

    {/* corbel brackets reaching out to the beam — the detail that sells a colonnade */}
    {[-1, 1].map((d) => (
      <mesh key={d} position={[0, 3.34, d * 0.34]} rotation={[d * 0.5, 0, 0]} castShadow>
        <boxGeometry args={[0.46, 0.5, 0.18]} />
        <meshStandardMaterial color={hex("#846a4f")} roughness={1} />
      </mesh>
    ))}
    <mesh position={[0, 3.58, 0]} castShadow receiveShadow>
      <boxGeometry args={[1.0, 0.22, 1.0]} />
      <meshStandardMaterial color={hex("#7d6048")} roughness={1} />
    </mesh>
  </group>
);

/** Oil lamp on a post — gives the colonnade its own small warm sources. */
const Lamp: React.FC<{ position: [number, number, number]; flicker: number }> = ({ position, flicker }) => (
  <group position={position}>
    <mesh castShadow>
      <cylinderGeometry args={[0.03, 0.045, 1.1, 8]} />
      <meshStandardMaterial color={hex("#3d2c20")} roughness={1} />
    </mesh>
    <mesh position={[0, 0.6, 0]} castShadow>
      <cylinderGeometry args={[0.11, 0.07, 0.1, 12]} />
      <meshStandardMaterial color={hex("#9a6b2e")} roughness={0.55} metalness={0.5} />
    </mesh>
    <mesh position={[0, 0.69, 0]}>
      <sphereGeometry args={[0.05 * flicker, 8, 8]} />
      <meshBasicMaterial color={hex("#ffd27a")} />
    </mesh>
    <pointLight position={[0, 0.72, 0]} intensity={2.6 * flicker} distance={5.5} color={hex("#ffb859")} />
  </group>
);

export const Courtyard: React.FC<{ flicker?: number }> = ({ flicker = 1 }) => (
  <group>
    {/* flagstone floor, with course-by-course tonal variation */}
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[80, 140]} />
      <meshStandardMaterial color={hex("#4e3a2b")} roughness={1} />
    </mesh>
    {Array.from({ length: 26 }).map((_, r) =>
      Array.from({ length: 11 }).map((_, c) => {
        const x = -10 + c * 2;
        const z = 10 - r * 2;
        const shade = 0.84 + rnd(r * 11 + c) * 0.26;
        return (
          <mesh key={`${r}-${c}`} position={[x, 0.014, z]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
            <planeGeometry args={[1.9, 1.9]} />
            <meshStandardMaterial color={hex("#6a5038").clone().multiplyScalar(shade)} roughness={1} />
          </mesh>
        );
      }),
    )}

    {/* a patnam laid on the courtyard floor — rings of powder */}
    {[1.5, 1.15, 0.8].map((r, i) => (
      <mesh key={i} position={[0, 0.02, 2]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[r - 0.07, r, 36]} />
        <meshStandardMaterial
          color={hex([PALETTE.bone, PALETTE.turmeric, PALETTE.vermillion][i])}
          roughness={1}
        />
      </mesh>
    ))}

    {/* colonnade */}
    {Array.from({ length: 10 }).map((_, i) => (
      <React.Fragment key={i}>
        <Pillar position={[-5.6, 0, 8 - i * 4]} />
        <Pillar position={[5.6, 0, 8 - i * 4]} flip />
      </React.Fragment>
    ))}

    {/* beams running the length, plus rafters across — real roof structure */}
    {[-5.6, 5.6].map((x, i) => (
      <group key={i}>
        <mesh position={[x, 3.78, -10]} castShadow receiveShadow>
          <boxGeometry args={[1.12, 0.26, 44]} />
          <meshStandardMaterial color={hex("#5d4433")} roughness={1} />
        </mesh>
        <mesh position={[x, 4.16, -10]} castShadow receiveShadow>
          <boxGeometry args={[2.9, 0.22, 44]} />
          <meshStandardMaterial color={hex("#4a3628")} roughness={1} />
        </mesh>
        {Array.from({ length: 22 }).map((_, k) => (
          <mesh key={k} position={[x, 3.98, 10 - k * 2]} castShadow>
            <boxGeometry args={[2.6, 0.12, 0.14]} />
            <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
          </mesh>
        ))}
      </group>
    ))}

    {/* outer walls behind the colonnade, so light does not leak into nothing */}
    {[-7.6, 7.6].map((x, i) => (
      <mesh key={i} position={[x, 2.1, -10]} receiveShadow castShadow>
        <boxGeometry args={[0.5, 4.2, 44]} />
        <meshStandardMaterial color={hex("#5a4532")} roughness={1} />
      </mesh>
    ))}

    {/* lamps along the colonnade */}
    {[2, -4, -10, -16].map((z, i) => (
      <React.Fragment key={i}>
        <Lamp position={[-4.5, 0.55, z]} flicker={flicker} />
        <Lamp position={[4.5, 0.55, z]} flicker={2 - flicker} />
      </React.Fragment>
    ))}

    {/* steps up to the shrine, with a nosing on each */}
    {Array.from({ length: 6 }).map((_, i) => (
      <group key={i}>
        <mesh position={[0, 0.15 + i * 0.3, -22 - i * 1.0]} receiveShadow castShadow>
          <boxGeometry args={[9.4 - i * 0.55, 0.3, 1.7]} />
          <meshStandardMaterial color={hex("#6b513c")} roughness={1} />
        </mesh>
        <mesh position={[0, 0.3 + i * 0.3, -21.2 - i * 1.0]} receiveShadow castShadow>
          <boxGeometry args={[9.4 - i * 0.55, 0.06, 0.16]} />
          <meshStandardMaterial color={hex("#8a6c4f")} roughness={1} />
        </mesh>
      </group>
    ))}

    {/* the shrine in its rock face */}
    <group position={[0, 0, -29]}>
      <mesh position={[0, 2.3, 0]} castShadow receiveShadow>
        <boxGeometry args={[7.6, 4.6, 4.2]} />
        <meshStandardMaterial color={hex("#74583f")} roughness={1} />
      </mesh>
      {Array.from({ length: 6 }).map((_, i) => (
        <mesh key={i} position={[0, 4.8 + i * 0.66, 0]} castShadow>
          <boxGeometry args={[6.0 - i * 0.9, 0.66, 3.4 - i * 0.46]} />
          <meshStandardMaterial color={hex(PALETTE.murtiGold)} roughness={0.62} metalness={0.22} />
        </mesh>
      ))}
      <mesh position={[0, 8.95, 0]} castShadow>
        <sphereGeometry args={[0.5, 14, 12]} />
        <meshStandardMaterial color={hex(PALETTE.murtiGold)} roughness={0.45} metalness={0.5} />
      </mesh>
      <mesh position={[0, 1.7, 2.12]}>
        <planeGeometry args={[1.9, 3.0]} />
        <meshBasicMaterial color={hex("#0b0710")} />
      </mesh>
      <pointLight position={[0, 1.6, 2.5]} intensity={13 * flicker} distance={11} color={hex(PALETTE.turmeric)} />
      {/* doorway frame */}
      {[-1.12, 1.12].map((x, i) => (
        <mesh key={i} position={[x, 1.7, 2.14]} castShadow>
          <boxGeometry args={[0.34, 3.3, 0.24]} />
          <meshStandardMaterial color={hex(PALETTE.murtiGold)} roughness={0.6} metalness={0.3} />
        </mesh>
      ))}
      <mesh position={[0, 3.45, 2.14]} castShadow>
        <boxGeometry args={[2.6, 0.34, 0.24]} />
        <meshStandardMaterial color={hex(PALETTE.murtiGold)} roughness={0.6} metalness={0.3} />
      </mesh>
      {/* rock the shrine is cut into */}
      <mesh position={[-6, 4, -3]} castShadow receiveShadow>
        <dodecahedronGeometry args={[7.5, 0]} />
        <meshStandardMaterial color={hex("#4a382a")} roughness={1} flatShading />
      </mesh>
      <mesh position={[6.5, 3.4, -3.5]} castShadow receiveShadow>
        <dodecahedronGeometry args={[6.6, 0]} />
        <meshStandardMaterial color={hex("#453425")} roughness={1} flatShading />
      </mesh>
      <mesh position={[0, 6.5, -6]} castShadow receiveShadow>
        <dodecahedronGeometry args={[9, 0]} />
        <meshStandardMaterial color={hex("#3e2f22")} roughness={1} flatShading />
      </mesh>
    </group>
  </group>
);

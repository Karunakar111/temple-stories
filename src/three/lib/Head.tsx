import React from "react";
import * as THREE from "three";

const hex = (c: string) => new THREE.Color(c);

/**
 * A head with an actual face.
 *
 * The previous version was a capsule with a half-sphere of hair, which is why the
 * characters read as prototypes. This builds a skull, brow, nose, lips, ears and
 * eyes with lids — still low-poly, but with the landmarks that make a face read as
 * a face rather than a blank.
 */
export const Head: React.FC<{ skin: string; hair?: string; mark?: string }> = ({
  skin,
  hair = "#140f0c",
  mark = "#E8A33D",
}) => {
  const skinMat = <meshStandardMaterial color={hex(skin)} roughness={0.72} />;
  return (
    <group>
      {/* skull — squashed sphere, slightly flattened at the back */}
      <mesh castShadow scale={[0.92, 1.06, 1]}>
        <sphereGeometry args={[0.102, 18, 16]} />
        {skinMat}
      </mesh>
      {/* jaw */}
      <mesh position={[0, -0.055, 0.012]} scale={[0.82, 0.72, 0.92]} castShadow>
        <sphereGeometry args={[0.092, 14, 12]} />
        {skinMat}
      </mesh>

      {/* brow ridge — the single biggest thing that makes a low-poly face read */}
      <mesh position={[0, 0.022, 0.082]} rotation={[0.18, 0, 0]} castShadow>
        <boxGeometry args={[0.14, 0.022, 0.03]} />
        {skinMat}
      </mesh>

      {/* eyes: socket, white, iris, upper lid */}
      {[-0.038, 0.038].map((x, i) => (
        <group key={i} position={[x, -0.002, 0.079]}>
          <mesh>
            <sphereGeometry args={[0.019, 12, 10]} />
            <meshStandardMaterial color={hex("#efe6d8")} roughness={0.4} />
          </mesh>
          <mesh position={[0, 0, 0.014]}>
            <sphereGeometry args={[0.0092, 10, 8]} />
            <meshStandardMaterial color={hex("#241713")} roughness={0.3} />
          </mesh>
          {/* lid, sitting a little low so the eye isn't staring */}
          <mesh position={[0, 0.009, 0.004]} rotation={[0.3, 0, 0]}>
            <sphereGeometry args={[0.0205, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2]} />
            {skinMat}
          </mesh>
        </group>
      ))}

      {/* nose — bridge and tip */}
      <mesh position={[0, -0.016, 0.088]} rotation={[0.26, 0, 0]} castShadow>
        <boxGeometry args={[0.025, 0.055, 0.03]} />
        {skinMat}
      </mesh>
      <mesh position={[0, -0.042, 0.098]} castShadow>
        <sphereGeometry args={[0.018, 10, 8]} />
        {skinMat}
      </mesh>

      {/* mouth */}
      <mesh position={[0, -0.07, 0.082]} rotation={[0.1, 0, 0]}>
        <boxGeometry args={[0.042, 0.009, 0.012]} />
        <meshStandardMaterial color={hex("#6b3a32")} roughness={0.6} />
      </mesh>

      {/* ears */}
      {[-0.094, 0.094].map((x, i) => (
        <mesh key={i} position={[x, -0.012, 0.004]} rotation={[0, 0, i ? -0.2 : 0.2]} scale={[0.5, 1, 0.7]} castShadow>
          <sphereGeometry args={[0.028, 10, 8]} />
          {skinMat}
        </mesh>
      ))}

      {/* hair — a shaped cap that meets the brow, plus a short nape */}
      <mesh position={[0, 0.016, -0.006]} scale={[1, 0.94, 1.03]} castShadow>
        <sphereGeometry args={[0.106, 16, 12, 0, Math.PI * 2, 0, Math.PI * 0.56]} />
        <meshStandardMaterial color={hex(hair)} roughness={1} />
      </mesh>
      <mesh position={[0, -0.016, -0.055]} scale={[0.86, 0.72, 0.6]} castShadow>
        <sphereGeometry args={[0.1, 12, 10]} />
        <meshStandardMaterial color={hex(hair)} roughness={1} />
      </mesh>

      {/* turmeric mark */}
      <mesh position={[0, 0.042, 0.088]} rotation={[0.2, 0, 0]}>
        <cylinderGeometry args={[0.009, 0.009, 0.004, 10]} />
        <meshStandardMaterial color={hex(mark)} roughness={0.8} emissive={hex(mark)} emissiveIntensity={0.18} />
      </mesh>
    </group>
  );
};

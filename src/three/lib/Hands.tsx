import React from "react";
import * as THREE from "three";

const hex = (c: string) => new THREE.Color(c);

/** A hand with a palm, four fingers and a thumb. Small, but no longer a stump. */
export const SimpleHand: React.FC<{ skin: string; curl?: number; scale?: number }> = ({
  skin, curl = 0.5, scale = 1,
}) => {
  const mat = <meshStandardMaterial color={hex(skin)} roughness={0.72} />;
  return (
    <group scale={scale}>
      <mesh castShadow scale={[0.62, 1, 1]}>
        <boxGeometry args={[0.046, 0.064, 0.034]} />
        {mat}
      </mesh>
      {[-0.012, -0.0005, 0.011, 0.022].map((z, i) => (
        <group key={i} position={[0.004, -0.032, z]} rotation={[0, 0, curl * 0.9]}>
          <mesh position={[0, -0.016, 0]} castShadow>
            <capsuleGeometry args={[0.0062, 0.018, 3, 6]} />
            {mat}
          </mesh>
          <group position={[0, -0.034, 0]} rotation={[0, 0, curl * 0.8]}>
            <mesh position={[0, -0.012, 0]} castShadow>
              <capsuleGeometry args={[0.0056, 0.014, 3, 6]} />
              {mat}
            </mesh>
          </group>
        </group>
      ))}
      <group position={[-0.016, -0.012, -0.02]} rotation={[0, 0, 0.7 + curl * 0.3]}>
        <mesh position={[0, -0.016, 0]} castShadow>
          <capsuleGeometry args={[0.0072, 0.02, 3, 6]} />
          {mat}
        </mesh>
      </group>
    </group>
  );
};

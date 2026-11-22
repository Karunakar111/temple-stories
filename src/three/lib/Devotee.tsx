import React from "react";
import * as THREE from "three";
import { PALETTE } from "../../design/palette";
import { Head } from "./Head";
import { SimpleHand } from "./Hands";

/**
 * A walking devotee, rigged procedurally.
 *
 * No model file and no animation clip: the body is built from primitives and every
 * joint angle is a function of one phase value, so the walk is deterministic and
 * every parameter is tunable by hand.
 *
 * The cycle follows the standard four contacts — contact, down, passing, up — with
 * the knee lagging the thigh, the arms opposing the legs, and the pelvis bobbing at
 * twice stride frequency. That lag is what stops a walk reading as a puppet.
 */

const hex = (c: string) => new THREE.Color(c);

export type DevoteeProps = {
  /** Walk phase in cycles. 1.0 = one full stride. */
  phase: number;
  position?: [number, number, number];
  rotation?: [number, number, number];
  cloth?: string;
  shawl?: string;
  skin?: string;
  /** 0 = standing still, 1 = full stride. */
  stride?: number;
  carryPot?: boolean;
};

const Limb: React.FC<{
  length: number; radius: number; color: string; children?: React.ReactNode;
}> = ({ length, radius, color, children }) => (
  <group>
    <mesh position={[0, -length / 2, 0]} castShadow>
      <capsuleGeometry args={[radius, length - radius * 2, 4, 8]} />
      <meshStandardMaterial color={hex(color)} roughness={0.85} />
    </mesh>
    <group position={[0, -length, 0]}>{children}</group>
  </group>
);

export const Devotee: React.FC<DevoteeProps> = ({
  phase,
  position = [0, 0, 0],
  rotation = [0, 0, 0],
  cloth = PALETTE.bone,
  shawl = PALETTE.turmeric,
  skin = "#8a5a3c",
  stride = 1,
  carryPot = false,
}) => {
  const t = phase * Math.PI * 2;
  const s = stride;

  // Legs: thigh leads, knee lags by ~0.35 of a cycle and only ever bends one way.
  const thighL = Math.sin(t) * 0.62 * s;
  const thighR = Math.sin(t + Math.PI) * 0.62 * s;
  const kneeL = Math.max(0, Math.sin(t - 1.1)) * 1.15 * s;
  const kneeR = Math.max(0, Math.sin(t + Math.PI - 1.1)) * 1.15 * s;
  const ankleL = -Math.sin(t - 0.5) * 0.3 * s;
  const ankleR = -Math.sin(t + Math.PI - 0.5) * 0.3 * s;

  // Arms oppose the legs; the elbow trails the shoulder.
  const armL = Math.sin(t + Math.PI) * 0.5 * s;
  const armR = Math.sin(t) * 0.5 * s;
  const elbowL = Math.max(0, Math.sin(t + Math.PI - 0.8)) * 0.5 * s;
  const elbowR = Math.max(0, Math.sin(t - 0.8)) * 0.5 * s;

  // Pelvis bobs at double frequency and rolls side to side once per cycle.
  const bob = -Math.abs(Math.cos(t)) * 0.052 * s;
  const sway = Math.sin(t) * 0.045 * s;
  const pelvisTwist = Math.sin(t) * 0.14 * s;
  const chestTwist = -pelvisTwist * 0.75;

  return (
    <group position={position} rotation={rotation as unknown as THREE.Euler["toArray"] extends never ? never : [number, number, number]}>
      <group position={[0, 0.92 + bob, 0]} rotation={[0, 0, sway]}>
        {/* pelvis */}
        <group rotation={[0, pelvisTwist, 0]}>
          {/* dhoti — a lathed skirt with a hem, which is what gives the silhouette */}
          <mesh castShadow receiveShadow position={[0, -0.02, 0]}>
            <latheGeometry
              args={[
                [
                  new THREE.Vector2(0.02, 0.1),
                  new THREE.Vector2(0.15, 0.08),
                  new THREE.Vector2(0.165, -0.02),
                  new THREE.Vector2(0.185, -0.16),
                  new THREE.Vector2(0.2, -0.3),
                  new THREE.Vector2(0.192, -0.33),
                  new THREE.Vector2(0.02, -0.33),
                ],
                18,
              ]}
            />
            <meshStandardMaterial color={hex(cloth)} roughness={0.95} side={THREE.DoubleSide} />
          </mesh>
          {/* waist cord */}
          <mesh position={[0, 0.06, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <torusGeometry args={[0.152, 0.012, 6, 20]} />
            <meshStandardMaterial color={hex(PALETTE.vermillion)} roughness={1} />
          </mesh>

          {/* legs */}
          {([[-0.11, thighL, kneeL, ankleL], [0.11, thighR, kneeR, ankleR]] as const).map(
            ([x, thigh, knee, ankle], i) => (
              <group key={i} position={[x, -0.04, 0]} rotation={[thigh, 0, 0]}>
                <Limb length={0.44} radius={0.075} color={cloth}>
                  <group rotation={[-knee, 0, 0]}>
                    <Limb length={0.42} radius={0.06} color={skin}>
                      <group rotation={[ankle, 0, 0]}>
                        <mesh position={[0, -0.025, 0.06]} castShadow>
                          <boxGeometry args={[0.1, 0.05, 0.22]} />
                          <meshStandardMaterial color={hex("#4a3328")} roughness={1} />
                        </mesh>
                      </group>
                    </Limb>
                  </group>
                </Limb>
              </group>
            ),
          )}
        </group>

        {/* torso */}
        <group position={[0, 0.3, 0]} rotation={[0.06, chestTwist, 0]}>
          {/* chest — lathed profile so it tapers from shoulder to waist like a body,
              not a capsule. Points are (radius, height) up the torso. */}
          <mesh castShadow receiveShadow>
            <latheGeometry
              args={[
                [
                  new THREE.Vector2(0.015, -0.2),
                  new THREE.Vector2(0.125, -0.18),
                  new THREE.Vector2(0.138, -0.08),
                  new THREE.Vector2(0.142, 0.02),
                  new THREE.Vector2(0.168, 0.12),
                  new THREE.Vector2(0.158, 0.2),
                  new THREE.Vector2(0.075, 0.24),
                  new THREE.Vector2(0.02, 0.25),
                ],
                20,
              ]}
            />
            <meshStandardMaterial color={hex(cloth)} roughness={0.92} side={THREE.DoubleSide} />
          </mesh>
          {/* shoulders */}
          {[-0.155, 0.155].map((x, i) => (
            <mesh key={i} position={[x, 0.13, 0]} castShadow scale={[1, 0.8, 1]}>
              <sphereGeometry args={[0.062, 12, 10]} />
              <meshStandardMaterial color={hex(cloth)} roughness={0.92} />
            </mesh>
          ))}
          {/* shawl over one shoulder — reads instantly as a pilgrim */}
          <mesh position={[0.08, 0.02, 0.02]} rotation={[0, 0, -0.34]} castShadow>
            <boxGeometry args={[0.055, 0.5, 0.26]} />
            <meshStandardMaterial color={hex(shawl)} roughness={0.95} />
          </mesh>

          {/* arms */}
          {([[-0.2, armL, elbowL], [0.2, armR, elbowR]] as const).map(([x, arm, elbow], i) => (
            <group key={i} position={[x, 0.16, 0]} rotation={[arm, 0, i ? -0.1 : 0.1]}>
              <Limb length={0.3} radius={0.052} color={skin}>
                <group rotation={[-elbow, 0, 0]}>
                  <Limb length={0.29} radius={0.045} color={skin}>
                    <SimpleHand skin={skin} curl={0.45} />
                  </Limb>
                </group>
              </Limb>
            </group>
          ))}

          {/* neck */}
          <mesh position={[0, 0.235, 0]} castShadow>
            <cylinderGeometry args={[0.042, 0.05, 0.07, 10]} />
            <meshStandardMaterial color={hex(skin)} roughness={0.75} />
          </mesh>

          {/* head */}
          <group position={[0, 0.345, 0]} rotation={[-0.04, -chestTwist * 0.5, 0]}>
            <Head skin={skin} />
          </group>

          {carryPot ? (
            // held against the hip, not balanced on the head
            <group position={[0.26, -0.12, 0.1]} rotation={[0.12, 0, -0.18]}>
              <mesh castShadow>
                <cylinderGeometry args={[0.095, 0.12, 0.16, 14]} />
                <meshStandardMaterial color={hex(PALETTE.sienna)} roughness={1} />
              </mesh>
              <mesh position={[0, 0.09, 0]} castShadow>
                <torusGeometry args={[0.095, 0.016, 6, 16]} />
                <meshStandardMaterial color={hex("#5a3a28")} roughness={1} />
              </mesh>
              <mesh position={[0, 0.085, 0]} rotation={[-Math.PI / 2, 0, 0]}>
                <circleGeometry args={[0.088, 14]} />
                <meshStandardMaterial color={hex(PALETTE.turmeric)} roughness={1} />
              </mesh>
            </group>
          ) : null}
        </group>
      </group>
    </group>
  );
};

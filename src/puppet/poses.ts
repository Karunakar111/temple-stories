import type { Pose } from "./rig";

/**
 * Named poses. A shot is written as a timeline of these, not as new drawing.
 * Angles are degrees; positive rotates clockwise in SVG space.
 */

export const IDLE: Pose = {
  armRU: -6, armRL: -14, handR: 0,
  armLU: 7, armLL: 12,
  legRU: 2, legRL: -2, legLU: -2, legLL: 2,
  chest: 0, headTilt: 0, headTurn: 0, rise: 0,
};

export const HOLDING: Pose = {
  ...IDLE,
  armRU: -34, armRL: -46, handR: 10,
  headTilt: 2, headTurn: 1,
};

export const LIFT: Pose = {
  ...IDLE,
  armRU: -118, armRL: -34, handR: -14,
  armLU: 16, armLL: 18,
  chest: -3, headTilt: -5, headTurn: 2, rise: -6,
};

export const SCATTER: Pose = {
  ...IDLE,
  armRU: -142, armRL: 22, handR: -52,
  armLU: 22, armLL: 24,
  chest: -6, headTilt: -8, headTurn: 3, rise: -10,
};

export const BLESS: Pose = {
  ...IDLE,
  armRU: -96, armRL: -8, handR: 0,
  armLU: 10, armLL: 14,
  chest: -1, headTilt: -2,
};

export const WALK_A: Pose = {
  ...IDLE,
  legRU: 26, legRL: -8, legLU: -24, legLL: 30,
  armRU: 20, armRL: -18, armLU: -18, armLL: 20,
  rise: -4,
};

export const WALK_B: Pose = {
  ...IDLE,
  legRU: -24, legRL: 30, legLU: 26, legLL: -8,
  armRU: -18, armRL: 20, armLU: 20, armLL: -18,
  rise: -4,
};

/**
 * Motion helpers for the local-animation experiment.
 *
 * `sine`, `easeInOut`, the irregular blink schedule and `coverCam` are adapted from
 * lubomier/explainer-video-skill, starter/src/motion.ts (MIT License, (c) 2026 Lubomier).
 * The rest is ours.
 */
export const FPS = 30;
export const clamp = (v: number, a: number, b: number) => Math.min(b, Math.max(a, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const sine = (frame: number, periodS: number, phase = 0) =>
  Math.sin((frame / FPS / periodS) * 2 * Math.PI + phase);
export const easeInOut = (t: number) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
export const smoother = (t: number) => {
  const x = clamp(t, 0, 1);
  return x * x * x * (x * (x * 6 - 15) + 10);
};
/** 0 before a, 1 after b, smooth in between (seconds or frames, any unit). */
export const ramp = (v: number, a: number, b: number) => smoother((v - a) / (b - a));

/** Deterministic pseudo-random in [0, 1) from an integer seed. */
export const rand = (seed: number) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

/** Flame flicker: three incommensurate sines plus a slow breath, ~0.75..1.05. */
export const flicker = (frame: number, seed: number) =>
  0.88 +
  0.07 * Math.sin(frame * 0.71 + seed * 3.1) +
  0.05 * Math.sin(frame * 1.37 + seed * 1.7) +
  0.04 * Math.sin(frame * 2.9 + seed * 0.3) +
  0.03 * sine(frame, 2.3, seed);

/** Clamp a pan so a parallax layer never uncovers its edge (from explainer-video-skill). */
export function coverCam(zoom: number, panX: number, depth: number, width: number): [number, number] {
  const layerZoom = 1 + (zoom - 1) * depth;
  const maxPan = Math.max(0, (layerZoom - 1) * width * 0.5);
  return [zoom, clamp(panX, -maxPan, maxPan)];
}

/** Linear interpolation through keyframes [[t, value], ...] (t ascending). */
export function keys(t: number, kf: [number, number][]): number {
  if (t <= kf[0][0]) return kf[0][1];
  for (let i = 1; i < kf.length; i++) {
    if (t <= kf[i][0]) {
      const [t0, v0] = kf[i - 1];
      const [t1, v1] = kf[i];
      return lerp(v0, v1, easeInOut((t - t0) / (t1 - t0)));
    }
  }
  return kf[kf.length - 1][1];
}

/** Mix two #rrggbb colours. */
export function mixHex(a: string, b: string, t: number): string {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const c = pa.map((v, i) => Math.round(lerp(v, pb[i], clamp(t, 0, 1))));
  return `#${c.map((v) => v.toString(16).padStart(2, "0")).join("")}`;
}

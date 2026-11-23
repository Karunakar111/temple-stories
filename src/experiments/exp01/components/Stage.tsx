import React from "react";
import { AbsoluteFill, Img } from "remotion";

/** All approved paintings are 1536 x 2752. Layers are positioned in these art pixels. */
export const ART_W = 1536;
export const ART_H = 2752;
const OUT_W = 1080;
const OUT_H = 1920;
const FIT = Math.max(OUT_W / ART_W, OUT_H / ART_H); // cover

export type Camera = { zoom: number; fx: number; fy: number; panX?: number; panY?: number };

/**
 * Art-space stage. The camera scales about a focal point (fx, fy in art px).
 * Each <Layer depth> moves by its depth: 0 = fixed sky, 1 = the painting plane, >1 = foreground.
 */
const CamCtx = React.createContext<Camera>({ zoom: 1, fx: ART_W / 2, fy: ART_H / 2 });

export const Stage: React.FC<{ camera: Camera; children: React.ReactNode; style?: React.CSSProperties }> = ({
  camera,
  children,
  style,
}) => (
  <AbsoluteFill style={{ backgroundColor: "#140c18", overflow: "hidden", ...style }}>
    <div
      style={{
        position: "absolute",
        width: ART_W,
        height: ART_H,
        left: (OUT_W - ART_W * FIT) / 2,
        top: (OUT_H - ART_H * FIT) / 2,
        transformOrigin: "0 0",
        transform: `scale(${FIT})`,
      }}
    >
      <CamCtx.Provider value={camera}>{children}</CamCtx.Provider>
    </div>
  </AbsoluteFill>
);

export const Layer: React.FC<{
  depth?: number;
  drift?: number; // extra horizontal drift in art px (clouds)
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({ depth = 1, drift = 0, children, style }) => {
  const cam = React.useContext(CamCtx);
  const z = 1 + (cam.zoom - 1) * depth;
  const px = (cam.panX ?? 0) * depth + drift;
  const py = (cam.panY ?? 0) * depth;
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        transformOrigin: `${cam.fx}px ${cam.fy}px`,
        transform: `translate(${px}px, ${py}px) scale(${z})`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};

/** A full-size art image inside a layer (Remotion's Img waits for the decode before the frame is taken). */
export const Art: React.FC<{ src: string; style?: React.CSSProperties }> = ({ src, style }) => (
  <Img src={src} style={{ position: "absolute", left: 0, top: 0, width: ART_W, height: ART_H, ...style }} />
);

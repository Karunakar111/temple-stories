import React from "react";
import { AbsoluteFill } from "remotion";
import { PALETTE } from "../design/palette";

/**
 * English subtitle, top third. Sits over the image, never under it — most of this
 * audience watches with the sound off at least some of the time.
 */
export const Subtitle: React.FC<{ text: string }> = ({ text }) => (
  <AbsoluteFill
    style={{
      justifyContent: "flex-start",
      alignItems: "center",
      paddingTop: 150,
      paddingLeft: 70,
      paddingRight: 70,
    }}
  >
    <div
      style={{
        color: PALETTE.bone,
        fontFamily: "Inter, Helvetica, sans-serif",
        fontSize: 46,
        lineHeight: 1.28,
        fontWeight: 700,
        textAlign: "center",
        letterSpacing: 0.2,
        textShadow: "0 3px 18px rgba(0,0,0,0.85)",
      }}
    >
      {text}
    </div>
  </AbsoluteFill>
);
